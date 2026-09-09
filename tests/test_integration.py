import pytest
import os
from pathlib import Path
from fuse.ffmpeg.backend import FFmpegBackend
from fuse.ffmpeg.probe import probe

def test_real_conversion_integration(tmp_path):
    # 1. Generate a synthetic input video
    input_file = tmp_path / "input.mp4"
    output_file = tmp_path / "output.webm"
    
    # We use FFmpegBackend directly to run the command
    FFmpegBackend.run_operation([
        "-f", "lavfi",
        "-i", "testsrc=duration=1:size=640x360:rate=30",
        "-c:v", "libx264",
        str(input_file)
    ])
    
    assert input_file.exists()
    assert input_file.stat().st_size > 0
    
    # 2. Run conversion to WEBM VP9
    FFmpegBackend.run_operation([
        "-i", str(input_file),
        "-c:v", "libvpx-vp9",
        "-b:v", "1M",
        str(output_file)
    ])
    
    # 3. Validate with FFprobe
    assert output_file.exists()
    assert output_file.stat().st_size > 0
    
    probe_data = probe(output_file)
    
    assert "format" in probe_data
    assert probe_data["format"]["format_name"] == "matroska,webm"
    
    assert "streams" in probe_data
    video_stream = next((s for s in probe_data["streams"] if s["codec_type"] == "video"), None)
    
    assert video_stream is not None
    assert video_stream["codec_name"] == "vp9"
    assert video_stream["width"] == 640
    assert video_stream["height"] == 360
