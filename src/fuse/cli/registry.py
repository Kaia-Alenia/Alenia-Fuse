from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass

@dataclass
class CommandArgument:
    name: str
    help_key: str
    nargs: Optional[str] = None
    action: Optional[str] = None
    completion: Optional[str] = None   # 'path' | 'format' | 'codec' | 'language' | 'enum'
    value_type: Optional[str] = None   # 'media_path' | 'format' | 'codec' | ... (§5)


@dataclass
class CommandDefinition:
    name: str
    description_key: str
    handler: Callable
    aliases: List[str] = None
    arguments: List[CommandArgument] = None
    category_key: str = "categories.general"
    syntax_key: str = ""
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

def register_command(name: str, description_key: str, aliases: List[str] = None, arguments: List[CommandArgument] = None, category_key: str = "categories.general", syntax_key: str = "", examples: List[str] = None):
    def decorator(handler):
        cmd = CommandDefinition(
            name=name,
            description_key=description_key,
            handler=handler,
            aliases=aliases,
            arguments=arguments,
            category_key=category_key,
            syntax_key=syntax_key,
            examples=examples
        )
        registry.register(cmd)
        return handler
    return decorator
