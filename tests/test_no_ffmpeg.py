"""Tests for the no-FFmpeg path (diagnosis failures #1-#4).

These tests never need a real FFmpeg binary: the resolver / probe /
image modules are given stub resolvers, and Pillow does the image work.
Run with:  pytest tests/test_no_ffmpeg.py -v
"""
import platform

import pytest
from PIL import Image as PILImage

from fuse.ffmpeg.downloader import FFmpegDownloadError, PLATFORM_ASSETS, _platform_dir


def _make_png(path, size=(64, 48), color=(10, 20, 30)):
    image = PILImage.new("RGB", size, color)
    image.save(path, "PNG")
    return path


class _NoFFmpegResolver:
    is_ffmpeg_available = False
    is_ffprobe_available = False
    ffmpeg_path = None
    ffprobe_path = None
    last_error = "test download failure"
    ffprobe_missing = False

    @property
    def unavailable_reason(self):
        return self.last_error


class _FFmpegNoFFprobeResolver(_NoFFmpegResolver):
    is_ffmpeg_available = True
    last_error = None

    @property
    def unavailable_reason(self):
        return ""


# --- 1. downloader -----------------------------------------------------------

def test_downloader_knows_all_three_platforms():
    assert set(PLATFORM_ASSETS) == {"windows-x64", "linux-x64", "macos-arm64"}
    for plat_dir, (ffmpeg_url, _ffprobe_url, _kind) in PLATFORM_ASSETS.items():
        assert ffmpeg_url.startswith("https://"), plat_dir
    # Windows/Linux use the same BtbN assets as .github/workflows/build.yml.
    assert "BtbN/FFmpeg-Builds" in PLATFORM_ASSETS["windows-x64"][0]
    assert "BtbN/FFmpeg-Builds" in PLATFORM_ASSETS["linux-x64"][0]
    # macOS ships ffmpeg and ffprobe in separate evermeet zips.
    assert PLATFORM_ASSETS["macos-arm64"][1] is not None
    assert "evermeet.cx" in PLATFORM_ASSETS["macos-arm64"][0]


def test_downloader_platform_dir_on_this_machine():
    assert _platform_dir() in PLATFORM_ASSETS


def test_downloader_rejects_unknown_platform(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "plan9")
    monkeypatch.setattr(platform, "machine", lambda: "x86_64")
    from fuse.ffmpeg.downloader import download_ffmpeg
    with pytest.raises(FFmpegDownloadError, match="no FFmpeg download"):
        download_ffmpeg()


def test_downloader_module_is_importable():
    # Failure #1 was literally this import raising ModuleNotFoundError.
    from fuse.ffmpeg.downloader import download_ffmpeg  # noqa: F401
    assert callable(download_ffmpeg)


# --- 2. resolver exposes the real cause --------------------------------------

def test_resolver_unavailable_reason_is_not_empty(monkeypatch, tmp_path):
    monkeypatch.setenv("FUSE_DISABLE_FFMPEG_DOWNLOAD", "1")
    monkeypatch.delenv("FUSE_FFMPEG_DIR", raising=False)
    monkeypatch.delenv("FUSE_FFMPEG_CACHE", raising=False)
    import fuse.ffmpeg.resolver as resolver_mod
    monkeypatch.setattr(resolver_mod.shutil, "which", lambda _name: None)
    resolver = resolver_mod.FFmpegResolver()
    assert resolver.is_ffmpeg_available is False
    assert resolver.unavailable_reason
    assert "FFmpeg" in resolver.unavailable_reason


# --- 3. probe never executes the literal path "None" --------------------------

def test_probe_ffmpeg_without_ffprobe_has_clear_message(monkeypatch):
    import fuse.ffmpeg.probe as probe_mod
    monkeypatch.setattr(probe_mod, "default_resolver", _FFmpegNoFFprobeResolver())
    with pytest.raises(probe_mod.FFprobeError) as excinfo:
        probe_mod.probe(__import__("pathlib").Path("whatever.mp4"))
    assert "ffprobe is missing" in str(excinfo.value)
    assert '"None"' not in str(excinfo.value)


# --- 4. still images work without FFmpeg, via Pillow --------------------------

