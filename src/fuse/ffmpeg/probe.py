import subprocess
import json
from typing import Dict, Any, List
from pathlib import Path
from fuse.ffmpeg.resolver import default_resolver

class FFprobeError(Exception):
    pass

def probe(file_path: Path) -> Dict[str, Any]:
    """
    Executes ffprobe to get metadata and stream information in JSON format.
    """
    if not default_resolver.is_ffmpeg_available:
        raise FFprobeError("FFprobe is not available")
        
    cmd = [
        str(default_resolver.ffprobe_path),
        "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(file_path)
    ]
    
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        raise FFprobeError(f"FFprobe failed with code {e.returncode}: {e.stderr}")
    except json.JSONDecodeError as e:
        raise FFprobeError(f"Failed to parse FFprobe JSON output: {e}")
    except Exception as e:
        raise FFprobeError(f"Error executing FFprobe: {e}")
