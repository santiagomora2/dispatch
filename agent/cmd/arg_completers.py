### Argument completer functions for commands ###

from agent.providers import list_models

def get_available_models():
    """
    Get available models from active provider, return empty list if there's an error.
    """
    try:
        return list_models()
    except Exception:
        return []
    
from agent.tools import TOOLS, LAZY

def get_tool_names():
    return list(TOOLS.keys()) + list(LAZY.keys())
