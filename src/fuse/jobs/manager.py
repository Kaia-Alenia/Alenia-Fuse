"""
Job Manager — tracks real FFmpeg jobs with states, progress, and cancellation.
"""
import os
import signal
import subprocess
import threading
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from fuse.ffmpeg.diagnostics import format_ffmpeg_error


class JobState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobProgress:
    current_time: float = 0.0   # seconds processed so far
    total_time: float = 0.0     # total duration in seconds
    speed: float = 0.0          # realtime speed multiplier (e.g. 1.8x)
    percent: float = 0.0        # 0..100

    def format_time(self, seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    @property
    def current_str(self) -> str:
        return self.format_time(self.current_time)

    @property
    def total_str(self) -> str:
        return self.format_time(self.total_time)


class Job:
    """
    Represents a single FFmpeg operation. Provides real progress and cancellation.
    """

    def __init__(
        self,
        cmd: list[str],
        total_duration: float = 0.0,
        output_path: Path | None = None,
        on_progress: Callable[[JobProgress], None] | None = None,
    ):
        self.cmd = cmd
        self.total_duration = total_duration
        self.output_path = output_path
        self.on_progress = on_progress

        self.state = JobState.PENDING
        self.error: str | None = None
        self._process: subprocess.Popen | None = None
        self._lock = threading.Lock()

    def run(self) -> bool:
        """
        Executes the FFmpeg command and blocks until done or cancelled.
        Returns True on success, False on failure/cancellation.
        """
        self.state = JobState.RUNNING
        progress = JobProgress(total_time=self.total_duration)

        try:
            self._process = subprocess.Popen(
                self.cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                shell=False,
            )

            stderr_lines = []
            for line in self._process.stderr:
                if self.state == JobState.CANCELLED:
                    break

                stderr_lines.append(line)

                # Parse FFmpeg stderr for time info
                # e.g. "frame= 100 fps=25.0 ... time=00:00:04.00 ... speed=1.8x"
                line = line.strip()
                if "time=" in line and "speed=" in line:
                    try:
                        time_part = line.split("time=")[1].split(" ")[0]
                        speed_part = line.split("speed=")[1].split("x")[0].strip()

                        # Parse time HH:MM:SS.ms
                        parts = time_part.split(":")
                        if len(parts) == 3:
                            h, m, s = parts
                            progress.current_time = int(h) * 3600 + int(m) * 60 + float(s)

                        progress.speed = float(speed_part) if speed_part not in ("N/A", "") else 0.0

                        if self.total_duration > 0:
                            progress.percent = min(100.0, (progress.current_time / self.total_duration) * 100)

                        if self.on_progress:
                            self.on_progress(progress)
                    except (ValueError, IndexError):
                        pass

            self._process.wait()

            if self.state == JobState.CANCELLED:
                self._cleanup_output()
                return False

            if self._process.returncode != 0:
                self.state = JobState.FAILED
                self.error = format_ffmpeg_error(
                    "".join(stderr_lines), self._process.returncode
                )
                return False

            # Strict output validation
            if self.output_path:
                out = Path(self.output_path)
                if not out.exists():
                    self.state = JobState.FAILED
                    self.error = "Output file was not created."
                    return False
                    
                if out.stat().st_size == 0:
                    self.state = JobState.FAILED
                    self.error = "Output file is 0 bytes."
                    self._cleanup_output()
                    return False
                    
                # Prevent fake success on pipes
                if out.name.endswith("_pipe"):
                    self.state = JobState.FAILED
                    self.error = "Operation resulted in an invalid pipe output instead of a real file."
                    self._cleanup_output()
                    return False

                # FFprobe validation
                from fuse.ffmpeg.probe import FFprobeError, probe
                try:
                    probe(out)
                except FFprobeError as e:
                    self.state = JobState.FAILED
                    self.error = f"Output file is corrupt or invalid: {e}"
                    self._cleanup_output()
                    return False

            self.state = JobState.COMPLETED
            return True

        except Exception as e:  # noqa: BLE001
            self.state = JobState.FAILED
            self.error = str(e)
            return False

    def cancel(self):
        """Cancel the running job gracefully."""
        with self._lock:
            if self.state == JobState.RUNNING and self._process:
                self.state = JobState.CANCELLED
                try:
                    # Send SIGTERM first for graceful shutdown
                    if os.name == "nt":
                        self._process.terminate()
                    else:
                        self._process.send_signal(signal.SIGTERM)
                except ProcessLookupError:
                    pass

    def _cleanup_output(self):
        """Remove incomplete output file after cancellation."""
        if self.output_path and Path(self.output_path).exists():
            try:
                Path(self.output_path).unlink()
            except OSError:
                pass
