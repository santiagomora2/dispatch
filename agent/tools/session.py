import json
import ollama
from agent.paths import SESSION_FILE


# No tool decorator here since this is a cmd, not a tool.
# The agent doesn't decide when to compact, but the user can trigger it.
# If config[context_limit] is at 80%, auto_compact will be handled in main agent.py loop.
def compact_conversation(messages, model):
    """
    Compacts the conversation history by summarizing it into a shorter form.
    This is useful for keeping the conversation history manageable while retaining context.
    The original messages are replaced with a system message containing the summary.
    """
    history_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}"
        for m in messages
        if m["role"] != "system"
    )

    response = ollama.chat(model=model, messages=[{
        "role": "user",
        "content": (
            "Summarize this conversation as a dense agent briefing. Include:\n"
            "- What was being worked on\n"
            "- Key decisions and outcomes\n"
            "- Files created or modified and how\n"
            "- Open tasks or next steps\n"
            "- Any facts worth remembering long-term\n\n"
            f"CONVERSATION:\n{history_text}"
        )
    }])

    summary = response.message.content
    SESSION_FILE.write_text(json.dumps({"summary": summary}, indent=2))
    return summary
