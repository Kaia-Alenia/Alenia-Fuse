"""
CompressOperation — compresses media using real FFmpeg strategies.
"""
import os
from pathlib import Path
from typing import Optional, Callable
from alenia_porter.media.models import Media
from alenia_porter.planner.planner import OperationPlanner
from alenia_porter.jobs.manager import Job, JobProgress
from alenia_porter.errors import ConversionError, MediaNotFoundError
from alenia_porter.ffmpeg.resolver import default_resolver


class CompressOperation:
    def __init__(
        self,
        media: Media,
        quality: str = "balanced",
        target_size_mb: Optional[float] = None,
    ):
        self.media = media
        self.quality = quality
        self.target_size_mb = target_size_mb
        self.output_path: Optional[str] = None

    def output(self, path: str) -> "CompressOperation":
        self.output_path = path
        return self

    def run(self, on_progress: Optional[Callable[[JobProgress], None]] = None) -> bool:
        if not self.output_path:
            p = Path(self.media.path)
            self.output_path = str(p.parent / f"compressed_{p.name}")

        if not Path(self.media.path).exists():
            raise MediaNotFoundError(f"Input file not found: {self.media.path}")

        planner = OperationPlanner()
        plan = planner.plan_compress(
            self.media, self.output_path,
            quality=self.quality,
            target_size_mb=self.target_size_mb
        )

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
            raise ConversionError("Compression failed.", technical_detail=job.error)

        return True
