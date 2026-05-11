from agent.cmd import arg_completers


def test_get_available_models_returns_values(monkeypatch):
    monkeypatch.setattr(arg_completers, "list_models", lambda: ["qwen3.5:9b", "gemma4:e4b"])
    assert arg_completers.get_available_models() == ["qwen3.5:9b", "gemma4:e4b"]


def test_get_available_models_handles_errors(monkeypatch):
    def explode():
        raise RuntimeError("boom")

    monkeypatch.setattr(arg_completers, "list_models", explode)
    assert arg_completers.get_available_models() == []
