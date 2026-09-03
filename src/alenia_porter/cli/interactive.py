import sys
from typing import List, Tuple, Optional
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import Application
from prompt_toolkit.layout.containers import Window, HSplit
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
import platform
from pathlib import Path

from alenia_porter.cli.registry import registry
from alenia_porter.cli.parser import parse_and_run
from alenia_porter.i18n.manager import t
from alenia_porter.ffmpeg.capabilities import default_registry as caps

# ─── Colors and Styling ───────────────────────────────────────────────────────

PORTER_STYLE = Style.from_dict({
    "background": "bg:#020617",
    "panel": "bg:#111827",
    "panel_secondary": "bg:#0F172A",
    "border": "#334155",
    "primary": "#7C5CFF",
    "primary_bright": "#9A84FF",
    "cyan": "#22D3EE",
    "success": "#22C55E",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "info": "#38BDF8",
    "text": "#F8FAFC",
    "secondary_text": "#CBD5E1",
    "muted": "#94A3B8",
    "disabled": "#64748B",
    
    # Custom styles for menu
    "menu_title": "#22D3EE bold",
    "menu_selected": "bg:#0F172A #9A84FF bold",
    "menu_unselected": "#CBD5E1",
    "menu_hint": "#94A3B8",
    "prompt": "#22D3EE bold",
    "search_box": "bg:#0F172A #F8FAFC",
})

BANNER = """\
╭──────────────────────────────────────────────────────╮
│                                                      │
│                     ALENIA PORTER                    │
│                 Multimedia made simple               │
│                                                      │
╰──────────────────────────────────────────────────────╯
"""

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
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        tokens = text.split()

        if not tokens or (len(tokens) == 1 and not text.endswith(" ")):
            word = tokens[0] if tokens else ""
            all_names = []
            for cmd in registry.get_all():
                all_names.append(cmd.name)
                all_names.extend(cmd.aliases)
            all_names += ["exit", "quit", "clear", "help"]

            for name in sorted(all_names):
                if name.startswith(word):
                    yield Completion(name, start_position=-len(word))
        elif len(tokens) >= 1:
            cmd_name = tokens[0]
            cmd = registry.get(cmd_name)
            if cmd:
                typed = tokens[-1] if not text.endswith(" ") else ""
                for arg in cmd.arguments:
                    if arg.name.startswith("--") and arg.name.startswith(typed):
                        yield Completion(arg.name, start_position=-len(typed))
                    # TODO: add contextual completions (e.g., formats) based on `arg.completion`


# ─── Advanced Menu Component ─────────────────────────────────────────────────

def show_menu(options: List[Tuple[str, str]], title: str = "", searchable: bool = False) -> Optional[str]:
    """Displays a keyboard-navigable menu. Options are (value, label)."""
    state = {
        "selected": 0,
        "search_text": "",
        "filtered": options,
    }

    def _update_filter():
        if not searchable or not state["search_text"]:
            state["filtered"] = options
        else:
            q = state["search_text"].lower()
            state["filtered"] = [o for o in options if q in o[1].lower() or q in o[0].lower()]
        state["selected"] = max(0, min(state["selected"], len(state["filtered"]) - 1))

    def render():
        lines = []
        if title:
            lines.append(("class:menu_title", f" {title}\n\n"))
            
        if searchable:
            lines.append(("class:search_box", f" Search: {state['search_text']}_ \n\n"))

        if not state["filtered"]:
            lines.append(("class:muted", "   No matches found.\n"))
        else:
            for i, (val, label) in enumerate(state["filtered"]):
                if i == state["selected"]:
                    lines.append(("class:menu_selected", f" ❯ {label} \n"))
                else:
                    lines.append(("class:menu_unselected", f"   {label} \n"))
                    
        lines.append(("class:menu_hint", "\n ↑ ↓ Navigate   Enter Select   Esc Back"))
        return lines

    kb = KeyBindings()

    @kb.add("up")
    def _up(event):
        state["selected"] = max(0, state["selected"] - 1)

    @kb.add("down")
    def _down(event):
        state["selected"] = min(len(state["filtered"]) - 1, state["selected"] + 1)

    @kb.add("enter")
    def _enter(event):
        if state["filtered"]:
            event.app.exit(result=state["filtered"][state["selected"]][0])
        else:
            event.app.exit(result=None)

    @kb.add("escape")
    @kb.add("c-c")
    def _cancel(event):
        event.app.exit(result=None)

    @kb.add("c-k")
    def _palette(event):
        event.app.exit(result="__palette__")

    if searchable:
        @kb.add("<any>")
        def _type(event):
            char = event.key_sequence[0].data
            if len(char) == 1 and char.isprintable():
                state["search_text"] += char
                _update_filter()

        @kb.add("backspace")
        def _backspace(event):
            state["search_text"] = state["search_text"][:-1]
            _update_filter()

    control = FormattedTextControl(render, focusable=True)
    window = Window(content=control)
    layout = Layout(window)
    app = Application(layout=layout, key_bindings=kb, full_screen=False, style=PORTER_STYLE)
    return app.run()


