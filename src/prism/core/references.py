"""Find where a file is referenced elsewhere in the project, via ripgrep
if it's installed. Returns an empty list (never raises) if rg is missing
or finds nothing — this is a nice-to-have, not a dependency."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

MAX_REFERENCES = 10


def find_references(target: Path, root: Path) -> list[str]:
    if not shutil.which("rg"):
        return []

    stem = target.stem
    if not stem or len(stem) < 2:
        return []

    try:
        result = subprocess.run(
            ["rg", "--files-with-matches", "--fixed-strings", stem, str(root)],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (subprocess.SubprocessError, OSError):
        return []

    if result.returncode not in (0, 1):
        return []

    files = [
        line for line in result.stdout.splitlines()
        if Path(line).resolve() != target.resolve()
    ]
    return files[:MAX_REFERENCES]
