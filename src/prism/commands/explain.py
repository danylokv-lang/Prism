"""`prism explain <file_or_folder>` — plain-English explanation of any
file or folder, grounded in deterministic facts (symbols, size, cross-file
references) with an optional AI narrative layered on top."""

from __future__ import annotations

import json
from pathlib import Path

from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from prism import llm
from prism.core.detect import IGNORE_DIRS, KEY_FILE_ROLES
from prism.core.references import find_references
from prism.core.symbols import extract_symbols
from prism.ui import console, banner, err, info, warn

MAX_CONTENT_CHARS = 8000


def run_json(target: Path) -> None:
    path = target.resolve()
    if not path.exists():
        print(json.dumps({"error": f"{path} does not exist."}))
        return

    if path.is_dir():
        print(json.dumps(_folder_data(path)))
    else:
        print(json.dumps(_file_data(path)))


def _file_data(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return {"kind": "file", "path": str(path), "error": "binary file, nothing readable to explain"}

    symbols = extract_symbols(path, text)
    refs = find_references(path, Path.cwd())
    narrative = llm.generate(_file_prompt(path, text, symbols, refs))
    return {
        "kind": "file",
        "path": str(path),
        "size_chars": len(text),
        "lines": text.count("\n") + 1,
        "type": path.suffix.lstrip(".") or "no extension",
        "symbols": symbols,
        "references": refs,
        "ai_explanation": narrative,
    }


def _folder_data(path: Path) -> dict:
    entries = sorted(path.iterdir())
    visible = [e for e in entries if e.name not in IGNORE_DIRS and not e.name.startswith(".")]
    subdirs = [e.name for e in visible if e.is_dir()]
    files = [e.name for e in visible if e.is_file()]
    roles = {name: KEY_FILE_ROLES[name] for name in files if name in KEY_FILE_ROLES}
    narrative = llm.generate(_folder_prompt(path, subdirs, files))
    return {
        "kind": "folder",
        "path": str(path),
        "subdirs": subdirs,
        "files": files,
        "roles": roles,
        "ai_explanation": narrative,
    }


def run(target: Path) -> None:
    banner("explain")
    path = target.resolve()

    if not path.exists():
        err(f"{path} does not exist.")
        return

    if path.is_dir():
        _explain_folder(path)
    else:
        _explain_file(path)


def _explain_file(path: Path) -> None:
    info(f"Explaining [bold]{path}[/bold] ...")

    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        warn("This looks like a binary file — nothing readable to explain.")
        return

    lines = text.count("\n") + 1
    symbols = extract_symbols(path, text)
    refs = find_references(path, Path.cwd())

    overview = Table.grid(padding=(0, 2))
    overview.add_column(style="prism.dim", justify="right")
    overview.add_column()
    overview.add_row("Size", f"{len(text)} chars, {lines} lines")
    overview.add_row("Type", path.suffix.lstrip(".") or "no extension")
    if refs:
        overview.add_row("Referenced in", ", ".join(refs))
    else:
        overview.add_row("Referenced in", "[prism.dim]none found (or ripgrep not installed)[/prism.dim]")
    console.print(Panel(overview, title="Overview", border_style="cyan"))

    if symbols:
        table = Table(title="Top-level symbols", border_style="grey50")
        table.add_column("Symbol", style="prism.accent")
        for symbol in symbols:
            table.add_row(symbol)
        console.print(table)

    _print_narrative(_file_prompt(path, text, symbols, refs))


def _explain_folder(path: Path) -> None:
    info(f"Explaining [bold]{path}[/bold] ...")

    try:
        entries = sorted(path.iterdir())
    except OSError as exc:
        err(f"Couldn't read folder: {exc}")
        return

    visible = [
        e for e in entries
        if e.name not in IGNORE_DIRS and not e.name.startswith(".")
    ]
    subdirs = [e for e in visible if e.is_dir()]
    files = [e for e in visible if e.is_file()]

    overview = Table.grid(padding=(0, 2))
    overview.add_column(style="prism.dim", justify="right")
    overview.add_column()
    overview.add_row("Subfolders", str(len(subdirs)))
    overview.add_row("Files", str(len(files)))
    console.print(Panel(overview, title="Overview", border_style="cyan"))

    table = Table(title="Contents", border_style="grey50")
    table.add_column("Name", style="prism.accent")
    table.add_column("Kind")
    table.add_column("Role")
    for entry in visible:
        kind = "dir" if entry.is_dir() else "file"
        role = KEY_FILE_ROLES.get(entry.name, "—")
        table.add_row(entry.name, kind, role)
    console.print(table)

    _print_narrative(_folder_prompt(path, [d.name for d in subdirs], [f.name for f in files]))


def _file_prompt(path: Path, text: str, symbols: list[str], refs: list[str]) -> str:
    prompt = (
        "You are Prism, explaining a code file to a complete beginner who may "
        "be new to programming. Do not write one dense paragraph. Structure "
        "your answer as short labeled sections, each 1-2 short sentences, "
        "using this exact format:\n\n"
        "**What this does** — plain-language summary, no jargon.\n"
        "**Why it exists** — the problem it solves.\n"
        "**How it connects** — what calls it or what it depends on.\n\n"
        "If you must use a technical term, briefly define it in parentheses "
        "the first time you use it. Be concrete and specific to this file, no "
        "generic filler, no restating the obvious file name.\n\n"
        f"Path: {path}\n"
        f"Top-level symbols: {symbols}\n"
        f"Referenced by: {refs}\n\n"
        f"Content:\n{text[:MAX_CONTENT_CHARS]}"
    )
    if len(text) > MAX_CONTENT_CHARS:
        prompt += "\n\n[truncated]"
    return prompt


def _folder_prompt(path: Path, subdirs: list[str], files: list[str]) -> str:
    return (
        "You are Prism, explaining a project folder to a complete beginner "
        "who may be new to programming. Do not write one dense paragraph. "
        "Structure your answer as short labeled sections, each 1-2 short "
        "sentences, using this exact format:\n\n"
        "**What this is** — plain-language summary, no jargon.\n"
        "**What's inside** — what the files/subfolders are for.\n"
        "**How it fits together** — its role in the wider project.\n\n"
        "If you must use a technical term, briefly define it in parentheses "
        "the first time you use it. Be concrete and specific, no generic "
        "filler.\n\n"
        f"Folder: {path.name}\n"
        f"Subfolders: {subdirs}\n"
        f"Files: {files}\n"
    )


def _print_narrative(prompt: str) -> None:
    with console.status("[prism.accent]Asking AI for an explanation...[/prism.accent]"):
        narrative = llm.generate(prompt)

    if narrative:
        console.print(Panel(Markdown(narrative), title="AI Explanation", border_style="cyan"))
    else:
        warn("No AI provider configured or reachable. Run `prism setup` to enable explanations.")
