class CapabilityRegistry:
    def __init__(self):
        self.codecs = set()
        self.formats = set()

    def load_from_ffmpeg(self, resolver):
        if not resolver.is_ffmpeg_available:
            return
        
        # In a real scenario, this would parse `ffmpeg -codecs` and `ffmpeg -formats`
        # For now, we mock some common capabilities.
        self.codecs.update(["h264", "hevc", "aac", "mp3", "copy"])
        self.formats.update(["mp4", "mkv", "webm", "mp3", "wav"])

    def supports_codec(self, codec: str) -> bool:
        return codec in self.codecs

    def supports_format(self, fmt: str) -> bool:
        return fmt in self.formats

default_registry = CapabilityRegistry()
