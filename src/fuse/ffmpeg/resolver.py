import os
import platform
import shutil
import subprocess
from pathlib import Path


class FFmpegUnavailableError(Exception):
    pass

class UnsupportedPlatformError(Exception):
    pass

class FFmpegResolver:
    def __init__(self):
        self.ffmpeg_path: Path | None = None
        self.ffprobe_path: Path | None = None
        self.version_info: dict[str, str] = {}
        self._download_attempted = False
        # The real reason FFmpeg is unavailable, when it is. Previously the
        # download failure was swallowed by a bare `except: return False`,
        # so users only ever saw "FFmpeg is not available" with no cause.
        self.last_error: str | None = None
        self.ffprobe_missing: bool = False

        self.resolve()

    @property
    def unavailable_reason(self) -> str:
        """Human-readable cause for FFmpeg being unavailable (or '')."""
        if self.is_ffmpeg_available:
            return ""
        return self.last_error or (
            "FFmpeg was not found in FUSE_FFMPEG_DIR, the bundled _bin "
            "folder, the user cache, or the system PATH."
        )

    def _get_platform_dir_and_ext(self):
        system = platform.system().lower()
        machine = platform.machine().lower()

        if system == "windows":
            if machine in ["amd64", "x86_64"]:
                return "windows-x64", ".exe"
            else:
                raise UnsupportedPlatformError(f"Fuse does not include an FFmpeg build for:\nPlatform: {system}\nArchitecture: {machine}")
        elif system == "linux":
            if machine in ["amd64", "x86_64"]:
                return "linux-x64", ""
            else:
                raise UnsupportedPlatformError(f"Fuse does not include an FFmpeg build for:\nPlatform: {system}\nArchitecture: {machine}")
        elif system == "darwin":
            if machine in ["arm64", "aarch64"]:
                return "macos-arm64", ""
            else:
                raise UnsupportedPlatformError(f"Fuse does not include an FFmpeg build for:\nPlatform: {system}\nArchitecture: {machine}")
        else:
            raise UnsupportedPlatformError(f"Fuse does not include an FFmpeg build for:\nPlatform: {system}\nArchitecture: {machine}")

    def resolve(self):
        candidates = []
        env_dir = os.environ.get("FUSE_FFMPEG_DIR")
        if env_dir:
            candidates.append(Path(env_dir))

        try:
            plat_dir, ext = self._get_platform_dir_and_ext()
            from importlib.resources import files
            candidates.append(Path(str(files("fuse") / "_bin" / plat_dir)))
        except (UnsupportedPlatformError, ImportError):
            ext = ".exe" if os.name == "nt" else ""

        # A user cache is intentionally supported, but Fuse never downloads
        # binaries implicitly. Downloads belong to an explicit setup command.
        cache_root = os.environ.get("FUSE_FFMPEG_CACHE")
        if cache_root:
            candidates.append(Path(cache_root))
        else:
            # The downloader's default cache (~/.cache/alenia-fuse/ffmpeg)
            # is a candidate too, so a previous `fuse setup` is reused.
            try:
                from fuse.ffmpeg.downloader import default_cache_dir
                candidates.append(default_cache_dir() / self._get_platform_dir_and_ext()[0])
            except Exception:
                pass

        names = [f"ffmpeg{ext}", "ffmpeg.exe" if ext != ".exe" else "ffmpeg"]
        probe_names = [f"ffprobe{ext}", "ffprobe.exe" if ext != ".exe" else "ffprobe"]
        for directory in candidates:
            ffmpeg = directory / names[0]
            ffprobe = directory / probe_names[0]
            if ffmpeg.is_file():
                self._set_paths(ffmpeg, ffprobe if ffprobe.is_file() else None)
                if self._verify(self.ffmpeg_path, "ffmpeg"):
                    if self.ffprobe_path:
                        self._verify(self.ffprobe_path, "ffprobe")
                    else:
                        self._note_missing_ffprobe(ffmpeg)
                    return

        # Lean pip installs use the operating system package manager instead
        # of shipping 100+ MB executables inside the wheel.
        system_ffmpeg = shutil.which("ffmpeg")
        system_ffprobe = shutil.which("ffprobe")
        if system_ffmpeg and self._verify(Path(system_ffmpeg), "ffmpeg"):
            ffprobe = Path(system_ffprobe) if system_ffprobe else self._sibling_ffprobe(Path(system_ffmpeg))
            self._set_paths(Path(system_ffmpeg), ffprobe)
            if self.ffprobe_path:
                self._verify(self.ffprobe_path, "ffprobe")
            else:
                self._note_missing_ffprobe(Path(system_ffmpeg))

    def _sibling_ffprobe(self, ffmpeg_path: Path) -> Path | None:
        """ffprobe usually ships next to ffmpeg even when not in PATH."""
        ext = ffmpeg_path.suffix
        candidate = ffmpeg_path.parent / f"ffprobe{ext}"
        if candidate.is_file():
            return candidate
        return None

    def _note_missing_ffprobe(self, ffmpeg_path: Path) -> None:
        self.ffprobe_missing = True
        self.last_error = (
            f"FFmpeg was found at {ffmpeg_path} but ffprobe is missing "
            "(checked PATH and the folder next to ffmpeg). "
            "Install a complete FFmpeg build that includes ffprobe, "
            "or set FUSE_FFMPEG_DIR to a folder containing both."
        )

    def _set_paths(self, ffmpeg: Path, ffprobe: Path | None):
        self.ffmpeg_path = ffmpeg
        self.ffprobe_path = ffprobe
        self.ffprobe_missing = ffprobe is None

    def _verify(self, path: Path | None, kind: str) -> bool:
        if not path or not path.exists():
            return False
        try:
            result = subprocess.run([str(path), "-version"], capture_output=True,
                                    text=True, shell=False,
                                    check=True)
            marker = f"{kind} version"
            if marker not in result.stdout:
                return False
            self.version_info[kind] = result.stdout.splitlines()[0]
            return True
        except (OSError, subprocess.SubprocessError):
            return False

    @property
    def is_ffmpeg_available(self) -> bool:
        if self.ffmpeg_path is not None and self.ffmpeg_path.exists():
            return True
        if self._download_attempted or os.environ.get("FUSE_DISABLE_FFMPEG_DOWNLOAD") == "1":
            return False
        self._download_attempted = True
        try:
            from fuse.ffmpeg.downloader import download_ffmpeg
            ffmpeg, ffprobe = download_ffmpeg()
            self._set_paths(ffmpeg, ffprobe)
            return self._verify(ffmpeg, "ffmpeg") and self._verify(ffprobe, "ffprobe")
        except Exception as exc:
            # Do NOT swallow the cause: record it so `fuse setup` and
            # every conversion can show the user why it failed.
            self.last_error = (
                f"Automatic FFmpeg download failed: {exc}. "
                "Install FFmpeg manually (see https://ffmpeg.org/download.html) "
                "or set FUSE_FFMPEG_DIR to a folder containing ffmpeg and ffprobe."
            )
            return False

    @property
    def is_ffprobe_available(self) -> bool:
        return self.ffprobe_path is not None and self.ffprobe_path.exists()

    def ensure_available(self) -> bool:
        """Explicit setup entry point used by `fuse setup`."""
        self._download_attempted = False
        return self.is_ffmpeg_available

default_resolver = FFmpegResolver()
