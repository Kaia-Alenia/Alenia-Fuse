"""
Alenia Porter — Public Python API

Usage:
    from alenia_porter import Video, Audio, Image, Media

    Video("movie.mp4").convert("webm").output("movie.webm").run()
    Audio("song.wav").convert("mp3").run()
    info = Media.inspect("file.mp4")
"""
from alenia_porter.media.models import Media, Stream
from alenia_porter.api.video import Video
from alenia_porter.api.audio import Audio
from alenia_porter.api.image import Image

__version__ = "7.1.0"

__all__ = ["Video", "Audio", "Image", "Media", "Stream"]
