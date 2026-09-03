"""
CLI Handlers — all command implementations.
Handlers registered here via @register_command are the single source of truth.
"""
import sys
import os
from pathlib import Path
from typing import Optional

from alenia_porter.cli.registry import register_command, CommandArgument, registry
from alenia_porter.errors import (
    MediaNotFoundError, MediaAnalysisError, IncompatibleOperationError,
    ConversionError, friendly_error
)


# ─── Progress display ──────────────────────────────────────────────────────

def make_progress_bar(percent: float, width: int = 30) -> str:
    filled = int(width * percent / 100)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {percent:.0f}%"


def build_progress_callback(label: str, total_duration: float):
    """Returns a callable that renders a real-time progress bar."""
    import sys

    def on_progress(progress):
        bar = make_progress_bar(progress.percent)
        time_info = f"Time: {progress.current_str} / {progress.total_str}"
        speed_info = f"  Speed: {progress.speed:.1f}x" if progress.speed > 0 else ""
        line = f"\r  {label}  {bar}  {time_info}{speed_info}"
        sys.stdout.write(line)
        sys.stdout.flush()

    return on_progress


def finish_progress():
    sys.stdout.write("\n")
    sys.stdout.flush()


# ─── File validation ────────────────────────────────────────────────────────

def require_file(path: str) -> "alenia_porter.media.models.Media":
    """Validate file existence and analyze it via FFprobe. Raises on error."""
    from alenia_porter.media.models import Media

    if not path or not Path(path).exists():
        raise MediaNotFoundError(f"File not found: '{path}'")
    if not os.access(path, os.R_OK):
        raise MediaNotFoundError(f"Cannot read file: '{path}'")
    return Media.inspect(path)


def confirm_overwrite(output_path: str) -> bool:
    """Ask user what to do if output file already exists. Returns True to continue."""
    if not Path(output_path).exists():
        return True

    from prompt_toolkit import prompt
    from prompt_toolkit.formatted_text import FormattedText

    print(f"\n  Output already exists: {output_path}")
    choice = prompt(
        FormattedText([("class:cyan", "  Overwrite? [y/N]: ")]),
        default="N"
    ).strip().lower()
    return choice in ("y", "yes")


# ─── info / analyze ─────────────────────────────────────────────────────────

@register_command(
    name="info",
    description="Show detailed media information via FFprobe.",
    aliases=["analyze"],
    arguments=[CommandArgument(name="file", help="Media file to inspect")]
)
def handle_info(args):
    file = getattr(args, "file", None)
    if not file:
        print("Error: provide a file path.", file=sys.stderr)
        return 1
    try:
        media = require_file(file)
        print(f"\n  File     : {media.path}")
        print(f"  Container: {media.container}")
        dur = f"{int(media.duration // 60)}:{int(media.duration % 60):02d}" if media.duration else "N/A"
        print(f"  Duration : {dur}")
        size_mb = media.size / 1024 / 1024
        print(f"  Size     : {size_mb:.2f} MB")
        print()
        for s in media.streams:
            print(f"  Stream #{s.index} ({s.codec_type}): {s.codec_name}")
            if s.codec_type == "video":
                print(f"    Resolution : {s.width}x{s.height}")
                print(f"    Frame rate : {s.fps:.2f} fps" if s.fps else "")
            elif s.codec_type == "audio":
                print(f"    Sample rate: {s.sample_rate} Hz")
                print(f"    Channels   : {s.channels}")
        print()
    except Exception as e:
        print(f"\n  Error: {friendly_error(e)}", file=sys.stderr)
        return 1
    return 0


# ─── convert ────────────────────────────────────────────────────────────────

