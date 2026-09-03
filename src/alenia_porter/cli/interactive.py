"""
Interactive CLI for Alenia Porter.
Shows a real menu with keyboard navigation, then drops to a prompt session.
"""
import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import Application
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.formatted_text import HTML

from alenia_porter.cli.registry import registry
from alenia_porter.cli.parser import parse_and_run
from alenia_porter.i18n.manager import t
from alenia_porter.config.manager import config

import platform
from pathlib import Path


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
    """
    Provides completions from CommandRegistry.
    - First token: command names + aliases
    - Subsequent tokens: --options from the command's argument list
    """

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        tokens = text.split()

        if not tokens or (len(tokens) == 1 and not text.endswith(" ")):
            # Complete command names
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
            # Complete --options for the current command
            cmd_name = tokens[0]
            cmd = registry.get(cmd_name)
            if cmd:
                typed = tokens[-1] if text.endswith(" ") else ""
                for arg in cmd.arguments:
                    if arg.name.startswith("--"):
                        if arg.name.startswith(typed):
                            yield Completion(arg.name, start_position=-len(typed))


# ─── Arrow-key menu ──────────────────────────────────────────────────────────

def show_menu(options: list) -> str:
    """
    Displays a keyboard-navigable menu. Returns selected value or None on cancel.
    options: list of (value, label) tuples
    """
    selected = [0]

    def render():
        lines = []
        lines.append(("class:cyan bold", f" {t('cli.prompt')}\n\n"))
        for i, (val, label) in enumerate(options):
            if i == selected[0]:
                lines.append(("class:selected", f" \u276f {label}\n"))
            else:
                lines.append(("", f"   {label}\n"))
        lines.append(("class:hint", "\n \u2191\u2193 Navigate   Enter Select   Ctrl+C Cancel"))
        return lines

    kb = KeyBindings()

    @kb.add("up")
    def _up(event):
        selected[0] = max(0, selected[0] - 1)

    @kb.add("down")
    def _down(event):
        selected[0] = min(len(options) - 1, selected[0] + 1)

    @kb.add("enter")
    def _enter(event):
        event.app.exit(result=options[selected[0]][0])

    @kb.add("c-c")
    def _cancel(event):
        event.app.exit(result=None)

    menu_style = Style.from_dict({
        "cyan bold": "ansibrightcyan bold",
        "selected": "ansibrightcyan bold",
        "hint": "ansigray",
        "": "",
    })

    control = FormattedTextControl(render, focusable=True)
    window = Window(content=control)
    layout = Layout(window)

    app = Application(layout=layout, key_bindings=kb, full_screen=False,
                      mouse_support=False, style=menu_style)
    return app.run()


# ─── Media type detection ─────────────────────────────────────────────────────

VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv", ".ts", ".m2ts",
              ".wmv", ".3gp", ".m4v", ".ogv", ".f4v", ".rmvb", ".asf"}
AUDIO_EXTS = {".mp3", ".aac", ".wav", ".flac", ".ogg", ".opus", ".m4a", ".wma",
              ".aiff", ".alac", ".ape", ".mka"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff",
              ".tif", ".avif", ".heic", ".svg"}

# Curated output format choices by media type
VIDEO_FORMATS = [
    ("mp4",  "MP4   — H.264/AAC  (universal compatibility)"),
    ("webm", "WebM  — VP9/Opus   (web optimized)"),
    ("mkv",  "MKV   — H.264/AAC  (high quality container)"),
    ("mov",  "MOV   — H.264/AAC  (Apple/editing)"),
    ("avi",  "AVI   — H.264/MP3  (legacy)"),
    ("gif",  "GIF   — animated   (short clips only)"),
]
AUDIO_FORMATS = [
    ("mp3",  "MP3   — libmp3lame (universal)"),
    ("aac",  "AAC   — iTunes/Android compatible"),
    ("opus", "Opus  — best quality/size ratio"),
    ("flac", "FLAC  — lossless"),
    ("wav",  "WAV   — uncompressed PCM"),
    ("ogg",  "OGG   — Vorbis, open source"),
]
IMAGE_FORMATS = [
    ("webp", "WebP  — best compression + quality"),
    ("jpg",  "JPG   — universal, lossy"),
    ("png",  "PNG   — lossless"),
    ("avif", "AVIF  — next-gen (requires modern FFmpeg)"),
]

OPTIMIZED_DIR = "alenia_optimized"


def detect_media_type(path: "Path") -> str:
    """Returns 'video', 'audio', 'image', or 'unknown'."""
    ext = path.suffix.lower()
    if ext in VIDEO_EXTS:
        return "video"
    if ext in AUDIO_EXTS:
        return "audio"
    if ext in IMAGE_EXTS:
        return "image"
    return "unknown"


