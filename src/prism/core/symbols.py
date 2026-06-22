"""Lightweight, AI-free extraction of top-level functions/classes per file.

Python uses the stdlib `ast` module for accuracy; everything else falls
back to a regex heuristic that's good enough for an overview, not a parser.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

REGEX_PATTERNS: dict[str, list[str]] = {
    ".js": [r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)", r"^\s*(?:export\s+)?class\s+(\w+)"],
    ".jsx": [r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)", r"^\s*(?:export\s+)?class\s+(\w+)"],
    ".ts": [r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)", r"^\s*(?:export\s+)?class\s+(\w+)"],
    ".tsx": [r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)", r"^\s*(?:export\s+)?class\s+(\w+)"],
    ".go": [r"^\s*func\s+(?:\([^)]*\)\s*)?(\w+)", r"^\s*type\s+(\w+)\s+struct"],
    ".rs": [r"^\s*(?:pub\s+)?fn\s+(\w+)", r"^\s*(?:pub\s+)?struct\s+(\w+)", r"^\s*(?:pub\s+)?enum\s+(\w+)"],
    ".rb": [r"^\s*def\s+(\w+)", r"^\s*class\s+(\w+)"],
    ".java": [r"^\s*(?:public|private|protected)\s+.*?\s+(\w+)\s*\(", r"^\s*(?:public|private)\s+class\s+(\w+)"],
    ".kt": [r"^\s*fun\s+(\w+)", r"^\s*class\s+(\w+)"],
    ".php": [r"^\s*function\s+(\w+)", r"^\s*class\s+(\w+)"],
    ".swift": [r"^\s*func\s+(\w+)", r"^\s*(?:class|struct)\s+(\w+)"],
}

MAX_SYMBOLS = 30


def extract_symbols(path: Path, text: str) -> list[str]:
    if path.suffix == ".py":
        return _extract_python(text)
    patterns = REGEX_PATTERNS.get(path.suffix)
    if not patterns:
        return []
    return _extract_regex(text, patterns)


def _extract_python(text: str) -> list[str]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    symbols = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(f"def {node.name}()")
        elif isinstance(node, ast.ClassDef):
            symbols.append(f"class {node.name}")
        if len(symbols) >= MAX_SYMBOLS:
            break
    return symbols


def _extract_regex(text: str, patterns: list[str]) -> list[str]:
    compiled = [re.compile(p) for p in patterns]
    symbols = []
    for line in text.splitlines():
        for pattern in compiled:
            match = pattern.match(line)
            if match:
                symbols.append(match.group(1))
                break
        if len(symbols) >= MAX_SYMBOLS:
            break
    return symbols
