"""
Video API — high-level interface for video files.

Usage:
    from fuse import Video

    Video("movie.mp4").convert("webm").output("movie.webm").run()
    Video("movie.mp4").resize(1280, 720).output("movie_hd.mp4").run()
    Video("movie.mp4").trim("00:01:00", end="00:02:00").output("clip.mp4").run()
"""
from pathlib import Path
from typing import Optional, Union, Callable
from fuse.media.models import Media
from fuse.operations.convert import ConvertOperation
from fuse.operations.compress import CompressOperation
from fuse.operations.video import VideoOperation
from fuse.errors import MediaNotFoundError, MediaAnalysisError


class Video:
    """
    High-level API for video files.
    Automatically inspects the file via FFprobe on construction.
    """

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

    def convert(self, target_format: str) -> ConvertOperation:
        """Convert to another format."""
        return ConvertOperation(self._media, target_format)

    def compress(self, quality: str = "balanced",
                 target_size_mb: Optional[float] = None) -> CompressOperation:
        """Compress the video."""
        return CompressOperation(self._media, quality=quality, target_size_mb=target_size_mb)

    def resize(self, width: int, height: int) -> VideoOperation:
        return VideoOperation(self._media).resize(width, height)

    def crop(self, width: int, height: int, x: int = 0, y: int = 0) -> VideoOperation:
        return VideoOperation(self._media).crop(width, height, x, y)

    def rotate(self, degrees: int) -> VideoOperation:
        return VideoOperation(self._media).rotate(degrees)

    def fps(self, new_fps: float) -> VideoOperation:
        return VideoOperation(self._media).fps(new_fps)

    def speed(self, factor: float) -> VideoOperation:
        return VideoOperation(self._media).speed(factor)

    def trim(self, start: Union[str, float], end: Optional[Union[str, float]] = None,
             duration: Optional[Union[str, float]] = None) -> VideoOperation:
        return VideoOperation(self._media).trim(start, end, duration)

    def mute(self) -> VideoOperation:
        return VideoOperation(self._media).mute()

    def extract_audio(self) -> VideoOperation:
        return VideoOperation(self._media).extract_audio()

    def thumbnail(self, timestamp: str = "00:00:05") -> VideoOperation:
        return VideoOperation(self._media).thumbnail(timestamp)

    def gif(self, start: str = "00:00:00", duration: Union[str, float] = 5,
            fps: int = 10, width: int = 480) -> VideoOperation:
        return VideoOperation(self._media).gif(start, duration, fps, width)

    def remux(self) -> VideoOperation:
        return VideoOperation(self._media).remux()
