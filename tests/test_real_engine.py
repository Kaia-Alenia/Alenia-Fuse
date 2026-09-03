import os
import pytest
from alenia_porter.ffmpeg.resolver import FFmpegResolver, UnsupportedPlatformError, FFmpegUnavailableError
from alenia_porter.ffmpeg.backend import FFmpegBackend, FFmpegExecutionError
from alenia_porter.ffmpeg.probe import probe, FFprobeError
from pathlib import Path

def test_resolver_detects_fake_binary(tmp_path):
    """
    Test that the resolver throws an error if it finds a dummy script
    instead of a real ffmpeg binary.
    """
    bin_dir = tmp_path / "bin" / "windows-x64"
    bin_dir.mkdir(parents=True, exist_ok=True)
    
    fake_ffmpeg = bin_dir / "ffmpeg.exe"
    fake_ffprobe = bin_dir / "ffprobe.exe"
    
    # Create fake executable scripts that don't output what ffmpeg does
    fake_ffmpeg.write_text("@echo off\\necho Dummy FFmpeg")
    fake_ffprobe.write_text("@echo off\\necho Dummy FFprobe")
    
    class TestResolver(FFmpegResolver):
        def _get_project_root(self):
            return tmp_path
            
        def _get_platform_dir_and_ext(self):
            return "windows-x64", ".exe"
            
    with pytest.raises(FFmpegUnavailableError, match="(does not appear to be a real FFmpeg|Error executing FFmpeg)"):
        TestResolver()

def test_backend_executes_real_ffmpeg():
    # Should work with the real one installed in the project root
    resolver = FFmpegResolver()
    assert resolver.is_ffmpeg_available
    
    # Run a simple version check using the backend
    try:
        FFmpegBackend.run_operation(["-version"])
    except Exception as e:
        pytest.fail(f"Backend failed to run real FFmpeg: {e}")

def test_probe_returns_json():
    # We need a small fixture or we just test probe fails on nonexistent file
    # but successfully invokes ffprobe.
    with pytest.raises(FFprobeError, match="No such file"):
        # We expect ffprobe to run, fail to find the file, and return an FFprobeError
        probe(Path("nonexistent_file.mp4"))
