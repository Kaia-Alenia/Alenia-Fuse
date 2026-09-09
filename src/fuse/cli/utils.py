"""
Shared CLI helpers used by all command modules.
"""
import sys
from collections.abc import Callable
from pathlib import Path

from fuse.errors import friendly_error  # noqa: re-exported for command modules
from fuse.i18n.manager import t
from fuse.media.privacy import apply_ffmpeg_privacy

# ── Media resolution ──────────────────────────────────────────────────────────

def require_file(file: str):
    """
    Load and return a Media object for the given path.
    Raises MediaNotFoundError if the file does not exist.
    Raises MediaAnalysisError if ffprobe cannot read it.
    """
    from fuse.errors import MediaAnalysisError, MediaNotFoundError
    from fuse.media.models import Media

    if not Path(file).exists():
        raise MediaNotFoundError(f"File not found: {file}")

    try:
        return Media.inspect(file)
    except Exception as exc:
        raise MediaAnalysisError(f"Cannot analyze '{file}': {exc}") from exc


def resolve_inputs(input_path: str) -> list:
    """
    Returns a list of Media objects from a file path or directory.
    For directories, scans recursively (delegating to batch.scan_directory).
    Invalid/non-media files are silently skipped in batch mode; single-file
    mode raises on failure so the user sees a clear error.
    """

    p = Path(input_path)

    if p.is_dir():
        from fuse.cli.batch import scan_directory
        return scan_directory(str(p))

    if not p.exists():
        from fuse.errors import MediaNotFoundError
        raise MediaNotFoundError(f"File not found: {input_path}")

    return [require_file(input_path)]


# ── Confirmation prompt ───────────────────────────────────────────────────────

def confirm_overwrite(path: str) -> bool:
    """
    Returns True when it is safe to write to path.
    If the file already exists, asks the user for confirmation.
    Skips prompt and returns True when path does not exist yet.
    """
    if not Path(path).exists():
        return True

    try:
        answer = input(f"\n  File already exists: {path}\n  Overwrite? [y/N] ").strip().lower()
        return answer in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        print()
        return False


# ── Progress display ──────────────────────────────────────────────────────────

# Module-level state so finish_progress() can clear the last line.
_last_progress_len: int = 0


def build_progress_callback(label: str, total_duration: float) -> Callable | None:
    """
    Returns a callback that prints a Rich-style inline progress line.
    When total_duration is 0 a spinner-only line is used instead.
    """
    try:
        from rich.console import Console
        _console = Console(stderr=True, highlight=False)
    except ImportError:
        _console = None

    def _cb(progress) -> None:
        global _last_progress_len

        if total_duration and total_duration > 0:
            pct = min(100.0, (progress.current_time / total_duration) * 100)
            bar_w = 20
            filled = int(bar_w * pct / 100)
            bar = "█" * filled + "░" * (bar_w - filled)
            speed = f"{progress.speed:.1f}x" if progress.speed else "…"
            line = f"  {label} [{bar}] {pct:5.1f}%  {speed}"
        else:
            line = f"  {label} … {progress.current_str}"

        if _console:
            _console.print(f"\r{line}", end="", soft_wrap=True)
        else:
            sys.stderr.write(f"\r{line}")
            sys.stderr.flush()

        _last_progress_len = len(line)

    return _cb


def finish_progress() -> None:
    """Clear the inline progress line after a job completes."""
    global _last_progress_len
    if _last_progress_len:
        sys.stderr.write("\r" + " " * (_last_progress_len + 4) + "\r")
        sys.stderr.flush()
        _last_progress_len = 0


# ── Shared FFmpeg dispatch ────────────────────────────────────────────────────

