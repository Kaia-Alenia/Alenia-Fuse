"""
Parser and dispatcher for Alenia Porter CLI.
Integrates human-syntax parser with argparse-based registry.
"""
import sys
import argparse
from alenia_porter.cli.registry import registry
from alenia_porter.cli.human_parser import parse_human_syntax


def get_parser():
    parser = argparse.ArgumentParser(
        prog="porter",
        description="Alenia Porter - Professional Multimedia Toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  porter info movie.mp4
  porter convert input.mp4 to webm
  porter convert input.mp4 output.webm
  porter compress movie.mp4 --quality high
  porter trim movie.mp4 --start 00:01:00 --end 00:02:00
  porter resize movie.mp4 1280x720
  porter rotate movie.mp4 90
  porter gif movie.mp4
  porter volume song.mp3 +20%
  porter normalize song.mp3
  porter formats
  porter lang es
"""
    )

    parser.add_argument("--version", action="version", version="Alenia Porter 7.1.0")

    subparsers = parser.add_subparsers(dest="command", metavar="command")

    for cmd in registry.get_all():
        p = subparsers.add_parser(
            cmd.name,
            help=cmd.description,
            aliases=cmd.aliases
        )
        for arg in cmd.arguments:
            kwargs = {"help": arg.help}
            if arg.nargs:
                kwargs["nargs"] = arg.nargs
            if arg.action and arg.action != "store":
                kwargs["action"] = arg.action
            elif arg.name.startswith("--"):
                # optional argument
                p.add_argument(arg.name, **kwargs)
            else:
                p.add_argument(arg.name, **kwargs)

    return parser


def parse_and_run(args_list=None) -> int:
    """
    Main dispatcher. First tries human-syntax parse, then falls back to argparse.
    Returns exit code.
    """
    tokens = args_list if args_list is not None else sys.argv[1:]

    if not tokens:
        get_parser().print_help()
        return 0

    # Try human-friendly syntax first
    human = parse_human_syntax(tokens)
    if human:
        return _dispatch_human(human)

    # Fall back to argparse
    parser = get_parser()
    try:
        args = parser.parse_args(tokens)
    except SystemExit as e:
        return e.code or 0

    if not args.command:
        parser.print_help()
        return 0

    cmd = registry.get(args.command)
    if cmd:
        return cmd.handler(args) or 0

    print(f"Unknown command: {args.command}", file=sys.stderr)
    return 1


def _dispatch_human(parsed) -> int:
    """Dispatch a ParsedCommand from human_parser to the matching handler."""
    from types import SimpleNamespace

    cmd = registry.get(parsed.command)
    if not cmd:
        # Fall back to standard argparse for this
        parser = get_parser()
        tokens = [parsed.command] + [str(v) for v in parsed.args.values() if v is not None]
        try:
            args = parser.parse_args(tokens)
            return cmd.handler(args) or 0 if cmd else 1
        except SystemExit:
            return 1

    # Build a namespace from the parsed dict
    ns = SimpleNamespace(**parsed.args)
    return cmd.handler(ns) or 0
