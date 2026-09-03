import argparse
import sys
from alenia_porter.ffmpeg import default_resolver
from alenia_porter.media import Media

def get_parser():
    parser = argparse.ArgumentParser(
        prog="porter",
        description="Alenia Porter - Professional Multimedia Toolkit"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # version
    parser.add_argument("--version", action="version", version="Alenia Porter 7.0.0")
    
    # info
    info_parser = subparsers.add_parser("info", help="Show environment information")
    info_parser.add_argument("--environment", action="store_true", help="Show detailed environment information")
    
    # convert
    convert_parser = subparsers.add_parser("convert", help="Convert media files")
    convert_parser.add_argument("input", help="Input file")
    convert_parser.add_argument("output", help="Output file")
    
    return parser

def cmd_info(args):
    print("╭──────────────────────────────╮")
    print("│        ALENIA PORTER         │")
    print("│      multimedia toolkit      │")
    print("╰──────────────────────────────╯")
    print("")
    
    if args.environment:
        print("FFmpeg:")
        print("  source: " + ("bundled" if default_resolver.is_ffmpeg_available else "not found"))
        print(f"  path: {default_resolver.ffmpeg_path}")
        print(f"  version: {default_resolver.get_version()}")
        print("")
        print("FFprobe:")
        print("  source: " + ("bundled" if default_resolver.is_ffprobe_available else "not found"))
        print(f"  path: {default_resolver.ffprobe_path}")
    else:
        ffmpeg_status = "ready" if default_resolver.is_ffmpeg_available else "missing"
        ffprobe_status = "ready" if default_resolver.is_ffprobe_available else "missing"
        
        print(f"{'✓' if ffmpeg_status == 'ready' else '✗'} FFmpeg {ffmpeg_status}")
        print(f"{'✓' if ffprobe_status == 'ready' else '✗'} FFprobe {ffprobe_status}")

def cmd_convert(args):
    print(f"Planning conversion from {args.input} to {args.output}...")
    if not default_resolver.is_ffmpeg_available:
        print("Error: FFmpeg is not available to perform this operation.", file=sys.stderr)
        sys.exit(1)
        
    try:
        from rich.console import Console
        from rich.progress import Progress, SpinnerColumn, TextColumn
        import time
        
        console = Console()
        with Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description=f"Converting {args.input}...", total=None)
            time.sleep(2) # Simulate work
            
    except ImportError:
        import time
        print("Converting...")
        time.sleep(2)
        
    print(f"✓ Successfully converted {args.input} -> {args.output} (Simulation)")

def main():
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    if len(sys.argv) == 1:
        from alenia_porter.cli.interactive import run_interactive
        run_interactive()
        sys.exit(0)
        
    parser = get_parser()
        
    args = parser.parse_args()
    
    if args.command == "info":
        cmd_info(args)
    elif args.command == "convert":
        cmd_convert(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
