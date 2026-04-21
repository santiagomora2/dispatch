TOOLS = {}  # name → (fn, schema)

def tool(schema):
    """
    Decorator: Adds tools to the TOOLS dictionary
    """
    def decorator(fn):
        TOOLS[fn.__name__] = (fn, schema)
        return fn
    return decorator

def dispatch(name, arguments):
    """
    Dispatch a tool use, verify it exists
    """
    if name not in TOOLS:
        return {"error": f"Unknown tool: {name}"}
    fn, _ = TOOLS[name]
    try:
        return fn(**arguments)
    except Exception as e:
        return {"error": str(e)}

def get_schemas():
    """
    Get the schemas of the tools
    """
    return [schema for _, schema in TOOLS.values()]

# From here on import all tools for the agent, they'll be added to TOOLS automatically
from agent.tools import files, memory #noqa