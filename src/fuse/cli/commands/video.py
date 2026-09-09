import sys
from pathlib import Path

from fuse.cli.registry import CommandArgument, register_command
from fuse.cli.utils import (
    _video_op,
    confirm_overwrite,
    friendly_error,
    resolve_inputs,
)


@register_command(name="resize", description_key="commands.resize.description",
                  arguments=[CommandArgument(name="file", help_key="Input file"),
                             CommandArgument(name="size", help_key="Target size, e.g. 1280x720")])
def handle_resize(args):
    import re
    m = re.match(r"(\d+)[xX](\d+)", args.size)
    if not m:
        print("Error: size must be WIDTHxHEIGHT, e.g. 1280x720", file=sys.stderr)
        return 1
    return _video_op("resize", args.file, None, "Resizing",
                     width=int(m.group(1)), height=int(m.group(2)))



@register_command(name="rotate", description_key="commands.rotate.description",
                  arguments=[CommandArgument(name="file", help_key="Input file"),
                             CommandArgument(name="degrees", help_key="Degrees: 90, 180, 270")])
def handle_rotate(args):
    try:
        deg = int(args.degrees)
    except ValueError:
        print("Error: degrees must be 90, 180, or 270", file=sys.stderr)
        return 1
    return _video_op("rotate", args.file, None, "Rotating", degrees=deg)



@register_command(name="fps", description_key="commands.fps.description",
                  arguments=[CommandArgument(name="file", help_key="Input file"),
                             CommandArgument(name="rate", help_key="Target FPS, e.g. 60")])
def handle_fps(args):
    try:
        new_fps = float(args.rate)
    except ValueError:
        print("Error: rate must be a number", file=sys.stderr)
        return 1
    return _video_op("fps", args.file, None, "Changing FPS", fps=new_fps)



@register_command(name="speed", description_key="commands.speed.description",
                  arguments=[CommandArgument(name="file", help_key="Input file"),
                             CommandArgument(name="factor", help_key="Speed factor, e.g. 2x or 0.5")])
def handle_speed(args):
    val_str = args.factor.rstrip("x")
    try:
        factor = float(val_str)
    except ValueError:
        print("Error: factor must be a number, e.g. 2x or 0.5", file=sys.stderr)
        return 1
    return _video_op("speed", args.file, None, "Changing speed", factor=factor)



@register_command(name="trim", description_key="commands.trim.description",
                  arguments=[CommandArgument(name="file", help_key="Input file"),
                             CommandArgument(name="--start", help_key="Start time, e.g. 00:01:00", action="store"),
                             CommandArgument(name="--end", help_key="End time, e.g. 00:02:00", action="store"),
                             CommandArgument(name="--duration", help_key="Duration, e.g. 60", action="store"),
                             CommandArgument(name="--output", help_key="Output file", action="store")])
def handle_trim(args):
    start = getattr(args, "start", None) or "00:00:00"
    end = getattr(args, "end", None)
    dur = getattr(args, "duration", None)
    out = getattr(args, "output", None)
    if not end and not dur:
        print("Error: specify --end or --duration", file=sys.stderr)
        return 1
    return _video_op("trim", args.file, out, "Trimming", start=start, end=end, duration=dur)



@register_command(name="mute", description_key="commands.mute.description",
                  arguments=[CommandArgument(name="file", help_key="Input file")])
def handle_mute(args):
    return _video_op("mute", args.file, None, "Muting")



@register_command(name="extract-audio", description_key="commands.extract-audio.description",
                  aliases=["extract_audio"],
                  arguments=[CommandArgument(name="file", help_key="Input file"),
                             CommandArgument(name="--output", help_key="Output audio file", action="store")])
def handle_extract_audio(args):
    file = getattr(args, "file", None) or getattr(args, "input", None)
    out_arg = getattr(args, "output", None)

    if not file:
        print("Usage: extract-audio <input> [output]", file=sys.stderr)
        return 1

    try:
        from fuse.cli.batch import get_auto_output_path
        media_list = resolve_inputs(file)
        if not media_list: return 0
        is_batch = Path(file).is_dir()
        success_all = True
        
        for media in media_list:
            output_file = out_arg if out_arg and not is_batch else get_auto_output_path(media.path, input_root=file if is_batch else None, target_ext="mp3")
            
            if Path(output_file).exists() and not is_batch:
                if not confirm_overwrite(output_file): continue

            print(f"\n  Extracting Audio {media.path} → {output_file} ...\n")
            # Audio extraction is an existing video operation in the planner;
            # do not route the CLI through a separate, nonexistent operation.
            rc = _video_op(
                "extract_audio",
                media.path,
                output_file,
                f"{Path(media.path).name} →",
            )
            if rc != 0:
                success_all = False

        return 0 if success_all else 1
    except Exception as e:
        print(f"  Error: {e}", file=sys.stderr)
        return 1


