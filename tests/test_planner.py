"""
Tests for the real Planner of Alenia Fuse.
"""
from unittest.mock import MagicMock

from fuse.media.models import Media, Stream
from fuse.planner.planner import OperationPlanner


def make_media(has_video=True, has_audio=True,
               video_codec="h264", audio_codec="aac",
               duration=60.0):
    streams = []
    if has_video:
        s = Stream(index=0, codec_type="video", codec_name=video_codec)
        s.width = 1920
        s.height = 1080
        s.fps = 30.0
        streams.append(s)
    if has_audio:
        s = Stream(index=1, codec_type="audio", codec_name=audio_codec)
        s.sample_rate = 44100
        s.channels = 2
        streams.append(s)

    return Media(
        path="/fake/movie.mp4",
        container="mp4",
        duration=duration,
        size=1024 * 1024 * 100,
        streams=streams
    )


def make_planner():
    """Create a planner with a real-looking registry mock."""
    registry = MagicMock()
    registry.supports_format.return_value = True
    return OperationPlanner(registry=registry)


def test_stream_copy_when_codecs_compatible():
    media = make_media(video_codec="h264", audio_codec="aac")
    planner = make_planner()
    plan = planner.plan_convert(media, "mp4", "/out/out.mp4")
    assert plan.is_valid
    assert plan.strategy == "stream_copy"
    assert "-c" in plan.args and "copy" in plan.args


def test_reencode_when_target_is_webm_with_h264():
    media = make_media(video_codec="h264", audio_codec="aac")
    planner = make_planner()
    plan = planner.plan_convert(media, "webm", "/out/out.webm")
    assert plan.is_valid
    assert plan.strategy == "reencode"
    # WebM needs VP9
    assert "libvpx-vp9" in plan.args


def test_invalid_format_rejected():
    registry = MagicMock()
    registry.supports_format.return_value = False
    planner = OperationPlanner(registry=registry)
    media = make_media()
    plan = planner.plan_convert(media, "xyz", "/out/out.xyz")
    assert not plan.is_valid
    assert "xyz" in plan.error_reason


def test_compress_balanced():
    media = make_media()
    planner = make_planner()
    plan = planner.plan_compress(media, "/out/compressed.mp4", quality="balanced")
    assert plan.is_valid
    assert "libx264" in plan.args
    assert "28" in plan.args   # CRF for balanced


def test_compress_high():
    media = make_media()
    planner = make_planner()
    plan = planner.plan_compress(media, "/out/out.mp4", quality="high")
    assert "23" in plan.args  # CRF for high


def test_video_op_requires_video_stream():
    media = make_media(has_video=False)
    planner = make_planner()
    plan = planner.plan_video_op("resize", media, "/out/out.mp4", width=1280, height=720)
    assert not plan.is_valid
    assert "video stream" in plan.error_reason


def test_resize_generates_scale_filter():
    media = make_media()
    planner = make_planner()
    plan = planner.plan_video_op("resize", media, "/out/out.mp4", width=1280, height=720)
    assert plan.is_valid
    assert any("scale=1280:720" in a for a in plan.args)


def test_trim_generates_ss_and_to():
    media = make_media()
    planner = make_planner()
    plan = planner.plan_video_op("trim", media, "/out/clip.mp4",
                                  start="00:01:00", end="00:02:00", duration=None)
    assert plan.is_valid
    assert "-ss" in plan.args
    assert "-to" in plan.args


def test_audio_volume_generates_filter():
    media = make_media(has_video=False)
    planner = make_planner()
    plan = planner.plan_audio_op("volume", media, "/out/loud.mp3", value="+20%")
    assert plan.is_valid
    assert any("volume=" in a for a in plan.args)


def test_audio_normalize_uses_loudnorm():
    media = make_media(has_video=False)
    planner = make_planner()
    plan = planner.plan_audio_op("normalize", media, "/out/norm.mp3")
    assert plan.is_valid
    assert any("loudnorm" in a for a in plan.args)


def test_audio_op_requires_audio_stream():
    media = make_media(has_audio=False)
    planner = make_planner()
    plan = planner.plan_audio_op("normalize", media, "/out/out.mp3")
    assert not plan.is_valid


def test_public_targets_have_explicit_strategies():
    media = make_media()
    planner = make_planner()
    for target in ("mp4", "webm", "mkv", "mov", "avi", "ts", "flv",
                   "mp3", "flac", "aac", "m4a", "opus", "ogg", "wav",
                   "wma", "webp", "jpg", "png", "avif", "bmp", "tiff",
                   "gif", "webp_animated", "apng"):
        ext = "webp" if target == "webp_animated" else target
        plan = planner.plan_convert(media, target, f"/out/out.{ext}")
        assert plan.is_valid, f"{target}: {plan.error_reason}"
        assert not plan.needs_preflight


def test_structure_rules_reject_impossible_conversion():
    media = make_media(has_video=False, has_audio=True)
    planner = make_planner()
    plan = planner.plan_convert(media, "mp4", "/out/out.mp4")
    assert not plan.is_valid
    assert "video stream" in plan.error_reason


def test_pdf_is_specialized_image_operation():
    media = make_media()
    planner = make_planner()
    plan = planner.plan_convert(media, "pdf", "/out/out.pdf")
    assert not plan.is_valid
    assert "Image.to_pdf" in plan.error_reason