@register_command(
    name="convert",
    description="Convert a media file to another format.",
    aliases=[],
    arguments=[
        CommandArgument(name="input", help="Input file"),
        CommandArgument(name="output", help="Output file (or format if using 'to' syntax)"),
    ]
)
def handle_convert(args):
    input_file = getattr(args, "input", None)
    output_file = getattr(args, "output", None)

    # Support "convert X to FORMAT" via human parser — args.output will be full path already
    if not input_file or not output_file:
        print("Usage: convert <input> <output>  OR  convert <input> to <format>", file=sys.stderr)
        return 1

    try:
        media = require_file(input_file)

        if not confirm_overwrite(output_file):
            print("  Cancelled.")
            return 0

        target_fmt = Path(output_file).suffix.lstrip(".")
        print(f"\n  Converting {input_file} → {output_file} ...\n")

        from alenia_porter.operations.convert import ConvertOperation
        op = ConvertOperation(media, target_fmt).output(output_file)
        progress_cb = build_progress_callback(f"{Path(input_file).name} →", media.duration)

        try:
            success = op.run(on_progress=progress_cb)
        except KeyboardInterrupt:
            print("\n  Operation cancelled.", file=sys.stderr)
            return 0

        finish_progress()

        if success:
            # Validate output with FFprobe and strict conditions
            out_p = Path(output_file)
            if out_p.exists():
                out_size = out_p.stat().st_size
                if out_size == 0 or "webp_pipe" in output_file:
                    out_p.unlink(missing_ok=True)
                    print(f"\n  Error: Conversion failed (result was 0 bytes or an invalid pipe).", file=sys.stderr)
                    return 1

                from alenia_porter.ffmpeg.probe import probe
                out_info = probe(out_p)
                out_fmt = out_info.get("format", {}).get("format_name", "?")
                out_size_kb = out_size // 1024
                print(f"  Conversion complete.")
                print(f"  Output  : {output_file}")
                print(f"  Format  : {out_fmt}")
                print(f"  Size    : {out_size_kb} KB\n")
            else:
                print(f"\n  Error: Conversion failed (output file not found).", file=sys.stderr)
                return 1
        return 0 if success else 1

    except IncompatibleOperationError as e:
        print(f"\n  Cannot convert: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n  Error: {friendly_error(e)}", file=sys.stderr)
        return 1


# ─── compress ───────────────────────────────────────────────────────────────

@register_command(
    name="compress",
    description="Compress a media file (smart quality options).",
    aliases=[],
    arguments=[
        CommandArgument(name="file", help="Input file"),
        CommandArgument(name="--quality", help="Quality: balanced, high, max (default: balanced)", action="store"),
        CommandArgument(name="--size", help="Target size, e.g. 20MB", action="store"),
        CommandArgument(name="--output", help="Output file path", action="store"),
    ]
)
def handle_compress(args):
    file = getattr(args, "file", None)
    quality = getattr(args, "quality", None) or "balanced"
    size_arg = getattr(args, "size", None)
    out = getattr(args, "output", None)

    try:
        media = require_file(file)

        p = Path(file)
        output_file = out or str(p.parent / f"compressed_{p.name}")

        if not confirm_overwrite(output_file):
            print("  Cancelled.")
            return 0

        target_size_mb = None
        if size_arg:
            size_str = size_arg.upper().rstrip("B").rstrip("M")
            try:
                target_size_mb = float(size_str)
            except ValueError:
                print(f"  Invalid size: {size_arg}", file=sys.stderr)
                return 1

        print(f"\n  Compressing {file} → {output_file} [{quality}] ...\n")

        from alenia_porter.operations.compress import CompressOperation
        op = CompressOperation(media, quality=quality, target_size_mb=target_size_mb).output(output_file)
        progress_cb = build_progress_callback("Compressing", media.duration)

        try:
            success = op.run(on_progress=progress_cb)
        except KeyboardInterrupt:
            print("\n  Operation cancelled.", file=sys.stderr)
            return 0

        finish_progress()

        if success:
            orig_mb = media.size / 1024 / 1024
            if Path(output_file).exists():
                new_mb = Path(output_file).stat().st_size / 1024 / 1024
                ratio = (1 - new_mb / orig_mb) * 100 if orig_mb > 0 else 0
                print(f"  Compression complete.")
                print(f"  Original : {orig_mb:.1f} MB")
                print(f"  Output   : {new_mb:.1f} MB  ({ratio:.0f}% reduction)\n")

        return 0 if success else 1

    except Exception as e:
        print(f"\n  Error: {friendly_error(e)}", file=sys.stderr)
        return 1


# ─── Video operations ────────────────────────────────────────────────────────

