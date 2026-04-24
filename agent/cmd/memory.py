from rich.console import Console
from rich.markdown import Markdown
from agent.cmd import command
from agent.tools.memory import update_memory
from agent.paths import MEMORY_FILE

console = Console()

@command("memory", description="Print current memory", usage="")
def cmd_memory(arg, ctx):
    console.print(Markdown(MEMORY_FILE.read_text()))

@command("note", description="Append a fact to memory", usage="<text>")
def cmd_note(arg, ctx):
    if not arg:
        console.print("[red]Usage: /note <text>[/red]")
        return
    update_memory(section="Facts", content=f"- {arg}")
    console.print("[green]Noted.[/green]")

@command("forget", description="Clear a memory section", usage="<section>", arg_completer=lambda: ["Top of Mind", "Projects", "Facts", "Task History"])
def cmd_forget(arg, ctx):
    if not arg:
        console.print("[red]Usage: /forget <Top of Mind|Projects|Facts|Task History>[/red]")
        return
    update_memory(section=arg, content="", replace=True)
    console.print(f"[yellow]Cleared: {arg}[/yellow]")