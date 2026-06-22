"""`prism scan` — analyze the current project and summarize it."""

from __future__ import annotations

import json
from pathlib import Path

from rich.table import Table
from rich.panel import Panel

from prism import llm
from prism.core.detect import detect_project
from prism.ui import console, banner, info, warn


def run_json(path: Path) -> None:
    root = path.resolve()
    summary = detect_project(root)
    narrative = llm.generate(_narrative_prompt(summary))
    print(json.dumps({
        "root": str(root),
        "project_types": summary.project_types,
        "tech_stack": summary.tech_stack,
        "file_count": summary.file_count,
        "languages": summary.languages,
        "top_level_dirs": summary.top_level_dirs,
        "key_files": summary.key_files,
        "ai_summary": narrative,
    }))


def run(path: Path) -> None:
    banner("scan")
    root = path.resolve()
    info(f"Scanning [bold]{root}[/bold] ...")

    summary = detect_project(root)

    overview = Table.grid(padding=(0, 2))
    overview.add_column(style="prism.dim", justify="right")
    overview.add_column()
    overview.add_row("Project type", ", ".join(summary.project_types))
    overview.add_row("Tech stack", ", ".join(summary.tech_stack) or "—")
    overview.add_row("Files scanned", str(summary.file_count))
    if summary.languages:
        lang_str = ", ".join(f"{lang} ({n})" for lang, n in list(summary.languages.items())[:5])
        overview.add_row("Top languages", lang_str)
    if summary.top_level_dirs:
        overview.add_row("Top-level dirs", ", ".join(summary.top_level_dirs[:12]))
    console.print(Panel(overview, title="Overview", border_style="cyan"))

    if summary.key_files:
        table = Table(title="Key files", border_style="grey50", show_lines=False)
        table.add_column("File", style="prism.accent")
        table.add_column("Role")
        for file, role in summary.key_files.items():
            table.add_row(file, role)
        console.print(table)
    else:
        warn("No recognized key files found in the project root.")

    _print_narrative(summary)


def _narrative_prompt(summary) -> str:
    return (
        "You are Prism, a terse project-intelligence assistant. Given this "
        "project metadata, write a 3-5 sentence plain-English architecture "
        "summary a new contributor would find useful. Be concrete, no fluff.\n\n"
        f"Project types: {summary.project_types}\n"
        f"Tech stack: {summary.tech_stack}\n"
        f"Key files: {summary.key_files}\n"
        f"Top-level dirs: {summary.top_level_dirs}\n"
        f"Languages by file count: {summary.languages}\n"
    )


def _print_narrative(summary) -> None:
    with console.status("[prism.accent]Asking local model for a summary...[/prism.accent]"):
        narrative = llm.generate(_narrative_prompt(summary))

    if narrative:
        console.print(Panel(narrative, title="AI Summary", border_style="cyan"))
    else:
        warn(
            "No AI provider configured or reachable. Run `prism setup` to enable "
            "AI summaries. Showing structural scan only."
        )
