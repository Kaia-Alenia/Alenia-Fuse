"""
Audio operations — volume, normalize, fade, speed, trim.
"""
from pathlib import Path
from typing import Optional, Callable, Union
from fuse.media.models import Media
from fuse.planner.planner import OperationPlanner
from fuse.jobs.manager import Job, JobProgress
from fuse.errors import ConversionError, MediaNotFoundError, IncompatibleOperationError
from fuse.ffmpeg.resolver import default_resolver
from fuse.media.privacy import apply_ffmpeg_privacy


def _run_audio_plan(operation: str, media: Media, output_path: str,
                    on_progress: Optional[Callable] = None, **kwargs) -> "OperationResult":
    from fuse.api.result import OperationResult
    if not Path(media.path).exists():
        return OperationResult.from_error(f"Input file not found: {media.path}", Path(output_path))
    if not default_resolver.is_ffmpeg_available:
        return OperationResult.from_error(
            "FFmpeg is not available. Install it or set FUSE_FFMPEG_DIR.",
            Path(output_path),
        )

    planner = OperationPlanner()
    plan = planner.plan_audio_op(operation, media, output_path, **kwargs)

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
        return OperationResult.from_error(job.error or f"Audio operation '{operation}' failed.", Path(output_path))
    return OperationResult.from_success(
        Path(output_path), operation=operation, input_path=Path(media.path)
    )


class AudioOperation:
    """Chainable audio operation builder."""

    def __init__(self, media: Media):
        self.media = media
        self._op: Optional[str] = None
        self._kwargs: dict = {}
        self._output_path: Optional[str] = None

    def output(self, path: str) -> "AudioOperation":
        self._output_path = path
        return self

    def run(self, on_progress: Optional[Callable] = None) -> "OperationResult":
        if not self._op:
            raise ValueError("No operation specified.")
        if not self._output_path:
            p = Path(self.media.path)
            self._output_path = str(p.parent / f"{self._op}_{p.name}")
        return _run_audio_plan(self._op, self.media, self._output_path, on_progress, **self._kwargs)

    def volume(self, value: Union[str, float]) -> "AudioOperation":
        """value: '+20%', '0.5', '1.5' etc."""
        self._op = "volume"
        self._kwargs = {"value": str(value)}
        return self

    def normalize(self) -> "AudioOperation":
        self._op = "normalize"
        return self

    def fade(self, fade_type: str = "in", duration: float = 3.0) -> "AudioOperation":
        self._op = "fade"
        self._kwargs = {"fade_type": fade_type, "duration": duration}
        return self

    def speed(self, factor: float) -> "AudioOperation":
        self._op = "speed"
        self._kwargs = {"factor": factor}
        return self

    def trim(self, start: Union[str, float], end: Optional[Union[str, float]] = None,
             duration: Optional[Union[str, float]] = None) -> "AudioOperation":
        self._op = "trim"
        self._kwargs = {"start": start, "end": end, "duration": duration}
        return self
