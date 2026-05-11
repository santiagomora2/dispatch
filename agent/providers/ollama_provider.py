import json

import ollama


def chat(model: str, messages: list[dict], tools=None, stream: bool = False):
    payload = _to_ollama_messages(messages)
    response = ollama.chat(model=model, messages=payload, tools=tools, stream=stream)
    if stream:
        return _stream(response)
    return _normalize_response(response)


def list_models():
    return [m.model for m in ollama.list().models]


def _stream(stream_response):
    for chunk in stream_response:
        msg = chunk.message if hasattr(chunk, "message") else chunk.get("message", {})
        yield {
            "message": {
                "content": _msg_content(msg),
                "tool_calls": _normalize_tool_calls(_msg_tool_calls(msg)),
            }
        }


def _normalize_response(response):
    msg = response.message if hasattr(response, "message") else response.get("message", {})
    return {
        "message": {
            "content": _msg_content(msg),
            "tool_calls": _normalize_tool_calls(_msg_tool_calls(msg)),
        }
    }


def _to_ollama_messages(messages: list[dict]):
    converted = []
    for m in messages:
        item = {"role": m.get("role"), "content": m.get("content", "")}
        if m.get("role") == "assistant" and m.get("tool_calls"):
            item["tool_calls"] = m["tool_calls"]
        if m.get("role") == "tool" and m.get("name"):
            item["name"] = m["name"]
        converted.append(item)
    return converted


def _msg_content(msg):
    if isinstance(msg, dict):
        return msg.get("content") or ""
    return getattr(msg, "content", "") or ""


def _msg_tool_calls(msg):
    if isinstance(msg, dict):
        return msg.get("tool_calls")
    return getattr(msg, "tool_calls", None)


def _normalize_tool_calls(raw_tool_calls):
    if not raw_tool_calls:
        return []

    normalized = []
    for call in raw_tool_calls:
        if isinstance(call, dict):
            fn = call.get("function", {})
            name = fn.get("name")
            arguments = fn.get("arguments", {})
            call_id = call.get("id")
        else:
            fn = getattr(call, "function", None)
            name = getattr(fn, "name", None) if fn else None
            arguments = getattr(fn, "arguments", {}) if fn else {}
            call_id = getattr(call, "id", None)

        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}

        normalized.append({
            "id": call_id,
            "type": "function",
            "function": {"name": name, "arguments": arguments if isinstance(arguments, dict) else {}},
        })
    return normalized