def _video_op(operation, file, output, on_progress_label, **kwargs):
    try:
        media = require_file(file)

        if not output:
            p = Path(file)
            output = str(p.parent / f"{operation}_{p.name}")

        if not confirm_overwrite(output):
            print("  Cancelled.")
            return 0

        print(f"\n  {operation.capitalize()} {file} → {output} ...\n")

        from alenia_porter.planner.planner import OperationPlanner
        from alenia_porter.jobs.manager import Job
        from alenia_porter.ffmpeg.resolver import default_resolver

        planner = OperationPlanner()
        plan = planner.plan_video_op(operation, media, output, **kwargs)

        if not plan.is_valid:
            print(f"\n  Cannot perform operation: {plan.error_reason}", file=sys.stderr)
            return 1

        progress_cb = build_progress_callback(on_progress_label, media.duration)
        cmd = [str(default_resolver.ffmpeg_path), "-y"] + plan.args
        job = Job(cmd=cmd, total_duration=media.duration,
                  output_path=Path(output), on_progress=progress_cb)

        try:
            success = job.run()
        except KeyboardInterrupt:
            job.cancel()
            print("\n  Operation cancelled.", file=sys.stderr)
            return 0

        finish_progress()
        if success:
            print(f"  Done → {output}\n")
        return 0 if success else 1

    except Exception as e:
        print(f"\n  Error: {friendly_error(e)}", file=sys.stderr)
        return 1


@register_command(name="resize", description="Resize video dimensions.",
                  arguments=[CommandArgument(name="file", help="Input file"),
                             CommandArgument(name="size", help="Target size, e.g. 1280x720")])
def handle_resize(args):
    import re
    m = re.match(r"(\d+)[xX](\d+)", args.size)
    if not m:
        print("Error: size must be WIDTHxHEIGHT, e.g. 1280x720", file=sys.stderr)
        return 1
    return _video_op("resize", args.file, None, "Resizing",
                     width=int(m.group(1)), height=int(m.group(2)))


@register_command(name="rotate", description="Rotate video.",
                  arguments=[CommandArgument(name="file", help="Input file"),
                             CommandArgument(name="degrees", help="Degrees: 90, 180, 270")])
def handle_rotate(args):
    try:
        deg = int(args.degrees)
    except ValueError:
        print("Error: degrees must be 90, 180, or 270", file=sys.stderr)
        return 1
    return _video_op("rotate", args.file, None, "Rotating", degrees=deg)


@register_command(name="fps", description="Change video frame rate.",
                  arguments=[CommandArgument(name="file", help="Input file"),
                             CommandArgument(name="rate", help="Target FPS, e.g. 60")])
def handle_fps(args):
    try:
        new_fps = float(args.rate)
    except ValueError:
        print("Error: rate must be a number", file=sys.stderr)
        return 1
    return _video_op("fps", args.file, None, "Changing FPS", fps=new_fps)


@register_command(name="speed", description="Change playback speed.",
                  arguments=[CommandArgument(name="file", help="Input file"),
                             CommandArgument(name="factor", help="Speed factor, e.g. 2x or 0.5")])
def handle_speed(args):
    val_str = args.factor.rstrip("x")
    try:
        factor = float(val_str)
    except ValueError:
        print("Error: factor must be a number, e.g. 2x or 0.5", file=sys.stderr)
        return 1
    return _video_op("speed", args.file, None, "Changing speed", factor=factor)


@register_command(name="trim", description="Trim a video clip.",
                  arguments=[CommandArgument(name="file", help="Input file"),
                             CommandArgument(name="--start", help="Start time, e.g. 00:01:00", action="store"),
                             CommandArgument(name="--end", help="End time, e.g. 00:02:00", action="store"),
                             CommandArgument(name="--duration", help="Duration, e.g. 60", action="store"),
                             CommandArgument(name="--output", help="Output file", action="store")])
def handle_trim(args):
    start = getattr(args, "start", None) or "00:00:00"
    end = getattr(args, "end", None)
    dur = getattr(args, "duration", None)
    out = getattr(args, "output", None)
    if not end and not dur:
        print("Error: specify --end or --duration", file=sys.stderr)
        return 1
    return _video_op("trim", args.file, out, "Trimming", start=start, end=end, duration=dur)


@register_command(name="mute", description="Remove audio from video.",
                  arguments=[CommandArgument(name="file", help="Input file")])
def handle_mute(args):
    return _video_op("mute", args.file, None, "Muting")


@register_command(name="extract-audio", description="Extract audio stream from video.",
                  aliases=["extract_audio"],
                  arguments=[CommandArgument(name="file", help="Input file"),
                             CommandArgument(name="--output", help="Output audio file", action="store")])
def handle_extract_audio(args):
    out = getattr(args, "output", None)
    if not out:
        p = Path(args.file)
        out = str(p.parent / f"{p.stem}_audio.aac")
    return _video_op("extract_audio", args.file, out, "Extracting audio")


