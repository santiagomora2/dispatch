import re
import ollama
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Confirm
from agent.cmd import command
from agent.system_prompt import build_system_prompt

console = Console()

def plan(task: str, messages: list, model: str, ctx: dict):
    plan_messages = [
        {"role": "system", "content": build_system_prompt()},  # system prompt only — clean context for planning
        {"role": "user", "content": task}
    ]

    # Stage 1: Understand + Decompose
    plan_messages.append({"role": "user", "content": (
        "You are planning a multi-step task. "
        "First, restate what is being asked clearly and concisely. "
        "Then break it down into discrete, atomic subtasks."
    )})
    with console.status("[yellow]Understanding request...[/yellow]", spinner="dots"):
        r = ollama.chat(model=model, messages=plan_messages)
        plan_messages.append({"role": "assistant", "content": r.message.content})

    # Stage 2: Sequence + Risks
    plan_messages.append({"role": "user", "content": (
        "Now sequence those subtasks in optimal order, noting dependencies. "
        "For each step, briefly note what could go wrong and how to handle it."
    )})
    with console.status("[yellow]Sequencing and assessing risks...[/yellow]", spinner="dots"):
        r = ollama.chat(model=model, messages=plan_messages)
        plan_messages.append({"role": "assistant", "content": r.message.content})

    # Stage 3: Final structured plan — ask for numbered list explicitly
    plan_messages.append({"role": "user", "content": (
        "Output the final plan as a numbered list of steps. "
        "Each step must start with a number and period (e.g. '1. '). "
        "Be concise — one line per step. No prose before or after the list."
    )})
    with console.status("[yellow]Finalizing plan...[/yellow]", spinner="dots"):
        r = ollama.chat(model=model, messages=plan_messages)
        raw_plan = r.message.content

    # Parse numbered steps
    steps = re.findall(r"^\d+\.\s+(.+)$", raw_plan, re.MULTILINE)
    if not steps:
        console.print("[red]Could not parse plan into steps. Raw output:[/red]")
        console.print(Markdown(raw_plan))
        return

    # Show plan to user
    console.print("\n[bold]Proposed Plan:[/bold]")
    for i, step in enumerate(steps, 1):
        console.print(f"  [dim]{i}.[/dim] {step}")

    if not Confirm.ask("\nExecute this plan step by step?"):
        return

    # Execute steps sequentially with live checklist
    completed = []
    for i, step in enumerate(steps, 1):
        # Print checklist state
        console.print()
        for j, s in enumerate(steps, 1):
            if j in completed:
                console.print(f"  [green]✓[/green] [dim]{j}. {s}[/dim]")
            elif j == i:
                console.print(f"  [bold cyan]→[/bold cyan] [bold]{j}. {s}[/bold]")
            else:
                console.print(f"  [dim]○ {j}. {s}[/dim]")

        console.print()
        if not Confirm.ask(f"Run step {i}?"):
            console.print(f"[yellow]Skipped step {i}.[/yellow]")
            continue

        # Inject step into main conversation as user turn
        messages.append({"role": "user", "content": (
            f"Execute step {i} of {len(steps)}: {step}\n"
            f"Focus only on this step. Do not proceed to the next step."
        )})
        ctx["plan_step_ready"] = True
        completed.append(i)

        # Run agent turn for this step — re-use main loop via flag
        _run_agent_turn(messages, model, ctx)

    # Final checklist
    console.print()
    for j, s in enumerate(steps, 1):
        icon = "[green]✓[/green]" if j in completed else "[yellow]—[/yellow]"
        console.print(f"  {icon} [dim]{j}. {s}[/dim]")
    console.print("\n[green]Plan complete.[/green]")


def _run_agent_turn(messages, model, ctx):
    """Run one full agent turn (with tool calls) inline for plan execution."""
    from agent.tools import dispatch, get_schemas
    import json

    pending = True
    while pending:
        stream = ollama.chat(model=model, messages=messages, tools=get_schemas(), stream=True)
        full_content = ""
        tool_calls = []

        console.print("[bold green]dispatch>[/bold green] ", end="")
        try:
            for chunk in stream:
                msg = chunk.message
                if msg.content:
                    console.print(msg.content, end="", highlight=False)
                    full_content += msg.content
                if msg.tool_calls:
                    tool_calls.extend(msg.tool_calls)
        except KeyboardInterrupt:
            console.print("\n[yellow]↩ Interrupted.[/yellow]")
            return

        console.print()
        messages.append({"role": "assistant", "content": full_content,
                         "tool_calls": tool_calls or None})

        if tool_calls:
            for call in tool_calls:
                name = call.function.name
                args = call.function.arguments
                console.print(f"[dim]→ tool: {name}({args})[/dim]")
                result = dispatch(name, args)
                messages.append({"role": "tool", "content": json.dumps(result), "name": name})
        else:
            pending = False


@command("plan", description="Generate and execute a step-by-step plan", usage="<task>")
def cmd_plan(arg, ctx):
    if not arg:
        console.print("[red]Usage: /plan <task description>[/red]")
        return
    plan(arg, ctx["messages"], ctx["model"], ctx)