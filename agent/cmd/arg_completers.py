### Argument completer functions for commands ###

import ollama

def get_available_models():
    """
    Get available models from ollama, return empty list if there's an error.
    """
    try:
        return [m.model for m in ollama.list().models]
    except Exception:
        return []
    
from agent.tools import TOOLS, LAZY

def get_tool_names():
    return list(TOOLS.keys()) + list(LAZY.keys())