@register_command(name="thumbnail", description="Extract a thumbnail image from video.",
                  arguments=[CommandArgument(name="file", help="Input file"),
                             CommandArgument(name="--at", help="Timestamp, e.g. 00:00:10", action="store")])
def handle_thumbnail(args):
    p = Path(args.file)
    ts = getattr(args, "at", None) or "00:00:05"
    out = str(p.parent / f"{p.stem}_thumb.jpg")
    return _video_op("thumbnail", args.file, out, "Extracting thumbnail", timestamp=ts)


@register_command(name="gif", description="Create an animated GIF from video.",
                  arguments=[CommandArgument(name="file", help="Input file"),
                             CommandArgument(name="--start", help="Start time", action="store"),
                             CommandArgument(name="--duration", help="Duration in seconds", action="store"),
                             CommandArgument(name="--fps", help="GIF frame rate (default 10)", action="store"),
                             CommandArgument(name="--width", help="GIF width (default 480)", action="store")])
def handle_gif(args):
    p = Path(args.file)
    out = str(p.parent / f"{p.stem}.gif")
    kw = {
        "start": getattr(args, "start", None) or "00:00:00",
        "duration": getattr(args, "duration", None) or 5,
        "fps": int(getattr(args, "fps", None) or 10),
        "width": int(getattr(args, "width", None) or 480),
    }
    return _video_op("gif", args.file, out, "Creating GIF", **kw)


@register_command(name="remux", description="Remux to another container without re-encoding.",
                  arguments=[CommandArgument(name="input", help="Input file"),
                             CommandArgument(name="output", help="Output file")])
def handle_remux(args):
    try:
        media = require_file(args.input)
        print(f"\n  Remuxing {args.input} → {args.output} (stream copy) ...\n")
        from alenia_porter.operations.convert import ConvertOperation
        target_fmt = Path(args.output).suffix.lstrip(".")
        op = ConvertOperation(media, target_fmt).output(args.output)
        # force stream copy by using remux intent
        from alenia_porter.planner.planner import OperationPlanner
        from alenia_porter.ffmpeg.resolver import default_resolver
        from alenia_porter.jobs.manager import Job
        plan = OperationPlanner().plan_video_op("remux", media, args.output)
        cmd = [str(default_resolver.ffmpeg_path), "-y"] + plan.args
        job = Job(cmd=cmd, total_duration=media.duration, output_path=Path(args.output))
        success = job.run()
        finish_progress()
        if success:
            print(f"  Done → {args.output}\n")
        return 0 if success else 1
    except Exception as e:
        print(f"\n  Error: {friendly_error(e)}", file=sys.stderr)
        return 1


# ─── Audio operations ────────────────────────────────────────────────────────

def _audio_op(operation, file, output, label, **kwargs):
    try:
        media = require_file(file)

        if not media.main_audio:
            print(f"\n  Error: The file does not contain an audio stream.", file=sys.stderr)
            return 1

        if not output:
            p = Path(file)
            output = str(p.parent / f"{operation}_{p.name}")

        if not confirm_overwrite(output):
            print("  Cancelled.")
            return 0

        print(f"\n  {label} {file} → {output} ...\n")

        from alenia_porter.planner.planner import OperationPlanner
        from alenia_porter.jobs.manager import Job
        from alenia_porter.ffmpeg.resolver import default_resolver

        planner = OperationPlanner()
        plan = planner.plan_audio_op(operation, media, output, **kwargs)

        if not plan.is_valid:
            print(f"\n  Cannot perform operation: {plan.error_reason}", file=sys.stderr)
            return 1

        progress_cb = build_progress_callback(label, media.duration)
        cmd = [str(default_resolver.ffmpeg_path), "-y"] + plan.args
        job = Job(cmd=cmd, total_duration=media.duration,
                  output_path=Path(output), on_progress=progress_cb)

        try:
            success = job.run()
        except KeyboardInterrupt:
            job.cancel()
            print("\n  Operation cancelled.", file=sys.stderr)
            return 0

        finish_progress()
        if success:
            print(f"  Done → {output}\n")
        return 0 if success else 1

    except Exception as e:
        print(f"\n  Error: {friendly_error(e)}", file=sys.stderr)
        return 1


@register_command(name="volume", description="Adjust audio volume.",
                  arguments=[CommandArgument(name="file", help="Input file"),
                             CommandArgument(name="value", help="Volume change: +20%, -10%, 1.5")])
