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

    # Load all command handlers (triggers @register_command decorators)
    import alenia_porter.cli.handlers  # noqa: F401

    if len(sys.argv) == 1:
        # No arguments → interactive mode
        from alenia_porter.cli.interactive import run_interactive
        run_interactive()
        sys.exit(0)

    from alenia_porter.cli.parser import parse_and_run
    sys.exit(parse_and_run())


if __name__ == "__main__":
    main()
