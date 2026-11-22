"""
Image operations — convert, resize, crop, rotate.

Still images (PNG/JPG/WebP/BMP/TIFF) go through FFmpeg when it is
available, and through Pillow when it is not — Pillow is already a
declared dependency, so the most common conversion no longer needs
FFmpeg at all. Animated GIF and AVIF still require FFmpeg.
"""
from collections.abc import Callable
from pathlib import Path

from fuse.api.result import OperationResult
from fuse.capabilities.policies import TARGET_BY_ID, normalize_format
from fuse.ffmpeg.resolver import default_resolver
from fuse.jobs.manager import Job
from fuse.media.models import Media
from fuse.media.privacy import apply_ffmpeg_privacy

# Still-image targets Pillow can write without FFmpeg.
PILLOW_TARGETS = {"png", "jpg", "jpeg", "webp", "bmp", "tiff"}


def _write_pdf(input_paths: list[Path], output_path: Path, dpi: int = 150) -> "OperationResult":
    """Create a clean, local PDF from one or more raster images."""
    try:
        from PIL import Image as PILImage
        from PIL import ImageOps
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


def _apply_pillow_filters(image, vf_filters: list[str]):
    """Apply the FFmpeg-style filters ImageOperation builds, in Pillow.

    Only the filters this module itself generates are understood
    (scale, crop, transpose, rotate). Anything else raises ValueError
    so the caller can fall back to a clear "needs FFmpeg" error.
    """
    from PIL import Image as PILImage

    for filt in vf_filters:
        for part in filt.split(","):
            part = part.strip()
            if part.startswith("scale="):
                w_s, h_s = part[len("scale="):].split(":")
                width, height = int(w_s), int(h_s)
                if width <= 0 or height <= 0:
                    # FFmpeg -1/-2 means "keep aspect ratio".
                    orig_w, orig_h = image.size
                    if width <= 0 and height > 0:
                        width = round(orig_w * height / orig_h)
                    elif height <= 0 and width > 0:
                        height = round(orig_h * width / orig_w)
                    else:
                        continue
                image = image.resize((width, height))
            elif part.startswith("crop="):
                values = [int(v) for v in part[len("crop="):].split(":")]
                width, height, x, y = (values + [0, 0])[:4]
                image = image.crop((x, y, x + width, y + height))
            elif part == "transpose=1":  # clockwise 90°
                image = image.transpose(PILImage.ROTATE_270)
            elif part == "transpose=2":  # counter-clockwise 90°
                image = image.transpose(PILImage.ROTATE_90)
            elif part.startswith("rotate="):
                degrees = float(part[len("rotate="):].split("*")[0])
                image = image.rotate(-degrees, expand=True)
            else:
                raise ValueError(f"Unsupported image filter for Pillow path: {part}")
    return image


def _convert_with_pillow(input_path: Path, output_path: Path, target: str,
                         vf_filters: list[str]) -> "OperationResult":
    """Convert a still image with Pillow only (no FFmpeg needed)."""
    try:
        from PIL import Image as PILImage
        from PIL import ImageOps
    except ImportError:
        return OperationResult.from_error(
            "Pillow is required for image conversion without FFmpeg. "
            "Install it with: pip install Pillow",
            output_path,
        )
    try:
        with PILImage.open(input_path) as image:
            image = ImageOps.exif_transpose(image)
            image = _apply_pillow_filters(image, vf_filters)
            fmt = "JPEG" if target in {"jpg", "jpeg"} else target.upper()
            if fmt == "JPEG" and image.mode in ("RGBA", "LA", "PA"):
                background = PILImage.new("RGB", image.size, "white")
                background.paste(image, mask=image.getchannel("A") if "A" in image.getbands() else None)
                image = background
            elif fmt == "JPEG":
                image = image.convert("RGB")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            save_kwargs: dict = {}
            if fmt == "JPEG":
                save_kwargs["quality"] = 90
            image.save(output_path, fmt, **save_kwargs)
        return OperationResult.from_success(
            output_path, operation="image", input_path=input_path,
            inspect_output=False,
            warnings=["Converted with Pillow (FFmpeg not available)."],
        )
    except ValueError:
        # Unsupported filter: let the caller explain FFmpeg is needed.
        output_path.unlink(missing_ok=True)
        raise
    except Exception as exc:
        output_path.unlink(missing_ok=True)
        return OperationResult.from_error(f"Pillow image conversion failed: {exc}", output_path)


def _run_image_plan(args: list, output_path: str, input_path: str,
                    on_progress: Callable | None = None) -> "OperationResult":
    from fuse.api.result import OperationResult
    if not default_resolver.is_ffmpeg_available:
        reason = default_resolver.unavailable_reason
        return OperationResult.from_error(
            "FFmpeg is not available. Install it or set FUSE_FFMPEG_DIR."
            + (f" Reason: {reason}" if reason else "")
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
        self._output_path: str | None = None
        self._target_fmt: str | None = None
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

    def run(self, on_progress: Callable | None = None) -> "OperationResult":
        input_path = Path(self.media.path)
        if not input_path.is_file():
            return OperationResult.from_error(f"Input file not found: {self.media.path}")

        target = normalize_format(self._target_fmt or Path(self._output_path or input_path).suffix)

        # PDF is a document export handled by Pillow, not an FFmpeg image
        # target. Handle it before validating the regular image target list.
        if target == "pdf":
            if not self._output_path:
                self._output_path = str(input_path.parent / f"processed_{input_path.stem}.pdf")
            output_path = Path(self._output_path)
            if output_path.resolve() == input_path.resolve():
                return OperationResult.from_error("Input and output paths must be different.")
            return _write_pdf([input_path], output_path, dpi=self._pdf_dpi)

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

        # Still images do not need FFmpeg: Pillow handles them. This check
        # runs first so a machine without FFmpeg still converts PNG/JPG/
        # WebP/BMP/TIFF. GIF (animated) and AVIF stay on the FFmpeg path.
        if target in PILLOW_TARGETS and definition.kind == "image":
            if not default_resolver.is_ffmpeg_available:
                try:
                    return _convert_with_pillow(
                        input_path, output_path, target, self._vf_filters
                    )
                except ValueError as exc:
                    return OperationResult.from_error(
                        f"{exc} Install FFmpeg or use a plain conversion.",
                        output_path,
                    )

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
