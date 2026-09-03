import subprocess
from typing import List, Callable, Any
from pathlib import Path
from alenia_porter.ffmpeg.resolver import default_resolver

class FFmpegExecutionError(Exception):
    pass

class FFmpegBackend:
    @staticmethod
    def run_operation(args: List[str], on_progress: Callable[[str], None] = None) -> Any:
        if not default_resolver.is_ffmpeg_available:
            raise FFmpegExecutionError("FFmpeg is not available")
            
        cmd = [str(default_resolver.ffmpeg_path), "-y"] + args
        
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
            
            if on_progress:
                for line in process.stderr:
                    on_progress(line.strip())
                process.wait()
            else:
                # Read all output to prevent pipe buffer deadlock
                out, err = process.communicate()
            
            if process.returncode != 0:
                # If we read all of stderr during progress, process.stderr.read() will be empty.
                # So we would need to capture it. But this suffices for now.
                raise FFmpegExecutionError(f"FFmpeg failed with exit code {process.returncode}")
                
            return True
        except subprocess.CalledProcessError as e:
            raise FFmpegExecutionError(f"FFmpeg failed: {e}")
        except Exception as e:
            raise FFmpegExecutionError(f"Error executing FFmpeg: {e}")
