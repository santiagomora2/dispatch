from prompt_toolkit.completion import Completer, Completion
from agent.cmd import COMMANDS
from prompt_toolkit.formatted_text import FormattedText

class SlashCompleter(Completer):

    def get_completions(self, document, complete_event):
        """
        Get "/command" completion suggestions for the current document.
            - If user is typing a command (starts with "/"), suggest matching commands from COMMANDS.
            - If user has typed a full command and is now typing arguments, 
                and if that command has an arg_completer, use it to suggest argument completions.}
        """        
        text = document.text_before_cursor

        if not text.startswith("/"):
            return

        parts = text[1:].split(maxsplit=1)

        # still typing the command name
        if len(parts) <= 1 and " " not in text:
            word = parts[0] if parts else ""
            for name, entry in COMMANDS.items():
                if name.startswith(word):
                    usage = f" {entry['usage']}" if entry["usage"] else ""
                    display = FormattedText([("bold", f"/{name}"), ("class:ansigray", usage)])
                    display_meta = FormattedText([("class:ansigray", entry["description"])])
                    yield Completion(name, start_position=-len(word),
                                     display=display, display_meta=display_meta)
            return

        # typing the argument — check if command has arg completions
        cmd_name = parts[0]
        arg_so_far = parts[1] if len(parts) > 1 else ""
        entry = COMMANDS.get(cmd_name)
        if not entry or not entry.get("arg_completer"):
            return

        for value in entry["arg_completer"]():
            if value.startswith(arg_so_far):
                yield Completion(value, start_position=-len(arg_so_far))