import json
import ollama
from rich.console import Console
from rich.markdown import Markdown
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML

from agent.paths import CONFIG_FILE, MEMORY_FILE
from agent.tools import dispatch, get_schemas
import agent.cmd  # noqa — registers all commands
from agent.completer import SlashCompleter
from agent.fancy_banner import print_banner, say_bye
from agent.cmd.session import do_compact

console = Console()

def load_config():
    """
    Read config file
    """
    return json.loads(CONFIG_FILE.read_text())

def build_system_prompt():
    """
    Builds the system prompt:
    - Loads memory from "memory.json file"
    - ...
    - Glues it all with the system prompt text.
    """
    memory = json.loads(MEMORY_FILE.read_text())
    return f"""You are Dispatch, a local agent assistant.
Today's working memory: {json.dumps(memory)}
Use tools when needed. Always return errors as tool results, never crash."""

def estimate_tokens(messages):
    """
    Rudimentary token estimation based on message content length.
    """
    return sum(len(str(m.get("content", ""))) for m in messages) // 4

def run():
    """
    Main function: runs the agent loop. 

    - Initializes the conversation with system prompt and memory, gets model from config.
    - Enters main loop:
        - Gets user input with prompt_toolkit, supports "/" command auto-completion.
        - Streams assistant response with ollama, supports tool calls.
        - Executes tool calls, appends results to conversation, re-enters loop so agent sees results.
        - Continues until user exits with Ctrl-C or Ctrl-D.
    """
    # Initialize conversation with system prompt and memory, get model from config
    config = load_config()
    system_prompt = build_system_prompt()
    model = config["model"]
    messages = [{"role": "system", "content": system_prompt}]
    pending_tool_response = False

    # ctx: a mutable context object passed to commands. 
    # Can be changes by commands to affect the agent's state, e.g. changing the model or system prompt on the fly.
    ctx = {
    "messages": messages,
    "model": config["model"],
    "config": config,
    "system_prompt": system_prompt  # ← add this
    }
    session = PromptSession(completer=SlashCompleter())

    print_banner(model, config.get("version", "0.1.0"))

    # Main loop
    while True:
        # If waiting for tool results, skip user input; re-run the agent with updated conversation
        if not pending_tool_response:
            try:
                user_input = session.prompt(HTML("<ansibrightcyan><b>you></b></ansibrightcyan> ")).strip()
            except (KeyboardInterrupt, EOFError):
                say_bye()
                break

            if not user_input:
                continue

            messages.append({"role": "user", "content": user_input})
        
            # Handle slash commands immediately, they don't go through the model
            if user_input.startswith("/"):
                agent.cmd.dispatch_command(user_input, ctx)
                model = ctx["model"]  # reflect /model changes
                continue

        pending_tool_response = False

        # Check context length and compact if needed before calling the model
        if estimate_tokens(messages) > ctx["config"]["context_limit"] * 0.8:
            do_compact(ctx, messages)

        # Stream text, accumulate tool calls
        stream = ollama.chat(
                model=model,
                messages=messages,
                tools=get_schemas(),
                stream=True,
            )

        full_content = ""
        tool_calls = []
        assistant_message = None

        # Stream assistant response, accumulate content and tool calls
        console.print("[bold green]dispatch>[/bold green] ", end="")
        for chunk in stream:
            msg = chunk.message
            if msg.content:
                console.print(msg.content, end="", highlight=False)
                full_content += msg.content
            if msg.tool_calls:
                tool_calls.extend(msg.tool_calls)
            assistant_message = msg.content  # last chunk has the full message

        console.print()  # newline after stream

        # Append assistant turn
        messages.append({"role": "assistant", "content": full_content,
                         "tool_calls": tool_calls if tool_calls else None})

        # Execute tool calls if any
        if tool_calls:
            for call in tool_calls:
                name = call.function.name
                args = call.function.arguments
                console.print(f"[dim]→ tool: {name}({args})[/dim]")
                result = dispatch(name, args)
                messages.append({
                    "role": "tool",
                    "content": json.dumps(result),
                    "name": name
                })

            pending_tool_response = True

            # Re-enter loop so agent sees tool results
            continue