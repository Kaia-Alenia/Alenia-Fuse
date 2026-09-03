"""
Interactive CLI mode for Alenia Porter
"""
import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style

from alenia_porter.cli.main import get_parser, cmd_info, cmd_convert

style = Style.from_dict({
    'prompt': 'ansicyan bold',
})

commands = ['help', 'version', 'info', 'convert', 'exit', 'quit', 'clear']
completer = WordCompleter(commands, ignore_case=True)

def run_interactive():
    print("╭──────────────────────────────╮")
    print("│        ALENIA PORTER         │")
    print("│      multimedia toolkit      │")
    print("╰──────────────────────────────╯")
    print("\nType 'help' for available commands, or 'exit' to quit.\n")
    
    session = PromptSession(
        history=InMemoryHistory(),
        style=style,
        completer=completer
    )
    
    parser = get_parser()
    
    while True:
        try:
            text = session.prompt('porter › ')
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
            
        text = text.strip()
        if not text:
            continue
            
        if text.lower() in ['exit', 'quit']:
            break
            
        if text.lower() == 'clear':
            # Use ANSI sequence to clear screen
            print('\033[2J\033[H', end='')
            continue
            
        args_list = text.split()
        try:
            # We don't want parser to sys.exit on error/help
            args = parser.parse_args(args_list)
            
            if args.command == "info":
                cmd_info(args)
            elif args.command == "convert":
                cmd_convert(args)
            else:
                parser.print_help()
                
        except SystemExit:
            # argparse calls sys.exit(2) on error, sys.exit(0) on help
            # We catch it so the interactive session doesn't die
            pass
