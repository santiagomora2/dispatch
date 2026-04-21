from rich.console import Console

console = Console()
COMMANDS = {}  # name → {"fn": fn, "description": str, "usage": str}

def command(name, description="", usage="", arg_completer=None):
    """
    Decorator: Adds commands to the COMMANDS dictionary. 
    Has optional description, usage and argument completer (for example list models from ollama).
    """
    def decorator(fn):
        COMMANDS[name] = {"fn": fn, "description": description,
                          "usage": usage, "arg_completer": arg_completer}
        return fn
    return decorator

def dispatch_command(raw_input, ctx):
    """
    Dispatches a command based on the raw input.
    """
    parts = raw_input[1:].split(maxsplit=1)
    name = parts[0]
    arg = parts[1] if len(parts) > 1 else ""
    entry = COMMANDS.get(name)
    if not entry:
        console.print(f"[red]Unknown command: /{name}[/red]")
        return
    entry["fn"](arg, ctx)

import ollama

def get_available_models():
    """
    Get available models from ollama, return empty list if there's an error.
    """
    try:
        return [m.model for m in ollama.list().models]
    except Exception:
        return []

from agent.cmd import memory, session, files  # noqa