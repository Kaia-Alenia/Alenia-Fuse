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
        
        self.resolve()

    def _get_platform_dir_and_ext(self):
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        if system == "windows":
            if machine in ["amd64", "x86_64"]:
                return "windows-x64", ".exe"
            else:
                raise UnsupportedPlatformError(f"Fuse does not include an FFmpeg build for:\\nPlatform: {system}\\nArchitecture: {machine}")
        elif system == "linux":
            if machine in ["amd64", "x86_64"]:
                return "linux-x64", ""
            else:
                raise UnsupportedPlatformError(f"Fuse does not include an FFmpeg build for:\\nPlatform: {system}\\nArchitecture: {machine}")
        elif system == "darwin":
            if machine in ["arm64", "aarch64"]:
                return "macos-arm64", ""
            else:
                raise UnsupportedPlatformError(f"Fuse does not include an FFmpeg build for:\\nPlatform: {system}\\nArchitecture: {machine}")
        else:
            raise UnsupportedPlatformError(f"Fuse does not include an FFmpeg build for:\\nPlatform: {system}\\nArchitecture: {machine}")

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
                    return

        # Lean pip installs use the operating system package manager instead
        # of shipping 100+ MB executables inside the wheel.
        system_ffmpeg = shutil.which("ffmpeg")
        system_ffprobe = shutil.which("ffprobe")
        if system_ffmpeg and self._verify(Path(system_ffmpeg), "ffmpeg"):
            self._set_paths(Path(system_ffmpeg), Path(system_ffprobe) if system_ffprobe else None)
            if self.ffprobe_path:
                self._verify(self.ffprobe_path, "ffprobe")

    def _set_paths(self, ffmpeg: Path, ffprobe: Path | None):
        self.ffmpeg_path = ffmpeg
        self.ffprobe_path = ffprobe

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
        return self.ffmpeg_path is not None and self.ffmpeg_path.exists()

default_resolver = FFmpegResolver()
