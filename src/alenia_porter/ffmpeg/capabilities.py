import subprocess
from typing import Set
from alenia_porter.ffmpeg.resolver import default_resolver

class CapabilityRegistry:
    def __init__(self):
        self.codecs: Set[str] = set()
        self.formats: Set[str] = set()
        self.filters: Set[str] = set()
        self.encoders: Set[str] = set()
        self.decoders: Set[str] = set()
        self._loaded = False

    def load_from_ffmpeg(self):
        if self._loaded or not default_resolver.is_ffmpeg_available:
            return
            
        try:
            self._load_list("-codecs", self.codecs)
            self._load_list("-formats", self.formats)
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

    def has_codec(self, codec: str) -> bool:
        if not self._loaded:
            self.load_from_ffmpeg()
        return codec in self.codecs

    def has_format(self, fmt: str) -> bool:
        if not self._loaded:
            self.load_from_ffmpeg()
        # formats output might have comma separated aliases, so we check sub-strings
        for f in self.formats:
            if fmt in f.split(','):
                return True
        return False

    def supports_format(self, fmt: str) -> bool:
        return self.has_format(fmt)

default_registry = CapabilityRegistry()