# ─── Media type detection & Helpers ──────────────────────────────────────────

VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv", ".ts", ".m2ts",
              ".wmv", ".3gp", ".m4v", ".ogv", ".f4v", ".rmvb", ".asf"}
AUDIO_EXTS = {".mp3", ".aac", ".wav", ".flac", ".ogg", ".opus", ".m4a", ".wma",
              ".aiff", ".alac", ".ape", ".mka"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff",
              ".tif", ".avif", ".heic", ".svg"}

OPTIMIZED_DIR = "alenia_optimized"

def detect_media_type(path: "Path") -> str:
    ext = path.suffix.lower()
    if ext in VIDEO_EXTS: return "video"
    if ext in AUDIO_EXTS: return "audio"
    if ext in IMAGE_EXTS: return "image"
    return "unknown"

def scan_directory(folder: "Path"):
    from pathlib import Path as P
    results = {"video": [], "audio": [], "image": [], "unknown": []}
    for item in sorted(folder.rglob("*")):
        if item.is_file() and not item.name.startswith("."):
            if OPTIMIZED_DIR in item.parts:
                continue
            media_type = detect_media_type(item)
            results[media_type].append(item)
    return results

def prompt_path(label: str) -> str:
    from prompt_toolkit import prompt as pt_prompt
    from prompt_toolkit.formatted_text import FormattedText
    while True:
        try:
            path = pt_prompt(FormattedText([("class:prompt", f"  {label} ")]), style=PORTER_STYLE).strip()
        except (KeyboardInterrupt, EOFError):
            return None
        if not path:
            return None
        from pathlib import Path as P
        p = P(path)
        if p.exists():
            return str(p)
        print(f"  Not found: {path}")

def select_format_for_type(media_type: str) -> str:
    # Use dynamically loaded capabilities
    available_muxers = caps.get_muxers_by_category(media_type)
    options = []
    
    # Highlight some curated popular options first if available
    popular = []
    if media_type == "video":
        popular = ["mp4", "mkv", "webm", "mov", "avi", "gif"]
    elif media_type == "audio":
        popular = ["mp3", "aac", "opus", "flac", "wav", "ogg"]
    elif media_type == "image":
        popular = ["webp", "jpg", "png", "avif", "bmp"]
        
    for p in popular:
        if any(m.name == p for m in available_muxers):
            desc = next(m.description for m in available_muxers if m.name == p)
            options.append((p, f"{p.upper():<5} — {desc}"))
            
    options.append(("__search__", "Other formats (Search...)"))
    
    choice = show_menu(options, title=f"Select target format for {media_type}")
    
    if choice == "__search__":
        # Show all valid formats for this type
        all_options = [(m.name, f"{m.name.upper():<6} — {m.description}") for m in available_muxers]
        choice = show_menu(all_options, title="Search all formats", searchable=True)
        
    return choice


# ─── Guided flows ─────────────────────────────────────────────────────────────

def guided_convert_file(file: str):
    from pathlib import Path as P
    p = P(file)
    media_type = detect_media_type(p)

    if media_type == "unknown":
        media_type = show_menu([("video", "Video"), ("audio", "Audio"), ("image", "Image")])
        if not media_type: return

    fmt = select_format_for_type(media_type)
    if not fmt: return

    output = str(p.parent / f"{p.stem}.{fmt}")
    parse_and_run(["convert", file, output])


def get_unique_path(base_path: "Path") -> "Path":
    """Returns a unique path by appending _1, _2 if file exists."""
    if not base_path.exists():
        return base_path
    
    parent = base_path.parent
    stem = base_path.stem
    ext = base_path.suffix
    counter = 1
    
    while True:
        new_path = parent / f"{stem}_{counter}{ext}"
        if not new_path.exists():
            return new_path
        counter += 1

def guided_convert_folder(folder: str):
    from pathlib import Path as P
    from alenia_porter.media.models import Media
    from alenia_porter.operations.convert import ConvertOperation
    
    p = P(folder)
    scan = scan_directory(p)
    total = sum(len(v) for k, v in scan.items() if k != "unknown")
    if total == 0:
        print(f"\n  No media files found in '{folder}'.\n")
        return

    print(f"\n  Found in '{p.name}':")
    for t in ["video", "audio", "image"]:
        if scan[t]: print(f"    {t.capitalize():<7}: {len(scan[t])} files")
    print()

    types_to_process = []
    for media_type in ("video", "audio", "image"):
        if not scan[media_type]: continue
        choice = show_menu([("yes", f"Convert {len(scan[media_type])} {media_type} files"), ("no", f"Skip {media_type}")])
        if choice == "yes":
            fmt = select_format_for_type(media_type)
            if fmt:
                types_to_process.append((media_type, fmt, scan[media_type]))

    if not types_to_process:
        print("  Nothing to process.\n")
        return

    out_base = p / OPTIMIZED_DIR
    for media_type, fmt, files in types_to_process:
        out_dir = out_base / media_type
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n  Converting {len(files)} {media_type} files → {out_dir.relative_to(p)} [{fmt}]\n")
        
        for i, src in enumerate(files, 1):
            dest = get_unique_path(out_dir / f"{src.stem}.{fmt}")
            
            def make_prog(current, total, name):
                return lambda prog: print(f"\r  Converting [{current}/{total}] {name} {prog.percent:.1f}% ", end="", flush=True)
                
            try:
                media = Media.inspect(str(src))
                op = ConvertOperation(media, fmt).output(str(dest))
                success = op.run(on_progress=make_prog(i, len(files), src.name))
                if not success:
                    print(f"\r  Converting [{i}/{len(files)}] {src.name} [FAILED]   ")
            except Exception as e:
                print(f"\r  Converting [{i}/{len(files)}] {src.name} [ERROR: {e}]")
        print("\n  Done.\n")


