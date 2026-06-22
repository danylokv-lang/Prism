"""Shared Rich theming and output helpers for Prism."""

from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.text import Text

THEME = Theme(
    {
        "prism.accent": "bold cyan",
        "prism.dim": "grey58",
        "prism.ok": "bold green",
        "prism.warn": "bold yellow",
        "prism.err": "bold red",
        "prism.title": "bold cyan",
    }
)

console = Console(theme=THEME)


def banner(command: str) -> None:
    title = Text()
    title.append("◆ Prism", style="prism.title")
    title.append(f"  ·  {command}", style="prism.dim")
    console.print(Panel(title, border_style="cyan", padding=(0, 2)))


def ok(message: str) -> None:
    console.print(f"[prism.ok]✓[/prism.ok] {message}")


def warn(message: str) -> None:
    console.print(f"[prism.warn]⚠[/prism.warn] {message}")


def err(message: str) -> None:
    console.print(f"[prism.err]✗[/prism.err] {message}")


def info(message: str) -> None:
    console.print(f"[prism.accent]›[/prism.accent] {message}")
