"""Dev environment tool detection for `prism env`."""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ToolCheck:
    name: str
    found: bool
    version: str | None
    required_by: str | None
    fix_hint: str | None


# (binary, --version flag, version regex)
TOOL_PROBES: list[tuple[str, str, str]] = [
    ("git", "--version", r"(\d+\.\d+(\.\d+)?)"),
    ("python3", "--version", r"(\d+\.\d+\.\d+)"),
    ("node", "--version", r"v?(\d+\.\d+\.\d+)"),
    ("npm", "--version", r"(\d+\.\d+\.\d+)"),
    ("rustc", "--version", r"(\d+\.\d+\.\d+)"),
    ("cargo", "--version", r"(\d+\.\d+\.\d+)"),
    ("go", "version", r"go(\d+\.\d+(\.\d+)?)"),
    ("docker", "--version", r"(\d+\.\d+\.\d+)"),
    ("ollama", "--version", r"(\d+\.\d+\.\d+)"),
]

INSTALL_HINTS = {
    "git": "brew install git  (macOS)  /  sudo apt install git  (Linux)",
    "python3": "brew install python  (macOS)  /  sudo apt install python3  (Linux)",
    "node": "brew install node  (macOS)  /  see https://nodejs.org",
    "npm": "comes bundled with Node.js — install node first",
    "rustc": "curl https://sh.rustup.rs -sSf | sh",
    "cargo": "comes bundled with rustc — install rustc first",
    "go": "brew install go  (macOS)  /  see https://go.dev/dl",
    "docker": "see https://docs.docker.com/get-docker/",
    "ollama": "curl -fsSL https://ollama.com/install.sh | sh  (Linux)  /  brew install ollama  (macOS)",
}

# project marker -> tools it implies are relevant
PROJECT_TOOL_RELEVANCE = {
    "pyproject.toml": ["python3"],
    "requirements.txt": ["python3"],
    "package.json": ["node", "npm"],
    "Cargo.toml": ["rustc", "cargo"],
    "go.mod": ["go"],
    "Dockerfile": ["docker"],
    "docker-compose.yml": ["docker"],
}


def _probe(binary: str, flag: str, pattern: str) -> str | None:
    path = shutil.which(binary)
    if not path:
        return None
    try:
        result = subprocess.run(
            [binary, flag], capture_output=True, text=True, timeout=5
        )
        output = result.stdout + result.stderr
        match = re.search(pattern, output)
        return match.group(1) if match else output.strip().splitlines()[0]
    except (subprocess.SubprocessError, OSError, IndexError):
        return "unknown"


def relevant_tools_for(root: Path) -> set[str]:
    relevant: set[str] = set()
    for marker, tools in PROJECT_TOOL_RELEVANCE.items():
        if (root / marker).exists():
            relevant.update(tools)
    return relevant


def run_checks(root: Path) -> list[ToolCheck]:
    relevant = relevant_tools_for(root)
    checks: list[ToolCheck] = []
    for binary, flag, pattern in TOOL_PROBES:
        found_path = shutil.which(binary)
        version = _probe(binary, flag, pattern) if found_path else None
        checks.append(
            ToolCheck(
                name=binary,
                found=bool(found_path),
                version=version,
                required_by="this project" if binary in relevant else None,
                fix_hint=None if found_path else INSTALL_HINTS.get(binary),
            )
        )
    return checks
