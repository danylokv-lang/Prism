"""Prism CLI entrypoint."""

from __future__ import annotations

from pathlib import Path

import typer
from typer import rich_utils

from prism.commands import scan as scan_cmd
from prism.commands import env as env_cmd
from prism.commands import setup as setup_cmd
from prism.commands import explain as explain_cmd

# Match Typer's --help/error styling to Prism's cyan theme instead of the
# default red/yellow/magenta mix, which clashes with our own panels.
rich_utils.STYLE_USAGE = "cyan"
rich_utils.STYLE_USAGE_COMMAND = "bold cyan"
rich_utils.STYLE_METAVAR = "cyan"
rich_utils.STYLE_HELPTEXT = "grey58"
rich_utils.STYLE_OPTION = "bold cyan"
rich_utils.STYLE_OPTIONS_PANEL_BORDER = "cyan"
rich_utils.STYLE_COMMANDS_PANEL_BORDER = "cyan"
rich_utils.STYLE_COMMANDS_TABLE_FIRST_COLUMN = "bold cyan"
rich_utils.STYLE_ERRORS_PANEL_BORDER = "cyan"
rich_utils.STYLE_ERRORS_SUGGESTION = "grey58"

app = typer.Typer(
    name="prism",
    help="Prism — a local AI-powered project intelligence layer.",
    no_args_is_help=True,
    add_completion=False,
)


@app.command()
def scan(
    path: Path = typer.Argument(Path("."), help="Path to the project to scan."),
    json_out: bool = typer.Option(False, "--json", help="Print structured JSON instead of formatted output."),
) -> None:
    """Analyze the current project and produce a structural + AI summary."""
    if json_out:
        scan_cmd.run_json(path)
    else:
        scan_cmd.run(path)


@app.command()
def env(
    path: Path = typer.Argument(Path("."), help="Path to the project to audit against."),
    json_out: bool = typer.Option(False, "--json", help="Print structured JSON instead of formatted output."),
) -> None:
    """Audit your local dev environment against this project's requirements."""
    if json_out:
        env_cmd.run_json(path)
    else:
        env_cmd.run(path)


@app.command()
def explain(
    path: Path = typer.Argument(..., help="File or folder to explain."),
    json_out: bool = typer.Option(False, "--json", help="Print structured JSON instead of formatted output."),
) -> None:
    """Explain what a file or folder does, why it exists, and how it connects."""
    if json_out:
        explain_cmd.run_json(path)
    else:
        explain_cmd.run(path)


@app.command()
def setup() -> None:
    """Pick and configure which AI provider Prism should use."""
    setup_cmd.run()


if __name__ == "__main__":
    app()
