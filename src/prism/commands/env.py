"""`prism env` — audit the local development environment."""

from __future__ import annotations

import json
from pathlib import Path

from rich.table import Table

from prism.config import is_configured
from prism.core.tools import run_checks
from prism.ui import console, banner, ok, warn, err, info


def run_json(path: Path) -> None:
    root = path.resolve()
    checks = run_checks(root)
    print(json.dumps({
        "root": str(root),
        "checks": [
            {
                "name": c.name,
                "found": c.found,
                "version": c.version,
                "required_by": c.required_by,
                "fix_hint": c.fix_hint,
            }
            for c in checks
        ],
        "ai_configured": is_configured(),
    }))


def run(path: Path) -> None:
    banner("env")
    root = path.resolve()
    info(f"Auditing environment for [bold]{root}[/bold] ...")

    checks = run_checks(root)

    table = Table(border_style="grey50")
    table.add_column("Status", justify="center", width=6)
    table.add_column("Tool", style="prism.accent")
    table.add_column("Version")
    table.add_column("Notes")

    missing_relevant = []
    for check in checks:
        if check.found:
            status = "[prism.ok]✓[/prism.ok]"
            version = check.version or "—"
            notes = "required by this project" if check.required_by else ""
        else:
            if check.required_by:
                status = "[prism.err]✗[/prism.err]"
                missing_relevant.append(check)
            else:
                status = "[prism.dim]·[/prism.dim]"
            version = "[prism.dim]not found[/prism.dim]"
            notes = check.required_by and "required by this project" or "not used here"
        table.add_row(status, check.name, version, notes)

    console.print(table)

    if missing_relevant:
        console.print()
        err(f"{len(missing_relevant)} required tool(s) missing:")
        for check in missing_relevant:
            console.print(f"    [prism.dim]→[/prism.dim] install {check.name}: [bold]{check.fix_hint}[/bold]")
    else:
        console.print()
        ok("All tools required by this project are installed.")

    if not is_configured():
        warn("No AI provider configured — run `prism setup` to enable AI-backed commands (scan, explain, debug).")
