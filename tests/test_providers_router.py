import pytest

from agent import providers


def test_get_provider_defaults_to_ollama():
    assert providers.get_provider({}) == "ollama"


def test_get_provider_rejects_unknown_value():
    with pytest.raises(ValueError):
        providers.get_provider({"provider": "not-a-provider"})


def test_chat_routes_to_ollama(monkeypatch):
    called = {}

    def fake_chat(**kwargs):
        called.update(kwargs)
        return {"message": {"content": "ok", "tool_calls": []}}

    monkeypatch.setattr(providers.ollama_provider, "chat", fake_chat)

    out = providers.chat(
        model="qwen",
        messages=[{"role": "user", "content": "hi"}],
        tools=[{"type": "function"}],
        stream=True,
        config={"provider": "ollama"},
    )

    assert out["message"]["content"] == "ok"
    assert called["model"] == "qwen"
    assert called["stream"] is True


def test_chat_routes_to_openai_compatible(monkeypatch):
    called = {}

    def fake_chat(**kwargs):
        called.update(kwargs)
        return {"message": {"content": "ok", "tool_calls": []}}

    monkeypatch.setattr(providers.openai_compatible_provider, "chat", fake_chat)

    out = providers.chat(
        model="gpt",
        messages=[{"role": "user", "content": "hi"}],
        stream=False,
        config={"provider": "openai-compatible"},
    )

    assert out["message"]["content"] == "ok"
    assert called["model"] == "gpt"
    assert called["stream"] is False


def test_list_models_routes_by_provider(monkeypatch):
    monkeypatch.setattr(providers.ollama_provider, "list_models", lambda: ["qwen"])
    monkeypatch.setattr(
        providers.openai_compatible_provider,
        "list_models",
        lambda cfg: ["gemma"],
    )

    assert providers.list_models({"provider": "ollama"}) == ["qwen"]
    assert providers.list_models({"provider": "openai-compatible"}) == ["gemma"]
