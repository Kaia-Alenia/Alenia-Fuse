"""Real A→B conversion tests for the public Fuse APIs."""

import subprocess
from pathlib import Path

import pytest
from PIL import Image as PILImage

from fuse import Audio, Image, Video
from fuse.ffmpeg.probe import probe
from fuse.ffmpeg.resolver import default_resolver
from fuse.media.models import Media, MediaType

pytestmark = pytest.mark.skipif(
    not default_resolver.is_ffmpeg_available,
    reason="FFmpeg/FFprobe are required for real conversion tests",
)


def _ffmpeg(*args: str) -> None:
    result = subprocess.run(
        [str(default_resolver.ffmpeg_path), "-y", *args],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def _assert_valid_media(path: Path, expected_type: MediaType, expected_stream: str):
    assert path.is_file()
    assert path.stat().st_size > 0
    data = probe(path)
    assert data.get("streams"), f"No streams found in {path}"
    assert any(s.get("codec_type") == expected_stream for s in data["streams"])

    media = Media.inspect(str(path))
    assert media.type == expected_type
    assert media.duration >= 0
    return media


def test_video_a_to_b_preserves_video_and_creates_real_webm(tmp_path):
    source = tmp_path / "source.mp4"
    output = tmp_path / "output.webm"
    _ffmpeg(
        "-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=10",
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=1",
        "-c:v", "libx264", "-c:a", "aac", str(source),
    )

    original = _assert_valid_media(source, MediaType.VIDEO, "video")
    result = Video(str(source)).convert("webm").output(str(output)).run()

    assert result.success, result.error
    converted = _assert_valid_media(output, MediaType.VIDEO, "video")
    assert converted.main_video is not None
    assert original.main_video.width == converted.main_video.width
    assert original.main_video.height == converted.main_video.height
    assert converted.duration > 0
    assert output.read_bytes()[:1] != b"{"  # not JSON/text masquerading as media


def test_audio_a_to_b_preserves_audio_and_removes_video(tmp_path):
    source = tmp_path / "source.wav"
    output = tmp_path / "output.mp3"
    _ffmpeg(
        "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
        "-c:a", "pcm_s16le", str(source),
    )

    original = _assert_valid_media(source, MediaType.AUDIO, "audio")
    result = Audio(str(source)).convert("mp3").output(str(output)).run()

    assert result.success, result.error
    converted = _assert_valid_media(output, MediaType.AUDIO, "audio")
    assert original.main_audio.channels == converted.main_audio.channels
    assert not converted.video_streams
    assert converted.duration > 0


def test_image_a_to_b_is_readable_and_has_no_source_metadata(tmp_path):
    source = tmp_path / "source.png"
    output = tmp_path / "output.webp"
    image = PILImage.new("RGB", (160, 100), "blue")
    exif = image.getexif()
    exif[315] = "Private Device"
    exif[306] = "2026:09:09 12:00:00"
    image.save(source, exif=exif)

    original = _assert_valid_media(source, MediaType.IMAGE, "video")
    result = Image(str(source)).convert("webp").output(str(output)).run()

    assert result.success, result.error
    converted = _assert_valid_media(output, MediaType.IMAGE, "video")
    assert converted.main_video.width == original.main_video.width
    assert converted.main_video.height == original.main_video.height
    assert converted.metadata == {}
