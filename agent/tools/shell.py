from agent.tools import tool
from agent.paths import INVOCATION_DIR
from rich.console import Console
from rich.prompt import Confirm
import subprocess
import threading

console = Console()


def stream_shell_command(cmd: str, timeout: int = 300):
    # Show the command and ask for confirmation before running anything
    console.print(f"[bold cyan]➜ {INVOCATION_DIR.name}[/bold cyan] $ {cmd}")
    console.print()

    if not Confirm.ask(f"Run: {cmd}?"):
        return {"error": "Command execution cancelled by user"}

    try:
        # Popen lets us stream output line-by-line as the process runs.
        # stdout=PIPE captures output, stderr=STDOUT merges stderr into stdout
        # so we only need to read one stream. bufsize=1 enables line buffering.
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=INVOCATION_DIR  # run in the directory dispatch was invoked from
        )

        output_buffer = ""

        # Kill the process if it exceeds the timeout.
        # threading.Timer fires process.kill() after `timeout` seconds
        # unless we cancel it first (which we do on clean exit).
        timer = threading.Timer(timeout, process.kill)
        timed_out = False

        try:
            timer.start()
            for line in process.stdout:
                console.print(line, end="")
                output_buffer += line
        except Exception:
            pass
        finally:
            # If timer already fired, process was killed — note it
            timed_out = not timer.cancel()

        process.wait()

        if timed_out:
            return {"error": f"Command timed out after {timeout}s", "output": output_buffer}

        # Return everything to the agent — let it interpret success/failure
        # from returncode and output rather than us guessing from strings
        return {
            "command": cmd,
            "returncode": process.returncode,
            "output": output_buffer,
        }

    except subprocess.SubprocessError as e:
        return {"error": f"Subprocess error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@tool({
    "type": "function",
    "function": {
        "name": "run_shell",
        "description": (
            "Run a shell command with human confirmation, streaming output line by line.\n\n"
            "Always confirm with the user before running. Use for:\n"
            "- Running scripts: 'python script.py'\n"
            "- Installing packages: 'pip install requests'\n"
            "- Git operations: 'git status', 'git diff'\n"
            "- Searching: 'grep -r \"TODO\" .'\n"
            "- Any system command that needs to run in the project directory"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute."
                },
                "timeout": {
                    "type": "integer",
                    "description": "Max execution time in seconds. Default 300. Increase for long installs or builds."
                }
            },
            "required": ["command"]
        }
    }
})
def run_shell(command: str, timeout: int = 300):
    return stream_shell_command(command, timeout)