import sys
import platform
import shlex
from pathlib import Path
from typing import Optional, Iterable, List

from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.completion import Completer, Completion, PathCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import FormattedText

from alenia_porter.cli.registry import registry
from alenia_porter.cli.parser import parse_and_run
from alenia_porter.ffmpeg.capabilities import default_registry as caps
from alenia_porter.i18n.manager import t

# ─── Colors and Styling ───────────────────────────────────────────────────────
# Palette according to MEGA SPEC section 4.4
PORTER_STYLE = Style.from_dict({
    "prompt.symbol": "#8B5CF6 bold",  # Primary for identity and prompt
    "prompt.text": "#F8FAFC",         # Text
    "completion-menu": "bg:#0F172A #CBD5E1",
    "completion-menu.completion.current": "bg:#8B5CF6 #F8FAFC bold",
    "bottom-toolbar": "bg:#0F172A #94A3B8",
    "primary": "#8B5CF6",
    "primary_bright": "#A78BFA",
    "cyan": "#22D3EE bold",
    "text": "#F8FAFC",
    "muted": "#94A3B8",
    "dim": "#64748B",
})

def get_banner() -> FormattedText:
    return FormattedText([
        ("class:cyan",           "\n    A L E N I A\n"),
        ("class:primary_bright", "  ___  ___  ___ _____ ___ ___ \n"),
        ("class:primary",        " | _ \\/ _ \\| _ \\_   _| __| _ \\\n"),
        ("class:primary",        " |  _/ (_) |   / | | | _||   /\n"),
        ("class:primary",        " |_|  \\___/|_|_\\ |_| |___|_|_\\\n\n"),
        ("class:text",           f"  {t('cli.banner_subtitle')}\n\n"),
        ("class:muted",          "  "),
        ("class:cyan",           "/help "),
        ("class:muted",          f" {t('cli.banner_help')}\n\n"),
    ])

# ─── Persistent history file ────────────────────────────────────────────────
def _history_path() -> Path:
    system = platform.system()
    if system == "Windows":
        base = Path.home() / "AppData" / "Local" / "alenia_porter"
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support" / "alenia_porter"
    else:
        base = Path.home() / ".local" / "share" / "alenia_porter"
    base.mkdir(parents=True, exist_ok=True)
    return base / "history.txt"

# ─── Context-aware Completer ─────────────────────────────────────────────────
class PorterCompleter(Completer):
    def __init__(self):
        self.path_completer = PathCompleter(expanduser=True)

    def get_completions(self, document, complete_event) -> Iterable[Completion]:
        text = document.text_before_cursor
        
        # Simple lexing to understand context
        try:
            tokens = shlex.split(text)
        except ValueError:
            tokens = text.split()
            
        is_typing_new_word = not text.endswith(" ")

        # 1. First token completion: Commands
        if not tokens or (len(tokens) == 1 and is_typing_new_word):
            word = tokens[0] if tokens else ""
            # Support the '/' prefix as specified in the MEGA SPEC
            strip_slash = word.startswith("/")
            word_clean = word[1:] if strip_slash else word

            all_cmds = []
            for cmd in registry.get_all():
                all_cmds.append((cmd.name, cmd.description))
                for alias in cmd.aliases:
                    all_cmds.append((alias, f"Alias for {cmd.name}"))
            all_cmds += [("exit", "Exit Porter"), ("clear", "Clear screen"), ("help", "Show help")]

            for name, desc in sorted(all_cmds):
                if name.startswith(word_clean):
                    display_name = f"/{name}" if strip_slash else name
                    yield Completion(
                        display_name,
                        start_position=-len(word),
                        display=display_name,
                        display_meta=desc
                    )
            return

        # 2. Contextual completion (Paths and Options)
        if len(tokens) >= 1:
            cmd_name = tokens[0].lstrip("/")
            cmd = registry.get(cmd_name)
            
            typed = tokens[-1] if is_typing_new_word else ""
            
            # If typing an option
            if typed.startswith("--"):
                if cmd:
                    for arg in cmd.arguments:
                        if arg.name.startswith(typed):
                            yield Completion(arg.name, start_position=-len(typed), display_meta=arg.help)
                return

            # Otherwise fallback to Path completion
            yield from self.path_completer.get_completions(document, complete_event)

# ─── Help System ─────────────────────────────────────────────────────────────
def _print_internal_help(topic: Optional[str] = None):
    if topic:
        cmd = registry.get(topic)
        if not cmd:
            print(f"\n  {t('cli.unknown_cmd')} {topic}\n")
            return
        print(f"\n  {cmd.name.upper()}")
        print(f"  {cmd.description}\n")
        print(f"  {t('cli.usage')}")
        if cmd.arguments:
            print(f"    {cmd.name} [options] <arguments>")
        else:
            print(f"    {cmd.name}")
        
        if cmd.arguments:
            print(f"\n  {t('cli.options')}")
            for arg in cmd.arguments:
                print(f"    {arg.name:<15} {arg.help}")
        print()
        return

    # General organized help as per MEGA SPEC #10
    print(f"\n  {t('cli.commands')}\n")
    
    categories = {
        "CONVERT": ["convert", "compress", "optimize", "remux"],
        "VIDEO": ["trim", "cut", "concat", "resize", "crop", "rotate", "fps", "speed"],
        "AUDIO": ["extract-audio", "mute", "volume", "normalize", "fade"],
        "EXTRACT": ["frame", "thumbnail", "gif"],
        "INFORMATION": ["info", "formats", "codecs", "filters", "hardware"],
        "PORTER": ["config", "lang", "clear", "help", "exit"]
    }

    all_registered = {c.name: c for c in registry.get_all()}
    
    for cat, cmds in categories.items():
        print(f"  {cat}")
        for cname in cmds:
            if cname in all_registered or cname in ("clear", "help", "exit", "formats"):
                desc = all_registered[cname].description if cname in all_registered else ""
                print(f"    /{cname:<14} {desc}")
        print()

# ─── Interactive Loop ────────────────────────────────────────────────────────
def run_interactive():
    # Load capabilities silently in background
    caps.load_from_ffmpeg()

    print_formatted_text(get_banner(), style=PORTER_STYLE)

    completer = PorterCompleter()
    
    kb = KeyBindings()
    @kb.add('escape')
    def _(event):
        # Escape closes suggestions in prompt_toolkit by default,
        # but binding it explicitly doesn't hurt.
        pass

    session = PromptSession(
        history=FileHistory(str(_history_path())),
        style=PORTER_STYLE,
        completer=completer,
        complete_while_typing=True,
        key_bindings=kb
    )
    
    prompt_text = FormattedText([("class:prompt.symbol", "porter ❯ ")])

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

        # Basic built-in handling
        lower_text = text.lower()
        if lower_text in ("exit", "quit", "/exit", "/quit"):
            break
        if lower_text in ("clear", "/clear"):
            print("\033[2J\033[H", end="")
            continue

        # Handle help
        if lower_text.startswith("help") or lower_text.startswith("/help"):
            parts = lower_text.split()
            topic = parts[1] if len(parts) > 1 else None
            _print_internal_help(topic)
            continue

        # Remove starting slash if present for execution
        if text.startswith("/"):
            text = text[1:]

        try:
            tokens = shlex.split(text)
            parse_and_run(tokens)
        except SystemExit:
            pass
        except KeyboardInterrupt:
            print(f"\n  {t('cli.cancelled')}")
        except Exception as e:
            print(f"\n  \033[31m{t('cli.error')}\033[0m {e}\n")
