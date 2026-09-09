import os
import sys
from pathlib import Path
from fuse.cli.registry import register_command, CommandArgument
from fuse.i18n.manager import t
from fuse.media.models import Media
from fuse.api.result import OperationResult
from fuse.cli.batch import get_auto_output_path, prompt_batch_formats
from fuse.cli.utils import (
    resolve_inputs, require_file, confirm_overwrite,
    build_progress_callback, finish_progress, friendly_error,
    _audio_op,
)

@register_command(name="audio-info", description_key="commands.audio-info.description",
                  arguments=[CommandArgument(name="file", help_key="Input audio file")])
def handle_audio_info(args):
    try:
        media = require_file(args.file)
        audio_streams = [s for s in media.streams if s.codec_type == "audio"]
        
        if not audio_streams:
            print("  No audio streams found in this file.", file=sys.stderr)
            return 1
            
        print(f"\n  Audio info for : {media.path}")
        for idx, s in enumerate(audio_streams, 1):
            bitrate_str = f"{s.bitrate // 1000} kbps" if s.bitrate else "Unknown"
            sample_rate_str = f"{s.sample_rate} Hz" if s.sample_rate else "Unknown"
            print(f"  Stream #{idx}:")
            print(f"    - Bitrate    : {bitrate_str}")
            print(f"    - Sample Rate: {sample_rate_str}")
            print(f"    - Channels   : {s.channels}")
            print(f"    - Codec      : {s.codec_name}")
        print()
        return 0
    except Exception as e:
        print(f"\n  Error: {friendly_error(e)}", file=sys.stderr)
        return 1

@register_command(name="volume", description_key="commands.volume.description",
                  arguments=[CommandArgument(name="file", help_key="Input file"),
                             CommandArgument(name="value", help_key="Volume change: +20%, -10%, 1.5")])
def handle_volume(args):
    return _audio_op("volume", args.file, None, "Adjusting volume", value=args.value)



@register_command(name="normalize", description_key="commands.normalize.description",
                  arguments=[CommandArgument(name="file", help_key="Input file")])
def handle_normalize(args):
    return _audio_op("normalize", args.file, None, "Normalizing")



@register_command(name="fade", description_key="commands.fade.description",
                  arguments=[CommandArgument(name="file", help_key="Input file"),
                             CommandArgument(name="type", help_key="in or out"),
                             CommandArgument(name="--duration", help_key="Fade duration in seconds", action="store")])
def handle_fade(args):
    fade_type = getattr(args, "type", "in")
    dur = float(getattr(args, "duration", None) or 3.0)
    return _audio_op("fade", args.file, None, f"Fading {fade_type}", fade_type=fade_type, duration=dur)


# ─── Inspection commands ─────────────────────────────────────────────────────