def _video_op(operation: str, file: str, output: str | None,
              on_progress_label: str, **kwargs) -> int:
    """
    Plan and execute a video operation via the OperationPlanner + Job.
    Returns exit code (0 = success, 1 = failure).
    """
    from pathlib import Path as _Path
    try:
        # Use the public API for operations that it exposes. The CLI must be
        # a presentation layer, not a second implementation of Fuse.
        from fuse import Video
        video = Video(file)
        media = video.info

        if not output:
            p = _Path(file)
            output = str(p.parent / f"{operation}_{p.name}")

        if not confirm_overwrite(output):
            print(t("cli.cancelled"))
            return 0

        print(t("operations.starting", operation=operation.capitalize(), input=file, output=output))

        progress_cb = build_progress_callback(on_progress_label, media.duration)
        operation_builders = {
            "resize": lambda: video.resize(kwargs["width"], kwargs["height"]),
            "crop": lambda: video.crop(kwargs["width"], kwargs["height"], kwargs.get("x", 0), kwargs.get("y", 0)),
            "rotate": lambda: video.rotate(kwargs["degrees"]),
            "fps": lambda: video.fps(kwargs["fps"]),
            "speed": lambda: video.speed(kwargs["factor"]),
            "trim": lambda: video.trim(kwargs.get("start", "00:00:00"), kwargs.get("end"), kwargs.get("duration")),
            "cut": lambda: video.trim(kwargs.get("start", "00:00:00"), kwargs.get("end"), kwargs.get("duration")),
            "mute": video.mute,
            "extract_audio": video.extract_audio,
            "thumbnail": lambda: video.thumbnail(kwargs.get("timestamp", "00:00:05")),
            "gif": lambda: video.gif(kwargs.get("start", "00:00:00"), kwargs.get("duration", 5), kwargs.get("fps", 10), kwargs.get("width", 480)),
            "remux": video.remux,
        }

        if operation in operation_builders:
            result = operation_builders[operation]().output(output).run(on_progress=progress_cb)
        else:
            # Advanced commands not yet exposed by Video remain on the shared
            # planner path until their public API methods are added.
            from fuse.ffmpeg.resolver import default_resolver
            from fuse.jobs.manager import Job
            from fuse.planner.planner import OperationPlanner
            planner = OperationPlanner()
            plan = planner.plan_video_op(operation, media, output, **kwargs)
            if not plan.is_valid:
                print(t("errors.cannot_perform", error=plan.error_reason), file=sys.stderr)
                return 1
            cmd = [str(default_resolver.ffmpeg_path), "-y"] + apply_ffmpeg_privacy(plan.args)
            result_job = Job(cmd=cmd, total_duration=media.duration,
                             output_path=_Path(output), on_progress=progress_cb)
            success = result_job.run()
            result = None

        finish_progress()
        if result is not None and result.success:
            print(t("operations.done", output=output))
            return 0
        if result is None and success:
            print(t("operations.done", output=output))
            return 0
        error = result.error if result is not None else result_job.error
        if error:
            print(t("errors.operation", error=error), file=sys.stderr)
        return 1

    except Exception as exc:
        print(t("errors.operation", error=friendly_error(exc)), file=sys.stderr)
        return 1


def _audio_op(operation: str, file: str, output: str | None,
              label: str, **kwargs) -> int:
    """
    Plan and execute an audio operation via the OperationPlanner + Job.
    Returns exit code (0 = success, 1 = failure).
    """
    from pathlib import Path as _Path
    try:
        from fuse import Audio
        audio = Audio(file)
        media = audio.info

        if not media.main_audio:
            print(t("errors.no_audio_stream"), file=sys.stderr)
            return 1

        if not output:
            p = _Path(file)
            output = str(p.parent / f"{operation}_{p.name}")

        if not confirm_overwrite(output):
            print(t("cli.cancelled"))
            return 0

        print(t("operations.starting", operation=label, input=file, output=output))

        progress_cb = build_progress_callback(label, media.duration)
        operation_builders = {
            "volume": lambda: audio.volume(kwargs["value"]),
            "normalize": audio.normalize,
            "fade": lambda: audio.fade(kwargs.get("fade_type", "in"), kwargs.get("duration", 3.0)),
            "speed": lambda: audio.speed(kwargs["factor"]),
            "trim": lambda: audio.trim(kwargs.get("start", "00:00:00"), kwargs.get("end"), kwargs.get("duration")),
        }
        if operation not in operation_builders:
            print(t("errors.cannot_perform", error=f"Unsupported audio operation: {operation}"), file=sys.stderr)
            return 1

        result = operation_builders[operation]().output(output).run(on_progress=progress_cb)

        finish_progress()
        if result.success:
            print(t("operations.done", output=output))
            return 0
        if result.error:
            print(t("errors.operation", error=result.error), file=sys.stderr)
        return 1

    except Exception as exc:
        print(t("errors.operation", error=friendly_error(exc)), file=sys.stderr)
        return 1
