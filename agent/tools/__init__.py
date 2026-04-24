TOOLS = {}
LAZY = {}

def tool(schema, lazy=False):
    def decorator(fn):
        entry = (fn, schema)
        if lazy:
            LAZY[fn.__name__] = entry
        else:
            TOOLS[fn.__name__] = entry
        return fn
    return decorator

def dispatch(name, arguments):
    if name not in TOOLS:
        return {"error": f"Unknown tool: {name}"}
    fn, _ = TOOLS[name]
    try:
        return fn(**arguments)
    except Exception as e:
        return {"error": str(e)}

def get_schemas():
    return [schema for _, schema in TOOLS.values()]

def enable_tool(name):
    if name in LAZY and name not in TOOLS:
        TOOLS[name] = LAZY.pop(name)
        return True
    return False

def disable_tool(name):
    if name in TOOLS:
        LAZY[name] = TOOLS.pop(name)
        return True
    return False

# imports — mark lazy tools
from agent.tools import files, memory  # noqa
from agent.tools import web, shell     # noqa  (mark these lazy=True in their decorators)