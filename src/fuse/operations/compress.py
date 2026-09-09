"""
CompressOperation — compresses media using real FFmpeg strategies.
"""
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fuse.api.result import OperationResult

from fuse.ffmpeg.resolver import default_resolver
from fuse.jobs.manager import Job, JobProgress
from fuse.media.models import Media
from fuse.media.privacy import apply_ffmpeg_privacy
from fuse.planner.planner import OperationPlanner


class CompressOperation:
    def __init__(
        self,
        media: Media,
        quality: str = "balanced",
        target_size_mb: float | None = None,
    ):
        self.media = media
        self.quality = quality
        self.target_size_mb = target_size_mb
        self.output_path: str | None = None

    def output(self, path: str) -> "CompressOperation":
        self.output_path = path
        return self

    def run(self, on_progress: Callable[[JobProgress], None] | None = None) -> "OperationResult":
        from fuse.api.result import OperationResult
        if not self.output_path:
            p = Path(self.media.path)
            self.output_path = str(p.parent / f"compressed_{p.name}")

        in_p = Path(self.media.path).resolve()
        out_p = Path(self.output_path).resolve()
        
        if in_p == out_p:
            return OperationResult.from_error("Input and output paths cannot be identical (would overwrite input).", Path(self.output_path))

        if not in_p.exists():
            return OperationResult.from_error(f"Input file not found: {self.media.path}", Path(self.output_path))
        if not default_resolver.is_ffmpeg_available:
            return OperationResult.from_error(
                "FFmpeg is not available. Install it or set FUSE_FFMPEG_DIR.",
                Path(self.output_path),
            )

        planner = OperationPlanner()
        plan = planner.plan_compress(
            self.media, self.output_path,
            quality=self.quality,
            target_size_mb=self.target_size_mb
        )

        ffmpeg_path = str(default_resolver.ffmpeg_path)
        cmd = [ffmpeg_path, "-y"] + apply_ffmpeg_privacy(plan.args)

        job = Job(
            cmd=cmd,
            total_duration=self.media.duration,
            output_path=Path(self.output_path),
            on_progress=on_progress,
        )

        success = job.run()
        if not success:
            if job.state.value == "cancelled":
                return OperationResult.from_error("Operation cancelled.", Path(self.output_path))
            return OperationResult.from_error(job.error or "Compression failed.", Path(self.output_path))

        return OperationResult.from_success(
            Path(self.output_path), operation="compress", input_path=Path(self.media.path)
        )
