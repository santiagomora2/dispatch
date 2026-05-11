from rich.console import Console
from rich.markdown import Markdown
from agent.cmd import command
from agent.system_prompt import build_system_prompt
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

@command("remember", description="Inject memory into dispatch", usage="")
def cmd_remember(arg, ctx):
    """
    Re-injects the current memory into the system prompt. Useful if you've made manual edits to memory.md or want to refresh the agent's context after a series of updates.
    """
    ctx["system_prompt"] = build_system_prompt()
    # Clear messages and re-add system prompt to reset context
    ctx["messages"].clear()
    ctx["messages"].append({"role": "system", "content": MEMORY_FILE.read_text()})
    console.print("[green]Memory reloaded into context.[/green]")