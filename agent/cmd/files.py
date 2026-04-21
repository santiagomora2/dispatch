from agent.cmd import command
from agent.tools.files import tree, list_dir
from rich.console import Console
console = Console()

@command("tree", description="Print directory tree", usage="<path> <depth>")
def cmd_tree(arg, ctx):
    """
    Print a directory tree of the specified path.
    Usage: /tree <path> <depth>
    """
    parts = arg.split() if arg else []
    path = parts[0] if parts else ""
    depth = int(parts[1]) if len(parts) > 1 else 3
    tree(path=path, depth=depth)

@command("ls", description="List directory contents", usage="<path>")
def cmd_ls(arg, ctx):
    """
    List files and directories at a given path.
    Usage: /ls <path>
    """
    result = list_dir(path=arg)
    for entry in result.get("entries", []):
        tag = "blue" if entry["type"] == "dir" else "dim"
        suffix = "/" if entry["type"] == "dir" else ""
        console.print(f"[{tag}]{entry['name']}{suffix}[/{tag}]")