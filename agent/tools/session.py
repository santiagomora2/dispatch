# agent/tools/session.py
import json
import requests
from agent.paths import SESSION_FILE

# Configuración para conectar con tu servidor llama.cpp local
API_URL = "http://127.0.0.1:8080/v1"
MODEL_NAME = "Qwen3-1.7B"  # Nombre dummy, llama.cpp usa el modelo cargado en el .bat

def _call_local_llm(prompt_content: str) -> str:
    """Envía una petición de chat al servidor local (llama-server.exe)"""
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt_content}],
        "temperature": 0.2,  # Temperatura baja para resúmenes objetivos y concisos
        "max_tokens": 1024
    }
    try:
        response = requests.post(f"{API_URL}/chat/completions", json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[Error compactando: {str(e)}]"

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

    prompt = (
        "Summarize this conversation as a dense agent briefing. Include:\n"
        "- What was being worked on\n"
        "- Key decisions and outcomes\n"
        "- Files created or modified and how\n"
        "- Open tasks or next steps\n"
        "- Any facts worth remembering long-term\n"
        "If there's a user prompt at the end, proceed with the summarization and append the user query at the end.\n\n"
        f"CONVERSATION:\n{history_text}"
    )

    summary = _call_local_llm(prompt)
    SESSION_FILE.write_text(json.dumps({"summary": summary}, indent=2))
    return summary

def compact_tool_results(messages, model):
    """
    Compacts tool result messages by summarizing them into a shorter form.
    This is useful for keeping the conversation history manageable while retaining important tool outputs.
    The original tool messages are replaced with one summary message.
    """
    # pull out tool result messages
    tool_msgs = [m for m in messages if m["role"] == "tool"]
    if not tool_msgs:
        return messages
    
    combined = "\n".join(m["content"] for m in tool_msgs)
    prompt = f"""Summarize these tool results concisely, keeping only what's useful for the task. 
    Specify whether each tool call resulted in a positive, negative, or neutral outcome:\n{combined}"""
    
    summary = _call_local_llm(prompt)

    # replace all tool messages with one summary
    new_messages = [m for m in messages if m["role"] != "tool"]
    new_messages.append({
        "role": "tool",
        "content": f"[TOOL RESULTS SUMMARY]\n{summary}",
        "name": "compact"
    })
    return new_messages