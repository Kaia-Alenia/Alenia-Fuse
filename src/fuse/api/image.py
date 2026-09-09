"""
Image API — high-level interface for image files via FFmpeg.

Usage:
    from fuse import Image

    Image("photo.png").convert("webp").output("photo.webp").run()
    Image("photo.jpg").resize(1920, 1080).output("resized.jpg").run()
"""
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fuse.api.result import OperationResult

from fuse.errors import MediaAnalysisError, MediaNotFoundError
from fuse.media.models import Media
from fuse.operations.image import ImageOperation


class Image:
    """High-level API for image files (via FFmpeg, no Pillow required)."""

    def __init__(self, path: str):
        if not Path(path).is_file():
            raise MediaNotFoundError(f"File not found: {path}")
        try:
            self._media = Media.inspect(path)
        except Exception as e:
            raise MediaAnalysisError(f"Cannot analyze '{path}': {e}", technical_detail=str(e))

    @property
    def info(self) -> Media:
        return self._media

    def convert(self, target_format: str) -> "ImageOperation":
        return ImageOperation(self._media).convert(target_format)

    def to_pdf(self, output: str, dpi: int = 150) -> "OperationResult":
        """Export this image as a readable PDF using a local Pillow pipeline."""
        return ImageOperation(self._media).pdf(dpi).output(output).run()

    def resize(self, width: int, height: int) -> ImageOperation:
        return ImageOperation(self._media).resize(width, height)

    def crop(self, width: int, height: int, x: int = 0, y: int = 0) -> ImageOperation:
        return ImageOperation(self._media).crop(width, height, x, y)

    def rotate(self, degrees: int) -> ImageOperation:
        return ImageOperation(self._media).rotate(degrees)
