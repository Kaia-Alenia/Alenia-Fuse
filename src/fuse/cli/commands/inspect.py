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
)

@register_command(
    name="info",
    description_key="commands.info.description",
    aliases=["analyze"],
    arguments=[CommandArgument(name="file", help_key="Media file to inspect")]
)
def handle_info(args):
    file = getattr(args, "file", None)
    if not file:
        print("Error: provide a file path.", file=sys.stderr)
        return 1
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.text import Text
        from rich import box

        media = require_file(file)
        console = Console(highlight=False)

        dur_secs = media.duration or 0
        h = int(dur_secs // 3600)
        m = int((dur_secs % 3600) // 60)
        s = int(dur_secs % 60)
        dur_str = f"{h:02d}:{m:02d}:{s:02d}" if dur_secs else "N/A"
        size_mb = media.size / 1024 / 1024

        console.print()
        console.print(f"  [bold #8B5CF6]◈ {Path(file).name}[/]")
        console.print(f"  [dim]Container:[/] [white]{media.container}[/]   "
                      f"[dim]Duration:[/] [white]{dur_str}[/]   "
                      f"[dim]Size:[/] [white]{size_mb:.2f} MB[/]")
        console.print()

        if media.streams:
            table = Table(box=box.SIMPLE_HEAD, show_header=True,
                          header_style="bold #A78BFA", border_style="#2D2B55",
                          padding=(0, 1))
            table.add_column("Stream", style="dim", width=8)
            table.add_column("Type",   style="#22D3EE", width=7)
            table.add_column("Codec",  style="white", width=12)
            table.add_column("Details", style="#CBD5E1")

            for st in media.streams:
                if st.codec_type == "video":
                    fps_str = f"{st.fps:.2f} fps" if st.fps else ""
                    detail = f"{st.width}x{st.height}  {fps_str}  {st.pix_fmt or ''}"
                elif st.codec_type == "audio":
                    detail = f"{st.sample_rate or '?'} Hz  {st.channels or '?'} ch"
                    if st.bitrate:
                        detail += f"  {st.bitrate // 1000} kbps"
                else:
                    detail = ""
                table.add_row(f"#{st.index}", st.codec_type, st.codec_name, detail.strip())

            console.print(table)
        else:
            console.print("  [dim]No streams found.[/]")

        console.print()
    except Exception as exc:
        print(f"\n  Error: {friendly_error(exc)}", file=sys.stderr)
        return 1
    return 0


# ─── convert ────────────────────────────────────────────────────────────────


@register_command(
    name="formats",
    description_key="commands.formats.description",
    arguments=[
        CommandArgument(
            name="input",
            help_key="Optional: category (video/audio/image) or media file path",
            nargs="?",
            action="store",
            completion="path",
        )
    ],
)
def handle_formats(args):
    from fuse.capabilities.policies import ALL_TARGETS, VIDEO_TARGETS, AUDIO_TARGETS, IMAGE_TARGETS, ANIMATED_TARGETS

    cat_filter = getattr(args, "input", None) or getattr(args, "category", None)

    # ── /formats <file> — contextual targets for a real media file (§12) ──────
    if cat_filter and Path(cat_filter).is_file():
        try:
            from fuse.media.models import Media
            from fuse.capabilities.engine import get_valid_targets
            media = Media.inspect(cat_filter)
            caps = get_valid_targets(media)
            recommended = [c for c in caps if c.target_kind in ("video", "audio", "image", "animated_image")]
            print(f"\n  Valid targets for {Path(cat_filter).name}\n")
            # Group by kind
            by_kind = {}
            for c in recommended:
                by_kind.setdefault(c.target_kind, []).append(c)
            order = ["video", "audio", "image", "animated_image"]
            for kind in order:
                if kind not in by_kind:
                    continue
                label = kind.replace("_", " ").title()
                print(f"  {label}")
                for c in sorted(by_kind[kind], key=lambda x: x.target_id):
                    from fuse.capabilities.policies import TARGET_BY_ID
                    t = TARGET_BY_ID.get(c.target_id)
                    display = t.display_name if t else c.target_id.upper()
                    print(f"    {display:<12} {c.target_extension}")
                print()
            print(f"  Total: {len(recommended)} valid target(s)\n")
        except Exception as exc:
            print(f"\n  Error analyzing file: {exc}\n", file=sys.stderr)
            return 1
        return 0

    # ── /formats [category] — product catalog listing ────────────────────────
    cat_map = {
        "video": ("Video / Containers", VIDEO_TARGETS),
        "audio": ("Audio", AUDIO_TARGETS),
        "image": ("Images", IMAGE_TARGETS + ANIMATED_TARGETS),
    }

    if cat_filter and cat_filter.lower() in cat_map:
        cat_key = cat_filter.lower()
        label, targets = cat_map[cat_key]
        print(f"\n  ALENIA FUSE — {label.upper()}\n")
        for tgt in sorted(targets, key=lambda x: x.display_name):
            exts = "  ".join(tgt.extensions)
            print(f"    {tgt.display_name:<16} {exts}")
        print(f"\n  Total: {len(targets)} format(s)\n")
        return 0

    if cat_filter and not Path(cat_filter).is_file():
        print(f"\n  Unknown: '{cat_filter}'")
        print("  Use: video  audio  image  or a media file path\n")
        return 1

    # ── No argument: overview ─────────────────────────────────────────────────
    print("\n  ALENIA FUSE — OUTPUT FORMATS\n")
    for cat_key, (cat_label, targets) in cat_map.items():
        names = sorted(tgt.display_name for tgt in targets)
        print(f"  {cat_label}")
        if len(names) > 6:
            print("    " + "   ".join(names[:6]) + "   ...")
            print(f"    + {len(names) - 6} more\n")
        else:
            print("    " + "   ".join(names) + "\n")

    print("  Use:")
    print("    fuse formats video")
    print("    fuse formats audio")
    print("    fuse formats image")
    print("    fuse formats <file>   # targets for a specific file\n")
    print("  Inside Fuse:")
    print("    /formats\n")
    return 0



@register_command(name="codecs", description_key="commands.codecs.description",
                  arguments=[])
def handle_codecs(args):
    from fuse.ffmpeg.capabilities import default_registry
    default_registry.load_from_ffmpeg()
    codecs = sorted(default_registry.codecs)
    print(f"\n  Supported codecs ({len(codecs)} total):\n")
    for i in range(0, len(codecs), 6):
        row = codecs[i:i+6]
        print("  " + "  ".join(f"{c:<16}" for c in row))
    print()
    return 0



@register_command(
    name="hardware",
    description_key="commands.hardware.description",
    category_key="categories.general",
    arguments=[],
)
def handle_hardware(args):
    from fuse.ffmpeg.capabilities import default_registry
    default_registry.load_from_ffmpeg()
    hw_prefixes = ("nvenc", "amf", "qsv", "videotoolbox", "vaapi", "vulkan")
    hw_encoders = [e for e in sorted(default_registry.encoders) if any(e.endswith(p) for p in hw_prefixes)]
    print(f"\n  Hardware encoders ({len(hw_encoders)} found):\n")
    if hw_encoders:
        for enc in hw_encoders:
            print(f"    {enc}")
    else:
        print("    None detected in bundled FFmpeg")
    print()
    return 0


# --- Filters -------------------------------------------------------------------


@register_command(
    name="filters",
    description_key="commands.filters.description",
    category_key="categories.general",
    arguments=[CommandArgument(name="search", help_key="Filter name to search for", nargs="?", action="store")],
)
def handle_filters(args):
    from fuse.ffmpeg.capabilities import default_registry
    default_registry.load_from_ffmpeg()
    search = getattr(args, "search", None)
    filters = sorted(default_registry.filters)
    if search:
        filters = [f for f in filters if search.lower() in f.lower()]
    print(f"\n  FFmpeg filters ({len(filters)} total):\n")
    for i in range(0, len(filters), 5):
        row = filters[i:i+5]
        print("  " + "  ".join(f"{f:<20}" for f in row))
    print()
    return 0