def handle_volume(args):
    return _audio_op("volume", args.file, None, "Adjusting volume", value=args.value)


@register_command(name="normalize", description="Normalize audio levels (loudnorm).",
                  arguments=[CommandArgument(name="file", help="Input file")])
def handle_normalize(args):
    return _audio_op("normalize", args.file, None, "Normalizing")


@register_command(name="fade", description="Add fade in/out to audio.",
                  arguments=[CommandArgument(name="file", help="Input file"),
                             CommandArgument(name="type", help="in or out"),
                             CommandArgument(name="--duration", help="Fade duration in seconds", action="store")])
def handle_fade(args):
    fade_type = getattr(args, "type", "in")
    dur = float(getattr(args, "duration", None) or 3.0)
    return _audio_op("fade", args.file, None, f"Fading {fade_type}", fade_type=fade_type, duration=dur)


# ─── Inspection commands ─────────────────────────────────────────────────────

@register_command(name="formats", description="List supported media formats.",
                  arguments=[CommandArgument(name="category", help="Optional category: video, audio, image", nargs="?", action="store")])
def handle_formats(args):
    from alenia_porter.ffmpeg.capabilities import default_registry
    default_registry.load_from_ffmpeg()
    cat_filter = getattr(args, "category", None)
    
    categories = {
        "video": "Video / Containers",
        "audio": "Audio",
        "image": "Images"
    }
    
    if not cat_filter:
        print("\n  ALENIA PORTER — OUTPUT FORMATS\n")
        
        for cat_key, cat_label in categories.items():
            muxers = sorted([m.name for m in default_registry.get_muxers_by_category(cat_key)])
            print(f"  {cat_label}")
            if len(muxers) > 6:
                print("    " + "   ".join(muxers[:6]) + "   ...")
                print(f"    + {len(muxers) - 6} more\n")
            else:
                print("    " + "   ".join(muxers) + "\n")
                
        print("  Use:")
        print("    porter formats video")
        print("    porter formats audio")
        print("    porter formats image\n")
        print("  Inside Porter:")
        print("    /formats\n")
    else:
        cat_key = cat_filter.lower()
        if cat_key not in categories:
            print(f"\n  Unknown category: {cat_filter}")
            print("  Use: video, audio, image\n")
            return 1
            
        print(f"\n  ALENIA PORTER — {categories[cat_key].upper()} FORMATS\n")
        muxers = sorted(default_registry.get_muxers_by_category(cat_key), key=lambda x: x.name)
        for i in range(0, len(muxers), 5):
            row = muxers[i:i+5]
            print("    " + "   ".join(f"{m.name:<6}" for m in row))
        print(f"\n  Total {cat_key} output formats: {len(muxers)}\n")

    return 0


@register_command(name="codecs", description="List supported codecs.",
                  arguments=[])
def handle_codecs(args):
    from alenia_porter.ffmpeg.capabilities import default_registry
    default_registry.load_from_ffmpeg()
    codecs = sorted(default_registry.codecs)
    print(f"\n  Supported codecs ({len(codecs)} total):\n")
    for i in range(0, len(codecs), 6):
        row = codecs[i:i+6]
        print("  " + "  ".join(f"{c:<16}" for c in row))
    print()
    return 0


@register_command(name="lang", description="Change the interface language.",
                  arguments=[CommandArgument(name="code", help="Language code: en, es, pt, fr, de...")])
def handle_lang(args):
    from alenia_porter.config.manager import config
    from alenia_porter.i18n.manager import i18n, t
    code = args.code.lower()
    supported = ["en", "es", "pt", "fr", "de", "it", "ja", "ko", "zh", "ru"]
    if code not in supported:
        print(f"\n  Unsupported language: '{code}'")
        print(f"  Supported: {', '.join(supported)}\n")
        return 1
    config.set("language", code)
    i18n.load_language(code)
    
    # After loading the new language, print the localized success message
    # (If no key exists, it will fallback to the key string)
    success_msg = t("settings.language")
    print(f"\n  {success_msg}: {code.upper()} -> OK")
    print(f"  ({t('cli.banner_help')})\n")
    return 0


@register_command(name="version", description="Show Porter version.",
                  arguments=[])
def handle_version(args):
    from alenia_porter import __version__
    print(f"\n  Alenia Porter v{__version__}\n")
    return 0
