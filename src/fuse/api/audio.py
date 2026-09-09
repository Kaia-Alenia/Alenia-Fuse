"""
Audio API — high-level interface for audio files.

Usage:
    from fuse import Audio

    Audio("song.wav").convert("mp3").run()
    Audio("song.mp3").normalize().output("normalized.mp3").run()
    Audio("song.mp3").volume("+20%").output("louder.mp3").run()
"""
from pathlib import Path

from fuse.errors import MediaAnalysisError, MediaNotFoundError
from fuse.media.models import Media
from fuse.operations.audio import AudioOperation
from fuse.operations.convert import ConvertOperation


class Audio:
    """High-level API for audio files."""

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
        return ConvertOperation(self._media, target_format)

    def volume(self, value: str | float) -> AudioOperation:
        return AudioOperation(self._media).volume(value)

    def normalize(self) -> AudioOperation:
        return AudioOperation(self._media).normalize()

    def fade(self, fade_type: str = "in", duration: float = 3.0) -> AudioOperation:
        return AudioOperation(self._media).fade(fade_type, duration)

    def speed(self, factor: float) -> AudioOperation:
        return AudioOperation(self._media).speed(factor)

    def trim(self, start: str | float, end: str | float | None = None,
             duration: str | float | None = None) -> AudioOperation:
        return AudioOperation(self._media).trim(start, end, duration)