def guided_convert():
    path_str = prompt_path("Input file or folder:")
    if not path_str: return
    from pathlib import Path as P
    p = P(path_str)
    if p.is_dir():
        guided_convert_folder(path_str)
    else:
        guided_convert_file(path_str)


def guided_compress():
    path_str = prompt_path("Input file to compress:")
    if not path_str: return
    from pathlib import Path as P
    p = P(path_str)
    if p.is_dir():
        print("  Batch compression not yet fully supported in guided mode.")
        input("  Press Enter to continue...")
        return
    parse_and_run(["compress", path_str])

def run_command_palette():
    options = []
    for cmd in registry.get_all():
        options.append((cmd.name, f"{cmd.name:<15} {cmd.description}"))
    choice = show_menu(options, title="Command Palette", searchable=True)
    if choice:
        # For simplicity, we just pre-fill a prompt session with the command name
        session = PromptSession(history=FileHistory(str(_history_path())), style=PORTER_STYLE, completer=PorterCompleter())
        try:
            text = session.prompt("porter ❯ ", default=f"{choice} ")
            if text.strip():
                parse_and_run(text.split())
        except (KeyboardInterrupt, EOFError):
            pass


def run_command_mode():
    completer = PorterCompleter()
    session = PromptSession(history=FileHistory(str(_history_path())), style=PORTER_STYLE, completer=completer, complete_while_typing=True)
    print("  Type a command or 'help' for options. Ctrl+C to cancel, 'exit' to quit.\n")
    while True:
        try:
            text = session.prompt("porter ❯ ")
        except KeyboardInterrupt:
            print()
            continue
        except EOFError:
            break

        text = text.strip()
        if not text: continue
        lower = text.lower()
        if lower in ("exit", "quit"): break
        if lower == "clear":
            print("\033[2J\033[H", end="")
            continue
        if lower == "menu":
            return
        if lower in ("help", "?"):
            _print_help()
            continue
        try:
            parse_and_run(text.split())
        except SystemExit:
            pass
        except KeyboardInterrupt:
            print("\n  Operation cancelled.")


def _print_help():
    print("\n  Available commands:\n")
    for cmd in registry.get_all():
        aliases = f"  [{', '.join(cmd.aliases)}]" if cmd.aliases else ""
        print(f"    {cmd.name:<20} {cmd.description}{aliases}")
    print("\n  Special:\n")
    print("    menu                 Return to the main menu")
    print("    clear                Clear the screen")
    print("    exit / quit          Exit Porter\n")


def run_main_menu():
    """Main loop for the interactive UI."""
    while True:
        print(BANNER)
        
        choice = show_menu([
            ("convert", t("cli.menu.convert")),
            ("compress", t("cli.menu.compress")),
            ("edit_video", t("cli.menu.edit_video")),
            ("edit_audio", t("cli.menu.edit_audio")),
            ("edit_image", t("cli.menu.process_images")),
            ("extract", t("cli.menu.extract_media")),
            ("analyze", t("cli.menu.analyze")),
            ("settings", t("cli.menu.settings")),
            ("palette", "Command Palette (Ctrl+K)"),
            ("command", "Command mode (advanced)"),
            ("help", t("cli.menu.help")),
            ("exit", t("cli.menu.exit")),
        ], title=t("cli.prompt"))

        if choice in (None, "exit"):
            sys.exit(0)

        if choice == "convert":
            guided_convert()
        elif choice == "compress":
            guided_compress()
        elif choice == "analyze":
            path_str = prompt_path("File or folder to analyze:")
            if path_str:
                parse_and_run(["info", path_str])
        elif choice in ("palette", "__palette__"):
            run_command_palette()
        elif choice == "command":
            run_command_mode()
        elif choice == "help":
            _print_help()
            input("  Press Enter to continue...")
        elif choice == "settings":
            lang = show_menu([("es", "Español"), ("en", "English"), ("pt", "Português"), ("fr", "Français"), ("de", "Deutsch"), ("it", "Italiano"), ("ja", "日本語"), ("ko", "한국어"), ("zh", "中文"), ("ru", "Русский")], title="Language")
            if lang:
                parse_and_run(["lang", lang])
        else:
            print(f"\n  Not yet fully implemented: {choice}")
            input("  Press Enter to continue...")

def run_interactive():
    # Make sure capabilities are loaded before showing menus that might need them
    caps.load_from_ffmpeg()
    try:
        run_main_menu()
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)
