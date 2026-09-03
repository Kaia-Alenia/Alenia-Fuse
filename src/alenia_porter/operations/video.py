"""
Video operations — resize, crop, rotate, fps, speed, trim, mute, extract_audio, thumbnail, gif.
"""
from pathlib import Path
from typing import Optional, Callable, Union
from alenia_porter.media.models import Media
from alenia_porter.planner.planner import OperationPlanner
from alenia_porter.jobs.manager import Job, JobProgress
from alenia_porter.errors import ConversionError, MediaNotFoundError, IncompatibleOperationError
from alenia_porter.ffmpeg.resolver import default_resolver


def _run_plan(operation: str, media: Media, output_path: str,
              on_progress: Optional[Callable] = None, **kwargs) -> bool:
    if not Path(media.path).exists():
        raise MediaNotFoundError(f"Input file not found: {media.path}")

    planner = OperationPlanner()
    plan = planner.plan_video_op(operation, media, output_path, **kwargs)

    if not plan.is_valid:
        raise IncompatibleOperationError(plan.error_reason)

    ffmpeg_path = str(default_resolver.ffmpeg_path)
    cmd = [ffmpeg_path, "-y"] + plan.args

    job = Job(
        cmd=cmd,
        total_duration=media.duration,
        output_path=Path(output_path),
        on_progress=on_progress,
    )

    success = job.run()
    if not success:
        if job.state.value == "cancelled":
            return False
        raise ConversionError(f"Video operation '{operation}' failed.", technical_detail=job.error)
    return True


class VideoOperation:
    """Chainable video operation builder."""

    def __init__(self, media: Media):
        self.media = media
        self._op: Optional[str] = None
        self._kwargs: dict = {}
        self._output_path: Optional[str] = None

    def output(self, path: str) -> "VideoOperation":
        self._output_path = path
        return self

    def run(self, on_progress: Optional[Callable] = None) -> bool:
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

    def trim(self, start: Union[str, float], end: Optional[Union[str, float]] = None,
             duration: Optional[Union[str, float]] = None) -> "VideoOperation":
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

    def gif(self, start: str = "00:00:00", duration: Union[str, float] = 5,
            fps: int = 10, width: int = 480) -> "VideoOperation":
        self._op = "gif"
        self._kwargs = {"start": start, "duration": duration, "fps": fps, "width": width}
        return self

    def remux(self) -> "VideoOperation":
        self._op = "remux"
        return self
