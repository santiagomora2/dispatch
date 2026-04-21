from agent.tools import tool
from agent.paths import INVOCATION_DIR 

from pathlib import Path
from rich.console import Console
from rich.syntax import Syntax
from rich.prompt import Confirm
import difflib
import glob
import os
from rich.tree import Tree
from rich import print as rprint

console = Console()

@tool({
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read a file and return its contents with line numbers",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file"}
            },
            "required": ["path"]
        }
    }
})
def read_file(path: str):
    """
    Read a file and return its contents with line numbers. 
    """
    try:
        with open(path) as f:
            lines = f.readlines()
        numbered = "".join(f"{i+1}: {l}" for i, l in enumerate(lines))
        return {"content": numbered}
    except Exception as e:
        return {"error": f"An  error occurred while reading the file: {str(e)}"}
    
@tool({
    "type": "function",
    "function": {
        "name": "create_file",
        "description": (
            "Create a new file with an initial skeleton. "
            "Always provide a meaningful skeleton with structure, placeholders, and comments — never create empty files. "
            "After creating, use patch_file to fill in the actual content section by section."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to create, relative to the working directory."
                },
                "content": {
                    "type": "string",
                    "description": "Initial skeleton content. Include imports, class/function stubs, section comments, and placeholders so patch_file has clear anchors to target."
                }
            },
            "required": ["path", "content"]
        }
    }
})
def create_file(path: str, content: str = ""):
    """
    Create a new file with an initial skeleton. 
    Agent should always provide a meaningful skeleton with structure, placeholders, and comments.
    After creating, use patch_file to fill in the actual content section by section.
    """
    p = Path(path)
    try:
        if p.exists():
            if not Confirm.ask(f"{path} already exists. Overwrite?"):
                return {"error": "aborted"}
        
        p.parent.mkdir(parents=True, exist_ok=True)
        
        if content:
            console.print(Syntax(content, p.suffix.lstrip(".") or "text"))
            if not Confirm.ask(f"Create {path}?"):
                return {"error": "aborted"}
        
        p.write_text(content)
        return {"created": path}
    except Exception as e:
        return {"error": f"An error occurred during file creation: {str(e)}"}

@tool({
    "type": "function",
    "function": {
        "name": "patch_file",
        "description": (
            "Edit a file by replacing old_str with new_str. Handles all edit types:\n"
            "- Replace: old_str is what changes, new_str is the replacement\n"
            "- Insert: include the anchor line in old_str, repeat it in new_str with new content added after\n"
            "- Delete: set new_str to empty string\n\n"
            "old_str MUST be unique in the file — include enough surrounding lines to make it unambiguous. "
            "If unsure, use read_file first to verify the exact content and location."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to edit, relative to the working directory."
                },
                "old_str": {
                    "type": "string",
                    "description": "The exact string to find in the file. Must appear exactly once. Include surrounding lines for context if needed to ensure uniqueness."
                },
                "new_str": {
                    "type": "string",
                    "description": "The string to replace old_str with. To insert after a line, repeat that line here and add new content below it. To delete, pass an empty string."
                }
            },
            "required": ["path", "old_str", "new_str"]
        }
    }
})
def patch_file(path: str, old_str: str, new_str: str):
    """
    Patch a file by replacing old_str with new_str. Handles all edit types:
        - Replace: old_str is what changes, new_str is the replacement
        - Insert: include the anchor line in old_str, repeat it in new_str with new content added after
        - Delete: set new_str to empty string
    """
    p = Path(path)
    try:
        content = p.read_text()
    except Exception as e:
        return {"error": f"An error occurred while reading the file: {str(e)}"}

    if old_str not in content:
        return {"error": "old_str not found in file"}
    if content.count(old_str) > 1:
        return {"error": "old_str matches multiple locations, be more specific"}
    
    new_content = content.replace(old_str, new_str, 1)
    
    try:
        diff = difflib.unified_diff(
            content.splitlines(), new_content.splitlines(),
            lineterm="", fromfile=path, tofile=path
        )
        console.print(Syntax("\n".join(diff), "diff"))
        if not Confirm.ask(f"Apply patch to {path}?"):
            return {"error": "aborted"}
        
        p.write_text(new_content)
        return {"patched": path}
    except PermissionError:
        return {"error": f"Permission denied: Cannot write to '{path}'."}
    except Exception as e:
        return {"error": f"An unexpected error occurred while writing the patched file: {str(e)}"}

