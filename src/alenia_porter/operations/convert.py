"""
ConvertOperation — runs a real media conversion via FFmpeg.
"""
from pathlib import Path
from typing import Optional, Callable
from alenia_porter.media.models import Media
from alenia_porter.planner.planner import OperationPlanner
from alenia_porter.jobs.manager import Job, JobProgress
from alenia_porter.errors import (
    IncompatibleOperationError, ConversionError, MediaNotFoundError
)
from alenia_porter.ffmpeg.resolver import default_resolver


class ConvertOperation:
    def __init__(self, media: Media, target_format: str):
        self.media = media
        self.target_format = target_format.lower().lstrip(".")
        self.output_path: Optional[str] = None

    def output(self, path: str) -> "ConvertOperation":
        self.output_path = path
        return self

    def run(self, on_progress: Optional[Callable[[JobProgress], None]] = None) -> bool:
        if not self.output_path:
            raise ValueError("Output path must be set before calling run(). Use .output('file.ext')")

        # Validate input still exists
        if not Path(self.media.path).exists():
            raise MediaNotFoundError(f"Input file not found: {self.media.path}")

        planner = OperationPlanner()
        plan = planner.plan_convert(self.media, self.target_format, self.output_path)

        if not plan.is_valid:
            raise IncompatibleOperationError(plan.error_reason)

        ffmpeg_path = str(default_resolver.ffmpeg_path)
        cmd = [ffmpeg_path, "-y"] + plan.args

        job = Job(
            cmd=cmd,
            total_duration=self.media.duration,
            output_path=Path(self.output_path),
            on_progress=on_progress,
        )

        success = job.run()
        if not success:
            if job.state.value == "cancelled":
                return False
            raise ConversionError(
                f"Conversion to {self.target_format} failed.",
                technical_detail=job.error
            )

        return True