def scan_directory(folder: "Path"):
    """
    Recursively scan a directory for media files.
    Returns dict: {'video': [Path, ...], 'audio': [...], 'image': [...], 'unknown': [...]}
    """
    from pathlib import Path as P
    results = {"video": [], "audio": [], "image": [], "unknown": []}
    for item in sorted(folder.rglob("*")):
        if item.is_file() and not item.name.startswith("."):
            # Skip files already inside alenia_optimized/
            if OPTIMIZED_DIR in item.parts:
                continue
            media_type = detect_media_type(item)
            results[media_type].append(item)
    return results


# ─── Guided flows ─────────────────────────────────────────────────────────────

def prompt_path(label: str) -> str:
    """Prompt for a file or directory path."""
    from prompt_toolkit import prompt as pt_prompt
    from prompt_toolkit.formatted_text import HTML
    while True:
        path = pt_prompt(HTML(f"  <ansicyan>{label}</ansicyan> ")).strip()
        if not path:
            return None
        from pathlib import Path as P
        p = P(path)
        if p.exists():
            return str(p)
        print(f"  Not found: {path}")


def select_format_for_type(media_type: str) -> str:
    """Show a menu of target formats based on media type."""
    if media_type == "video":
        options = VIDEO_FORMATS
    elif media_type == "audio":
        options = AUDIO_FORMATS
    elif media_type == "image":
        options = IMAGE_FORMATS
    else:
        return None
    return show_menu(options)


def guided_convert_file(file: str):
    """Convert a single file — detect type, show relevant formats."""
    from pathlib import Path as P

    p = P(file)
    media_type = detect_media_type(p)

    # If unknown type, let user decide
    if media_type == "unknown":
        media_type = show_menu([
            ("video", "Video"),
            ("audio", "Audio"),
            ("image", "Image"),
        ])
        if not media_type:
            return

    print(f"\n  Detected type: {media_type}")
    print(f"  Available output formats:\n")

    fmt = select_format_for_type(media_type)
    if not fmt:
        return

    output = str(p.parent / f"{p.stem}.{fmt}")
    parse_and_run(["convert", file, output])


def guided_convert_folder(folder: str):
    """Recursively convert all media files in a folder."""
    from pathlib import Path as P

    p = P(folder)
    scan = scan_directory(p)

    total = sum(len(v) for k, v in scan.items() if k != "unknown")
    if total == 0:
        print(f"\n  No media files found in '{folder}'.\n")
        return

    print(f"\n  Found in '{p.name}':")
    if scan["video"]:
        print(f"    Video  : {len(scan['video'])} files")
    if scan["audio"]:
        print(f"    Audio  : {len(scan['audio'])} files")
    if scan["image"]:
        print(f"    Image  : {len(scan['image'])} files")
    if scan["unknown"]:
        print(f"    Unknown: {len(scan['unknown'])} files (skipped)")
    print()

    # Ask which types to process
    types_to_process = []
    for media_type in ("video", "audio", "image"):
        if not scan[media_type]:
            continue
        choice = show_menu([
            ("yes", f"Convert {len(scan[media_type])} {media_type} files"),
            ("no",  f"Skip {media_type}"),
        ])
        if choice == "yes":
            fmt = select_format_for_type(media_type)
            if fmt:
                types_to_process.append((media_type, fmt, scan[media_type]))

    if not types_to_process:
        print("  Nothing to process.\n")
        return

    # Build output directory inside the source folder
    out_base = p / OPTIMIZED_DIR
    processed = 0
    failed = 0

    for media_type, fmt, files in types_to_process:
        out_dir = out_base / media_type
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n  Converting {len(files)} {media_type} files → {out_dir.relative_to(p)} [{fmt}]\n")

        for src in files:
            dest = out_dir / f"{src.stem}.{fmt}"
            print(f"    {src.name} → {dest.name}")
            try:
                parse_and_run(["convert", str(src), str(dest)])
                processed += 1
            except Exception as e:
                print(f"    Error: {e}")
                failed += 1

    print(f"\n  Done. {processed} converted, {failed} failed.")
    print(f"  Output: {out_base}\n")


def guided_convert():
    """Main guided convert flow — handles file or folder."""
    from pathlib import Path as P

    path_str = prompt_path("Input file or folder:")
    if not path_str:
        return

    p = P(path_str)
    if p.is_dir():
        guided_convert_folder(path_str)
    else:
        guided_convert_file(path_str)


