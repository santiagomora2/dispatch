import json
from agent.tools import tool
from agent.paths import MEMORY_FILE

def load_memory():
    return json.loads(MEMORY_FILE.read_text())

def save_memory(data):
    MEMORY_FILE.write_text(json.dumps(data, indent=2))

@tool({
    "type": "function",
    "function": {
        "name": "read_memory",
        "description": "Read the agent's persistent memory, including user facts, task history, and scratch space.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    }
})
def read_memory():
    """
    Return the agent's persistent memory, including user facts, task history, and scratch space.
    memory.json schema:
        {
        "facts": [],
        "task_history": [],
        "scratch": {}
        }
    """
    try:
        return load_memory()
    except Exception as e:
        return {"error": f"An error occurred while reading memory: {str(e)}"}

@tool({
    "type": "function",
    "function": {
        "name": "add_fact",
        "description": "Append a user-facing fact to memory. Use for preferences, context, or anything the user would want remembered across sessions. Example: 'user prefers snake_case', 'project root is ~/code/myapp'.",
        "parameters": {
            "type": "object",
            "properties": {
                "fact": {"type": "string", "description": "The fact to remember."}
            },
            "required": ["fact"]
        }
    }
})
def add_fact(fact: str):
    """
    Add a user-facing fact to memory. 
    Use for preferences, context, or anything the user would want remembered across sessions. 
    Example facts: 'user prefers snake_case', 'project root is ~/code/myapp'.
    """
    try:
        data = load_memory()
        data.setdefault("facts", []).append(fact)
        save_memory(data)
        return {"added_fact": fact}
    except Exception as e:
        return {"error": f"An error occurred while adding a fact: {str(e)}"}

@tool({
    "type": "function",
    "function": {
        "name": "forget_fact",
        "description": "Remove a fact from memory by its exact text.",
        "parameters": {
            "type": "object",
            "properties": {
                "fact": {"type": "string", "description": "The exact fact string to remove."}
            },
            "required": ["fact"]
        }
    }
})
def forget_fact(fact: str):
    """
    Delete a fact from memory by its exact text.
    """
    try:
        data = load_memory()
        facts = data.get("facts", [])
        if fact not in facts:
            return {"error": f"Fact not found: '{fact}'"}
        facts.remove(fact)
        data["facts"] = facts
        save_memory(data)
        return {"forgotten_fact": fact}
    except Exception as e:
        return {"error": f"An error occurred while forgetting a fact: {str(e)}"}

@tool({
    "type": "function",
    "function": {
        "name": "log_task",
        "description": "Append an entry to task history. Use after completing a meaningful task to record what was done and the outcome.",
        "parameters": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Brief description of the task."},
                "outcome": {"type": "string", "description": "What happened or was produced."}
            },
            "required": ["task", "outcome"]
        }
    }
})
def log_task(task: str, outcome: str):
    """
    Log a completed task to memory with a brief description and its outcome.
    """
    try:
        data = load_memory()
        data.setdefault("task_history", []).append({"task": task, "outcome": outcome})
        save_memory(data)
        return {"logged": task}
    except Exception as e:
        return {"error": f"An error occurred while logging the task: {str(e)}"}

@tool({
    "type": "function",
    "function": {
        "name": "update_scratch",
        "description": "Store or update a value in the scratch space. Use for intermediate state, counters, or working notes that don't belong in facts.",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Scratch key."},
                "value": {"description": "Any JSON-serializable value."}
            },
            "required": ["key", "value"]
        }
    }
})
def update_scratch(key: str, value):
    """
    Update a key-value pair in the scratch space.
    Use for intermediate state, counters, or working notes that don't belong in facts.
    """
    try:
        data = load_memory()
        data.setdefault("scratch", {})[key] = value
        save_memory(data)
        return {"scratch_updated": key}
    except Exception as e:
        return {"error": f"An error occurred while updating scratch: {str(e)}"}