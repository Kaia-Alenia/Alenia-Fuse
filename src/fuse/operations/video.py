"""
Video operations — resize, crop, rotate, fps, speed, trim, mute, extract_audio, thumbnail, gif.
"""
from collections.abc import Callable
from pathlib import Path

from fuse.ffmpeg.resolver import default_resolver
from fuse.jobs.manager import Job
from fuse.media.models import Media
from fuse.media.privacy import apply_ffmpeg_privacy
from fuse.planner.planner import OperationPlanner


def _run_plan(operation: str, media: Media, output_path: str,
              on_progress: Callable | None = None, **kwargs) -> "OperationResult":
    from fuse.api.result import OperationResult
    if not Path(media.path).exists():
        return OperationResult.from_error(f"Input file not found: {media.path}", Path(output_path))
    if not default_resolver.is_ffmpeg_available:
        return OperationResult.from_error(
            "FFmpeg is not available. Install it or set FUSE_FFMPEG_DIR.",
            Path(output_path),
        )

    planner = OperationPlanner()
    plan = planner.plan_video_op(operation, media, output_path, **kwargs)

    if not plan.is_valid:
        return OperationResult.from_error(plan.error_reason, Path(output_path))

    ffmpeg_path = str(default_resolver.ffmpeg_path)
    cmd = [ffmpeg_path, "-y"] + apply_ffmpeg_privacy(plan.args)

    job = Job(
        cmd=cmd,
        total_duration=media.duration,
        output_path=Path(output_path),
        on_progress=on_progress,
    )

    success = job.run()
    if not success:
        if job.state.value == "cancelled":
            return OperationResult.from_error("Operation cancelled.", Path(output_path))
        return OperationResult.from_error(job.error or f"Video operation '{operation}' failed.", Path(output_path))
    return OperationResult.from_success(
        Path(output_path), operation=operation, input_path=Path(media.path)
    )


class VideoOperation:
    """Chainable video operation builder."""

    def __init__(self, media: Media):
        self.media = media
        self._op: str | None = None
        self._kwargs: dict = {}
        self._output_path: str | None = None

    def output(self, path: str) -> "VideoOperation":
        self._output_path = path
        return self

    def run(self, on_progress: Callable | None = None) -> "OperationResult":
        if not self._op:
            raise ValueError("No operation specified.")
        if not self._output_path:
            p = Path(self.media.path)
            self._output_path = str(p.parent / f"{self._op}_{p.name}")
        return _run_plan(self._op, self.media, self._output_path, on_progress, **self._kwargs)

    def resize(self, width: int, height: int) -> "VideoOperation":
        self._op = "resize"
        self._kwargs = {"width": width, "height": height}
        return self

    def crop(self, width: int, height: int, x: int = 0, y: int = 0) -> "VideoOperation":
        self._op = "crop"
        self._kwargs = {"width": width, "height": height, "x": x, "y": y}
        return self

    def rotate(self, degrees: int) -> "VideoOperation":
        self._op = "rotate"
        self._kwargs = {"degrees": degrees}
        return self

    def fps(self, new_fps: float) -> "VideoOperation":
        self._op = "fps"
        self._kwargs = {"fps": new_fps}
        return self

    def speed(self, factor: float) -> "VideoOperation":
        self._op = "speed"
        self._kwargs = {"factor": factor}
        return self

    def trim(self, start: str | float, end: str | float | None = None,
             duration: str | float | None = None) -> "VideoOperation":
        self._op = "trim"
        self._kwargs = {"start": start, "end": end, "duration": duration}
        return self

    def mute(self) -> "VideoOperation":
        self._op = "mute"
        return self

    def extract_audio(self) -> "VideoOperation":
        self._op = "extract_audio"
        return self

    def thumbnail(self, timestamp: str = "00:00:05") -> "VideoOperation":
        self._op = "thumbnail"
        self._kwargs = {"timestamp": timestamp}
        return self

    def gif(self, start: str = "00:00:00", duration: str | float = 5,
            fps: int = 10, width: int = 480) -> "VideoOperation":
        self._op = "gif"
        self._kwargs = {"start": start, "duration": duration, "fps": fps, "width": width}
        return self

    def remux(self) -> "VideoOperation":
        self._op = "remux"
        return self
