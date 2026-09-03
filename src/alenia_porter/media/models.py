from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

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

class Video(Media):
    """Specific wrapper for video content."""
    pass

class Audio(Media):
    """Specific wrapper for audio content."""
    pass

class Image(Media):
    """Specific wrapper for image content."""
    pass
