"""LLM provider abstraction. `prism setup` picks one and saves it to config;
every command calls the module-level `generate()` and gets None back if
nothing is configured or reachable, so callers always have a safe fallback."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod

import httpx

from prism.config import load_config

ANTHROPIC_VERSION = "2023-06-01"


class LLMProvider(ABC):
    name: str

    @abstractmethod
    def generate(self, prompt: str, system: str | None = None) -> str | None:
        ...


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, host: str, model: str):
        self.host = host
        self.model = model

    def is_running(self) -> bool:
        try:
            httpx.get(f"{self.host}/api/version", timeout=1.0)
            return True
        except httpx.HTTPError:
            return False

    def list_models(self) -> list[str]:
        try:
            response = httpx.get(f"{self.host}/api/tags", timeout=2.0)
            response.raise_for_status()
            return [m["name"] for m in response.json().get("models", [])]
        except (httpx.HTTPError, KeyError, ValueError):
            return []

    def generate(self, prompt: str, system: str | None = None) -> str | None:
        try:
            response = httpx.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "system": system or "",
                    "stream": False,
                },
                timeout=120.0,
            )
            response.raise_for_status()
            return response.json().get("response", "").strip() or None
        except httpx.HTTPError:
            return None


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str, system: str | None = None) -> str | None:
        try:
            response = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": ANTHROPIC_VERSION,
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 1024,
                    "system": system or "",
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=60.0,
            )
            response.raise_for_status()
            blocks = response.json().get("content", [])
            text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
            return text.strip() or None
        except httpx.HTTPError:
            return None


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str, system: str | None = None) -> str | None:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        try:
            response = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "messages": messages},
                timeout=60.0,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip() or None
        except (httpx.HTTPError, KeyError, IndexError):
            return None


def get_provider() -> LLMProvider | None:
    """Builds the configured provider, or None if nothing is set up."""
    cfg = load_config()["llm"]
    provider = cfg.get("provider")

    if provider == "ollama":
        return OllamaProvider(cfg["ollama_host"], cfg["ollama_model"])

    if provider == "anthropic":
        key = cfg.get("anthropic_api_key") or os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            return None
        return AnthropicProvider(key, cfg["anthropic_model"])

    if provider == "openai":
        key = cfg.get("openai_api_key") or os.environ.get("OPENAI_API_KEY", "")
        if not key:
            return None
        return OpenAIProvider(key, cfg["openai_model"])

    return None


def generate(prompt: str, system: str | None = None) -> str | None:
    """Returns generated text, or None if no provider is configured/reachable."""
    provider = get_provider()
    if provider is None:
        return None
    return provider.generate(prompt, system)