def test_image_convert_png_to_webp_without_ffmpeg(monkeypatch, tmp_path):
    import fuse.operations.image as image_mod
    from fuse.media.models import Media, MediaType

    monkeypatch.setattr(image_mod, "default_resolver", _NoFFmpegResolver())
    src = _make_png(tmp_path / "test.png")
    out = tmp_path / "test.webp"
    media = Media(path=str(src), container="png", duration=0.0,
                  size=src.stat().st_size, type=MediaType.IMAGE)
    result = image_mod.ImageOperation(media).convert("webp").output(str(out)).run()
    assert result.success, result.error
    assert out.is_file() and out.stat().st_size > 0
    with PILImage.open(out) as converted:
        assert converted.size == (64, 48)


def test_image_convert_png_to_jpg_without_ffmpeg(monkeypatch, tmp_path):
    import fuse.operations.image as image_mod
    from fuse.media.models import Media, MediaType

    monkeypatch.setattr(image_mod, "default_resolver", _NoFFmpegResolver())
    src = _make_png(tmp_path / "test.png")
    out = tmp_path / "test.jpg"
    media = Media(path=str(src), container="png", duration=0.0,
                  size=src.stat().st_size, type=MediaType.IMAGE)
    result = image_mod.ImageOperation(media).convert("jpg").output(str(out)).run()
    assert result.success, result.error
    with PILImage.open(out) as converted:
        assert converted.format == "JPEG"


def test_image_resize_without_ffmpeg(monkeypatch, tmp_path):
    import fuse.operations.image as image_mod
    from fuse.media.models import Media, MediaType

    monkeypatch.setattr(image_mod, "default_resolver", _NoFFmpegResolver())
    src = _make_png(tmp_path / "test.png")
    out = tmp_path / "small.png"
    media = Media(path=str(src), container="png", duration=0.0,
                  size=src.stat().st_size, type=MediaType.IMAGE)
    result = image_mod.ImageOperation(media).resize(32, 24).output(str(out)).run()
    assert result.success, result.error
    with PILImage.open(out) as converted:
        assert converted.size == (32, 24)


def test_convert_operation_image_route_without_ffmpeg(monkeypatch, tmp_path):
    import fuse.operations.convert as convert_mod
    import fuse.operations.image as image_mod
    from fuse.media.models import Media, MediaType

    stub = _NoFFmpegResolver()
    monkeypatch.setattr(convert_mod, "default_resolver", stub)
    monkeypatch.setattr(image_mod, "default_resolver", stub)
    src = _make_png(tmp_path / "test.png")
    out = tmp_path / "test.webp"
    media = Media(path=str(src), container="png", duration=0.0,
                  size=src.stat().st_size, type=MediaType.IMAGE)
    result = convert_mod.ConvertOperation(media, "webp").output(str(out)).run()
    assert result.success, result.error
    assert out.is_file()


def test_media_inspect_image_without_ffmpeg(monkeypatch, tmp_path):
    import fuse.ffmpeg.probe as probe_mod
    from fuse.media.models import Media, MediaType

    monkeypatch.setattr(probe_mod, "default_resolver", _NoFFmpegResolver())
    src = _make_png(tmp_path / "test.png")
    media = Media.inspect(str(src))
    assert media.type == MediaType.IMAGE
    assert media.main_video is not None
    assert (media.main_video.width, media.main_video.height) == (64, 48)


def test_video_convert_without_ffmpeg_names_the_cause(monkeypatch, tmp_path):
    import fuse.operations.convert as convert_mod
    from fuse.media.models import Media, MediaType

    monkeypatch.setattr(convert_mod, "default_resolver", _NoFFmpegResolver())
    src = tmp_path / "movie.mp4"
    src.write_bytes(b"not a real video")
    media = Media(path=str(src), container="mp4", duration=2.0,
                  size=src.stat().st_size, type=MediaType.VIDEO)
    result = convert_mod.ConvertOperation(media, "webm").output(str(tmp_path / "out.webm")).run()
    assert not result.success
    assert "test download failure" in (result.error or "")


# --- 5. `fuse setup` fails with a useful message -------------------------------

def test_fuse_setup_shows_reason(monkeypatch, capsys):
    import fuse.cli.commands.system as system_mod
    import fuse.ffmpeg.resolver as resolver_mod

    class _FailingResolver(_NoFFmpegResolver):
        def ensure_available(self):
            return False

    monkeypatch.setattr(resolver_mod, "default_resolver", _FailingResolver())
    assert system_mod.handle_setup(None) == 1
    captured = capsys.readouterr()
    assert "Reason: test download failure" in captured.err
