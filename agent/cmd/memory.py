import json
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from agent.cmd import command
from agent.tools.memory import load_memory, save_memory

console = Console()

def get_facts():
    return load_memory().get("facts", [])

@command("memory", description="Print current memory", usage="")
def cmd_memory(arg, ctx):
    """
    Prints the current memory, including facts, task history and scratch space. 
    Facts are shown as a readable list, while task history and scratch are shown as JSON for clarity.
    Usage: /memory
    """
    data = load_memory()
    # show facts as a readable list, agent internals as json
    facts = data.get("facts", [])
    if facts:
        console.print("[bold]Facts:[/bold]")
        for i, f in enumerate(facts):
            console.print(f"  [cyan]{i}[/cyan]  {f}")
    else:
        console.print("[dim]No facts stored.[/dim]")

    console.print("\n[bold]Task history:[/bold]")
    history = data.get("task_history", [])
    if history:
        for entry in history[-5:]:  # last 5 only
            console.print(f"  [dim]→ {entry['task']}: {entry['outcome']}[/dim]")
    else:
        console.print("[dim]No task history.[/dim]")

    console.print("\n[bold]Scratch:[/bold]")
    scratch = data.get("scratch", {})
    if scratch:
        console.print(Syntax(json.dumps(scratch, indent=2), "json"))
    else:
        console.print("[dim]Empty.[/dim]")

@command("note", description="Append a fact to memory", usage="<fact>")
def cmd_note(arg, ctx):
    """
    Saves a fact to memory.
    Usage: /note <fact>
    """
    if not arg:
        console.print("[red]Usage: /note <fact>[/red]")
        return
    data = load_memory()
    data.setdefault("facts", []).append(arg)
    save_memory(data)
    console.print("[green]Noted.[/green]")

@command("forget", description="Remove a fact from memory", usage="<fact>",
         arg_completer=get_facts)
def cmd_forget(arg, ctx):
    """
    Removes a fact from memory.
    Usage: /forget <fact>
    """
    if not arg:
        console.print("[red]Usage: /forget <fact>[/red]")
        return
    data = load_memory()
    facts = data.get("facts", [])
    if arg not in facts:
        console.print(f"[red]Fact not found: '{arg}'[/red]")
        console.print("[dim]Use /memory to see stored facts.[/dim]")
        return
    facts.remove(arg)
    data["facts"] = facts
    save_memory(data)
    console.print("[green]Forgotten.[/green]")