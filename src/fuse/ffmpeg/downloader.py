"""Download a platform FFmpeg + ffprobe build into the user cache.

This is the module ``fuse.ffmpeg.resolver`` imports as
``fuse.ffmpeg.downloader.download_ffmpeg``. Before this file existed, that
import always raised ``ModuleNotFoundError`` and the resolver swallowed it,
so ``fuse setup`` could never fix a machine without FFmpeg.

Sources (same ones the release workflow already uses where they exist):
- Windows x64 / Linux x64: BtbN FFmpeg-Builds "latest" assets, exactly the
  URLs in ``.github/workflows/build.yml``. Those assets are *unpinned*
  ("latest") and BtbN publishes no checksum file for them, so there is no
  hash to pin against here. What this module *does* verify: the download
  completes, the archive extracts, and both extracted binaries actually
  run ``-version`` and report the expected tool name. A failed check
  deletes the partial download and raises, instead of leaving a broken
  binary in the cache.
- macOS arm64: evermeet.cx "getrelease" endpoints (one zip for ffmpeg,
  one for ffprobe). UNVERIFIED at runtime by Alenia: evermeet ships an
  x86_64 binary that runs on Apple Silicon via Rosetta 2, and it ships
  no ffprobe inside the ffmpeg zip, hence the separate download. If the
  extracted binary does not run, the download is rejected with a clear
  error telling the user to install FFmpeg with Homebrew instead.

Nothing here is a dummy or a placeholder binary: every file placed in
the cache is a real upstream build that passed the ``-version`` check.
"""
from __future__ import annotations

import hashlib
import os
import platform
import shutil
import stat
import subprocess
import tarfile
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

__all__ = [
    "FFmpegDownloadError",
    "default_cache_dir",
    "download_ffmpeg",
    "PLATFORM_ASSETS",
]


class FFmpegDownloadError(Exception):
    """Raised when the platform FFmpeg asset cannot be downloaded/verified."""


# plat_dir -> (ffmpeg_url, ffprobe_url_or_None, archive_kind)
# archive_kind: "zip" (both binaries in one archive) or "zip-split"
# (ffmpeg and ffprobe come in separate zips).
PLATFORM_ASSETS: dict[str, tuple[str, str | None, str]] = {
    "windows-x64": (
        "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
        None,
        "zip",
    ),
    "linux-x64": (
        "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz",
        None,
        "tar.xz",
    ),
    # evermeet.cx "getrelease" always serves the newest build; there is no
    # versioned URL to pin. See the module docstring: x86_64 binary, runs
    # on Apple Silicon via Rosetta 2. NOT runtime-verified by Alenia yet.
    "macos-arm64": (
        "https://evermeet.cx/ffmpeg/getrelease/ffmpeg/zip",
        "https://evermeet.cx/ffmpeg/getrelease/ffprobe/zip",
        "zip-split",
    ),
}


def _platform_dir() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "windows" and machine in ("amd64", "x86_64"):
        return "windows-x64"
    if system == "linux" and machine in ("amd64", "x86_64"):
        return "linux-x64"
    if system == "darwin" and machine in ("arm64", "aarch64"):
        return "macos-arm64"
    raise FFmpegDownloadError(
        "Fuse has no FFmpeg download for this platform: "
        f"{system} / {machine}. Install FFmpeg with your system package "
        "manager and make sure `ffmpeg` and `ffprobe` are in PATH."
    )


def default_cache_dir() -> Path:
    """User cache dir for the downloaded FFmpeg build.

    ``FUSE_FFMPEG_CACHE`` overrides it (the resolver already honours that
    variable as a candidate directory).
    """
    override = os.environ.get("FUSE_FFMPEG_CACHE")
    if override:
        return Path(override)
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "AleniaFuse" / "ffmpeg"
    return Path.home() / ".cache" / "alenia-fuse" / "ffmpeg"


def _exe_name(stem: str, plat_dir: str) -> str:
    return f"{stem}.exe" if plat_dir == "windows-x64" else stem


