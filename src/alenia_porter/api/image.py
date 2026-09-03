"""
Image API — high-level interface for image files via FFmpeg.

Usage:
    from alenia_porter import Image

    Image("photo.png").convert("webp").output("photo.webp").run()
    Image("photo.jpg").resize(1920, 1080).output("resized.jpg").run()
"""
from pathlib import Path
from typing import Optional
from alenia_porter.media.models import Media
from alenia_porter.operations.convert import ConvertOperation
from alenia_porter.operations.image import ImageOperation
from alenia_porter.errors import MediaNotFoundError, MediaAnalysisError


class Image:
    """High-level API for image files (via FFmpeg, no Pillow required)."""

    def __init__(self, path: str):
        if not Path(path).exists():
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

    def resize(self, width: int, height: int) -> ImageOperation:
        return ImageOperation(self._media).resize(width, height)

    def crop(self, width: int, height: int, x: int = 0, y: int = 0) -> ImageOperation:
        return ImageOperation(self._media).crop(width, height, x, y)

    def rotate(self, degrees: int) -> ImageOperation:
        return ImageOperation(self._media).rotate(degrees)