@register_command(
    name="cut",
    description_key="commands.cut.description",
    category_key="categories.video",
    arguments=[
        CommandArgument(name="file", help_key="Input file", completion="path", value_type="media_path"),
        CommandArgument(name="--start", help_key="Start time, e.g. 00:01:00", action="store"),
        CommandArgument(name="--end", help_key="End time, e.g. 00:02:00", action="store"),
        CommandArgument(name="--duration", help_key="Duration, e.g. 60", action="store"),
        CommandArgument(name="--output", help_key="Output file", action="store"),
    ],
)
def handle_cut(args):
    file = getattr(args, "file", None)
    start = getattr(args, "start", None) or "00:00:00"
    end = getattr(args, "end", None)
    dur = getattr(args, "duration", None)
    out = getattr(args, "output", None)
    if not file:
        print("Usage: cut <file> --start <t> [--end <t> | --duration <s>]", file=sys.stderr)
        return 1
    if not end and not dur:
        print("Error: specify --end or --duration", file=sys.stderr)
        return 1
    return _video_op("cut", file, out, "Cutting", start=start, end=end, duration=dur)


# ─── Concat ──────────────────────────────────────────────────────────────────


@register_command(
    name="concat",
    description_key="commands.concat.description",
    category_key="categories.video",
    arguments=[
        CommandArgument(name="files", help_key="Input files separated by spaces", completion="path"),
        CommandArgument(name="--output", help_key="Output file", action="store"),
    ],
)
def handle_concat(args):
    import tempfile
    files_raw = getattr(args, "files", None)
    out = getattr(args, "output", None)
    if not files_raw or not out:
        print("Usage: concat <file1> <file2> ... --output <output>", file=sys.stderr)
        return 1

    file_list = files_raw if isinstance(files_raw, list) else [files_raw]
    for f in file_list:
        if not Path(f).exists():
            print(f"  File not found: {f}", file=sys.stderr)
            return 1

    try:
        from fuse.ffmpeg.resolver import default_resolver
        from fuse.jobs.manager import Job
        from fuse.media.privacy import apply_ffmpeg_privacy

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt",
                                         delete=False, encoding="utf-8") as flist:
            for f in file_list:
                flist.write(f"file '{f}'\n")
            flist_path = flist.name

        print(f"\n  Concatenating {len(file_list)} files → {out} ...\n")
        args = [
            "-f", "concat", "-safe", "0",
            "-i", flist_path,
            "-c", "copy",
            out,
        ]
        cmd = [
            str(default_resolver.ffmpeg_path), "-y",
        ] + apply_ffmpeg_privacy(args)
        job = Job(cmd=cmd, total_duration=0, output_path=Path(out))
        try:
            success = job.run()
        except KeyboardInterrupt:
            job.cancel()
            print("\n  Cancelled.", file=sys.stderr)
            return 0
        Path(flist_path).unlink(missing_ok=True)
        if success:
            print(f"  Done → {out}\n")
        return 0 if success else 1
    except Exception as e:
        print(f"\n  Error: {friendly_error(e)}", file=sys.stderr)
        return 1


# ─── Subtitle ────────────────────────────────────────────────────────────────


@register_command(
    name="subtitle",
    description_key="commands.subtitle.description",
    category_key="categories.video",
    arguments=[
        CommandArgument(name="file", help_key="Input video file", completion="path", value_type="media_path"),
        CommandArgument(name="--subtitle", help_key="Subtitle file (.srt, .ass)", action="store"),
        CommandArgument(name="--output", help_key="Output video file", action="store"),
    ],
)
def handle_subtitle(args):
    file = getattr(args, "file", None)
    sub = getattr(args, "subtitle", None)
    out = getattr(args, "output", None)
    if not file or not sub:
        print("Usage: subtitle <video> --subtitle <file.srt> [--output <file>]", file=sys.stderr)
        return 1
    if not Path(sub).exists():
        print(f"  Subtitle file not found: {sub}", file=sys.stderr)
        return 1
    p = Path(file)
    output = out or str(p.parent / f"sub_{p.name}")
    return _video_op("subtitle", file, output, "Burning subtitles", subtitle=sub)


# ─── Watermark ───────────────────────────────────────────────────────────────


@register_command(
    name="watermark",
    description_key="commands.watermark.description",
    category_key="categories.video",
    arguments=[
        CommandArgument(name="file", help_key="Input video file", completion="path", value_type="media_path"),
        CommandArgument(name="--watermark", help_key="Watermark image file", action="store"),
        CommandArgument(name="--position", help_key="Position: topleft, topright, bottomleft, bottomright, center", action="store"),
        CommandArgument(name="--output", help_key="Output video file", action="store"),
    ],
)
def handle_watermark(args):
    file = getattr(args, "file", None)
    wm = getattr(args, "watermark", None)
    pos = getattr(args, "position", None) or "bottomright"
    out = getattr(args, "output", None)
    if not file or not wm:
        print("Usage: watermark <video> --watermark <image> [--position <pos>]", file=sys.stderr)
        return 1
    if not Path(wm).exists():
        print(f"  Watermark file not found: {wm}", file=sys.stderr)
        return 1
    p = Path(file)
    output = out or str(p.parent / f"wm_{p.name}")
    return _video_op("watermark", file, output, "Adding watermark", watermark=wm, position=pos)


# ─── Metadata ────────────────────────────────────────────────────────────────
