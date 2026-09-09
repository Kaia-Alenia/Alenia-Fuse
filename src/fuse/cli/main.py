"""
Alenia Fuse CLI entry point.
"""
import sys


def main():
    # Ensure UTF-8 output on Windows
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    if len(sys.argv) == 1:
        # No arguments → interactive mode
        import fuse.cli.commands
        from fuse.cli.interactive import run_interactive
        run_interactive()
        sys.exit(0)
        
    # Load all command handlers (triggers @register_command decorators)
    import fuse.cli.commands  # noqa: F401
    if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help"):
        # Build help from the same registry used for dispatch. This prevents
        # the top-level help from drifting away from the available commands.
        from fuse.cli.parser import get_parser
        get_parser().print_help()
        sys.exit(0)

    from fuse.cli.parser import parse_and_run
    sys.exit(parse_and_run())

if __name__ == "__main__":
    main()
