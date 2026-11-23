from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fuse.operations.convert import ConvertOperation


class MediaType(Enum):
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    UNKNOWN = "unknown"


@dataclass
class Stream:
    index: int
    codec_type: str
    codec_name: str
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # Video specific
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    pix_fmt: str | None = None
    
    # Audio specific
    sample_rate: int | None = None
    channels: int | None = None
    
    bitrate: int | None = None

@dataclass
class Media:
    path: str
    container: str
    duration: float
    size: int
    streams: list[Stream] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    type: MediaType = MediaType.UNKNOWN

    @property
    def video_streams(self) -> list[Stream]:
        return [s for s in self.streams if s.codec_type == 'video']

    @property
    def audio_streams(self) -> list[Stream]:
        return [s for s in self.streams if s.codec_type == 'audio']

    @property
    def main_video(self) -> Stream | None:
        streams = self.video_streams
        return streams[0] if streams else None

    @property
    def main_audio(self) -> Stream | None:
        streams = self.audio_streams
        return streams[0] if streams else None

    @staticmethod
    def _inspect_image_with_pillow(file_path: str) -> "Media | None":
        """Inspect a still image with Pillow when ffprobe is unavailable.

        Returns None when Pillow cannot read the file (not an image, or a
        corrupt one) so the caller can report the original ffprobe error.
        """
        suffix = Path(file_path).suffix.lower()
        if suffix not in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif", ".gif"}:
            return None
        try:
            from PIL import Image as PILImage
        except ImportError:
            return None
        try:
            with PILImage.open(file_path) as image:
                width, height = image.size
                fmt = (image.format or suffix.lstrip(".")).lower()
        except Exception:
            return None
        media = Media(
            path=str(file_path),
            container=fmt,
            duration=0.0,
            size=Path(file_path).stat().st_size,
            type=MediaType.IMAGE,
        )
        media.streams.append(Stream(
            index=0, codec_type="video", codec_name=fmt,
            width=width, height=height,
        ))
        return media

    @staticmethod
    def inspect(file_path: str) -> 'Media':
        from fuse.ffmpeg.probe import probe
        try:
            data = probe(Path(file_path))
        except Exception:
            # Still images do not need ffprobe: Pillow already knows their
            # size and format. Without this, every image operation failed
            # on machines without FFmpeg before any conversion was tried.
            pillow_media = Media._inspect_image_with_pillow(file_path)
            if pillow_media is not None:
                return pillow_media
            raise

        format_info = data.get("format", {})
        streams_info = data.get("streams", [])

        media = Media(
            path=str(file_path),
            container=format_info.get("format_name", ""),
            duration=float(format_info.get("duration", 0.0)),
            size=int(format_info.get("size", 0)),
            metadata=format_info.get("tags", {}),
        )

        for s in streams_info:
            stream = Stream(
                index=s.get("index", 0),
                codec_type=s.get("codec_type", "unknown"),
                codec_name=s.get("codec_name", "unknown"),
                metadata=s.get("tags", {}),
            )
            if stream.codec_type == "video":
                stream.width = int(s.get("width", 0))
                stream.height = int(s.get("height", 0))
                stream.pix_fmt = s.get("pix_fmt")
                fps_str = s.get("r_frame_rate", "0/1")
                if "/" in fps_str:
                    num, den = fps_str.split("/")
                    stream.fps = float(num) / float(den) if float(den) != 0 else 0.0
            elif stream.codec_type == "audio":
                stream.sample_rate = int(s.get("sample_rate", 0))
                stream.channels = int(s.get("channels", 0))

            bitrate = s.get("bit_rate")
            if bitrate:
                stream.bitrate = int(bitrate)

            media.streams.append(stream)

        # Infer media type from streams and container name.
        # Images and animated images (gif, apng, webp) show up as a single
        # video stream with no audio and duration near 0.
        image_codecs = {"png", "mjpeg", "gif", "apng", "webp", "bmp", "tiff",
                        "dpx", "exr", "pbm", "pgm", "ppm", "sgi", "tga",
                        "xbm", "xpm", "av1", "avif"}
        image_containers = {"image2", "gif", "apng", "webp", "png_pipe",
                            "jpeg_pipe", "bmp_pipe", "tiff_pipe"}

        has_video = any(s.codec_type == "video" for s in media.streams)
        has_audio = any(s.codec_type == "audio" for s in media.streams)
        container_name = media.container.split(",")[0].strip()

        if has_video and not has_audio:
            video_codec = next(
                (s.codec_name for s in media.streams if s.codec_type == "video"), ""
            )
            if video_codec in image_codecs or container_name in image_containers:
                media.type = MediaType.IMAGE
            else:
                media.type = MediaType.VIDEO
        elif has_video and has_audio:
            media.type = MediaType.VIDEO
        elif has_audio and not has_video:
            media.type = MediaType.AUDIO
        else:
            media.type = MediaType.UNKNOWN

        return media


class Video(Media):
    """Specific wrapper for video content."""
    
    def convert(self, target_format: str) -> "ConvertOperation":
        from fuse.operations.convert import ConvertOperation
        return ConvertOperation(self, target_format)

class Audio(Media):
    """Specific wrapper for audio content."""
    
    def convert(self, target_format: str) -> "ConvertOperation":
        from fuse.operations.convert import ConvertOperation
        return ConvertOperation(self, target_format)

class Image(Media):
    """Specific wrapper for image content."""
    
    def convert(self, target_format: str) -> "ConvertOperation":
        from fuse.operations.convert import ConvertOperation
        return ConvertOperation(self, target_format)