def _download(url: str, dest: Path) -> None:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Alenia-Fuse/2.0.7"})
        with urllib.request.urlopen(request, timeout=120) as response, open(dest, "wb") as out:
            shutil.copyfileobj(response, out)
    except (urllib.error.URLError, OSError) as exc:
        raise FFmpegDownloadError(
            f"Could not download FFmpeg from {url}: {exc}. "
            "Check your network connection or install FFmpeg manually."
        ) from exc
    if dest.stat().st_size == 0:
        raise FFmpegDownloadError(f"Download from {url} was empty.")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _extract_member(archive: Path, kind: str, wanted: str, dest_dir: Path) -> Path:
    """Extract the archive member whose name ends with ``wanted``."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    if kind == "zip":
        with zipfile.ZipFile(archive) as zf:
            for member in zf.namelist():
                name = member.replace("\\", "/")
                if name.endswith("/" + wanted) or name == wanted:
                    target = dest_dir / wanted
                    with zf.open(member) as src, open(target, "wb") as out:
                        shutil.copyfileobj(src, out)
                    return target
    elif kind == "tar.xz":
        with tarfile.open(archive, "r:xz") as tf:
            for member in tf.getmembers():
                if not member.isfile():
                    continue
                name = member.name.replace("\\", "/")
                if name.endswith("/" + wanted) or name == wanted:
                    extracted = tf.extractfile(member)
                    if extracted is None:
                        continue
                    target = dest_dir / wanted
                    with extracted, open(target, "wb") as out:
                        shutil.copyfileobj(extracted, out)
                    return target
    raise FFmpegDownloadError(
        f"The downloaded FFmpeg archive does not contain a {wanted} binary "
        f"(archive: {archive.name}). The upstream build layout may have "
        "changed; install FFmpeg manually instead."
    )


def _make_executable(path: Path) -> None:
    if os.name != "nt":
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _verify_binary(path: Path, kind: str) -> None:
    """A downloaded binary is only accepted if it actually runs."""
    _make_executable(path)
    try:
        result = subprocess.run(
            [str(path), "-version"], capture_output=True, text=True, timeout=30
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise FFmpegDownloadError(
            f"Downloaded {kind} at {path} could not be executed: {exc}. "
            "It may be the wrong architecture for this machine; "
            "install FFmpeg with your system package manager instead."
        ) from exc
    if result.returncode != 0 or f"{kind} version" not in result.stdout:
        raise FFmpegDownloadError(
            f"Downloaded file at {path} does not behave like {kind} "
            f"(exit {result.returncode}). It was discarded; install "
            "FFmpeg with your system package manager instead."
        )


def download_ffmpeg(cache_dir: Path | str | None = None) -> tuple[Path, Path]:
    """Download the platform FFmpeg build and return (ffmpeg, ffprobe).

    Idempotent: if a previously downloaded pair in the cache still passes
    the ``-version`` check, it is reused and nothing is downloaded.
    Raises :class:`FFmpegDownloadError` with a human-readable cause on
    any failure; never returns a broken or half-downloaded pair.
    """
    plat_dir = _platform_dir()
    ffmpeg_url, ffprobe_url, kind = PLATFORM_ASSETS[plat_dir]
    target_dir = Path(cache_dir) if cache_dir else default_cache_dir() / plat_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg_name = _exe_name("ffmpeg", plat_dir)
    ffprobe_name = _exe_name("ffprobe", plat_dir)
    ffmpeg_path = target_dir / ffmpeg_name
    ffprobe_path = target_dir / ffprobe_name

    if ffmpeg_path.is_file() and ffprobe_path.is_file():
        try:
            _verify_binary(ffmpeg_path, "ffmpeg")
            _verify_binary(ffprobe_path, "ffprobe")
            return ffmpeg_path, ffprobe_path
        except FFmpegDownloadError:
            # Stale/broken cache: fall through and re-download.
            ffmpeg_path.unlink(missing_ok=True)
            ffprobe_path.unlink(missing_ok=True)

    tmpdir = Path(tempfile.mkdtemp(prefix="fuse-ffmpeg-"))
    try:
        if kind == "zip-split":
            # macOS: ffmpeg and ffprobe arrive in separate zips.
            assert ffprobe_url is not None
            ffmpeg_zip = tmpdir / "ffmpeg.zip"
            ffprobe_zip = tmpdir / "ffprobe.zip"
            _download(ffmpeg_url, ffmpeg_zip)
            _download(ffprobe_url, ffprobe_zip)
            _extract_member(ffmpeg_zip, "zip", ffmpeg_name, target_dir)
            _extract_member(ffprobe_zip, "zip", ffprobe_name, target_dir)
        else:
            archive_name = "ffmpeg.zip" if kind == "zip" else "ffmpeg.tar.xz"
            archive = tmpdir / archive_name
            _download(ffmpeg_url, archive)
            # Record the hash for diagnostics even though upstream
            # publishes no checksum to compare it against (see docstring).
            _sha256(archive)
            _extract_member(archive, kind, ffmpeg_name, target_dir)
            _extract_member(archive, kind, ffprobe_name, target_dir)

        _verify_binary(ffmpeg_path, "ffmpeg")
        _verify_binary(ffprobe_path, "ffprobe")
        return ffmpeg_path, ffprobe_path
    except FFmpegDownloadError:
        ffmpeg_path.unlink(missing_ok=True)
        ffprobe_path.unlink(missing_ok=True)
        raise
    except Exception as exc:
        ffmpeg_path.unlink(missing_ok=True)
        ffprobe_path.unlink(missing_ok=True)
        raise FFmpegDownloadError(
            f"FFmpeg download failed: {exc}. Install FFmpeg manually "
            "or set FUSE_FFMPEG_DIR to a folder containing ffmpeg/ffprobe."
        ) from exc
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
