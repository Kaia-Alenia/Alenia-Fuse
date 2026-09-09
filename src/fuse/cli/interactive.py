import platform
import shlex
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from fuse.cli.parser import parse_and_run
from fuse.cli.registry import registry
from fuse.ffmpeg.capabilities import default_registry as caps
from fuse.i18n.manager import t

_console = Console(highlight=False)

FUSE_STYLE = Style.from_dict({
    "prompt.symbol":                      "#8B5CF6 bold",
    "prompt.text":                        "#F8FAFC",
    "completion-menu":                    "bg:#0F172A #CBD5E1",
    "completion-menu.completion.current": "bg:#7C3AED #F8FAFC bold",
    "completion-menu.meta":               "bg:#0F172A #64748B",
    "completion-menu.meta.completion.current": "bg:#7C3AED #CBD5E1",
    "bottom-toolbar":                     "bg:#0F172A #475569",
    "scrollbar.background":               "bg:#0F172A",
    "scrollbar.button":                   "bg:#7C3AED",
})

# Category display order and colors
_CATEGORY_COLORS = {
    "categories.convert":     "#A78BFA",
    "categories.video":       "#22D3EE",
    "categories.audio":       "#34D399",
    "categories.extract":     "#FB923C",
    "categories.information": "#F472B6",
    "categories.general":     "#94A3B8",
    "categories.fuse":      "#64748B",
}
_CATEGORY_ORDER = list(_CATEGORY_COLORS.keys())


def _print_banner():
    from fuse import __version__
    title = Text()
    title.append("◈  ", style="bold #22D3EE")
    title.append("ALENIA FUSE", style="bold #F8FAFC")
    title.append(f"  v{__version__}", style="#A78BFA")

    body = Text()
    body.append(f"{t('cli.banner_subtitle')}\n", style="#CBD5E1")
    body.append(f"{t('cli.banner_hint')}", style="dim #94A3B8")

    _console.print()
    _console.print(Panel(
        Text.assemble(title, "\n", body),
        border_style="#7C3AED",
        box=box.ROUNDED,
        padding=(1, 2),
        expand=False,
    ))
    _console.print()


def _print_slash_discoverer():
    """Rich table of all commands, grouped by category."""
    all_cmds = registry.get_all()
    categories: dict[str, list] = {}
    for c in all_cmds:
        categories.setdefault(c.category_key, []).append(c)

    _console.print()

    ordered_keys = sorted(
        categories.keys(),
        key=lambda k: _CATEGORY_ORDER.index(k) if k in _CATEGORY_ORDER else 99,
    )

    for cat_key in ordered_keys:
        color = _CATEGORY_COLORS.get(cat_key, "#94A3B8")
        table = Table(
            title=f"[bold {color}]{t(cat_key).upper()}[/]",
            title_justify="left",
            box=box.SIMPLE_HEAD,
            padding=(0, 1),
            border_style="#1E293B",
            show_edge=False,
        )
        table.add_column("Command", style=f"bold {color}", no_wrap=True)
        table.add_column("Description", style="#94A3B8")
        for c in sorted(categories[cat_key], key=lambda x: x.name):
            desc = t(c.description_key)
            table.add_row(f"/{c.name}", desc)
        _console.print(table)


def _print_internal_help(topic: str | None = None):
    if topic:
        cmd = registry.get(topic)
        if not cmd:
            _console.print(f"\n  [#EF4444]Unknown command:[/] {topic}\n")
            return

        _console.print()
        _console.print(Panel(
            f"[#CBD5E1]{t(cmd.description_key)}[/]",
            title=f"[bold #A78BFA]/{cmd.name}[/]",
            subtitle="[dim]Command reference[/]",
            border_style="#7C3AED",
            box=box.ROUNDED,
            padding=(1, 2),
        ))

        if cmd.arguments:
            table = Table(
                title="Arguments",
                box=box.SIMPLE_HEAD,
                padding=(0, 1),
                border_style="#1E293B",
            )
            table.add_column("Argument", style="#22D3EE", no_wrap=True)
            table.add_column("Description", style="#94A3B8")
            for arg in cmd.arguments:
                marker = "[dim]optional[/] " if arg.action else "[bold #F8FAFC]required[/] "
                table.add_row(arg.name, marker + t(arg.help_key))
            _console.print(table)

        if cmd.aliases:
            aliases_str = "  ".join(f"[#A78BFA]/{a}[/]" for a in cmd.aliases)
            _console.print(f"  [dim]Aliases:[/] {aliases_str}\n")
        else:
            _console.print()
        return

    _console.print()
    _console.print(
        Rule("[bold #8B5CF6]Fuse Commands[/]", style="#2D2B55")
    )
    _print_slash_discoverer()


def _history_path() -> Path:
    system = platform.system()
    if system == "Windows":
        base = Path.home() / "AppData" / "Local" / "fuse"
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support" / "fuse"
    else:
        base = Path.home() / ".local" / "share" / "fuse"
    base.mkdir(parents=True, exist_ok=True)
    return base / "history.txt"


def _clear_history():
    p = _history_path()
    if p.exists():
        p.unlink()
        _console.print(f"\n  [#34D399]{t('cli.history_cleared')}[/]\n")
    else:
        _console.print(f"\n  [dim]{t('cli.history_empty')}[/]\n")


def run_interactive():
    try:
        caps.load_from_ffmpeg()
    except Exception:
        pass

    from fuse.cli.completion import ContextualCompleter
    _print_banner()

    kb = KeyBindings()

    @kb.add("escape")
    def _(event):
        pass

    session = PromptSession(
        history=FileHistory(str(_history_path())),
        style=FUSE_STYLE,
        completer=ContextualCompleter(),
        complete_while_typing=True,
        key_bindings=kb,
    )

    prompt_text = FormattedText([("class:prompt.symbol", "fuse ❯ ")])

    def _toolbar():
        """Keep the prompt informative without adding noise to command output."""
        from fuse.config.manager import config
        language = config.get("language", "en")
        cwd = str(Path.cwd())
        if len(cwd) > 42:
            cwd = "…" + cwd[-41:]
        return FormattedText([
            ("", f"  {cwd}"),
            ("", f"   ·   {language.upper()}   ·   /help   ·   /exit"),
        ])

    session.bottom_toolbar = _toolbar

    while True:
        try:
            text = session.prompt(prompt_text)
        except KeyboardInterrupt:
            print()
            continue
        except EOFError:
            print()
            break

        text = text.strip()
        if not text:
            continue

        lower = text.lower()

        if lower in ("exit", "quit", "/exit", "/quit"):
            _console.print("\n  [dim]Goodbye.[/]\n")
            break

        if lower in ("clear", "/clear"):
            _console.print("\033[2J\033[H", end="")
            continue

        if lower in ("/history clear", "history clear"):
            _clear_history()
            continue

        if lower.startswith(("/help", "help")):
            parts = text.split()
            topic = parts[1].lstrip("/") if len(parts) > 1 else None
            _print_internal_help(topic)
            continue

        # Slash discoverer: bare "/" shows all commands
        if text == "/":
            _print_slash_discoverer()
            continue

        text = text.removeprefix("/")

        try:
            tokens = shlex.split(text, posix=False)
            parse_and_run(tokens)
        except SystemExit:
            pass
        except KeyboardInterrupt:
            _console.print(f"\n  [dim]{t('cli.cancelled')}[/]")
        except Exception as exc:
            _console.print(f"\n  [bold #EF4444]Error:[/] {exc}\n")
