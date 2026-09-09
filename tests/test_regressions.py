import pytest
from pathlib import Path
from fuse.media.models import Media, Stream
from fuse.planner.planner import OperationPlanner, OperationPlan
from fuse.jobs.manager import Job
from fuse.operations.convert import ConvertOperation
from fuse.errors import IncompatibleOperationError, ConversionError

def test_input_equals_output_rejected(tmp_path):
    # Setup dummy media file
    in_file = tmp_path / "test.mp4"
    in_file.write_text("dummy")
    
    media = Media(path=str(in_file), container="mp4", duration=1.0, size=5)
    op = ConvertOperation(media, "mp4").output(str(in_file))
    
    result = op.run()
    assert not result.success
    assert "cannot be identical" in result.error

def test_planner_rgba_to_jpeg_rejected():
    planner = OperationPlanner()
    planner.registry.supports_format = lambda x: True
    media = Media(path="dummy.png", container="png", duration=0.0, size=100)
    
    # Mock video stream with alpha
    v_stream = Stream(index=0, codec_type="video", codec_name="png", width=100, height=100)
    v_stream.pix_fmt = "rgba"
    media.streams.append(v_stream)
    
    plan = planner.plan_convert(media, "jpg", "out.jpg")
    
    assert not plan.is_valid
    assert "alpha channel" in plan.error_reason.lower()

def test_job_fails_on_zero_bytes(tmp_path):
    out_file = tmp_path / "out.mp4"
    
    # Run a dummy script that creates a 0-byte file and exits 0
    # In Windows/Linux compatible way: python -c "open('out.mp4', 'w').close()"
    import sys
    cmd = [sys.executable, "-c", f"open(r'{out_file}', 'w').close()"]
    
    job = Job(cmd=cmd, output_path=out_file)
    success = job.run()
    
    assert not success
    assert job.error == "Output file is 0 bytes."
    assert not out_file.exists(), "Job manager should have deleted the 0-byte file"



def test_interactive_prompt_no_crash():
    from prompt_toolkit.formatted_text import FormattedText
    # Verify that FormattedText handles raw tags safely unlike HTML()
    text = FormattedText([("class:prompt", " <test_tag> hello ")])
    assert len(text) == 1
    assert text[0][1] == " <test_tag> hello "

def test_job_fails_on_webp_pipe(tmp_path):
    out_file = tmp_path / "out_webp_pipe"
    import sys
    cmd = [sys.executable, "-c", f"with open(r'{out_file}', 'wb') as f: f.write(b'fake_data')"]
    
    job = Job(cmd=cmd, output_path=out_file)
    success = job.run()
    
    assert not success
    assert "invalid pipe output" in job.error
    assert not out_file.exists()


def test_job_error_contains_ffmpeg_stderr_instead_of_only_exit_code(tmp_path):
    import sys

    out_file = tmp_path / "out.mp4"
    cmd = [
        sys.executable,
        "-c",
        "import sys; print('Invalid data found when processing input', file=sys.stderr); sys.exit(1)",
    ]

    job = Job(cmd=cmd, output_path=out_file)
    assert not job.run()
    assert job.error == "Invalid data found when processing input"
    assert "exit code 1" not in job.error


def test_ffmpeg_error_omits_build_banner_and_keeps_actionable_lines():
    from fuse.ffmpeg.diagnostics import format_ffmpeg_error

    stderr = """built with gcc 15.2.0
configuration: --enable-gpl --enable-libx264
Input #0, image2, from 'input.jpg':
Unable to choose an output format for 'output.jp'
Error initializing the muxer: Invalid argument
Error opening output files: Invalid argument
"""

    error = format_ffmpeg_error(stderr, returncode=1)
    assert "configuration:" not in error
    assert "Unable to choose an output format" in error
    assert "Error opening output files" in error


def test_planner_rejects_output_extension_that_does_not_match_target():
    planner = OperationPlanner()
    planner.registry.supports_format = lambda x: True
    planner.registry.has_encoder = lambda x: True
    media = Media(path="input.jpg", container="image2", duration=0.0, size=100)
    media.streams.append(Stream(index=0, codec_type="video", codec_name="mjpeg", width=320, height=240))

    plan = planner.plan_convert(media, "png", "output.jp")

    assert not plan.is_valid
    assert "valid 'png' extension" in plan.error_reason

def test_planner_mp4_to_mkv():
    planner = OperationPlanner()
    planner.registry.supports_format = lambda x: True
    
    media = Media(path="dummy.mp4", container="mp4", duration=10.0, size=100)
    v_stream = Stream(index=0, codec_type="video", codec_name="h264", width=1920, height=1080)
    a_stream = Stream(index=1, codec_type="audio", codec_name="aac", channels=2)
    media.streams.extend([v_stream, a_stream])
    
    plan = planner.plan_convert(media, "mkv", "out.mkv")
    
    assert plan.is_valid
    assert plan.strategy == "stream_copy"
    assert "copy" in plan.args

def test_planner_png_to_webp():
    planner = OperationPlanner()
    planner.registry.supports_format = lambda x: True
    planner.registry.has_encoder = lambda x: True
    
    media = Media(path="dummy.png", container="image2", duration=0.0, size=100)
    v_stream = Stream(index=0, codec_type="video", codec_name="png", width=100, height=100)
    media.streams.append(v_stream)
    
    plan = planner.plan_convert(media, "webp", "out.webp")
    
    assert plan.is_valid
    assert plan.strategy == "reencode"
    assert "libwebp" in plan.args

def test_planner_png_to_bmp():
    planner = OperationPlanner()
    planner.registry.supports_format = lambda x: True
    planner.registry.has_encoder = lambda x: True
    
    media = Media(path="dummy.png", container="image2", duration=0.0, size=100)
    v_stream = Stream(index=0, codec_type="video", codec_name="png", width=100, height=100)
    media.streams.append(v_stream)
    
    plan = planner.plan_convert(media, "bmp", "out.bmp")
    
    assert plan.is_valid
    assert plan.strategy == "reencode"
    assert "bmp" in plan.args

