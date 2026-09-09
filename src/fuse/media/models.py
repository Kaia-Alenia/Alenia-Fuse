from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from pathlib import Path


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
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Video specific
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    pix_fmt: Optional[str] = None
    
    # Audio specific
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    
    bitrate: Optional[int] = None

@dataclass
class Media:
    path: str
    container: str
    duration: float
    size: int
    streams: List[Stream] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    type: MediaType = MediaType.UNKNOWN

    @property
    def video_streams(self) -> List[Stream]:
        return [s for s in self.streams if s.codec_type == 'video']

    @property
    def audio_streams(self) -> List[Stream]:
        return [s for s in self.streams if s.codec_type == 'audio']

    @property
    def main_video(self) -> Optional[Stream]:
        streams = self.video_streams
        return streams[0] if streams else None

    @property
    def main_audio(self) -> Optional[Stream]:
        streams = self.audio_streams
        return streams[0] if streams else None

    @staticmethod
    def inspect(file_path: str) -> 'Media':
        from fuse.ffmpeg.probe import probe
        data = probe(Path(file_path))

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
    
    def convert(self, target_format: str) -> 'fuse.operations.convert.ConvertOperation':
        from fuse.operations.convert import ConvertOperation
        return ConvertOperation(self, target_format)

class Audio(Media):
    """Specific wrapper for audio content."""
    
    def convert(self, target_format: str) -> 'fuse.operations.convert.ConvertOperation':
        from fuse.operations.convert import ConvertOperation
        return ConvertOperation(self, target_format)

class Image(Media):
    """Specific wrapper for image content."""
    
    def convert(self, target_format: str) -> 'fuse.operations.convert.ConvertOperation':
        from fuse.operations.convert import ConvertOperation
        return ConvertOperation(self, target_format)
