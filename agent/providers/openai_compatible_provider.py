import json
import os

import requests


def chat(model: str, messages: list[dict], tools=None, stream: bool = False, config: dict | None = None):
    cfg = config or {}
    base_url = cfg.get("openai_base_url", "http://localhost:8000/v1").rstrip("/")
    headers = {"Content-Type": "application/json"}
    api_key_env = cfg.get("openai_api_key_env", "OPENAI_API_KEY")
    api_key = os.getenv(api_key_env, "")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "messages": _to_openai_messages(messages),
        "stream": stream,
    }
    if tools:
        payload["tools"] = tools

    response = requests.post(
        f"{base_url}/chat/completions",
        headers=headers,
        json=payload,
        stream=stream,
        timeout=300,
    )
    response.raise_for_status()

    if stream:
        return _stream(response)
    return _normalize_response(response.json())


def list_models(config: dict | None = None):
    cfg = config or {}
    base_url = cfg.get("openai_base_url", "http://localhost:8000/v1").rstrip("/")
    headers = {}
    api_key_env = cfg.get("openai_api_key_env", "OPENAI_API_KEY")
    api_key = os.getenv(api_key_env, "")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    response = requests.get(f"{base_url}/models", headers=headers, timeout=30)
    response.raise_for_status()
    return [m.get("id") for m in response.json().get("data", []) if m.get("id")]


def _stream(response):
    tool_call_parts = {}
    sent_tool_calls = False

    for line in response.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if data == "[DONE]":
            break

        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            continue

        choice = (payload.get("choices") or [{}])[0]
        delta = choice.get("delta", {})
        content = delta.get("content")
        if content:
            yield {"message": {"content": content, "tool_calls": []}}

        for tc in delta.get("tool_calls", []):
            index = tc.get("index", 0)
            part = tool_call_parts.setdefault(index, {"id": None, "name": "", "args": []})
            if tc.get("id"):
                part["id"] = tc["id"]
            fn = tc.get("function", {})
            if fn.get("name"):
                part["name"] = fn["name"]
            if fn.get("arguments"):
                part["args"].append(fn["arguments"])

        if choice.get("finish_reason") == "tool_calls":
            sent_tool_calls = True
            yield {"message": {"content": "", "tool_calls": _finalize_tool_calls(tool_call_parts)}}

    if tool_call_parts and not sent_tool_calls:
        yield {"message": {"content": "", "tool_calls": _finalize_tool_calls(tool_call_parts)}}


def _normalize_response(payload: dict):
    message = ((payload.get("choices") or [{}])[0]).get("message", {})
    return {
        "message": {
            "content": message.get("content") or "",
            "tool_calls": _normalize_tool_calls(message.get("tool_calls", [])),
        }
    }


def _to_openai_messages(messages: list[dict]):
    out = []
    for m in messages:
        role = m.get("role")

        if role == "assistant":
            item = {"role": "assistant", "content": m.get("content") or ""}
            if m.get("tool_calls"):
                item["tool_calls"] = []
                for tc in m["tool_calls"]:
                    args = tc.get("function", {}).get("arguments", {})
                    item["tool_calls"].append({
                        "id": tc.get("id"),
                        "type": "function",
                        "function": {
                            "name": tc.get("function", {}).get("name"),
                            "arguments": args if isinstance(args, str) else json.dumps(args),
                        },
                    })
            out.append(item)
            continue

        if role == "tool":
            tool_call_id = m.get("tool_call_id")
            if not tool_call_id:
                raise ValueError("OpenAI-compatible provider requires tool_call_id in tool messages.")
            out.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": m.get("content", ""),
            })
            continue

        out.append({"role": role, "content": m.get("content", "")})
    return out


def _normalize_tool_calls(calls: list[dict]):
    if not calls:
        return []
    out = []
    for call in calls:
        fn = call.get("function", {})
        out.append({
            "id": call.get("id"),
            "type": "function",
            "function": {
                "name": fn.get("name"),
                "arguments": _parse_args(fn.get("arguments", "{}")),
            },
        })
    return out


def _finalize_tool_calls(parts: dict):
    calls = []
    for _, item in sorted(parts.items()):
        calls.append({
            "id": item.get("id"),
            "type": "function",
            "function": {
                "name": item.get("name"),
                "arguments": _parse_args("".join(item.get("args", []))),
            },
        })
    return calls


def _parse_args(raw: str):
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}
