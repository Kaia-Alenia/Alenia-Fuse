"""
Alenia Porter CLI entry point.
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
        import alenia_porter.cli.handlers  # noqa: F401
        from alenia_porter.cli.interactive import run_interactive
        run_interactive()
        sys.exit(0)
        
    if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help"):
        print("""ALENIA PORTER
Professional multimedia toolkit

Usage:
  porter                 Start interactive Porter CLI
  porter formats         Browse supported output formats
  porter --version       Show version
  porter --help          Show this help

Interactive commands:
  Start Porter and type /help

Examples:
  porter
  porter formats
  porter formats video""")
        sys.exit(0)

    # Load all command handlers (triggers @register_command decorators)
    import alenia_porter.cli.handlers  # noqa: F401
    from alenia_porter.cli.parser import parse_and_run
    sys.exit(parse_and_run())

if __name__ == "__main__":
    main()
