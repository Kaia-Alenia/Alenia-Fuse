import sys
from pathlib import Path

from fuse.cli.registry import CommandArgument, register_command
from fuse.cli.utils import (
    _video_op,
)


@register_command(
    name="metadata",
    description_key="commands.metadata.description",
    category_key="categories.general",
    arguments=[
        CommandArgument(name="file", help_key="Input file", completion="path", value_type="media_path"),
        CommandArgument(name="--title", help_key="Title tag", action="store"),
        CommandArgument(name="--artist", help_key="Artist tag", action="store"),
        CommandArgument(name="--album", help_key="Album tag", action="store"),
        CommandArgument(name="--year", help_key="Year tag", action="store"),
        CommandArgument(name="--output", help_key="Output file (default: overwrites input)", action="store"),
    ],
)
def handle_metadata(args):
    file = getattr(args, "file", None)
    if not file:
        print("Usage: metadata <file> [--title <t>] [--artist <a>] ...", file=sys.stderr)
        return 1
    p = Path(file)
    out = getattr(args, "output", None) or str(p.parent / f"meta_{p.name}")
    title = getattr(args, "title", None) or ""
    artist = getattr(args, "artist", None) or ""
    album = getattr(args, "album", None) or ""
    year = getattr(args, "year", None) or ""
    return _video_op("metadata", file, out, "Setting metadata",
                     title=title, artist=artist, album=album, year=year)


# --- Hardware -------------------------------------------------------------------
