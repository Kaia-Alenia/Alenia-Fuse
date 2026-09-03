import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

class FFmpegResolver:
    """Resolves and validates FFmpeg and FFprobe executables."""

    def __init__(self):
        self._ffmpeg_path: Optional[str] = None
        self._ffprobe_path: Optional[str] = None
        self._is_resolved = False

    def _get_project_root(self) -> Path:
        # Assuming this file is at src/alenia_porter/ffmpeg/resolver.py
        # project root would be 4 levels up: src/alenia_porter/ffmpeg -> alenia_porter -> src -> root
        return Path(__file__).resolve().parent.parent.parent.parent

    def _find_bundled(self, executable: str) -> Optional[str]:
        # Platform extension
        exts = [".exe", ".bat"] if os.name == "nt" else [""]
        
        # Check project root bin/
        root = self._get_project_root()
        
        for ext in exts:
            exec_name = f"{executable}{ext}"
            bin_path = root / "bin" / exec_name
            
            if bin_path.exists() and os.access(bin_path, os.X_OK):
                return str(bin_path)
            
            # Check inside package bin/ (for installed package)
            pkg_bin_path = Path(__file__).resolve().parent.parent / "bin" / exec_name
            if pkg_bin_path.exists() and os.access(pkg_bin_path, os.X_OK):
                return str(pkg_bin_path)
                
        return None

    def _find_system(self, executable: str) -> Optional[str]:
        # Fallback to system PATH only if explicitly permitted (as per rule 5A.2 fallback)
        import shutil
        return shutil.which(executable)

    def resolve(self) -> None:
        """Locates the executables prioritizing bundled versions."""
        if self._is_resolved:
            return

        self._ffmpeg_path = self._find_bundled("ffmpeg")
        self._ffprobe_path = self._find_bundled("ffprobe")

        # Fallback to system if not found (only as last resort)
        if not self._ffmpeg_path:
            self._ffmpeg_path = self._find_system("ffmpeg")
        
        if not self._ffprobe_path:
            self._ffprobe_path = self._find_system("ffprobe")
            
        self._is_resolved = True

    @property
    def ffmpeg_path(self) -> Optional[str]:
        self.resolve()
        return self._ffmpeg_path

    @property
    def ffprobe_path(self) -> Optional[str]:
        self.resolve()
        return self._ffprobe_path

    @property
    def is_ffmpeg_available(self) -> bool:
        return self.ffmpeg_path is not None

    @property
    def is_ffprobe_available(self) -> bool:
        return self.ffprobe_path is not None

    def get_version(self) -> Optional[str]:
        if not self.is_ffmpeg_available:
            return None
            
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            # Usually the first line contains the version
            return result.stdout.split('\n')[0]
        except (subprocess.SubprocessError, FileNotFoundError):
            return None

default_resolver = FFmpegResolver()
