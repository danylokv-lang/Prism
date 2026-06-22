# Prism

A local AI-powered project intelligence layer for developers.

## Install

Global, works from any directory (recommended):

```bash
brew install pipx
pipx ensurepath
pipx install --editable .
```

Local dev venv instead:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Commands

- `prism setup` — pick and configure an AI provider (local Ollama, Anthropic, or OpenAI). Detects what you already have and lets you keep or change it.
- `prism scan [path]` — analyze a project's structure and stack, with an AI-generated narrative summary if a provider is configured.
- `prism env [path]` — audit installed dev tools against what the project needs, with install hints for anything missing.
- `prism explain <file_or_folder>` — what it does, why it exists, and how it connects to the rest of the project (cross-file references via ripgrep, if installed).

Run `prism setup` first — everything else falls back to structural-only output if no AI provider is configured.

More commands (`debug`, `recipe`, `init`) are planned.
