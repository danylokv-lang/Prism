"""Lightweight, dependency-free project type and stack detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# (marker file, project type, tech tag)
MARKERS: list[tuple[str, str, str]] = [
    ("pyproject.toml", "Python", "Python"),
    ("setup.py", "Python", "Python"),
    ("requirements.txt", "Python", "Python"),
    ("package.json", "Node.js", "Node.js"),
    ("Cargo.toml", "Rust", "Rust"),
    ("go.mod", "Go", "Go"),
    ("Gemfile", "Ruby", "Ruby"),
    ("composer.json", "PHP", "PHP"),
    ("pom.xml", "Java (Maven)", "Java"),
    ("build.gradle", "Java/Kotlin (Gradle)", "Java/Kotlin"),
    ("CMakeLists.txt", "C/C++", "C/C++"),
    ("mix.exs", "Elixir", "Elixir"),
]

KEY_FILE_ROLES: dict[str, str] = {
    "pyproject.toml": "Python project metadata & dependencies",
    "setup.py": "Legacy Python packaging script",
    "requirements.txt": "Python dependency list",
    "package.json": "Node.js project metadata & dependencies",
    "tsconfig.json": "TypeScript compiler configuration",
    "Cargo.toml": "Rust package manifest",
    "go.mod": "Go module definition",
    "Gemfile": "Ruby dependency manifest",
    "Dockerfile": "Container build definition",
    "docker-compose.yml": "Multi-container orchestration",
    "docker-compose.yaml": "Multi-container orchestration",
    ".env": "Environment variable defaults",
    ".env.example": "Environment variable template",
    "Makefile": "Build/task automation",
    ".github/workflows": "CI/CD pipelines (GitHub Actions)",
    "README.md": "Project documentation entry point",
    ".gitignore": "Git exclusion rules",
}

IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
    ".mypy_cache", ".pytest_cache", "target", ".idea", ".vscode", ".next",
    "coverage", ".tox",
}


@dataclass
class ProjectSummary:
    root: Path
    project_types: list[str] = field(default_factory=list)
    tech_stack: list[str] = field(default_factory=list)
    key_files: dict[str, str] = field(default_factory=dict)
    top_level_dirs: list[str] = field(default_factory=list)
    file_count: int = 0
    languages: dict[str, int] = field(default_factory=dict)


LANGUAGE_EXTENSIONS = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".rs": "Rust", ".go": "Go",
    ".rb": "Ruby", ".php": "PHP", ".java": "Java", ".kt": "Kotlin",
    ".c": "C", ".h": "C", ".cpp": "C++", ".hpp": "C++", ".swift": "Swift",
    ".ex": "Elixir", ".exs": "Elixir", ".sh": "Shell",
}


def detect_project(root: Path) -> ProjectSummary:
    summary = ProjectSummary(root=root)

    for marker, ptype, tag in MARKERS:
        if (root / marker).exists():
            if ptype not in summary.project_types:
                summary.project_types.append(ptype)
            if tag not in summary.tech_stack:
                summary.tech_stack.append(tag)

    for key_file, role in KEY_FILE_ROLES.items():
        if (root / key_file).exists():
            summary.key_files[key_file] = role

    try:
        summary.top_level_dirs = sorted(
            p.name for p in root.iterdir()
            if p.is_dir() and p.name not in IGNORE_DIRS and not p.name.startswith(".")
        )
    except OSError:
        pass

    language_counts: dict[str, int] = {}
    file_count = 0
    for path in _walk(root):
        file_count += 1
        lang = LANGUAGE_EXTENSIONS.get(path.suffix)
        if lang:
            language_counts[lang] = language_counts.get(lang, 0) + 1

    summary.file_count = file_count
    summary.languages = dict(
        sorted(language_counts.items(), key=lambda kv: kv[1], reverse=True)
    )

    if not summary.project_types:
        summary.project_types.append("Unknown")

    return summary


def _walk(root: Path, max_files: int = 5000):
    count = 0
    stack = [root]
    while stack and count < max_files:
        current = stack.pop()
        try:
            entries = list(current.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_dir():
                if entry.name not in IGNORE_DIRS and not entry.name.startswith("."):
                    stack.append(entry)
            else:
                count += 1
                yield entry
                if count >= max_files:
                    return
