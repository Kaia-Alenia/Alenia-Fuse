"""
Image operations — convert, resize, crop, rotate via FFmpeg.
Note: No Pillow dependency. All processing via FFmpeg video filters.
"""
from pathlib import Path
from typing import Optional, Callable
from alenia_porter.media.models import Media
from alenia_porter.planner.planner import OperationPlanner
from alenia_porter.jobs.manager import Job, JobProgress
from alenia_porter.errors import ConversionError, MediaNotFoundError, IncompatibleOperationError
from alenia_porter.ffmpeg.resolver import default_resolver


def _run_image_plan(args: list, output_path: str,
                    on_progress: Optional[Callable] = None) -> bool:
    ffmpeg_path = str(default_resolver.ffmpeg_path)
    cmd = [ffmpeg_path, "-y"] + args

    job = Job(
        cmd=cmd,
        total_duration=0,   # images have no duration
        output_path=Path(output_path),
        on_progress=on_progress,
    )

    success = job.run()
    if not success:
        raise ConversionError("Image operation failed.", technical_detail=job.error)
    return True


class ImageOperation:
    """Chainable image operation builder using FFmpeg."""

    def __init__(self, media: Media):
        self.media = media
        self._vf_filters: list = []
        self._output_path: Optional[str] = None
        self._target_fmt: Optional[str] = None

    def output(self, path: str) -> "ImageOperation":
        self._output_path = path
        return self

    def resize(self, width: int, height: int) -> "ImageOperation":
        self._vf_filters.append(f"scale={width}:{height}")
        return self

    def crop(self, width: int, height: int, x: int = 0, y: int = 0) -> "ImageOperation":
        self._vf_filters.append(f"crop={width}:{height}:{x}:{y}")
        return self

    def rotate(self, degrees: int) -> "ImageOperation":
        rotation_map = {90: "transpose=1", 180: "transpose=1,transpose=1", 270: "transpose=2"}
        self._vf_filters.append(rotation_map.get(degrees % 360, f"rotate={degrees}*PI/180"))
        return self

    def convert(self, target_format: str) -> "ImageOperation":
        self._target_fmt = target_format.lower().lstrip(".")
        return self

    def run(self, on_progress: Optional[Callable] = None) -> bool:
        if not Path(self.media.path).exists():
            raise MediaNotFoundError(f"Input file not found: {self.media.path}")

        if not self._output_path:
            p = Path(self.media.path)
            ext = f".{self._target_fmt}" if self._target_fmt else p.suffix
            self._output_path = str(p.parent / f"processed_{p.stem}{ext}")

        args = ["-i", self.media.path]

        if self._vf_filters:
            args += ["-vf", ",".join(self._vf_filters)]

        args += ["-vframes", "1", self._output_path]

        return _run_image_plan(args, self._output_path, on_progress)
