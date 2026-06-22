"""Prism configuration: ~/.prism/config.toml and recipe storage."""

from pathlib import Path
import sys

import tomli_w

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

PRISM_HOME = Path.home() / ".prism"
CONFIG_PATH = PRISM_HOME / "config.toml"
RECIPES_DIR = PRISM_HOME / "recipes"

DEFAULTS = {
    "llm": {
        "provider": "",
        "ollama_host": "http://localhost:11434",
        "ollama_model": "",
        "anthropic_model": "claude-sonnet-4-6",
        "anthropic_api_key": "",
        "openai_model": "gpt-4o-mini",
        "openai_api_key": "",
    }
}


def ensure_dirs() -> None:
    PRISM_HOME.mkdir(parents=True, exist_ok=True)
    RECIPES_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    ensure_dirs()
    if not CONFIG_PATH.exists():
        return {"llm": dict(DEFAULTS["llm"])}
    with CONFIG_PATH.open("rb") as f:
        data = tomllib.load(f)
    merged = {**DEFAULTS, **data}
    merged["llm"] = {**DEFAULTS["llm"], **data.get("llm", {})}
    return merged


def save_config(config: dict) -> None:
    ensure_dirs()
    with CONFIG_PATH.open("wb") as f:
        tomli_w.dump(config, f)
    CONFIG_PATH.chmod(0o600)


def is_configured() -> bool:
    return bool(load_config()["llm"].get("provider"))
