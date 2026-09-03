from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import input_dialog
from alenia_porter.i18n.manager import t
from alenia_porter.cli.parser import parse_and_run
from alenia_porter.config.manager import config
import sys

def show_menu(title: str, options: list) -> str:
    selected_index = 0

    def get_formatted_text():
        result = []
        result.append(HTML(f"<b><ansicyan>{title}</ansicyan></b>\n\n"))
        for i, (val, label) in enumerate(options):
            if i == selected_index:
                result.append(HTML(f"<ansicyan> ❯ {label}</ansicyan>\n"))
            else:
                result.append(HTML(f"   {label}\n"))
        
        result.append(HTML("\n<ansigray> ↑↓ Navigate   Enter Select   Ctrl+C Cancel</ansigray>"))
        return result

    kb = KeyBindings()

    @kb.add("up")
    def _(event):
        nonlocal selected_index
        selected_index = max(0, selected_index - 1)

    @kb.add("down")
    def _(event):
        nonlocal selected_index
        selected_index = min(len(options) - 1, selected_index + 1)

    @kb.add("enter")
    def _(event):
        event.app.exit(result=options[selected_index][0])

    @kb.add("c-c")
    def _(event):
        event.app.exit(result=None)

    control = FormattedTextControl(get_formatted_text)
    window = Window(content=control)
    layout = Layout(window)

    app = Application(
        layout=layout,
        key_bindings=kb,
        full_screen=False
    )

    return app.run()

def run_guided_flow():
    while True:
        choice = show_menu(t("cli.prompt"), [
            ("convert", t("cli.menu.convert")),
            ("compress", t("cli.menu.compress")),
            ("analyze", t("cli.menu.analyze")),
            ("settings", t("cli.menu.settings")),
            ("command", "Command mode"),
            ("exit", t("cli.menu.exit")),
        ])
        
        if choice in ("exit", None):
            sys.exit(0)
            
        if choice == "command":
            return
            
        if choice == "settings":
            lang = show_menu("Select Language:", [("en", "English"), ("es", "Español")])
            if lang:
                config.set("language", lang)
                print(f"Language set to {lang}. Please restart for full effect.")
            continue
            
        if choice == "analyze":
            file = input_dialog(title="Input File", text="Enter file to analyze:").run()
            if file:
                parse_and_run(["info", file])
            continue
            
        if choice in ("convert", "compress"):
            file = input_dialog(title="Input File", text="Enter input file:").run()
            if not file: continue
            out = input_dialog(title="Output File", text="Enter output file (or empty for default):").run()
            
            args = [choice, file]
            if out:
                if choice == "compress":
                    args.extend(["--output", out])
                else:
                    args.append(out)
                    
            parse_and_run(args)
