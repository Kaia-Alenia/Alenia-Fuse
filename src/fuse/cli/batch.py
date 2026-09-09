"""
Batch processing and smart output routing for Alenia Fuse.

Responsibilities:
  - scan_directory: recursive media scan, ignoring Alenia_Optimized
  - get_auto_output_path: smart output path under Alenia_Optimized/<Category>/
  - prompt_batch_formats: Rich-powered interactive format selection per media type
"""
import os
from pathlib import Path
from typing import List, Dict, Optional

from fuse.media.models import Media
from fuse.i18n.manager import t

# ---------------------------------------------------------------------------
# Format catalogs per type (conservative defaults only)
# ---------------------------------------------------------------------------
_FORMAT_OPTIONS: dict[str, list[str]] = {
    "Video": ["mp4", "webm", "mkv", "avi", "mov", "gif"],
    "Audio": ["mp3", "aac", "ogg", "flac", "wav", "m4a"],
    "Image": ["webp", "jpg", "png", "avif"],
}


# ---------------------------------------------------------------------------
# Directory scan
# ---------------------------------------------------------------------------

def scan_directory(input_root: str) -> List[Media]:
    """
    Recursively scan the directory for media files, skipping Alenia_Optimized.
    Returns Media objects; silently skips non-media or corrupted files.
    """
    results: list[Media] = []
    root_path = Path(input_root).resolve()

    for root, dirs, files in os.walk(root_path):
        # Never recurse into the output directory
        if "Alenia_Optimized" in dirs:
            dirs.remove("Alenia_Optimized")

        for file in sorted(files):
            path = Path(root) / file
            try:
                media = Media.inspect(str(path))
                results.append(media)
            except Exception:
                pass  # not a recognised media file

    return results


# ---------------------------------------------------------------------------
# Smart output path
# ---------------------------------------------------------------------------

def get_auto_output_path(
    input_path: str,
    input_root: Optional[str] = None,
    output_root: Optional[str] = None,
    target_ext: Optional[str] = None,
) -> str:
    """
    Compute the output path using smart routing:
      <output_root or input_root or input_parent>/Alenia_Optimized/<Category>/<rel_path>

    Args:
        input_path:  Path to the source media file.
        input_root:  Root directory being batch-converted (for preserving tree).
        output_root: User-supplied output directory (overrides Alenia_Optimized location).
        target_ext:  Target file extension without dot, e.g. "mp4".
    """
    p = Path(input_path).resolve()
    try:
        media = Media.inspect(str(p))
        category = media.type.name.capitalize()   # "Video", "Audio", "Image"
    except Exception:
        category = "Other"

    # Determine base output root
    if output_root:
        base = Path(output_root).resolve() / "Alenia_Optimized" / category
    elif input_root:
        base = Path(input_root).resolve() / "Alenia_Optimized" / category
    else:
        base = p.parent / "Alenia_Optimized" / category

    # Preserve relative subdirectory structure
    if input_root:
        try:
            rel = p.relative_to(Path(input_root).resolve())
            out_dir = base / rel.parent
        except ValueError:
            out_dir = base
    else:
        out_dir = base

    out_dir.mkdir(parents=True, exist_ok=True)

    ext = target_ext or p.suffix.lstrip(".")
    if ext and not ext.startswith("."):
        ext = f".{ext}"

    return str(out_dir / f"{p.stem}{ext}")


# ---------------------------------------------------------------------------
# Interactive format selection (Rich)
# ---------------------------------------------------------------------------

def prompt_batch_formats(
    media_list: List[Media],
    use_rich: bool = True,
) -> Dict[str, str]:
    """
    For each media type present in media_list, display available formats using
    Rich and prompt the user to choose one (or skip that type).

    Returns a dict: {"Video": "mp4", "Audio": "mp3", ...}
    """
    from rich.console import Console
    from rich.table import Table
    from rich.text import Text
    from rich import box
    from prompt_toolkit import prompt as pt_prompt
    from prompt_toolkit.completion import WordCompleter

    console = Console(highlight=False)

    # Count files per type
    counts: dict[str, int] = {}
    for m in media_list:
        cat = m.type.name.capitalize()
        counts[cat] = counts.get(cat, 0) + 1

    choices: dict[str, str] = {}
    skip_word = t("cli.convert.skip")

    for cat in ("Video", "Audio", "Image"):
        count = counts.get(cat, 0)
        if count == 0:
            continue

        opts = _FORMAT_OPTIONS.get(cat, [])
        all_opts = opts + [skip_word]

        console.print()
        console.print(
            f"  [bold #A78BFA]{t('cli.convert.section_header').format(type=cat, count=count)}[/]"
        )

        # Format table
        table = Table(
            box=box.SIMPLE_HEAD,
            show_header=True,
            header_style="dim #64748B",
            border_style="#1E293B",
            padding=(0, 1),
            expand=False,
        )
        table.add_column(t("cli.convert.format_options"), style="#22D3EE", no_wrap=True)
        for i in range(0, len(opts), 6):
            table.add_row("  ".join(opts[i : i + 6]))
        console.print(table)

        completer = WordCompleter(all_opts, ignore_case=True)
        chosen = None
        while chosen is None:
            try:
                raw = pt_prompt(
                    f"  {t('cli.convert.choose_format')} [{'/'.join(opts[:4])}.../{skip_word}]: ",
                    completer=completer,
                ).strip().lower()
            except (KeyboardInterrupt, EOFError):
                console.print(f"\n  [dim]{t('cli.convert.cancelled_user')}[/]\n")
                return {}

            if raw == skip_word or raw == "skip":
                console.print(f"  [dim]{t('cli.convert.skipping_type').format(type=cat)}[/]")
                chosen = "__skip__"
            elif raw in opts:
                chosen = raw
            else:
                console.print(f"  [#EF4444]{t('cli.convert.invalid_format')}[/]")

        if chosen != "__skip__":
            choices[cat] = chosen

    return choices
