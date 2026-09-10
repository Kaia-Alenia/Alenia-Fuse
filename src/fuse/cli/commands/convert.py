"""
convert command — single file and batch directory conversion.

Flow (directory):
  1. Scan recursively, count files by type (Video / Audio / Image)
  2. Display summary and per-type format selector (Rich table + Tab completion)
  3. Convert all selected files to Alenia_Optimized/ (or user-specified dir)
  4. Show Rich progress and final summary

Flow (single file):
  - If output argument has no extension, error with helpful hint
  - If only input given, prompt for target format
"""
from pathlib import Path

from rich.console import Console

from fuse.cli.registry import CommandArgument, register_command
from fuse.cli.utils import (
    build_progress_callback,
    finish_progress,
    friendly_error,
    require_file,
)
from fuse.i18n.manager import t

_console = Console(highlight=False)


@register_command(
    name="convert",
    description_key="commands.convert.description",
    aliases=[],
    arguments=[
        CommandArgument(name="input",  help_key="commands.args.input",  completion="path"),
        CommandArgument(name="output", help_key="commands.args.output", completion="path", nargs="?"),
    ],
)
def handle_convert(args):
    input_arg  = getattr(args, "input",  None)
    output_arg = getattr(args, "output", None)

    if not input_arg:
        _console.print(f"\n  [dim]{t('cli.convert.use_slash')}[/]\n")
        return 0

    input_path = Path(input_arg)

    if input_path.is_dir():
        return _batch_convert(input_path, output_dir=output_arg)
    else:
        return _single_convert(input_path, output_arg)


# ---------------------------------------------------------------------------
# Single-file conversion
# ---------------------------------------------------------------------------

def _single_convert(input_path: Path, output_arg: str | None) -> int:
    from prompt_toolkit import prompt as pt_prompt
    from prompt_toolkit.completion import WordCompleter

    from fuse.cli.batch import get_auto_output_path

    try:
        media = require_file(str(input_path))
    except Exception as exc:
        _console.print(f"\n  [#EF4444]{t('cli.error')}[/] {friendly_error(exc)}\n")
        return 1

    # Determine target format
    if output_arg:
        # "convert video.mp4 .mp4" or ".mp4" (format shorthand)
        if output_arg.startswith(".") and "/" not in output_arg and "\\" not in output_arg:
            target_fmt = output_arg.lstrip(".")
            output_file = get_auto_output_path(str(input_path), target_ext=target_fmt)
        else:
            output_file = output_arg
            target_fmt = Path(output_file).suffix.lstrip(".")
            if not target_fmt:
                _console.print(
                    f"\n  [#EF4444]{t('cli.error')}[/] "
                    + t("cli.convert.no_output_extension").format(
                        output=output_arg, input=str(input_path)
                    ) + "\n"
                )
                return 1
    else:
        # Interactive: ask for format
        cat = media.type.name.capitalize()
        from fuse.cli.batch import _FORMAT_OPTIONS
        opts = _FORMAT_OPTIONS.get(cat, ["mp4"])
        completer = WordCompleter(opts, ignore_case=True)

        _console.print(
            f"\n  [bold #A78BFA]{input_path.name}[/] "
            f"[dim]({media.type.value})[/]"
        )
        try:
            target_fmt = pt_prompt(
                f"  {t('cli.convert.choose_format')} [{'/'.join(opts[:4])}...]: ",
                completer=completer,
            ).strip().lower()
        except (KeyboardInterrupt, EOFError):
            _console.print(f"\n  [dim]{t('cli.convert.cancelled_user')}[/]\n")
            return 0

        if target_fmt not in opts:
            _console.print(f"  [#EF4444]{t('cli.convert.invalid_format')}[/]\n")
            return 1

        output_file = get_auto_output_path(str(input_path), target_ext=target_fmt)

    return _run_conversion(media, target_fmt, output_file)


# ---------------------------------------------------------------------------
# Batch directory conversion
# ---------------------------------------------------------------------------

