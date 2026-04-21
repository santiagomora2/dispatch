from rich.console import Console
from rich.prompt import Confirm
from agent.cmd import command, get_available_models
from agent.paths import MEMORY_FILE
from agent.fancy_banner import say_bye
from agent.tools.session import compact_conversation
import json

console = Console()

@command("clear", description="Clear the current session", usage="")
def cmd_clear(arg, ctx):
    """
    Clears the current session messages but keeps memory intact. 
    Useful for starting a new conversation thread while retaining known facts.
    Usage: /clear
    """
    ctx["messages"].clear()
    ctx["messages"].append({"role": "system", "content": ctx["system_prompt"]})
    console.print("[yellow]Session cleared. Memory kept.[/yellow]")

@command("reset", description="Reset the current session", usage="")
def cmd_reset(arg, ctx):
    """
    Resets the current session by clearing messages and wiping memory.
    Usage: /reset
    """
    if not Confirm.ask("Reset messages and memory?"):
        return
    ctx["messages"].clear()
    ctx["messages"].append({"role": "system", "content": ctx["system_prompt"]})
    MEMORY_FILE.write_text(json.dumps({"facts": [], "task_history": [], "scratch": {}}, indent=2))
    console.print("[yellow]Full reset done.[/yellow]")

@command("model",
         description="Switch the active Ollama model",
         usage="<model>",
         arg_completer=get_available_models)
def cmd_model(arg, ctx):
    """
    Switches the active Ollama model. 
    If no argument is given, shows the current model and available models.
    Usage: /model <model>
    """
    available = get_available_models()
    if not arg:
        console.print(f"[cyan]Current: {ctx['model']}[/cyan]")
        console.print("[dim]Available:[/dim]")
        for m in available:
            console.print(f"  [dim]{m}[/dim]")
        return
    if arg not in available:
        console.print(f"[red]Model '{arg}' not found in Ollama.[/red]")
        console.print(f"[dim]Available: {', '.join(available)}[/dim]")
        return
    ctx["model"] = arg
    console.print(f"[green]Switched to: {arg}[/green]")

@command("help", description="Show help information", usage="")
def cmd_help(arg, ctx):
    """
    Shows help information about available commands.
    Usage: /help
    """
    from agent.cmd import COMMANDS
    console.print("[bold]Available commands:[/bold]\n")
    
    # pre-compute max width for alignment
    max_cmd = max(len(name) for name in COMMANDS)
    max_usage = max(len(entry["usage"]) for entry in COMMANDS.values())

    # print commands sorted by name with description and usage.
    for name, entry in sorted(COMMANDS.items()):
        cmd_col = f"/{name}".ljust(max_cmd + 1)
        usage_col = entry["usage"].ljust(max_usage)
        console.print(f"  [cyan]{cmd_col}[/cyan]  [dim]{usage_col}[/dim]  {entry['description']}")

@command("exit", description="Exit the application", usage="")
def cmd_exit(arg, ctx):
    """
    Exits the application.
    Usage: /exit
    """
    say_bye()
    raise SystemExit

def do_compact(ctx, messages):
    """
    Compacts the session messages by summarizing them into a shorter form.
    This is useful for keeping the conversation history manageable while retaining context.
    The original messages are replaced with a system message containing the summary.
    """
    with console.status("[yellow]Compacting session...[/yellow]", spinner="dots"):
        summary = compact_conversation(messages, ctx["model"])
    
    system = messages[0]
    messages.clear()
    messages.append(system)
    messages.append({"role": "assistant", "content": f"[COMPACTED]\n{summary}"})
    console.print("[green]✓ Compacted.[/green]")

@command("compact", description="Compact session into a summary", usage="")
def cmd_compact(arg, ctx):
    """
    Compacts the current session messages by summarizing them into a shorter form.
    """
    do_compact(ctx, ctx["messages"])