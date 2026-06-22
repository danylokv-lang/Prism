"""`prism explain <file_or_folder>` — plain-English explanation of any
file or folder, grounded in deterministic facts (symbols, size, cross-file
references) with an optional AI narrative layered on top."""

from __future__ import annotations

from pathlib import Path

from rich.table import Table
from rich.panel import Panel

from prism import llm
from prism.core.detect import IGNORE_DIRS, KEY_FILE_ROLES
from prism.core.references import find_references
from prism.core.symbols import extract_symbols
from prism.ui import console, banner, err, info, warn

MAX_CONTENT_CHARS = 8000


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

    prompt = (
        "You are Prism, a terse code-explanation assistant. Given this file's "
        "path, symbols, and content, explain in 3-5 sentences: what it does, "
        "why it likely exists, and how it connects to the rest of the project. "
        "Be concrete, no fluff, no restating the obvious file name.\n\n"
        f"Path: {path}\n"
        f"Top-level symbols: {symbols}\n"
        f"Referenced by: {refs}\n\n"
        f"Content:\n{text[:MAX_CONTENT_CHARS]}"
    )
    if len(text) > MAX_CONTENT_CHARS:
        prompt += "\n\n[truncated]"

    _print_narrative(prompt)


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

    prompt = (
        "You are Prism, a terse code-explanation assistant. Given this "
        "folder's name and contents, explain in 2-4 sentences what role this "
        "folder likely plays in the project's architecture. Be concrete, no "
        "fluff.\n\n"
        f"Folder: {path.name}\n"
        f"Subfolders: {[d.name for d in subdirs]}\n"
        f"Files: {[f.name for f in files]}\n"
    )
    _print_narrative(prompt)


def _print_narrative(prompt: str) -> None:
    with console.status("[prism.accent]Asking AI for an explanation...[/prism.accent]"):
        narrative = llm.generate(prompt)

    if narrative:
        console.print(Panel(narrative, title="AI Explanation", border_style="cyan"))
    else:
        warn("No AI provider configured or reachable. Run `prism setup` to enable explanations.")