def _batch_convert(input_dir: Path, output_dir: str | None) -> int:
    from fuse.cli.batch import (
        get_auto_output_path,
        prompt_batch_formats,
        scan_directory,
    )

    # Determine output root
    # output_dir could be:
    #   - None   → use Alenia_Optimized inside input_dir
    #   - a path (no extension) → custom output directory
    output_root: str | None = None
    if output_dir:
        op = Path(output_dir)
        if op.suffix:   # has extension → probably a mistake, treat as dir anyway
            output_root = str(op.parent)
        else:
            output_root = str(op)

    _console.print(f"\n  [dim]{t('cli.convert.scanning').format(path=str(input_dir))}[/]")

    media_list = scan_directory(str(input_dir))

    if not media_list:
        _console.print(
            f"  [#EF4444]{t('cli.convert.no_media').format(path=str(input_dir))}[/]\n"
        )
        return 0

    # Count by type
    counts: dict[str, int] = {}
    for m in media_list:
        cat = m.type.name.capitalize()
        counts[cat] = counts.get(cat, 0) + 1

    videos = counts.get("Video", 0)
    audios = counts.get("Audio", 0)
    images = counts.get("Image", 0)

    _console.print(
        f"  [white]{t('cli.convert.found_summary').format(videos=videos, audios=audios, images=images)}[/]"
    )

    # Interactive format selection
    format_choices = prompt_batch_formats(media_list)
    if not format_choices:
        _console.print(f"\n  [dim]{t('cli.convert.cancelled_user')}[/]\n")
        return 0

    # Filter media to only those with a chosen format
    selected = [m for m in media_list if m.type.name.capitalize() in format_choices]
    total = len(selected)

    if total == 0:
        _console.print(f"\n  [dim]{t('cli.convert.cancelled_user')}[/]\n")
        return 0

    _console.print(
        f"\n  [dim]{t('cli.convert.start').format(total=total)}[/]"
    )
    default_out = output_root or str(input_dir / "Alenia_Optimized")
    _console.print(
        f"  [dim]{t('cli.convert.output_dir')}:[/] [white]{default_out}[/]\n"
    )

    errors = 0
    for idx, media in enumerate(selected, 1):
        cat = media.type.name.capitalize()
        target_fmt = format_choices[cat]
        output_file = get_auto_output_path(
            media.path,
            input_root=str(input_dir),
            output_root=output_root,
            target_ext=target_fmt,
        )

        name = Path(media.path).name
        _console.print(
            f"  [{idx}/{total}] [#22D3EE]{name}[/] [dim]→[/] [#A78BFA]{target_fmt}[/]",
            end="  ",
        )

        rc = _run_conversion(media, target_fmt, output_file, quiet=True)
        if rc == 0:
            out_mb = Path(output_file).stat().st_size / 1024 / 1024
            _console.print(f"[#34D399]{t('cli.convert.done')}[/] [dim]{out_mb:.1f} MB[/]")
        else:
            errors += 1
            _console.print("[#EF4444]Error[/]")

    _console.print()
    if errors == 0:
        _console.print(f"  [bold #34D399]{t('cli.convert.done')}[/] {total} files converted.\n")
    else:
        _console.print(
            f"  [#EF4444]{errors} error(s)[/] / {total - errors} converted successfully.\n"
        )
    return 0 if errors == 0 else 1


# ---------------------------------------------------------------------------
# Shared conversion runner
# ---------------------------------------------------------------------------

def _run_conversion(media, target_fmt: str, output_file: str, quiet: bool = False) -> int:
    from fuse.operations.convert import ConvertOperation

    try:
        op = ConvertOperation(media, target_fmt).output(output_file)
        progress_cb = build_progress_callback(
            Path(media.path).name, media.duration
        ) if not quiet else None

        result = op.run(on_progress=progress_cb)
        if not quiet:
            finish_progress()

        if not result.success:
            if not quiet:
                _console.print(
                    f"\n  [#EF4444]{t('cli.error')}[/] {result.error or 'Conversion failed.'}\n"
                )
            return 1

        if not quiet:
            orig_mb = media.size / 1024 / 1024
            out_mb  = Path(output_file).stat().st_size / 1024 / 1024
            _console.print(
                f"\n  [#34D399]{t('cli.convert.complete').format(orig=f'{orig_mb:.1f}', out=f'{out_mb:.1f}')}[/]\n"
            )
        return 0

    except KeyboardInterrupt:
        if not quiet:
            _console.print(f"\n  [dim]{t('cli.convert.cancelled_user')}[/]\n")
        return 0
    except Exception as exc:
        if not quiet:
            _console.print(
                f"\n  [#EF4444]{t('cli.error')}[/] {friendly_error(exc)}\n"
            )
        return 1
