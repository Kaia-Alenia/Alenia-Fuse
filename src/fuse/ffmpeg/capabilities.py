import subprocess
from typing import Set, Dict, List, Optional
from dataclasses import dataclass
from fuse.ffmpeg.resolver import default_resolver


@dataclass
class FormatInfo:
    name: str
    description: str
    can_demux: bool
    can_mux: bool
    # Category derived from the product-level catalog in capabilities/policies.py
    category: str   # 'video' | 'audio' | 'image' | 'unknown'


class CapabilityRegistry:
    """
    Low-level FFmpeg capability registry.
    For product-level conversion decisions, use fuse.capabilities.engine.
    """

    # Non-file targets that should never be presented to users (§10)
    EXCLUDED_FORMATS = {
        "image2", "image2pipe", "rtsp", "http", "https", "udp", "tcp", "rtp",
        "alsa", "dshow", "null", "tee", "fifo", "dash", "hls", "smoothstreaming",
        "chromaprint", "framemd5", "crc", "sdl", "opengl", "fbdev", "v4l2",
        "oss", "pulse",
    }

    def __init__(self):
        self.codecs: Set[str] = set()
        self.filters: Set[str] = set()
        self.encoders: Set[str] = set()
        self.decoders: Set[str] = set()
        self.formats: Dict[str, FormatInfo] = {}

        # Load status exposed for diagnostics (§32)
        self._load_status: str = "not_loaded"  # 'not_loaded' | 'loaded' | 'failed'
        self._load_error: Optional[str] = None

    @property
    def load_status(self) -> str:
        return self._load_status

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    def load_from_ffmpeg(self):
        if self._load_status == "loaded":
            return
        if not default_resolver.is_ffmpeg_available:
            self._load_status = "failed"
            self._load_error = "Bundled FFmpeg binary is not available."
            return

        try:
            self._load_list("-codecs", self.codecs)
            self._load_formats()
            self._load_list("-filters", self.filters)
            self._load_list("-encoders", self.encoders)
            self._load_list("-decoders", self.decoders)
            self._load_status = "loaded"
            self._load_error = None
        except Exception as exc:
            self._load_status = "failed"
            self._load_error = str(exc)
            raise  # re-raise — §32 forbids silencing errors here

    def _load_list(self, arg: str, target_set: Set[str]):
        result = subprocess.run(
            [str(default_resolver.ffmpeg_path), arg],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
            check=True,
        )
        for line in result.stdout.splitlines():
            if len(line) > 8 and " " in line[1:8]:
                parts = line.strip().split()
                if len(parts) >= 2:
                    target_set.add(parts[1])

    def _load_formats(self):
        result = subprocess.run(
            [str(default_resolver.ffmpeg_path), "-formats"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
            check=True,
        )
        for line in result.stdout.splitlines():
            if len(line) > 4 and line.startswith(" ") and not line.strip().startswith("--"):
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
                if "pipe" in names_str.lower():
                    continue
                names = names_str.split(",")
                for name in names:
                    clean_name = name.lower()
                    if "pipe" in clean_name or clean_name in self.EXCLUDED_FORMATS:
                        continue
                    cat = self._classify_format(name)
                    # FFmpeg may list the same format once as a demuxer and
                    # once as a muxer. Merge both rows instead of letting the
                    # later row erase one of the capabilities.
                    previous = self.formats.get(name)
                    self.formats[name] = FormatInfo(
                        name=name,
                        description=description or (previous.description if previous else ""),
                        can_demux=can_demux or (previous.can_demux if previous else False),
                        can_mux=can_mux or (previous.can_mux if previous else False),
                        category=cat if cat != "unknown" else (previous.category if previous else cat),
                    )

    def _classify_format(self, name: str) -> str:
        """
        Classify via the product catalog first; fall back to unknown.
        The product catalog (capabilities/policies.py) is the source of truth.
        """
        from fuse.capabilities.policies import ALL_TARGETS
        for target in ALL_TARGETS:
            if name == target.muxer or name == target.id:
                return target.kind if target.kind != "animated_image" else "video"
        return "unknown"

    def has_codec(self, codec: str) -> bool:
        if self._load_status == "not_loaded":
            self.load_from_ffmpeg()
        return codec in self.codecs

    def has_encoder(self, encoder: str) -> bool:
        if self._load_status == "not_loaded":
            self.load_from_ffmpeg()
        return encoder in self.encoders

    def has_decoder(self, decoder: str) -> bool:
        if self._load_status == "not_loaded":
            self.load_from_ffmpeg()
        return decoder in self.decoders

    def has_format(self, fmt: str) -> bool:
        if self._load_status == "not_loaded":
            self.load_from_ffmpeg()
        return fmt in self.formats

    def supports_format(self, fmt: str) -> bool:
        if self._load_status == "not_loaded":
            self.load_from_ffmpeg()
        # Product IDs can differ from FFmpeg muxer names (m4a, jpg, tiff,
        # animated WebP). Resolve those IDs through the Fuse catalog.
        from fuse.capabilities.policies import TARGET_BY_ID
        target = TARGET_BY_ID.get(fmt)
        if target:
            if fmt == "pdf":
                return False
            if target.muxer == "image2":
                return True
            return target.muxer in self.formats and self.formats[target.muxer].can_mux
        return fmt in self.formats and self.formats[fmt].can_mux

    def get_muxers_by_category(self, category: str) -> List[FormatInfo]:
        if self._load_status == "not_loaded":
            self.load_from_ffmpeg()
        return [f for f in self.formats.values() if f.category == category and f.can_mux]


default_registry = CapabilityRegistry()
