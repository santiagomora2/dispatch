import json

from agent.paths import CONFIG_FILE
from . import ollama_provider, openai_compatible_provider

SUPPORTED = ["ollama", "openai-compatible"]


def get_provider(config: dict | None = None):
    cfg = load_config() if config is None else config
    provider = cfg.get("provider", "ollama")
    if provider not in SUPPORTED:
        raise ValueError(f"Unsupported provider '{provider}'. Supported: {', '.join(SUPPORTED)}")
    return provider


def load_config():
    return json.loads(CONFIG_FILE.read_text())


def list_models(config: dict | None = None):
    cfg = load_config() if config is None else config
    provider = get_provider(cfg)
    if provider == "ollama":
        return ollama_provider.list_models()
    return openai_compatible_provider.list_models(cfg)


def chat(model: str, messages: list[dict], tools=None, stream: bool = False, config: dict | None = None):
    cfg = load_config() if config is None else config
    provider = get_provider(cfg)
    if provider == "ollama":
        return ollama_provider.chat(model=model, messages=messages, tools=tools, stream=stream)
    return openai_compatible_provider.chat(
        model=model,
        messages=messages,
        tools=tools,
        stream=stream,
        config=cfg,
    )
