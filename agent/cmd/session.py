from rich.console import Console
from rich.prompt import Confirm
from agent.cmd import COMMANDS, command
from agent.paths import MEMORY_FILE
from agent.fancy_banner import say_bye
from agent.tools.session import compact_conversation, compact_tool_results
from agent.tools import TOOLS, LAZY, enable_tool, disable_tool
import json
from agent.cmd.arg_completers import get_available_models, get_tool_names

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

    console.print("[bold]Available commands:[/bold]\n")
    
    # pre-compute max width for alignment
    max_cmd = max(len(name) for name in COMMANDS) + 1  # +1 for the "/"
    max_usage = max(len(entry.get("usage", "")) for entry in COMMANDS.values())

    # print commands sorted by name with description and usage.
    for name, entry in sorted(COMMANDS.items()):
        cmd_col = f"/{name}".ljust(max_cmd + 1)
        usage_col = entry.get("usage", "").replace("[", "\\[").ljust(max_usage)
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

def do_tool_compact(ctx, messages):
    """
    Compacts the tool result messages by summarizing them into a shorter form.
    This is useful for keeping the conversation history manageable while retaining important tool outputs.
    The original tool messages are replaced with one summary message.
    """
    with console.status("[yellow]Compacting tool results...[/yellow]", spinner="dots"):
        new_messages = compact_tool_results(messages, ctx["model"])
    
    messages.clear()
    messages.extend(new_messages)
    console.print("[green]✓ Tool results compacted.[/green]")

@command("compact", description="Compact session into a summary", usage="")
def cmd_compact(arg, ctx):
    """
    Compacts the current session messages by summarizing them into a shorter form.
    """
    do_compact(ctx, ctx["messages"])

@command("compact_tools", description="Compact tool results into a summary", usage="")
def cmd_compact_tools(arg, ctx):
    """
    Compacts the tool result messages by summarizing them into a shorter form.
    """
    do_tool_compact(ctx, ctx["messages"])

from agent.tools import TOOLS, LAZY, enable_tool, disable_tool

@command("tools",
         description="List, enable, or disable tools",
         usage="[enable|disable <name>]",
         arg_completer=lambda: ["enable " + t for t in get_tool_names()] + 
                               ["disable " + t for t in get_tool_names()])
def cmd_tools(arg, ctx):
    """
    Lists active and lazy tools, or enables/disables a tool.
    Usage:
        /tools - lists active and lazy tools
        /tools enable <name> - enables a lazy tool
        /tools disable <name> - disables an active tool
    """
    if not arg:
        console.print("[bold green]Active tools:[/bold green]")
        for name in sorted(TOOLS):
            console.print(f"  [green]✓[/green] {name}")
        if LAZY:
            console.print("\n[bold dim]Lazy (inactive):[/bold dim]")
            for name in sorted(LAZY):
                console.print(f"  [dim]○ {name}[/dim]")
        return

    parts = arg.split(maxsplit=1)
    if len(parts) != 2 or parts[0] not in ("enable", "disable"):
        console.print("[red]Usage: /tools enable <name> | /tools disable <name>[/red]")
        return

    action, name = parts
    if action == "enable":
        if enable_tool(name):
            console.print(f"[green]✓ Enabled: {name}[/green]")
        else:
            console.print(f"[red]Not found in lazy tools: {name}[/red]")
    elif action == "disable":
        if disable_tool(name):
            console.print(f"[yellow]○ Disabled: {name}[/yellow]")
        else:
            console.print(f"[red]Not found in active tools: {name}[/red]")
