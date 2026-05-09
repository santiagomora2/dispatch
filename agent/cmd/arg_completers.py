### Argument completer functions for commands ###

import json
from agent.paths import CONFIG_FILE
from agent.tools import TOOLS, LAZY

def get_available_models():
    """
    Returns the model currently configured in the local config.
    We don't query Ollama; we just read what's in config.json.
    """
    try:
        config = json.loads(CONFIG_FILE.read_text())
        return [config.get("model", "Qwen3-1.7B")]
    except Exception:
        return ["Qwen3-1.7B"]
    
def get_tool_names():
    """
    Returns the list of tool names for auto-completion.
    """
    try:
        return list(TOOLS.keys()) + list(LAZY.keys())
    except Exception:
        return []