@tool({
    "type": "function",
    "function": {
        "name": "find_pattern",
        "description": (
            "Search for files matching a glob pattern within a directory. "
            "Use this before read_file or patch_file if unsure of exact paths. "
            "Examples: '**/*.py', '*.json', 'src/**/*.ts'"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern to match."},
                "root": {"type": "string", "description": "Directory to search in. Defaults to working directory if omitted.", "default": ""}
            },
            "required": ["pattern"]
        }
    }
})
def find_pattern(pattern: str, root: str = ""):
    """ 
    Search for files matching a glob pattern within a directory. (.gitignore-like)
    """
    try:
        base = Path(root) if root else INVOCATION_DIR
        matches = [str(p) for p in base.glob(pattern)]
        if not matches:
            return {"matches": [], "note": f"No files matched '{pattern}' in {base}"}
        return {"matches": sorted(matches), "root": str(base)}
    except Exception as e:
        return {"error": f"An error occurred while searching for files: {str(e)}"}


@tool({
    "type": "function",
    "function": {
        "name": "list_dir",
        "description": "List files and directories at a given path. Use to explore structure before acting on files.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory to list. Defaults to working directory if omitted.", "default": ""}
            },
            "required": []
        }
    }
})
def list_dir(path: str = ""):
    """
    List files and directories at a given path.
    """
    try:
        base = Path(path) if path else INVOCATION_DIR
        if not base.exists():
            return {"error": f"{base} does not exist"}
        entries = []
        for entry in sorted(base.iterdir()):
            entries.append({
                "name": entry.name,
                "type": "dir" if entry.is_dir() else "file",
                "size": entry.stat().st_size if entry.is_file() else None
            })
        return {"path": str(base), "entries": entries}
    except Exception as e:
            return {"error": f"An error occurred while listing the directory: {str(e)}"}    

@tool({
    "type": "function",
    "function": {
        "name": "tree",
        "description": "Print a directory tree. Use to understand project structure at a glance before navigating files.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Root directory for the tree. Defaults to working directory.", "default": ""},
                "depth": {"type": "integer", "description": "Max depth to traverse. Default 3.", "default": 3}
            },
            "required": []
        }
    }
})
def tree(path: str = "", depth: int = 3):
    """
    Print a directory tree. Used by agent to understand project structure at a glance before navigating files."""
    base = Path(path) if path else INVOCATION_DIR
    if not base.exists():
        return {"error": f"{base} does not exist"}

    def build(node: Path, rich_tree: Tree, current_depth: int):
        if current_depth == 0:
            return
        entries = sorted(node.iterdir(), key=lambda e: (e.is_file(), e.name))
        for entry in entries:
            if entry.name.startswith(".") or entry.name == "__pycache__" or ".egg-info" in entry.name:
                continue
            if entry.is_dir():
                branch = rich_tree.add(f"[bold blue]{entry.name}/[/bold blue]")
                build(entry, branch, current_depth - 1)
            else:
                rich_tree.add(f"[dim]{entry.name}[/dim]")

    try:
        rich_tree = Tree(f"[bold]{base.name}/[/bold]")
        build(base, rich_tree, depth)
        rprint(rich_tree)
    except Exception as e:
        return {"error": f"An error occurred while building the directory tree: {str(e)}"}

    # also return a plain text version for the agent
    def plain(node: Path, prefix: str, current_depth: int):
        if current_depth == 0:
            return []
        lines = []
        entries = sorted(node.iterdir(), key=lambda e: (e.is_file(), e.name))
        for entry in entries:
            if entry.name.startswith(".") or entry.name == "__pycache__":
                continue
            lines.append(f"{prefix}{entry.name}{'/' if entry.is_dir() else ''}")
            if entry.is_dir():
                lines.extend(plain(entry, prefix + "  ", current_depth - 1))
        return lines

    return {"tree": "\n".join(plain(base, "", depth)), "root": str(base)}


@tool({
    "type": "function",
    "function": {
        "name": "append_file",
        "description": "Append content to the end of an existing file. Use for adding to logs, notes, or files where you must not overwrite existing content.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file."},
                "content": {"type": "string", "description": "Content to append."}
            },
            "required": ["path", "content"]
        }
    }
})
def append_file(path: str, content: str):
    """
    Add content to the end of an existing file.
    Used by agent for adding to logs, notes, or files where you must not overwrite existing content.
    """
    p = Path(path)
    if not p.exists():
        return {"error": f"{path} does not exist. Use create_file instead."}
    try:
        console.print(f"[dim]Appending to {path}:[/dim]\n{content}")
        if not Confirm.ask(f"Append to {path}?"):
            return {"error": "aborted"}
        with open(p, "a") as f:
            f.write(content)
        return {"appended": path}
    except Exception as e:
        return {"error": f"An error occurred while appending to the file: {str(e)}"}