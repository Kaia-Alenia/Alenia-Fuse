from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass

@dataclass
class CommandArgument:
    name: str
    help: str
    nargs: Optional[str] = None
    action: Optional[str] = None
    completion: Optional[str] = None

@dataclass
class CommandDefinition:
    name: str
    description: str
    handler: Callable
    aliases: List[str] = None
    arguments: List[CommandArgument] = None
    category: str = "General"
    syntax: str = ""
    examples: List[str] = None

    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []
        if self.arguments is None:
            self.arguments = []
        if self.examples is None:
            self.examples = []

class CommandRegistry:
    def __init__(self):
        self._commands: Dict[str, CommandDefinition] = {}
        self._aliases: Dict[str, str] = {}

    def register(self, cmd: CommandDefinition):
        self._commands[cmd.name] = cmd
        for alias in cmd.aliases:
            self._aliases[alias] = cmd.name

    def get(self, name: str) -> Optional[CommandDefinition]:
        resolved_name = self._aliases.get(name, name)
        return self._commands.get(resolved_name)

    def get_all(self) -> List[CommandDefinition]:
        return list(self._commands.values())

    def resolve_alias(self, name: str) -> str:
        return self._aliases.get(name, name)

registry = CommandRegistry()

def register_command(name: str, description: str, aliases: List[str] = None, arguments: List[CommandArgument] = None, category: str = "General", syntax: str = "", examples: List[str] = None):
    def decorator(handler):
        cmd = CommandDefinition(
            name=name,
            description=description,
            handler=handler,
            aliases=aliases,
            arguments=arguments,
            category=category,
            syntax=syntax,
            examples=examples
        )
        registry.register(cmd)
        return handler
    return decorator
