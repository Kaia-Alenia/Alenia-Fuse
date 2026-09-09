"""
Parser and dispatcher for Alenia Fuse CLI.
Integrates human-syntax parser with argparse-based registry.
"""
import sys
import argparse
from fuse.cli.registry import registry
from fuse.cli.human_parser import parse_human_syntax


def get_parser():
    parser = argparse.ArgumentParser(
        prog="fuse",
        description="Alenia Fuse - Professional Multimedia Toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  fuse info movie.mp4
  fuse convert input.mp4 to webm
  fuse convert input.mp4 output.webm
  fuse compress movie.mp4 --quality high
  fuse trim movie.mp4 --start 00:01:00 --end 00:02:00
  fuse resize movie.mp4 1280x720
  fuse rotate movie.mp4 90
  fuse gif movie.mp4
  fuse volume song.mp3 +20%
  fuse normalize song.mp3
  fuse formats
  fuse lang es
"""
    )

    from fuse import __version__
    parser.add_argument("--version", action="version", version=f"Alenia Fuse {__version__}")

    subparsers = parser.add_subparsers(dest="command", metavar="command")

    from fuse.i18n.manager import t
    for cmd in registry.get_all():
        p = subparsers.add_parser(
            cmd.name,
            help=t(cmd.description_key),
            aliases=cmd.aliases
        )
        for arg in cmd.arguments:
            kwargs = {"help": t(arg.help_key)}
            if arg.nargs:
                kwargs["nargs"] = arg.nargs
            if arg.action and arg.action != "store":
                kwargs["action"] = arg.action
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

    from fuse.i18n.manager import t
    print(t("errors.unknown_command", command=args.command), file=sys.stderr)
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
