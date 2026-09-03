import os
import platform
import subprocess
from pathlib import Path
from typing import Optional, Dict

class FFmpegUnavailableError(Exception):
    pass

class UnsupportedPlatformError(Exception):
    pass

class FFmpegResolver:
    def __init__(self):
        self.project_root = self._get_project_root()
        self.ffmpeg_path: Optional[Path] = None
        self.ffprobe_path: Optional[Path] = None
        self.version_info: Dict[str, str] = {}
        
        self.resolve()

    def _get_project_root(self) -> Path:
        current_file = Path(__file__).resolve()
        # Navigate up: ffmpeg/ <- alenia_porter/ <- src/ <- project_root
        return current_file.parents[3]

    def _get_platform_dir_and_ext(self):
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        if system == "windows":
            if machine in ["amd64", "x86_64"]:
                return "windows-x64", ".exe"
            else:
                raise UnsupportedPlatformError(f"Alenia-Porter does not include an FFmpeg build for:\\nPlatform: {system}\\nArchitecture: {machine}")
        elif system == "linux":
            if machine in ["amd64", "x86_64"]:
                return "linux-x64", ""
            else:
                raise UnsupportedPlatformError(f"Alenia-Porter does not include an FFmpeg build for:\\nPlatform: {system}\\nArchitecture: {machine}")
        elif system == "darwin":
            if machine in ["arm64", "aarch64"]:
                return "macos-arm64", ""
            else:
                raise UnsupportedPlatformError(f"Alenia-Porter does not include an FFmpeg build for:\\nPlatform: {system}\\nArchitecture: {machine}")
        else:
            raise UnsupportedPlatformError(f"Alenia-Porter does not include an FFmpeg build for:\\nPlatform: {system}\\nArchitecture: {machine}")

    def resolve(self):
        plat_dir, ext = self._get_platform_dir_and_ext()
        bin_dir = self.project_root / "bin" / plat_dir
        
        ffmpeg = bin_dir / f"ffmpeg{ext}"
        ffprobe = bin_dir / f"ffprobe{ext}"
        
        if not ffmpeg.exists():
            raise FFmpegUnavailableError(f"Bundled FFmpeg not found at {ffmpeg}")
        if not ffprobe.exists():
            raise FFmpegUnavailableError(f"Bundled FFprobe not found at {ffprobe}")
            
        # Verify they are executable
        if not os.access(ffmpeg, os.X_OK):
            raise FFmpegUnavailableError(f"FFmpeg binary at {ffmpeg} is not executable")
        if not os.access(ffprobe, os.X_OK):
            raise FFmpegUnavailableError(f"FFprobe binary at {ffprobe} is not executable")
            
        # Verify by running -version
        self.ffmpeg_path = ffmpeg
        self.ffprobe_path = ffprobe
        
        try:
            result = subprocess.run([str(self.ffmpeg_path), "-version"], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE, 
                                    text=True, 
                                    shell=False,
                                    check=True)
            if "ffmpeg version" not in result.stdout:
                raise FFmpegUnavailableError("Binary responded but does not appear to be a real FFmpeg.")
                
            first_line = result.stdout.splitlines()[0]
            self.version_info["ffmpeg"] = first_line
        except subprocess.CalledProcessError as e:
            raise FFmpegUnavailableError(f"FFmpeg failed to run -version. Exit code: {e.returncode}")
        except Exception as e:
            raise FFmpegUnavailableError(f"Error executing FFmpeg: {e}")
            
        try:
            result = subprocess.run([str(self.ffprobe_path), "-version"], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE, 
                                    text=True, 
                                    shell=False,
                                    check=True)
            if "ffprobe version" not in result.stdout:
                raise FFmpegUnavailableError("Binary responded but does not appear to be a real FFprobe.")
                
            first_line = result.stdout.splitlines()[0]
            self.version_info["ffprobe"] = first_line
        except subprocess.CalledProcessError as e:
            raise FFmpegUnavailableError(f"FFprobe failed to run -version. Exit code: {e.returncode}")
        except Exception as e:
            raise FFmpegUnavailableError(f"Error executing FFprobe: {e}")

    @property
    def is_ffmpeg_available(self) -> bool:
        return self.ffmpeg_path is not None and self.ffmpeg_path.exists()

default_resolver = FFmpegResolver()
