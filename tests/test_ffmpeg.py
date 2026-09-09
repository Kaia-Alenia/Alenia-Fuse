from fuse.ffmpeg import default_resolver


def test_ffmpeg_resolver_initializes():
    assert hasattr(default_resolver, 'resolve')

def test_ffmpeg_availability():
    # Since we don't have bundled ffmpeg yet, it might fallback to system or return None
    # We just ensure it doesn't crash
    path = default_resolver.ffmpeg_path
    if path:
        from pathlib import Path
        assert isinstance(path, Path)
        assert default_resolver.is_ffmpeg_available
