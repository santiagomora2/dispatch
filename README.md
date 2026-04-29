
```
██████╗ ██╗███████╗██████╗  █████╗ ████████╗ ██████╗██╗  ██╗
██╔══██╗██║██╔════╝██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██║  ██║
██║  ██║██║███████╗██████╔╝███████║   ██║   ██║     ███████║
██║  ██║██║╚════██║██╔═══╝ ██╔══██║   ██║   ██║     ██╔══██║
██████╔╝██║███████║██║     ██║  ██║   ██║   ╚██████╗██║  ██║
╚═════╝ ╚═╝╚══════╝╚═╝     ╚═╝  ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝
```

A local AI agent harness written in python, built on ollama; with tool calling, streaming, and a persistent memory system.

> Dispatch does not intend to compete with Claude Code, DeepAgents, OpenCode or other famous CLIs.

> It is a tool I built for the love of the game, and is meant to be an easy-to-understand, easily-to-modify, light-weight, local CLI agent that you can study to understand how popular agentic systems and famous Agentic AI CLIs work. 

---

## Index

- [Index](#index) - This section
- [Installation](#installation) - Setup and prerequisites
- [Project Structure](#project-structure) - Directory tree overview
- [How It Works](#how-it-works) - Boot and main loop explained
- [Tool Registry](#tool-registry) - Available tools
- [Slash Command Registry](#slash-command-registry) - All slash commands
- [What's Next](#whats-next) - Planned features
- [How to build on top of Dispatch](#how-to-build-on-top-of-dispatch) - Adding custom tools/commands
- [License](#license)

---

## Installation

> Quick note: I developed dispatch on Mac so it should work for MacOs and Linux. Windows is untested, but it should also work.

### Prerequisites

**1. Install `uv`**
```bash
# mac/linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# windows (powershell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**2. Install and start Ollama**

Download from [ollama.com](https://ollama.com) or via Homebrew:
```bash
# mac
brew install ollama

# linux
curl -fsSL https://ollama.com/install.sh | sh

# windows
# download installer from https://ollama.com/download
```

Start the Ollama server:
```bash
ollama serve
```

**3. Pull a model**

Dispatch works with any Ollama model that supports tool calling. Recommended:
```bash
ollama pull gemma4:e4b       # strong reasoning
ollama pull qwen3.5:9b       # fast, good tool calling
```

### Setup

Clone the repo and install as a global tool:
```bash
git clone https://github.com/santiagomora2/dispatch.git
cd dispatch
uv tool install --editable .
```

Update `config.json` to match the model you pulled:
```json
{
  "model": "gemma4:e4b",
  "context_limit": 6000,
  "mode": "auto",
  "version": "0.1.0"
}
```

Then invoke from any directory:
```bash
dispatch
```

Dispatch will operate on the directory you invoke it from, while keeping its own memory and config in the project root.

---

## Project Structure

```
dispatch/
├── agent/
│   ├── cmd/
│   │   ├── __init__.py     # registry + dispatch
│   │   ├── arg_completers.py        # contains arg_completer functions for commands
│   │   ├── files.py        # file commands (/tree, /ls etc.)
│   │   ├── memory.py.      # memory commands (/note, /forget, etc.)
│   │   ├── plan.py         # plan command
│   │   └── session.py      # session commands (/clear, /compact, /model, etc.)
│   ├── tools/
│   │   ├── __init__.py     # registry + dispatch + get_schemas
│   │   ├── files.py        # file tools (read_file, patch_file, tree, etc.)
│   │   ├── memory.py       # memory tools (add_fact, forget_fact, etc.)
│   │   ├── session.py      # compact conversation (not callable, handled in main loop)
│   │   ├── shell.py.       # shell tools (run_shell)
│   │   └── web.py          # web search tools (web_search, fetch_url)
│   ├── plans/              # directory where agent's plans and statuses are logged
│   ├── __init__.py
│   ├── agent.py            # main loop
│   ├── completer.py        # slash commands auto-completer
│   ├── fancy_banner.py     # fancy welcome banner, ways to goodbye 
│   ├── main.py             # CLI entrypoint (typer)
│   ├── paths.py            # ROOT-anchored file
│   └── system_prompt.py    # system prompt
├── README.md               
├── config.json             # model, context_limit, mode
├── memory.md               # persistent agent memory
├── pyproject.toml          # entry point: `dispatch` command
├── session.json            # last compact summary
└── uv.lock
```

---

## How It Works

### Boot

1. `dispatch` is invoked from anywhere in the terminal
2. `main.py` calls `run()` in `agent.py`
3. `agent.py` loads `config.json` (model, context limit, mode)
4. `memory.md` is read and injected into the system prompt
5. The message history is initialized with the system prompt
6. The main loop starts

### Main Loop

```
START
│
├── pending_tool_response = False?
│   YES ──> get user input
│         ├── "/" ──> run slash command ──> back to START
│         ├── empty ──> back to START
│         └── normal ──> append to messages
│
├── check token estimate > 80% limit?
│   YES ──> compact conversation (summarize history) ──> continue
│
├── call ollama.chat(stream=True, tools=get_schemas())
│   └── stream chunks to terminal as they arrive
│       ├── text content ──> print immediately
│       └── tool_calls ──> accumulate, execute after stream ends
│
├── tool_calls found?
│   YES ──> for each call:
│         ├── print [dim] tool: name(args)
│         ├── dispatch(name, args)
│         ├── append result to messages (role=tool)
│         └── set pending_tool_response = True ──> back to START (skip user input)
│
│   NO  ──> response already streamed
             wait for next user input ──> back to START
```

### Tool Registry

Every tool is a decorated Python function in `tools/`:

```python
@tool(schema_dict, lazy=False)
def read_file(path: str):
    ...
```

* The `@tool` decorator registers the function and its JSON schema into `TOOLS = {}` or into `LAZY{}` if `lazy=True`(tool disabled). 
* The modules are imported at the bottom of `tools/__init__.py` so decorators run on startup. `get_schemas()` returns all schemas to pass to Ollama. 
* `dispatch(name, args)` looks up and calls the function, always returning `{"error": "..."}` on failure instead of raising.

### Slash Command Registry

Every slash command is a decorated Python function in `cmd/`:

```python
@command("note", description="Append a fact to memory", usage="")
def cmd_note(arg, ctx):
    ...
```

* The `@command` decorator registers the function into `COMMANDS = {}` with its name, description, and usage hint. 
* Modules are imported in `cmd/__init__.py` so decorators run on startup.
 * `dispatch_command(raw_input, ctx)` parses the command name and argument, looks up the function, and calls it.
* `ctx` is a dict holding live references to `messages`, `model`, `config`, and `system_prompt` so commands can mutate agent state directly. 
* The `SlashCompleter` reads from `COMMANDS` at runtime so any new command automatically appears in the `/` menu.

> Flow note: if a command and a tool perform the same function, the command file should import from the corresponding tool file (Example: `/note` uses `save_memory()` tool).

### Path Anchoring

* `paths.py` uses `__file__` to resolve all Dispatch-internal files (config, memory, session) to the project root; regardless of where you invoke `dispatch` from.
* File operations the agent performs use `os.getcwd()` captured at startup as the working directory.

---

## Current Tools

| Tool | File | What it does |
|---|---|---|
| `read_file` | `tools/files.py` | Reads a file, returns content with line numbers |
| `create_file` | `tools/files.py` | Creates a file with an initial skeleton |
| `patch_file` | `tools/files.py` | Replaces, inserts, or deletes content via `old_str/new_str` |
| `append_file` | `tools/files.py` | Appends content to end of existing file |
| `find_pattern` | `tools/files.py` | Glob search for files matching a pattern |
| `list_dir` | `tools/files.py` | Lists files and dirs at a path |
| `tree` | `tools/files.py` | Prints a directory tree up to a given depth |
| `update_memory` | `tools/memory.py` | Update a section of the agent's persistent memory markdown file|
| `web_search` | `tools/web.py` | Searches the web for relevant URLs |
| `fetch_url` | `tools/web.py` | Fetches the content from a given URL, parses it as Markdown (`jina` + `tralifatura` fallback) |
| `run_shell` | `tools/shell.py` | Run a shell command with human confirmation, streaming output line by line |

## Current Slash Commands

| Command | Usage | What it does |
|---|---|---|
| `/memory` | `/memory` | Print current memory.md |
| `/note` | `/note <text>` | Append a fact to memory directly |
| `/forget` | `/forget <section>` | Clear a memory section |
| `/clear` | `/clear` | Reset messages, keep memory |
| `/reset` | `/reset` | Reset messages and memory |
| `/compact` | `/compact` | Summarize session and replace history |
| `/compact_tools` | `/compact_tools` | Compact tool results into a summary |
| `/tools` | `/tools [enable/disable] <tool>` | List, enable, or disable tools |
| `/model` | `/model [name]` | Show or switch the active Ollama model |
| `/tree` | `/tree <path> <depth>` | Print directory tree |
| `/ls` | `/ls <path>` | List directory contents |
| `/plan` | `/plan <task>` | Generate and execute a step-by-step plan |
| `/help` | `/help` | List all available commands |
| `/exit` | `/exit` | Quit Dispatch |

---

## What's Next

- `/mode` - toggle careful/auto HITL aggressiveness
- `/retry` - resend last user message
- `/history` - print condensed message log
- `/plan` - prevent context window limit, optimize token usage

> - Maybe in the future MCP servers and custom skills idk

---

## How to build on top of Dispatch

I know it may seem complicated but bear with me, customizing it is actually simple.

### Add a tool

1. **Create your tool** as a python function, return a `dict` even if the function doesn't return anything. Make sure to wrap it in a `try, except` block that returns an error `dict`.

```python
def read_file(path: str):
    try:
        with open(path) as f:
            lines = f.readlines()
        numbered = "".join(f"{i+1}: {l}" for i, l in enumerate(lines))
        return {"content": numbered}
        # or if the function shouldn't return anything
        return {"read_file": path}
    except Exception as e:
        return {"error": f"An  error occurred while reading the file: {str(e)}"}
    
```



2. **Add the `@tool` decorator** with an adequate description. 
    - The **description**: think which of these are necessary to tell the agent: what the tool does, when to use it, which tools it may use before/after, examples of usage, etc.
    - The **parameters** the function recieves: their type and description; which ones are required
    - Whether or not the tool is disabled on startup (`lazy`)

```python
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
}, lazy = False)
def read_file(path: str):
    try:
        with open(path) as f:
            lines = f.readlines()
        numbered = "".join(f"{i+1}: {l}" for i, l in enumerate(lines))
        return {"content": numbered}
    except Exception as e:
        return {"error": f"An  error occurred while reading the file: {str(e)}"}
    
```

It seems like a lot but is really quite simple.

3. If it was in a new file, add the import to `/agent/tools/__init__.py`

```python
from agent.tools import files, memory, your_new_file #noqa
```

#### HITL gated

4. If you need a human-in-the-loop confirmation, add the following lines *before* executing the function that needs to be confirmed in the tool and returning.

```python
from rich.prompt import Confirm # this,

@tool({...})
def read_file(path: str):
    try:
        if not Confirm.ask(f"Read file {path}?"): # this
          return {"error": "aborted"} # and this
        with open(path) as f:
            lines = f.readlines()
        numbered = "".join(f"{i+1}: {l}" for i, l in enumerate(lines))
        return {"content": numbered}
    except Exception as e:
        return {"error": f"An  error occurred while reading the file: {str(e)}"}


```

### Add a slash command

Works very similar to the tool creation.

1. **Create your command** as a python function, only now you may execute some function and then print the result or that the function was executed correctly or completed.

> Note: if a command and a tool perform the same function, just import the function from the corresponding tool file (Example: `/read_file <path>` uses the `read_file(path)` tool we just defined).

```python
from agent.tools.files import read_file
from rich.console import Console
console = Console()

def cmd_read_file(path: str):
    content = read_file(path).get("content")
    console.print(content)
```

2. **Add the `@command` decorator** with an adequate description. 
    - The **description** will be seen by the user when using `/help` or the auto-completer suggests `/` commands.
    - The **usage** (optional) is also seen by the user and is basically the argument (or arguments) of your function.
    - **arg_completer** (also optional) is a function that will give the user the options they can choose as their argument(s).

```python
@command("read", description="Print a file's content", usage="<path>",
         arg_completer=None)
def cmd_read_file(path: str):
    content = read_file(path).get("content")
    console.print(content)
```

3. If it was in a new file, add the import to `/agent/cmd/__init__.py`

```python
from agent.cmd import memory, files, your_new_file #noqa
```

This was maybe a bad example because this command isn't actually implemented (why print it in console if you can just open the file) but you get the gist.

#### Arg completer

It is, again, a function that will give the user the options they can choose as their argument(s). For example, the models they can choose when using `/model`:

```python
import ollama

def get_available_models():
    try:
        return [m.model for m in ollama.list().models]
    except Exception:
        return []
  
@command("model",
         description="Switch the active Ollama model",
         usage="<model>",
         arg_completer=get_available_models)
def cmd_model(arg, ctx):
    ctx["model"] = arg
    console.print(f"[green]Switched to: {arg}[/green]")
# Oversimplified version for illustrative purposes
# check agent/cmd/session.py for the actual implementation
```

Prefer putting it into `arg_completers.py` unless definable as a `lambda`function inside the decorator.

### Everything else

All of the other stuff like welcome banner in the `fancy_banner.py` file or the main loop in `agent.py` can also be modified to make your own version of dispatch and learn how agentic AI and tools work.

### My favorite feature? (personal note)

I really enjoyed implementing `/plan`. 

Because of the natural constraints of running models locally on a computer without that much memory capacity, Mixture of Experts (MoE) models are an attractive option due to their speed and lower memory usage with only some parameters active at inference.

A possible problem when trying to implement a big change suddenly is prompt trajectory: the early tokens heavily influence which experts activate, and a poorly structured initial prompt locks you into a suboptimal expert path for the entire generation.

Hence `/plan`, which breaks the task into a guided reasoning sequence before any action is taken:

    1. Understand & Decompose: Restate the task and break it into discrete subtasks.
    2. Sequence & Assess Risks: Order the subtasks and note potential risks.
    3. Finalize Plan: Output a structured markdown plan with steps and placeholders for decisions/artifacts.
    4. Execute Sequentially: For each step, run it in isolation, allowing tool calls, and update the plan file with progress and artifacts.

I've found it works pretty well with both dense and MoE models. 

The reason for the plan file is not filling up KV cache too quickly, but still having a shared memory between the sub-agents which implement the task (and also have logs for implemented plans); and for MoE models, also having each step activate the appropriate experts for the task.

---

### License

MIT License. Use, modify, teach, learn. It's all yours.

---

Built with ❤️, as always.
