import subprocess
from typing import List, Callable, Any
from pathlib import Path
from fuse.ffmpeg.resolver import default_resolver
from fuse.media.privacy import apply_ffmpeg_privacy
from fuse.ffmpeg.diagnostics import format_ffmpeg_error

class FFmpegExecutionError(Exception):
    pass

class FFmpegBackend:
    @staticmethod
    def run_operation(args: List[str], on_progress: Callable[[str], None] = None) -> Any:
        if not default_resolver.is_ffmpeg_available:
            raise FFmpegExecutionError("FFmpeg is not available")
            
        cmd = [str(default_resolver.ffmpeg_path), "-y"] + apply_ffmpeg_privacy(args)
        
        try:
            # We use subprocess.Popen to capture output live if we want to handle progress.
            # For simplicity, we can use subprocess.run for now if progress is not needed.
            # But the spec says "Permitir progreso". We will capture stderr line by line.
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                shell=False
            )
            
            stderr_text = ""
            if on_progress:
                stderr_lines = []
                for line in process.stderr:
                    stderr_lines.append(line)
                    on_progress(line.strip())
                stderr_text = "".join(stderr_lines)
                process.wait()
            else:
                # Read all output to prevent pipe buffer deadlock
                _, stderr_text = process.communicate()

            if process.returncode != 0:
                raise FFmpegExecutionError(
                    format_ffmpeg_error(stderr_text, process.returncode)
                )
                
            return True
        except subprocess.CalledProcessError as e:
            raise FFmpegExecutionError(f"FFmpeg failed: {e}")
        except Exception as e:
            raise FFmpegExecutionError(f"Error executing FFmpeg: {e}")
