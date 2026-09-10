import sys
from pathlib import Path

from fuse.cli.registry import CommandArgument, register_command
from fuse.cli.utils import (
    _video_op,
    build_progress_callback,
    confirm_overwrite,
    finish_progress,
    resolve_inputs,
)
from fuse.i18n.manager import t


@register_command(
    name="compress",
    description_key="commands.compress.description",
    aliases=[],
    arguments=[
        CommandArgument(name="file", help_key="Input file"),
        CommandArgument(name="--quality", help_key="Quality: balanced, high, max (default: balanced)", action="store"),
        CommandArgument(name="--size", help_key="Target size, e.g. 20MB", action="store"),
        CommandArgument(name="--output", help_key="Output file path", action="store"),
    ]
)
def handle_compress(args):
    file = getattr(args, "file", None) or getattr(args, "input", None)
    quality = getattr(args, "quality", None) or "balanced"
    size_arg = getattr(args, "size", None)
    out_arg = getattr(args, "output", None)

    if not file:
        print(t("usage_messages.compress"), file=sys.stderr)
        return 1

    try:
        from fuse.cli.batch import get_auto_output_path
        media_list = resolve_inputs(file)
        if not media_list:
            return 0
            
        is_batch = Path(file).is_dir()
        success_all = True
        
        for media in media_list:
            if out_arg and not is_batch:
                output_file = out_arg
            else:
                output_file = get_auto_output_path(media.path, input_root=file if is_batch else None)

            if Path(output_file).exists() and not is_batch:
                if not confirm_overwrite(output_file):
                    continue

            target_size_mb = None
            if size_arg:
                try:
                    target_size_mb = float(size_arg.upper().rstrip("B").rstrip("M"))
                except ValueError:
                    print(t("errors.invalid_size", size=size_arg), file=sys.stderr)
                    return 1

            print(t("operations.compressing", input=media.path, output=output_file, quality=quality))
            from fuse.operations.compress import CompressOperation
            op = CompressOperation(media, quality=quality, target_size_mb=target_size_mb).output(output_file)
            progress_cb = build_progress_callback(f"{Path(media.path).name} →", media.duration)

            try:
                result = op.run(on_progress=progress_cb)
                finish_progress()
                if not result.success:
                    print(t("errors.operation", error=result.error_message))
                    success_all = False
                else:
                    orig_mb = media.size / 1024 / 1024
                    new_mb = Path(output_file).stat().st_size / 1024 / 1024
                    ratio = (1 - new_mb / orig_mb) * 100 if orig_mb > 0 else 0
                    print(t("operations.compression_complete", original=f"{orig_mb:.1f}", output=f"{new_mb:.1f}", ratio=f"{ratio:.0f}"))
            except KeyboardInterrupt:
                print(t("cli.cancelled"), file=sys.stderr)
                return 0

        return 0 if success_all else 1
    except Exception as e:
        print(t("errors.operation", error=e), file=sys.stderr)
        return 1


@register_command(name="lang", description_key="commands.lang.description",
                  arguments=[CommandArgument(name="code", help_key="commands.args.code")])
def handle_lang(args):
    code = args.code.lower()
    from fuse.i18n.manager import i18n
    supported = ["en", "es", "pt", "fr", "de", "it", "ja", "ko", "zh", "ru"]
    if code not in supported or not i18n.set_language(code):
        print(t("errors.unsupported_language", code=code))
        print(t("errors.supported_languages", languages=", ".join(supported)))
        return 1
    print(t("settings.language_changed", code=code.upper()))
    print(f"  ({t('cli.banner_help')})\n")
    return 0



@register_command(name="version", description_key="commands.version.description",
                  arguments=[])
def handle_version(args):
    from fuse import __version__
    print(f"\n  Alenia Fuse v{__version__}\n")
    return 0


@register_command(name="setup", description_key="commands.setup.description", arguments=[])
def handle_setup(args):
    """Download and verify the platform FFmpeg asset into the user cache."""
    from fuse.ffmpeg.resolver import default_resolver
    print("\n  Preparing Fuse media engine...\n")
    if not default_resolver.ensure_available():
        print("  FFmpeg setup failed. Install FFmpeg manually or check your network and release tag.", file=sys.stderr)
        return 1
    print(f"  FFmpeg ready: {default_resolver.ffmpeg_path}\n")
    return 0


# ─── Thumbnail ───────────────────────────────────────────────────────────────


@register_command(
    name="optimize",
    description_key="commands.optimize.description",
    category_key="categories.convert",
    arguments=[
        CommandArgument(name="file", help_key="Input file", completion="path", value_type="media_path"),
        CommandArgument(name="--preset", help_key="Encoding preset: ultrafast/medium/slow (default: medium)", action="store"),
        CommandArgument(name="--crf", help_key="CRF quality 0-51 (default: 23)", action="store"),
        CommandArgument(name="--output", help_key="Output file", action="store"),
    ],
)
def handle_optimize(args):
    file = getattr(args, "file", None)
    if not file:
        print(t("usage_messages.optimize"), file=sys.stderr)
        return 1
    p = Path(file)
    preset = getattr(args, "preset", None) or "medium"
    crf = int(getattr(args, "crf", None) or 23)
    out = getattr(args, "output", None) or str(p.parent / f"optimized_{p.name}")
    return _video_op("optimize", file, out, "Optimizing", preset=preset, crf=crf)


# ─── Remux ───────────────────────────────────────────────────────────────────


@register_command(
    name="remux",
    description_key="commands.remux.description",
    category_key="categories.convert",
    arguments=[
        CommandArgument(name="file", help_key="Input file", completion="path", value_type="media_path"),
        CommandArgument(name="output", help_key="Output file with desired extension", completion="path"),
    ],
)
def handle_remux(args):
    file = getattr(args, "file", None)
    out = getattr(args, "output", None)
    if not file or not out:
        print(t("usage_messages.remux"), file=sys.stderr)
        return 1
    return _video_op("remux", file, out, "Remuxing")


# ─── Cut ─────────────────────────────────────────────────────────────────────
