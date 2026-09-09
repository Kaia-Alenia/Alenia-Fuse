"""
ConvertOperation — runs a real media conversion via FFmpeg.
"""
from pathlib import Path
from typing import Optional, Callable
from fuse.media.models import Media
from fuse.planner.planner import OperationPlanner
from fuse.jobs.manager import Job, JobProgress
from fuse.errors import (
    IncompatibleOperationError, ConversionError, MediaNotFoundError
)
from fuse.ffmpeg.resolver import default_resolver
from fuse.capabilities.policies import normalize_format
from fuse.media.privacy import apply_ffmpeg_privacy


class ConvertOperation:
    def __init__(self, media: Media, target_format: str):
        self.media = media
        self.target_format = normalize_format(target_format)
        self.output_path: Optional[str] = None

    def output(self, path: str) -> "ConvertOperation":
        self.output_path = path
        return self

    def run(self, on_progress: Optional[Callable[[JobProgress], None]] = None) -> "OperationResult":
        from fuse.api.result import OperationResult
        if not self.output_path:
            raise ValueError("Output path must be set before calling run(). Use .output('file.ext')")
            
        in_p = Path(self.media.path).resolve()
        out_p = Path(self.output_path).resolve()
        
        if in_p == out_p:
            return OperationResult.from_error("Input and output paths cannot be identical (would overwrite input).", Path(self.output_path))

        # Validate input still exists
        if not in_p.exists():
            return OperationResult.from_error(f"Input file not found: {self.media.path}", Path(self.output_path))
        if not default_resolver.is_ffmpeg_available:
            return OperationResult.from_error(
            "FFmpeg is not available. Install it or set FUSE_FFMPEG_DIR.",
                Path(self.output_path),
            )

        planner = OperationPlanner()
        plan = planner.plan_convert(self.media, self.target_format, self.output_path)

        if not plan.is_valid:
            return OperationResult.from_error(plan.error_reason, Path(self.output_path))

        if getattr(plan, "needs_preflight", False):
            if not planner.preflight_check(plan):
                return OperationResult.from_error(plan.error_reason or "Preflight check failed. This format conversion is not supported.", Path(self.output_path))

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
            return OperationResult.from_error(job.error or f"Conversion to {self.target_format} failed.", Path(self.output_path))

        return OperationResult.from_success(
            Path(self.output_path), operation=f"convert:{self.target_format}",
            input_path=Path(self.media.path)
        )
