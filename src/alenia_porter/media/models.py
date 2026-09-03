from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path

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
        from alenia_porter.ffmpeg.probe import probe
        data = probe(Path(file_path))
        
        format_info = data.get("format", {})
        streams_info = data.get("streams", [])
        
        media = Media(
            path=str(file_path),
            container=format_info.get("format_name", ""),
            duration=float(format_info.get("duration", 0.0)),
            size=int(format_info.get("size", 0)),
            metadata=format_info.get("tags", {})
        )
        
        for s in streams_info:
            stream = Stream(
                index=s.get("index", 0),
                codec_type=s.get("codec_type", "unknown"),
                codec_name=s.get("codec_name", "unknown"),
                metadata=s.get("tags", {})
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
            
        return media

class Video(Media):
    """Specific wrapper for video content."""
    
    def convert(self, target_format: str) -> 'alenia_porter.operations.convert.ConvertOperation':
        from alenia_porter.operations.convert import ConvertOperation
        return ConvertOperation(self, target_format)

class Audio(Media):
    """Specific wrapper for audio content."""
    
    def convert(self, target_format: str) -> 'alenia_porter.operations.convert.ConvertOperation':
        from alenia_porter.operations.convert import ConvertOperation
        return ConvertOperation(self, target_format)

class Image(Media):
    """Specific wrapper for image content."""
    
    def convert(self, target_format: str) -> 'alenia_porter.operations.convert.ConvertOperation':
        from alenia_porter.operations.convert import ConvertOperation
        return ConvertOperation(self, target_format)
