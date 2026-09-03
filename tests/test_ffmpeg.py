import pytest
from alenia_porter.ffmpeg import default_resolver

def test_ffmpeg_resolver_initializes():
    assert hasattr(default_resolver, 'resolve')

def test_ffmpeg_availability():
    # Since we don't have bundled ffmpeg yet, it might fallback to system or return None
    # We just ensure it doesn't crash
    path = default_resolver.ffmpeg_path
    if path:
        assert isinstance(path, str)
        assert default_resolver.is_ffmpeg_available
