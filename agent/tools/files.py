from agent.tools import tool
from agent.paths import INVOCATION_DIR 

from pathlib import Path
from rich.console import Console
from rich.syntax import Syntax
from rich.prompt import Confirm
import difflib
import fnmatch
import glob
import os
from rich.tree import Tree
from rich import print as rprint

console = Console()

# .dispatchignore handling inspired by gitignore
DISPATCHIGNORE = INVOCATION_DIR / ".dispatchignore"


def get_dispatchignore_rules():
    if not DISPATCHIGNORE.exists():
        return []
    return [
        line.strip() for line in DISPATCHIGNORE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def is_dispatch_ignored(path: str):
    target = Path(path)
    if not target.is_absolute():
        target = (INVOCATION_DIR / target).resolve()
    try:
        rel = target.relative_to(INVOCATION_DIR.resolve()).as_posix()
    except ValueError:
        rel = target.as_posix()
    
    for rule in get_dispatchignore_rules():
        if (
            (rule.endswith("/") and rel.startswith(rule.rstrip("/") + "/"))
            or fnmatch.fnmatch(rel, rule)
            or fnmatch.fnmatch(Path(rel).name, rule)
        ):
            return True
    return None

@tool({
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read a file and return its contents with line numbers. Output truncated to 2000 lines",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file (relative)"},
                "offset": {"type": "integer", "description": "Line offset to start reading from (0 indexed)", "default": 0},
                "limit": {"type": "integer", "description": "Maximum number of lines to read", "default": 2000}
            },
            "required": ["path"]
        }
    }
})
def read_file(path: str, offset: int = 0, limit: int = 2000):
    """
    Read a file and return its contents with line numbers. Output truncated to 2000 lines.
    """
    if is_dispatch_ignored(path):
        return {"error": f"Blocked: {path} matches .dispatchignore"}

    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        numbered = "".join(f"{i+1}: {l}" for i, l in enumerate(lines[offset:offset+limit]))
        return {"content": numbered}
    except Exception as e:
        return {"error": f"An  error occurred while reading the file: {str(e)}"}
    
@tool({
    "type": "function",
    "function": {
        "name": "write_file",
        "description": (
            "Writes content to a file, creating it if it doesn't exist. If the file already exists, prompts for confirmation before overwriting."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to write, relative to the working directory."
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file."
                }
            },
            "required": ["path", "content"]
        }
    }
})
def write_file(path: str, content: str = ""):
    """
    Write content to a file, creating it if it doesn't exist. If the file already exists, prompts for confirmation before overwriting.
    """
    if is_dispatch_ignored(path):
        return {"error": f"Blocked: {path} matches .dispatchignore"}
    
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
        
        p.write_text(content, encoding="utf-8")
        return {"created": path}
    except Exception as e:
        return {"error": f"An error occurred during file creation: {str(e)}"}

@tool({
    "type": "function",
    "function": {
        "name": "patch_file",
        "description": (
            ""
            

            "Edit a file by replacing exact text replacement. replaces the items from old_str with the ones in new_str. Handles all edit types:\n"
            "- Replace: old_str is what changes, new_str is the replacement\n"
            "- Insert: include the anchor line in old_str, repeat it in new_str with new content added after\n"
            "- Delete: set new_str to empty string\n\n"
            "old_str items MUST be unique in the file. "
            "If two or more close-by edits are to be applied, merge them into one edit with a shared anchor line."
            "Don't include large unchanged sections of the file in old_str for very distant edits."
            "Finally, if multiple "
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to edit, relative to the working directory. (required)"
                },
                "old_str": {
                    "type": "array",
                    "description": "The exact string to be replaced. Must appear exactly once and must not overlp with other items in old_str.",
                    "items": {"type": "string"}
                },
                "new_str": {
                    "type": "array",
                    "description": "The string to replace old_str with. To insert after a line, repeat that line here and add new content below it. To delete, pass an empty string.",
                    "items": {"type": "string"}
                }
            },
            "required": ["path", "old_str", "new_str"]
        }
    }
})
def patch_file(path: str, old_str: list, new_str: list):
    """
    Patch a file by replacing old_str with new_str. Handles all edit types:
        - Replace: old_str is what changes, new_str is the replacement
        - Insert: include the anchor line in old_str, repeat it in new_str with new content added after
        - Delete: set new_str to empty string
    """
    if is_dispatch_ignored(path):
        return {"error": f"Blocked: {path} matches .dispatchignore"}
    
    p = Path(path)
    try:
        content = p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"error": f"An error occurred while reading the file: {str(e)}"}

    if not any(old in content for old in old_str):
        return {"error": "old_str not found in file"}
    if sum(content.count(old) for old in old_str) > len(old_str):
        return {"error": "old_str matches multiple locations, be more specific"}
    
    new_content = content
    for old, new in zip(old_str, new_str):
        new_content = new_content.replace(old, new, 1)

    try:
        diff = difflib.unified_diff(
            content.splitlines(), new_content.splitlines(),
            lineterm="", fromfile=path, tofile=path
        )
        console.print(Syntax("\n".join(diff), "diff"))
        if not Confirm.ask(f"Apply patch to {path}?"):
            return {"error": "aborted"}
        
        p.write_text(new_content, encoding="utf-8")
        return {"patched": path}
    except PermissionError:
        return {"error": f"Permission denied: Cannot write to '{path}'."}
    except Exception as e:
        return {"error": f"An unexpected error occurred while writing the patched file: {str(e)}"}