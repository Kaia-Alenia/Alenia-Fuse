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
        import fuse.cli.commands  # noqa: F401
        from fuse.cli.interactive import run_interactive
        run_interactive()
        sys.exit(0)
        
    if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help"):
        print("""ALENIA FUSE
Professional multimedia toolkit

Usage:
  fuse                       Start interactive Fuse CLI
  fuse formats               Browse supported output formats
  fuse --version             Show version
  fuse --help                Show this help

Interactive commands:
  Start Fuse and type /help

Examples:
  fuse
  fuse formats
  fuse formats video

""")
        sys.exit(0)

    # Load all command handlers (triggers @register_command decorators)
    import fuse.cli.commands  # noqa: F401
    from fuse.cli.parser import parse_and_run
    sys.exit(parse_and_run())

if __name__ == "__main__":
    main()
