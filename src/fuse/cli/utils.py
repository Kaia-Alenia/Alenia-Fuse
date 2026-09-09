"""
Shared CLI helpers used by all command modules.
"""
import sys
from pathlib import Path
from typing import List, Optional, Callable

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
    from fuse.errors import MediaNotFoundError, MediaAnalysisError
    from fuse.media.models import Media

    if not Path(file).exists():
        raise MediaNotFoundError(f"File not found: {file}")

    try:
        return Media.inspect(file)
    except Exception as exc:
        raise MediaAnalysisError(f"Cannot analyze '{file}': {exc}") from exc


def resolve_inputs(input_path: str) -> List:
    """
    Returns a list of Media objects from a file path or directory.
    For directories, scans recursively (delegating to batch.scan_directory).
    Invalid/non-media files are silently skipped in batch mode; single-file
    mode raises on failure so the user sees a clear error.
    """
    from fuse.media.models import Media

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


def build_progress_callback(label: str, total_duration: float) -> Optional[Callable]:
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

def _video_op(operation: str, file: str, output: Optional[str],
              on_progress_label: str, **kwargs) -> int:
    """
    Plan and execute a video operation via the OperationPlanner + Job.
    Returns exit code (0 = success, 1 = failure).
    """
    from pathlib import Path as _Path
    try:
        media = require_file(file)

        if not output:
            p = _Path(file)
            output = str(p.parent / f"{operation}_{p.name}")

        if not confirm_overwrite(output):
            print(t("cli.cancelled"))
            return 0

        print(t("operations.starting", operation=operation.capitalize(), input=file, output=output))

        from fuse.planner.planner import OperationPlanner
        from fuse.jobs.manager import Job
        from fuse.ffmpeg.resolver import default_resolver

        planner = OperationPlanner()
        plan = planner.plan_video_op(operation, media, output, **kwargs)

        if not plan.is_valid:
            print(t("errors.cannot_perform", error=plan.error_reason), file=sys.stderr)
            return 1

        progress_cb = build_progress_callback(on_progress_label, media.duration)
        cmd = [str(default_resolver.ffmpeg_path), "-y"] + apply_ffmpeg_privacy(plan.args)
        job = Job(cmd=cmd, total_duration=media.duration,
                  output_path=_Path(output), on_progress=progress_cb)

        try:
            success = job.run()
        except KeyboardInterrupt:
            job.cancel()
            print(t("cli.cancelled"), file=sys.stderr)
            return 0

        finish_progress()
        if success:
            print(t("operations.done", output=output))
        elif job.error:
            print(t("errors.operation", error=job.error), file=sys.stderr)
        return 0 if success else 1

    except Exception as exc:
        print(t("errors.operation", error=friendly_error(exc)), file=sys.stderr)
        return 1


def _audio_op(operation: str, file: str, output: Optional[str],
              label: str, **kwargs) -> int:
    """
    Plan and execute an audio operation via the OperationPlanner + Job.
    Returns exit code (0 = success, 1 = failure).
    """
    from pathlib import Path as _Path
    try:
        media = require_file(file)

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

        from fuse.planner.planner import OperationPlanner
        from fuse.jobs.manager import Job
        from fuse.ffmpeg.resolver import default_resolver

        planner = OperationPlanner()
        plan = planner.plan_audio_op(operation, media, output, **kwargs)

        if not plan.is_valid:
            print(t("errors.cannot_perform", error=plan.error_reason), file=sys.stderr)
            return 1

        progress_cb = build_progress_callback(label, media.duration)
        cmd = [str(default_resolver.ffmpeg_path), "-y"] + apply_ffmpeg_privacy(plan.args)
        job = Job(cmd=cmd, total_duration=media.duration,
                  output_path=_Path(output), on_progress=progress_cb)

        try:
            success = job.run()
        except KeyboardInterrupt:
            job.cancel()
            print(t("cli.cancelled"), file=sys.stderr)
            return 0

        finish_progress()
        if success:
            print(t("operations.done", output=output))
        elif job.error:
            print(t("errors.operation", error=job.error), file=sys.stderr)
        return 0 if success else 1

    except Exception as exc:
        print(t("errors.operation", error=friendly_error(exc)), file=sys.stderr)
        return 1
