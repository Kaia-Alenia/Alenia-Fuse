import sys
from pathlib import Path

from fuse.cli.registry import CommandArgument, register_command
from fuse.cli.utils import (
    _video_op,
)


@register_command(
    name="thumbnail",
    description_key="commands.thumbnail.description",
    category_key="categories.video",
    arguments=[
        CommandArgument(name="file", help_key="Input video file", completion="path", value_type="media_path"),
        CommandArgument(name="--at", help_key="Timestamp (default: 00:00:05)", action="store"),
        CommandArgument(name="--output", help_key="Output image file", action="store"),
    ],
)
def handle_thumbnail(args):
    file = getattr(args, "file", None)
    timestamp = getattr(args, "at", None) or "00:00:05"
    out_arg = getattr(args, "output", None)
    if not file:
        print("Usage: thumbnail <video> [--at <time>] [--output <image>]", file=sys.stderr)
        return 1
    p = Path(file)
    output = out_arg or str(p.parent / f"thumb_{p.stem}.jpg")
    return _video_op("thumbnail", file, output, "Extracting thumbnail", timestamp=timestamp)


# ─── GIF ─────────────────────────────────────────────────────────────────────


@register_command(
    name="gif",
    description_key="commands.gif.description",
    category_key="categories.video",
    arguments=[
        CommandArgument(name="file", help_key="Input video file", completion="path", value_type="media_path"),
        CommandArgument(name="--start", help_key="Start time (default: 00:00:00)", action="store"),
        CommandArgument(name="--duration", help_key="Duration in seconds (default: 5)", action="store"),
        CommandArgument(name="--fps", help_key="Frames per second (default: 10)", action="store"),
        CommandArgument(name="--width", help_key="Width in pixels (default: 480)", action="store"),
        CommandArgument(name="--output", help_key="Output GIF file", action="store"),
    ],
)
def handle_gif(args):
    file = getattr(args, "file", None)
    if not file:
        print("Usage: gif <video> [--start <time>] [--duration <secs>] [--output <file>]", file=sys.stderr)
        return 1
    p = Path(file)
    out = getattr(args, "output", None) or str(p.parent / f"{p.stem}.gif")
    start = getattr(args, "start", None) or "00:00:00"
    duration = float(getattr(args, "duration", None) or 5)
    fps = int(getattr(args, "fps", None) or 10)
    width = int(getattr(args, "width", None) or 480)
    return _video_op("gif", file, out, "Creating GIF",
                     start=start, duration=duration, fps=fps, width=width)


# ─── Frame ───────────────────────────────────────────────────────────────────


@register_command(
    name="frame",
    description_key="commands.frame.description",
    category_key="categories.video",
    arguments=[
        CommandArgument(name="file", help_key="Input video file", completion="path", value_type="media_path"),
        CommandArgument(name="--at", help_key="Timestamp (default: 00:00:00)", action="store"),
        CommandArgument(name="--output", help_key="Output image file", action="store"),
    ],
)
def handle_frame(args):
    file = getattr(args, "file", None)
    if not file:
        print("Usage: frame <video> [--at <time>] [--output <image>]", file=sys.stderr)
        return 1
    p = Path(file)
    timestamp = getattr(args, "at", None) or "00:00:00"
    out = getattr(args, "output", None) or str(p.parent / f"frame_{p.stem}.png")
    return _video_op("frame", file, out, "Extracting frame", timestamp=timestamp)


# ─── Optimize ────────────────────────────────────────────────────────────────
