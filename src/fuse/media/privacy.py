"""Privacy defaults applied to every generated media file."""



def apply_ffmpeg_privacy(args: list[str]) -> list[str]:
    """Disable automatic metadata and chapter copying for a file output.

    Technical stream properties needed for playback are left to FFmpeg. This
    removes global tags such as GPS, device, software and creation metadata
    without changing the encoded audio/video samples.
    """
    if not args or any(arg in {"-version", "-formats", "-codecs", "-filters", "-encoders", "-decoders"} for arg in args):
        return args
    # Diagnostic commands do not have a file output to sanitize.
    if str(args[-1]).startswith("-"):
        return args
    return args[:-1] + ["-map_metadata", "-1", "-map_chapters", "-1", args[-1]]
