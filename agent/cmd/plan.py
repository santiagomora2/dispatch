import re
import uuid
import ollama
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Confirm
from agent.cmd import command
from agent.system_prompt import build_system_prompt
from agent.tools import dispatch, get_schemas
from agent.paths import PLANS_DIR
import json

console = Console()


def plan(task: str, messages: list, model: str, ctx: dict):
    """
    Generates and executes a step-by-step plan for a given task.
     1. Understand & Decompose: Restate the task and break it into discrete subtasks.
     2. Sequence & Assess Risks: Order the subtasks and note potential risks.
     3. Finalize Plan: Output a structured markdown plan with steps and placeholders for decisions/artifacts.
     4. Execute Sequentially: For each step, run it in isolation, allowing tool calls, and update the plan file with progress and artifacts.
     The plan is saved as a markdown file in the plans/ directory with a unique ID.
    """
    plan_messages = [
        {"role": "system", "content": build_system_prompt()},
        {"role": "user", "content": task}
    ]

    # Stage 1: Understand + Decompose
    plan_messages.append({"role": "user", "content": (
        "You are planning a multi-step task. "
        "Restate what is being asked clearly and concisely. "
        "Then break it down into discrete, atomic subtasks."
    )})
    with console.status("[yellow]Understanding request...[/yellow]", spinner="dots"):
        r = ollama.chat(model=model, messages=plan_messages)
        plan_messages.append({"role": "assistant", "content": r.message.content})

    # Stage 2: Sequence + Risks
    plan_messages.append({"role": "user", "content": (
        "Sequence those subtasks in optimal order, noting dependencies. "
        "For each step, briefly note what could go wrong and how to handle it."
    )})
    with console.status("[yellow]Sequencing and assessing risks...[/yellow]", spinner="dots"):
        r = ollama.chat(model=model, messages=plan_messages)
        plan_messages.append({"role": "assistant", "content": r.message.content})

    # Stage 3: Final structured plan as markdown
    plan_messages.append({"role": "user", "content": (
        "Output the final plan as markdown with this exact format:\n"
        "# Plan: <task>\n"
        "## Objective\n"
        "<one line>\n\n"
        "## Steps\n"
        "- [ ] 1. <step>\n"
        "- [ ] 2. <step>\n\n"
        "## Decisions & Artifacts\n"
        "<leave empty>\n\n"
        "## Current Step\n"
        "1\n\n"
        "Each step must start with a number and period. Be concise — one line per step."
    )})
    with console.status("[yellow]Finalizing plan...[/yellow]", spinner="dots"):
        r = ollama.chat(model=model, messages=plan_messages)
        raw_plan = r.message.content

    # Parse steps
    steps = re.findall(r"^\s*-\s*\[[ x]\]\s*\d+\.\s+(.+)$", raw_plan, re.MULTILINE)
    if not steps:
        # fallback: try plain numbered list
        steps = re.findall(r"^\d+\.\s+(.+)$", raw_plan, re.MULTILINE)
    if not steps:
        console.print("[red]Could not parse plan into steps. Raw output:[/red]")
        console.print(Markdown(raw_plan))
        return

    # Write plan file
    plan_id = str(uuid.uuid4())[:8]
    plan_file = PLANS_DIR / f"{plan_id}.md"
    plan_file.write_text(raw_plan)
    console.print(f"[dim]Plan saved: plans/{plan_id}.md[/dim]")

    # Show plan
    console.print("\n[bold]Proposed Plan:[/bold]")
    for i, step in enumerate(steps, 1):
        console.print(f"  [dim]{i}.[/dim] {step}")

    if not Confirm.ask("\nExecute this plan step by step?"):
        console.print(f"[dim]Plan kept at plans/{plan_id}.md[/dim]")
        return

    # Execute sequentially
    completed = []
    for i, step in enumerate(steps, 1):
        _print_checklist(steps, i, completed)

        if not Confirm.ask(f"Run step {i}?"):
            console.print(f"[yellow]Skipped step {i}.[/yellow]")
            continue

        # Build isolated context for this step
        step_messages = _build_step_messages(
            system_prompt=build_system_prompt(),
            step=step,
            i=i,
            total=len(steps),
            plan_md=plan_file.read_text()
        )

        _run_agent_turn(step_messages, model, ctx)

        # Update plan file — mark step done
        _update_plan_file(step, i, plan_file, model)
        completed.append(i)

    # Final checklist
    _print_checklist(steps, len(steps) + 1, completed)
    console.print(f"\n[green]Plan complete.[/green] [dim]Log: plans/{plan_id}.md[/dim]")


def _print_checklist(steps, current_i, completed):
    console.print()
    for j, s in enumerate(steps, 1):
        if j in completed:
            console.print(f"  [green]✓[/green] [dim]{j}. {s}[/dim]")
        elif j == current_i:
            console.print(f"  [bold cyan]→[/bold cyan] [bold]{j}. {s}[/bold]")
        else:
            console.print(f"  [dim]○ {j}. {s}[/dim]")


def _build_step_messages(system_prompt, step, i, total, plan_md):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": (
            f"## Current Plan State\n{plan_md}\n\n"
            f"## Your Task\n"
            f"Execute step {i} of {total}: {step}\n"
            f"Focus only on this step. Do not proceed further."
        )}
    ]


def _update_plan_file(step, i, plan_file, model):
    current = plan_file.read_text()
    r = ollama.chat(model=model, messages=[{"role": "user", "content": (
        f"Update this plan file: mark step {i} as completed (change [ ] to [x]) "
        f"and add any artifacts or decisions made to ## Decisions & Artifacts. "
        f"Update ## Current Step to {i + 1}. "
        f"Return only the updated markdown, nothing else.\n\n"
        f"STEP COMPLETED: {step}\n\n"
        f"PLAN:\n{current}"
    )}])
    plan_file.write_text(r.message.content)


def _run_agent_turn(messages, model, ctx):
    """Run one full agent turn with tool calls using isolated step context."""
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