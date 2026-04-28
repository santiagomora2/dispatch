from agent.paths import MEMORY_FILE

def build_system_prompt():
    memory = MEMORY_FILE.read_text()
    return f"""You are Dispatch, a local agent assistant.

## Your Memory
{memory}

Use tools when needed. Always return errors as tool results, never crash.
For persistent facts, preferences, or completed tasks — update memory.
Prioritize tool use when needed."""