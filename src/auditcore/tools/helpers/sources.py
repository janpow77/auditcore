"""Find the source files of an application repository.

Tracked and untracked-but-not-ignored files come from ``git ls-files``; outside
a Git checkout the directory is walked. Tests, generated code, dependencies and
build output are left out, because the tool looks at production helpers.
"""

from __future__ import annotations

import fnmatch
import os
import re
import subprocess  # nosec B404
from collections.abc import Iterable
from pathlib import Path

from auditcore.tools.helpers.model import PYTHON, TYPESCRIPT, SourceFile

PYTHON_SUFFIXES = (".py",)
TS_SUFFIXES = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue")
MAX_FILE_BYTES = 1_000_000
SKIP_PARTS = frozenset(
    {
        "node_modules",
        ".git",
        "dist",
        "build",
        ".venv",
        "venv",
        "env",
        "site-packages",
        "__pycache__",
        "graphify-out",
        "worktrees",
        "coverage",
        ".next",
        ".nuxt",
        "vendor",
        "generated",
        "migrations",
        "alembic",
        "public",
        "static",
        ".auditcore",
        "e2e",
        "tests",
        "test",
        "__tests__",
        "__mocks__",
        "fixtures",
        "demo",
        "docs",
        "playwright-report",
    }
)
SKIP_NAME = re.compile(
    r"(\.d\.ts$|\.min\.js$|\.test\.|\.spec\.|\.stories\.|^test_.*\.py$|_test\.py$|^conftest\.py$"
    r"|^(vite|vitest|webpack|rollup|tailwind|postcss|eslint|babel|jest|playwright)\.config\.)"
)


def language_of(path: str) -> str | None:
    """Return the language of a path or ``None`` for other files."""
    if path.endswith(PYTHON_SUFFIXES):
        return PYTHON
    if path.endswith(TS_SUFFIXES):
        return TYPESCRIPT
    return None


def is_skipped(path: str, excludes: Iterable[str] = ()) -> bool:
    """True for tests, dependencies, build output and explicitly excluded paths."""
    parts = path.split("/")
    if any(part in SKIP_PARTS or part.endswith("-wt") for part in parts[:-1]):
        return True
    if SKIP_NAME.search(parts[-1]):
        return True
    return any(fnmatch.fnmatch(path, pattern) for pattern in excludes)


def _git_files(root: Path) -> list[str] | None:
    try:
        process = subprocess.run(  # nosec B603 B607
            [
                "git",
                "-C",
                str(root),
                "ls-files",
                "-z",
                "--cached",
                "--others",
                "--exclude-standard",
            ],
            capture_output=True,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if process.returncode != 0:
        return None
    names = process.stdout.decode("utf-8", errors="replace").split("\0")
    return sorted({name for name in names if name})


def _walk_files(root: Path) -> list[str]:
    found: list[str] = []
    for directory, subdirs, files in os.walk(root):
        subdirs[:] = [
            name for name in subdirs if name not in SKIP_PARTS and not name.startswith(".")
        ]
        base = Path(directory).relative_to(root)
        found.extend((base / name).as_posix() for name in files)
    return sorted(found)


def list_sources(root: Path, excludes: Iterable[str] = ()) -> list[tuple[str, str]]:
    """Return ``(relative path, language)`` for every relevant source file."""
    patterns = list(excludes)
    names = _git_files(root)
    if names is None:
        names = _walk_files(root)
    selected: list[tuple[str, str]] = []
    for name in names:
        language = language_of(name)
        if language is None or is_skipped(name, patterns):
            continue
        path = root / name
        if path.is_file() and path.stat().st_size <= MAX_FILE_BYTES:
            selected.append((name, language))
    return selected


def read_sources(root: Path, excludes: Iterable[str] = ()) -> list[SourceFile]:
    """Read every relevant source file as text."""
    files = []
    for name, language in list_sources(root, excludes):
        text = (root / name).read_text(encoding="utf-8", errors="replace")
        files.append(SourceFile(name, language, text))
    return files
