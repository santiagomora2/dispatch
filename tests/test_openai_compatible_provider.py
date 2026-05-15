import pytest

from agent.providers import openai_compatible_provider as provider


class FakeSSE:
    def __init__(self, lines):
        self._lines = lines

    def iter_lines(self, decode_unicode=True):
        return iter(self._lines)


def test_to_openai_messages_requires_tool_call_id():
    with pytest.raises(ValueError):
        provider._to_openai_messages([{"role": "tool", "content": "x"}])


def test_stream_merges_tool_call_chunks():
    lines = [
        'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"id":"call_1","function":{"name":"read_file","arguments":"{\\"path\\": \\"a"}}]}}]}',
        'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"arguments":"b.txt\\"}"}}]}}]}',
        'data: {"choices":[{"delta":{},"finish_reason":"tool_calls"}]}',
        "data: [DONE]",
    ]

    chunks = list(provider._stream(FakeSSE(lines)))
    tool_chunks = [c for c in chunks if c["message"]["tool_calls"]]

    assert len(tool_chunks) == 1
    tool_call = tool_chunks[0]["message"]["tool_calls"][0]
    assert tool_call["id"] == "call_1"
    assert tool_call["function"]["name"] == "read_file"
    assert tool_call["function"]["arguments"] == {"path": "ab.txt"}


def test_stream_does_not_duplicate_tool_calls_on_repeated_finish_reason():
    lines = [
        'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"id":"call_1","function":{"name":"read_file","arguments":"{\\"path\\": \\"a.txt\\"}"}}]}}]}',
        'data: {"choices":[{"delta":{},"finish_reason":"tool_calls"}]}',
        'data: {"choices":[{"delta":{},"finish_reason":"tool_calls"}]}',
        "data: [DONE]",
    ]

    chunks = list(provider._stream(FakeSSE(lines)))
    tool_chunks = [c for c in chunks if c["message"]["tool_calls"]]

    assert len(tool_chunks) == 1
    assert len(tool_chunks[0]["message"]["tool_calls"]) == 1
