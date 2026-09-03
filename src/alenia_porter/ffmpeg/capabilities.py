import subprocess
from typing import Set, Dict, List, Optional
from dataclasses import dataclass
from alenia_porter.ffmpeg.resolver import default_resolver

@dataclass
class FormatInfo:
    name: str
    description: str
    can_demux: bool
    can_mux: bool
    category: str # 'video', 'audio', 'image', 'unknown'

class CapabilityRegistry:
    # Known categorizations to map FFmpeg format names to our internal categories
    KNOWN_VIDEO = {"mp4", "mkv", "matroska", "webm", "mov", "avi", "flv", "mpeg", "mpg", "m4v", "ts", "m2ts", "mts", "3gp", "3g2", "ogv", "ogg", "f4v", "asf", "wmv", "vob", "mxf", "nut", "gif"}
    KNOWN_AUDIO = {"mp3", "wav", "flac", "aac", "m4a", "opus", "ogg", "oga", "wma", "ac3", "eac3", "mka", "aiff", "aif", "alac", "amr", "au"}
    KNOWN_IMAGE = {"png", "jpg", "jpeg", "webp", "bmp", "tiff", "tif", "gif", "ico", "ppm", "pgm", "pbm", "pam", "tga", "pcx", "sgi", "jp2", "j2k", "jpf", "jpx", "avif", "exr", "image2"}

    def __init__(self):
        self.codecs: Set[str] = set()
        self.filters: Set[str] = set()
        self.encoders: Set[str] = set()
        self.decoders: Set[str] = set()
        
        self.formats: Dict[str, FormatInfo] = {}
        self._loaded = False

    def load_from_ffmpeg(self):
        if self._loaded or not default_resolver.is_ffmpeg_available:
            return
            
        try:
            self._load_list("-codecs", self.codecs)
            self._load_formats()
            self._load_list("-filters", self.filters)
            self._load_list("-encoders", self.encoders)
            self._load_list("-decoders", self.decoders)
            self._loaded = True
        except Exception as e:
            pass

    def _load_list(self, arg: str, target_set: Set[str]):
        result = subprocess.run(
            [str(default_resolver.ffmpeg_path), arg],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
            check=True
        )
        for line in result.stdout.splitlines():
            # FFmpeg list format typically has some leading spaces, then flags, then the name
            if len(line) > 8 and " " in line[1:8]:
                parts = line.strip().split()
                if len(parts) >= 2:
                    # Name is usually the second token (first token is flags like D.V.L.)
                    target_set.add(parts[1])

    def _load_formats(self):
        result = subprocess.run(
            [str(default_resolver.ffmpeg_path), "-formats"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
            check=True
        )
        
        # Flags for formats: D (demuxing), E (muxing). A 'd' might mean device in some contexts if printed.
        for line in result.stdout.splitlines():
            if len(line) > 4 and line.startswith(" ") and not line.strip().startswith("--"):
                # " D  3dostr          3DO STR"
                # "  E 3g2             3GP2 (3GPP2 file format)"
                # " DE ac3             raw AC-3"
                flags_str = line[0:4]
                can_demux = "D" in flags_str
                can_mux = "E" in flags_str
                is_device = "d" in flags_str
                
                if is_device:
                    continue
                    
                rest = line[4:].strip()
                if not rest:
                    continue
                
                parts = rest.split(" ", 1)
                names_str = parts[0]
                description = parts[1].strip() if len(parts) > 1 else ""
                
                if "_pipe" in names_str:
                    continue
                    
                names = names_str.split(",")
                for name in names:
                    cat = self._classify_format(name)
                    self.formats[name] = FormatInfo(
                        name=name,
                        description=description,
                        can_demux=can_demux,
                        can_mux=can_mux,
                        category=cat
                    )

    def _classify_format(self, name: str) -> str:
        if name in self.KNOWN_VIDEO:
            return "video"
        if name in self.KNOWN_AUDIO:
            return "audio"
        if name in self.KNOWN_IMAGE:
            return "image"
        return "unknown"

    def has_codec(self, codec: str) -> bool:
        if not self._loaded:
            self.load_from_ffmpeg()
        return codec in self.codecs
        
    def has_encoder(self, encoder: str) -> bool:
        if not self._loaded:
            self.load_from_ffmpeg()
        return encoder in self.encoders
        
    def has_decoder(self, decoder: str) -> bool:
        if not self._loaded:
            self.load_from_ffmpeg()
        return decoder in self.decoders

    def has_format(self, fmt: str) -> bool:
        if not self._loaded:
            self.load_from_ffmpeg()
        return fmt in self.formats

    def supports_format(self, fmt: str) -> bool:
        if not self._loaded:
            self.load_from_ffmpeg()
        return fmt in self.formats and self.formats[fmt].can_mux
        
    def get_muxers_by_category(self, category: str) -> List[FormatInfo]:
        if not self._loaded:
            self.load_from_ffmpeg()
        return [f for f in self.formats.values() if f.category == category and f.can_mux]

default_registry = CapabilityRegistry()
