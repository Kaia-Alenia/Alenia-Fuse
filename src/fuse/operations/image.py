"""
Image operations — convert, resize, crop, rotate via FFmpeg.
Note: No Pillow dependency. All processing via FFmpeg video filters.
"""
from pathlib import Path
from typing import Optional, Callable
from fuse.media.models import Media
from fuse.jobs.manager import Job, JobProgress
from fuse.api.result import OperationResult
from fuse.capabilities.policies import TARGET_BY_ID, normalize_format
from fuse.ffmpeg.resolver import default_resolver
from fuse.media.privacy import apply_ffmpeg_privacy


def _write_pdf(input_paths: list[Path], output_path: Path, dpi: int = 150) -> "OperationResult":
    """Create a clean, local PDF from one or more raster images."""
    try:
        from PIL import Image as PILImage, ImageOps
    except ImportError:
        return OperationResult.from_error(
            "PDF export requires Pillow. Install it with: pip install Pillow",
            output_path,
        )

    pages = []
    try:
        for source in input_paths:
            with PILImage.open(source) as image:
                image = ImageOps.exif_transpose(image)
                if image.mode in ("RGBA", "LA") or "transparency" in image.info:
                    rgba = image.convert("RGBA")
                    background = PILImage.new("RGB", rgba.size, "white")
                    background.paste(rgba, mask=rgba.getchannel("A"))
                    page = background
                else:
                    page = image.convert("RGB")
                pages.append(page.copy())

        if not pages:
            return OperationResult.from_error("At least one image is required for PDF export.", output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        first, *rest = pages
        first.save(output_path, "PDF", save_all=True, append_images=rest,
                   resolution=max(72, int(dpi)))
        return OperationResult.from_success(
            output_path, operation="image_to_pdf", input_path=input_paths[0],
            inspect_output=False,
        )
    except Exception as exc:
        output_path.unlink(missing_ok=True)
        return OperationResult.from_error(f"PDF export failed: {exc}", output_path)
    finally:
        for page in pages:
            page.close()


def _run_image_plan(args: list, output_path: str, input_path: str,
                    on_progress: Optional[Callable] = None) -> "OperationResult":
    from fuse.api.result import OperationResult
    if not default_resolver.is_ffmpeg_available:
        return OperationResult.from_error(
            "FFmpeg is not available. Install it or set FUSE_FFMPEG_DIR."
        )
    ffmpeg_path = str(default_resolver.ffmpeg_path)
    cmd = [ffmpeg_path, "-y"] + apply_ffmpeg_privacy(args)

    job = Job(
        cmd=cmd,
        total_duration=0,   # images have no duration
        output_path=Path(output_path),
        on_progress=on_progress,
    )

    success = job.run()
    if not success:
        return OperationResult.from_error(job.error or "Image operation failed.", Path(output_path))
    return OperationResult.from_success(
        Path(output_path), operation="image", input_path=Path(input_path)
    )


class ImageOperation:
    """Chainable image operation builder using FFmpeg."""

    def __init__(self, media: Media):
        self.media = media
        self._vf_filters: list = []
        self._output_path: Optional[str] = None
        self._target_fmt: Optional[str] = None
        self._pdf_dpi: int = 150

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

    def pdf(self, dpi: int = 150) -> "ImageOperation":
        self._target_fmt = "pdf"
        self._pdf_dpi = max(72, int(dpi))
        return self

    def run(self, on_progress: Optional[Callable] = None) -> "OperationResult":
        input_path = Path(self.media.path)
        if not input_path.is_file():
            return OperationResult.from_error(f"Input file not found: {self.media.path}")

        target = normalize_format(self._target_fmt or Path(self._output_path or input_path).suffix)
        definition = TARGET_BY_ID.get(target)
        if not definition or definition.kind not in {"image", "animated_image"}:
            return OperationResult.from_error(
                f"Unsupported image target '{target}'. Use a supported image format."
            )

        if not self._output_path:
            p = input_path
            ext = f".{target}"
            self._output_path = str(p.parent / f"processed_{p.stem}{ext}")

        output_path = Path(self._output_path)
        if output_path.resolve() == input_path.resolve():
            return OperationResult.from_error("Input and output paths must be different.")

        if target == "pdf":
            return _write_pdf([input_path], output_path, dpi=self._pdf_dpi)

        args = ["-i", str(input_path)]

        if self._vf_filters:
            args += ["-vf", ",".join(self._vf_filters)]

        encoder = {
            "webp": "libwebp", "jpg": "mjpeg", "png": "png", "avif": "libaom-av1",
            "bmp": "bmp", "tiff": "tiff", "gif": "gif", "webp_animated": "libwebp",
            "apng": "apng",
        }.get(target)
        if encoder:
            args += ["-c:v", encoder]
        if definition.kind == "image":
            args += ["-frames:v", "1"]
        args += [str(output_path)]

        return _run_image_plan(args, str(output_path), str(input_path), on_progress)
