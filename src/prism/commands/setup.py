"""`prism setup` — interactive wizard to pick and configure an AI provider."""

from __future__ import annotations

import os

import questionary
from questionary import Style

from prism.config import load_config, save_config
from prism.llm import AnthropicProvider, OllamaProvider, OpenAIProvider
from prism.ui import banner, console, err, ok, warn

QSTYLE = Style(
    [
        ("qmark", "fg:#00d7d7 bold"),
        ("question", "bold"),
        ("answer", "fg:#00d7d7 bold"),
        ("pointer", "fg:#00d7d7 bold"),
        ("highlighted", "fg:#00d7d7 bold"),
        ("selected", "fg:#00d7d7"),
    ]
)

DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "llama3.1"


def _describe_current(config: dict) -> str | None:
    llm = config["llm"]
    provider = llm.get("provider")
    if provider == "ollama" and llm.get("ollama_model"):
        return f"Ollama ({llm['ollama_model']})"
    if provider == "anthropic" and llm.get("anthropic_model"):
        return f"Anthropic ({llm['anthropic_model']})"
    if provider == "openai" and llm.get("openai_model"):
        return f"OpenAI ({llm['openai_model']})"
    return None


def run() -> None:
    banner("setup")

    config = load_config()
    current = _describe_current(config)
    if current:
        choice = questionary.select(
            f"You already have {current} configured.",
            choices=[
                questionary.Choice(f"Keep using {current}", value="keep"),
                questionary.Choice("Change provider / reconfigure", value="change"),
            ],
            style=QSTYLE,
        ).ask()
        if choice is None or choice == "keep":
            ok(f"Keeping current setup: {current}")
            return

    console.print("Let's set up the AI provider Prism will use for AI-backed commands.\n")

    ollama = OllamaProvider(DEFAULT_OLLAMA_HOST, DEFAULT_OLLAMA_MODEL)
    ollama_running = ollama.is_running()
    ollama_models = ollama.list_models() if ollama_running else []

    has_anthropic_env = bool(os.environ.get("ANTHROPIC_API_KEY"))
    has_openai_env = bool(os.environ.get("OPENAI_API_KEY"))

    console.print("[prism.dim]Detecting what's already available...[/prism.dim]")
    if ollama_running:
        ok(f"Ollama is running ({len(ollama_models)} model(s) installed)")
    else:
        warn("Ollama not detected on localhost:11434")
    if has_anthropic_env:
        ok("ANTHROPIC_API_KEY found in environment")
    if has_openai_env:
        ok("OPENAI_API_KEY found in environment")
    console.print()

    choices = []
    if ollama_running:
        choices.append(questionary.Choice("Ollama (local, free, private) — recommended", value="ollama"))
    else:
        choices.append(questionary.Choice("Ollama (local) — not running, will need setup", value="ollama"))
    choices.append(questionary.Choice("Anthropic Claude (cloud API)", value="anthropic"))
    choices.append(questionary.Choice("OpenAI (cloud API)", value="openai"))
    choices.append(questionary.Choice("Skip — structural output only, no AI", value="skip"))

    provider = questionary.select(
        "Which AI provider should Prism use?",
        choices=choices,
        style=QSTYLE,
    ).ask()

    if provider is None:
        warn("Setup cancelled.")
        return

    if provider == "skip":
        config["llm"]["provider"] = ""
        save_config(config)
        warn("No AI provider configured. AI-backed commands will fall back to structural output.")
        return

    if provider == "ollama":
        _setup_ollama(config, ollama_running, ollama_models)
        return

    if provider == "anthropic":
        _setup_cloud(
            config,
            provider="anthropic",
            env_var="ANTHROPIC_API_KEY",
            has_env=has_anthropic_env,
            model_key="anthropic_model",
            api_key_field="anthropic_api_key",
            default_model=config["llm"]["anthropic_model"],
            provider_cls=AnthropicProvider,
        )
        return

    if provider == "openai":
        _setup_cloud(
            config,
            provider="openai",
            env_var="OPENAI_API_KEY",
            has_env=has_openai_env,
            model_key="openai_model",
            api_key_field="openai_api_key",
            default_model=config["llm"]["openai_model"],
            provider_cls=OpenAIProvider,
        )
        return


def _setup_ollama(config: dict, running: bool, models: list[str]) -> None:
    if not running:
        err("Ollama isn't reachable at localhost:11434.")
        console.print(
            "  [prism.dim]→[/prism.dim] install: curl -fsSL https://ollama.com/install.sh | sh\n"
            "  [prism.dim]→[/prism.dim] then run: ollama serve  &  ollama pull llama3.2"
        )
        return

    if not models:
        warn("Ollama is running but has no models pulled yet.")
        console.print("  [prism.dim]→[/prism.dim] run: ollama pull llama3.2  (small, ~2GB, fast)")
        return

    previous = config["llm"].get("ollama_model")
    model = questionary.select(
        "Which installed model should Prism use?",
        choices=models,
        default=previous if previous in models else None,
        style=QSTYLE,
    ).ask()
    if model is None:
        warn("Setup cancelled.")
        return

    with console.status("[prism.accent]Verifying model responds...[/prism.accent]"):
        result = OllamaProvider(DEFAULT_OLLAMA_HOST, model).generate("Reply with the single word: ok")

    if not result:
        err(f"Couldn't get a response from '{model}'. Configuration not saved.")
        return

    config["llm"]["provider"] = "ollama"
    config["llm"]["ollama_host"] = DEFAULT_OLLAMA_HOST
    config["llm"]["ollama_model"] = model
    save_config(config)
    ok(f"Using Ollama ({model}). Saved to ~/.prism/config.toml")


def _setup_cloud(
    config: dict,
    *,
    provider: str,
    env_var: str,
    has_env: bool,
    model_key: str,
    api_key_field: str,
    default_model: str,
    provider_cls,
) -> None:
    api_key = None
    saved_key = config["llm"].get(api_key_field, "")

    if saved_key:
        keep_saved = questionary.confirm(
            f"You already have a saved {provider.title()} API key. Keep using it?",
            default=True,
            style=QSTYLE,
        ).ask()
        if keep_saved:
            api_key = saved_key

    if not api_key and has_env:
        use_env = questionary.confirm(
            f"Use the {env_var} from your environment?", default=True, style=QSTYLE
        ).ask()
        if use_env:
            api_key = os.environ[env_var]

    if not api_key:
        api_key = questionary.password(
            f"Paste your {provider.title()} API key (stored locally in ~/.prism/config.toml, chmod 600):"
        ).ask()

    if not api_key:
        warn("Setup cancelled.")
        return

    model = questionary.text("Model name to use:", default=default_model, style=QSTYLE).ask()
    if not model:
        warn("Setup cancelled.")
        return

    with console.status(f"[prism.accent]Verifying {provider.title()} key...[/prism.accent]"):
        result = provider_cls(api_key, model).generate("Reply with the single word: ok")

    if not result:
        err("Couldn't get a response — check your API key and model name. Configuration not saved.")
        return

    config["llm"]["provider"] = provider
    config["llm"][model_key] = model
    if has_env and api_key == os.environ.get(env_var):
        config["llm"][api_key_field] = ""
    else:
        config["llm"][api_key_field] = api_key
    save_config(config)
    ok(f"Using {provider.title()} ({model}). Saved to ~/.prism/config.toml")
