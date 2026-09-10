"""
Alenia Fuse — Public Python API

Usage:
    from fuse import Video, Audio, Image, Media

    Video("movie.mp4").convert("webm").output("movie.webm").run()
    Audio("song.wav").convert("mp3").run()
    info = Media.inspect("file.mp4")
"""
from fuse.api.audio import Audio
from fuse.api.image import Image
from fuse.api.result import OperationResult
from fuse.api.video import Video
from fuse.media.models import Media, Stream

__version__ = "2.0.1"

__all__ = ["Audio", "Image", "Media", "OperationResult", "Stream", "Video"]
