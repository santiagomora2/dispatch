from agent.tools import tool
from agent.paths import MEMORY_FILE
from rich.console import Console
from rich.prompt import Confirm

console = Console()

@tool({
    "type": "function",
    "function": {
        "name": "update_memory",
        "description": (
            "Update a section of the agent's persistent memory markdown file. "
            "Sections: 'Top of Mind', 'Projects', 'Facts', 'Task History'. "
            "Content is appended under the matching section header. "
            "Use for anything worth remembering across sessions: current tasks, "
            "user preferences, project context, completed work."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "enum": ["Top of Mind", "Projects", "Facts", "Task History"],
                    "description": "Which section to update."
                },
                "content": {
                    "type": "string",
                    "description": "Markdown content to append under the section. Use bullet points for facts/tasks."
                },
                "replace": {
                    "type": "boolean",
                    "description": "If true, replace the section content instead of appending. Use for Top of Mind and Projects which should reflect current state, not accumulate.",
                    "default": False
                }
            },
            "required": ["section", "content"]
        }
    }
})
def update_memory(section: str, content: str, replace: bool = False):
    text = MEMORY_FILE.read_text()
    header = f"## {section}"

    if header not in text:
        return {"error": f"Section '{section}' not found in memory.md"}

    # Find section boundaries
    start = text.index(header)
    # Next section starts at next "## " after current header
    next_section = text.find("\n## ", start + 1)
    end = next_section if next_section != -1 else len(text)

    section_text = text[start:end]

    if replace:
        new_section = f"{header}\n{content.strip()}\n"
    else:
        # Strip trailing comment/whitespace, append new content
        existing = section_text.strip()
        new_section = f"{existing}\n{content.strip()}\n"

    new_text = text[:start] + new_section + ("\n" + text[end:].lstrip() if next_section != -1 else "")
    MEMORY_FILE.write_text(new_text)
    return {"updated": section}