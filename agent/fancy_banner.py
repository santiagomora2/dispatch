import os
import shutil
import random
from rich.console import Console
from rich.columns import Columns
from rich.text import Text

WAYS_TO_BYE = ["See ya.", "Catch you later.", "Take it easy.", "*dap*", "Peace out."]

console = Console()

def print_banner(model: str, version: str = "0.1.0"):
    """
    Print a fancy banner with the agent's name, version, current model, and some helpful tips.
    The banner is designed to fit within the terminal width, with an ASCII art logo on the left
    and dynamic info on the right. It also shows up to 3 facts from memory for quick reference.
    """
    width = min(shutil.get_terminal_size().columns, 100)
    cwd = os.getcwd()

    # ASCII logo
    logo_lines = [
        " ██████╗ ██╗███████╗██████╗  █████╗ ████████╗ ██████╗██╗  ██╗",
        " ██╔══██╗██║██╔════╝██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██║  ██║",
        " ██║  ██║██║███████╗██████╔╝███████║   ██║   ██║     ███████║",
        " ██║  ██║██║╚════██║██╔═══╝ ██╔══██║   ██║   ██║     ██╔══██║",
        " ██████╔╝██║███████║██║     ██║  ██║   ██║   ╚██████╗██║  ██║",
        " ╚═════╝ ╚═╝╚══════╝╚═╝     ╚═╝  ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝",
    ]

    # Top border
    console.print(f"╭{'─' * (width - 2)}╮", style="green")

    # logo + right panel side by side
    tips = [
        ("/help",  "list all commands"),
        ("/note",  "add something to memory"),
        ("/tree",  "explore current directory"),
        ("/model", "switch ollama model"),
    ]

    logo_width = 66
    right_width = width - logo_width - 5

    logo_lines_padded = logo_lines + [
        f"  [dim]v{version}[/dim]",
        f"  [green]{model}[/green]",
        f"  [dim]{cwd[:]}[/dim]",
    ]

    right_lines = ["[dim]getting started[/dim]", "─" * (right_width - 2)]
    for cmd, desc in tips:
        right_lines.append(f"[green]{cmd}[/green]  [dim]{desc}[/dim]")
    right_lines.append("")
    right_lines.append("")
    right_lines.append("")

    max_rows = max(len(logo_lines_padded), len(right_lines))
    for i in range(max_rows):
        left = logo_lines_padded[i] if i < len(logo_lines_padded) else ""
        right = right_lines[i] if i < len(right_lines) else ""
        left_plain = left.ljust(logo_width)
        console.print(f"│ {left_plain}  ", end="", style="green")
        console.print(right)

    console.print(f"╰{'─' * (width - 2)}╯", style="green")

def say_bye():
    """
    Print a random goodbye message when exiting the application.
    """
    console.print(f"\n[yellow]{random.choice(WAYS_TO_BYE)}[/yellow]")