def guided_compress():
    from pathlib import Path as P

    path_str = prompt_path("Input file or folder:")
    if not path_str:
        return

    p = P(path_str)

    if p.is_dir():
        scan = scan_directory(p)
        total = len(scan["video"]) + len(scan["audio"])
        if total == 0:
            print(f"\n  No compressible media files found.\n")
            return
        print(f"\n  Found: {len(scan['video'])} video, {len(scan['audio'])} audio files")

    quality = show_menu([
        ("balanced", "Balanced  (recommended)"),
        ("high", "High quality"),
        ("max", "Maximum compression"),
    ])
    if not quality:
        return

    if p.is_dir():
        scan = scan_directory(p)
        out_base = p / OPTIMIZED_DIR
        for media_type in ("video", "audio"):
            for src in scan[media_type]:
                out_dir = out_base / media_type
                out_dir.mkdir(parents=True, exist_ok=True)
                dest = out_dir / src.name
                print(f"  Compressing {src.name} ...")
                parse_and_run(["compress", str(src), "--quality", quality, "--output", str(dest)])
    else:
        parse_and_run(["compress", path_str, "--quality", quality])



def guided_settings():
    choice = show_menu([
        ("lang", "Change language"),
        ("back", "Back"),
    ])
    if choice == "lang":
        lang = show_menu([
            ("en", "English"),
            ("es", "Español"),
            ("pt", "Português"),
            ("fr", "Français"),
            ("de", "Deutsch"),
            ("it", "Italiano"),
            ("ja", "日本語"),
            ("ko", "한국어"),
            ("zh", "中文"),
            ("ru", "Русский"),
        ])
        if lang:
            parse_and_run(["lang", lang])


def run_main_menu():
    """Show the main interactive menu and handle selection."""
    choice = show_menu([
        ("convert", t("cli.menu.convert")),
        ("compress", t("cli.menu.compress")),
        ("analyze", t("cli.menu.analyze")),
        ("settings", t("cli.menu.settings")),
        ("command", "Command mode  (advanced)"),
        ("exit", t("cli.menu.exit")),
    ])

    if choice in (None, "exit"):
        sys.exit(0)

    if choice == "convert":
        guided_convert()
    elif choice == "compress":
        guided_compress()
    elif choice == "analyze":
        path_str = prompt_path("File or folder to analyze:")
        if path_str:
            from pathlib import Path as P
            p = P(path_str)
            if p.is_dir():
                scan = scan_directory(p)
                print(f"\n  Scan of '{p.name}':")
                print(f"    Video  : {len(scan['video'])} files")
                print(f"    Audio  : {len(scan['audio'])} files")
                print(f"    Image  : {len(scan['image'])} files")
                if scan["unknown"]:
                    print(f"    Unknown: {len(scan['unknown'])} files")
                print()
                # Offer to analyze the first file of each type
                for media_type in ("video", "audio", "image"):
                    if scan[media_type]:
                        first = scan[media_type][0]
                        print(f"  Sample {media_type}: {first.name}")
                        parse_and_run(["info", str(first)])
            else:
                parse_and_run(["info", path_str])
    elif choice == "settings":
        guided_settings()
    elif choice == "command":
        return  # fall through to prompt loop



# ─── Main interactive entry point ─────────────────────────────────────────────

BANNER = """\
╭──────────────────────────────────────────────╮
│                                              │
│               ALENIA PORTER                  │
│           Multimedia made simple             │
│                                              │
╰──────────────────────────────────────────────╯
"""

style = Style.from_dict({"prompt": "ansicyan bold"})


def run_interactive():
    print(BANNER)

    # Show main menu first
    try:
        run_main_menu()
    except KeyboardInterrupt:
        print()
    except EOFError:
        sys.exit(0)

    # Drop into prompt loop
    completer = PorterCompleter()
    session = PromptSession(
        history=FileHistory(str(_history_path())),
        style=style,
        completer=completer,
        complete_while_typing=True,
    )

    print("  Type a command or 'help' for options. Ctrl+C to cancel, 'exit' to quit.\n")

    while True:
        try:
            text = session.prompt("porter › ")
        except KeyboardInterrupt:
            print()
            continue
        except EOFError:
            break

        text = text.strip()
        if not text:
            continue

        lower = text.lower()

        if lower in ("exit", "quit"):
            break

        if lower == "clear":
            print("\033[2J\033[H", end="")
            continue

        if lower == "menu":
            try:
                run_main_menu()
            except KeyboardInterrupt:
                print()
            continue

        if lower in ("help", "?"):
            _print_help()
            continue

        tokens = text.split()
        try:
            parse_and_run(tokens)
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
