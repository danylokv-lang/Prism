# Prism

A local AI-powered project intelligence layer for developers.

## Install (dev)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Commands

- `prism scan` — analyze the current project's structure and stack, with an optional AI-generated narrative summary if [Ollama](https://ollama.com) is running.
- `prism env` — audit installed dev tools against what this project needs, with install hints for anything missing.

More commands (`explain`, `debug`, `recipe`, `init`) are planned.
# Prism
