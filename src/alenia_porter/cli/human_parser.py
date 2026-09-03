"""
Human-syntax parser for Alenia Porter CLI.

Supports:
  convert input.mp4 to webm
  convert input.mp4 output.webm
  trim movie.mp4 from 00:01:00 to 00:02:00
  extract audio from movie.mp4
  resize movie.mp4 1280x720
  speed movie.mp4 2x
"""
import re
import sys
from typing import List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ParsedCommand:
    command: str
    args: dict


def parse_human_syntax(tokens: List[str]) -> Optional[ParsedCommand]:
    """
    Attempt to parse human-friendly syntax before falling back to argparse.
    Returns a ParsedCommand if recognized, None otherwise.
    """
    if not tokens:
        return None

    cmd = tokens[0].lower()

    # "convert input.mp4 to webm" OR "convert input.mp4 output.webm"
    if cmd == "convert" and len(tokens) >= 3:
        if tokens[2].lower() == "to" and len(tokens) >= 4:
            # convert X to FORMAT -> auto-name output
            input_file = tokens[1]
            target_fmt = tokens[3].lstrip(".")
            ext = f".{target_fmt}"
            import os
            base = os.path.splitext(input_file)[0]
            output_file = base + ext
            return ParsedCommand("convert", {"input": input_file, "output": output_file})
        elif not tokens[2].startswith("--"):
            # convert X output.ext
            return ParsedCommand("convert", {"input": tokens[1], "output": tokens[2]})

    # "trim movie.mp4 from 00:01:00 to 00:02:00"
    if cmd == "trim" and len(tokens) >= 2:
        file = tokens[1]
        start = "00:00:00"
        end = None
        rest = tokens[2:]
        if "from" in [t.lower() for t in rest]:
            idx = [t.lower() for t in rest].index("from")
            if idx + 1 < len(rest):
                start = rest[idx + 1]
        if "to" in [t.lower() for t in rest]:
            idx = [t.lower() for t in rest].index("to")
            if idx + 1 < len(rest):
                end = rest[idx + 1]
        return ParsedCommand("trim", {"file": file, "start": start, "end": end})

    # "extract audio from movie.mp4" / "extract audio movie.mp4"
    if cmd in ("extract", "extract-audio") and len(tokens) >= 2:
        if tokens[1].lower() == "audio":
            file = tokens[3] if len(tokens) >= 4 and tokens[2].lower() == "from" else (
                tokens[2] if len(tokens) >= 3 else None
            )
            if file:
                return ParsedCommand("extract-audio", {"file": file})

    # "resize movie.mp4 1280x720"
    if cmd == "resize" and len(tokens) >= 3:
        size_pat = re.match(r"(\d+)[xX](\d+)", tokens[2])
        if size_pat:
            return ParsedCommand("resize", {
                "file": tokens[1],
                "width": int(size_pat.group(1)),
                "height": int(size_pat.group(2))
            })

    # "rotate movie.mp4 90"
    if cmd == "rotate" and len(tokens) >= 3:
        try:
            deg = int(tokens[2])
            return ParsedCommand("rotate", {"file": tokens[1], "degrees": deg})
        except ValueError:
            pass

    # "fps movie.mp4 60"
    if cmd == "fps" and len(tokens) >= 3:
        try:
            new_fps = float(tokens[2])
            return ParsedCommand("fps", {"file": tokens[1], "fps": new_fps})
        except ValueError:
            pass

    # "speed movie.mp4 2x" or "speed movie.mp4 2"
    if cmd == "speed" and len(tokens) >= 3:
        val_str = tokens[2].rstrip("x")
        try:
            factor = float(val_str)
            return ParsedCommand("speed", {"file": tokens[1], "factor": factor})
        except ValueError:
            pass

    # "mute movie.mp4"
    if cmd == "mute" and len(tokens) >= 2:
        return ParsedCommand("mute", {"file": tokens[1]})

    # "thumbnail movie.mp4" or "thumbnail movie.mp4 at 00:00:10"
    if cmd == "thumbnail" and len(tokens) >= 2:
        timestamp = "00:00:05"
        if "at" in [t.lower() for t in tokens]:
            idx = [t.lower() for t in tokens].index("at")
            if idx + 1 < len(tokens):
                timestamp = tokens[idx + 1]
        return ParsedCommand("thumbnail", {"file": tokens[1], "timestamp": timestamp})

    # "gif movie.mp4"
    if cmd == "gif" and len(tokens) >= 2:
        return ParsedCommand("gif", {"file": tokens[1]})

    # "volume song.mp3 +20%" or "volume song.mp3 1.5"
    if cmd == "volume" and len(tokens) >= 3:
        return ParsedCommand("volume", {"file": tokens[1], "value": tokens[2]})

    # "normalize song.mp3"
    if cmd == "normalize" and len(tokens) >= 2:
        return ParsedCommand("normalize", {"file": tokens[1]})

    # "fade song.mp3 in 3s"
    if cmd == "fade" and len(tokens) >= 2:
        file = tokens[1]
        fade_type = "in"
        duration = 3.0
        if len(tokens) >= 3 and tokens[2].lower() in ("in", "out"):
            fade_type = tokens[2].lower()
        if len(tokens) >= 4:
            try:
                duration = float(tokens[3].rstrip("s"))
            except ValueError:
                pass
        return ParsedCommand("fade", {"file": file, "fade_type": fade_type, "duration": duration})

    # "compress movie.mp4" (no flags — pass through)
    if cmd == "compress" and len(tokens) >= 2 and not tokens[1].startswith("-"):
        return ParsedCommand("compress", {"file": tokens[1]})

    # "info file" / "analyze file"
    if cmd in ("info", "analyze") and len(tokens) >= 2:
        return ParsedCommand(cmd, {"file": tokens[1]})

    # "remux input.mp4 output.mkv"
    if cmd == "remux" and len(tokens) >= 3:
        return ParsedCommand("remux", {"input": tokens[1], "output": tokens[2]})

    return None
