#!/usr/bin/env python3
"""PostToolUse hook: ruff and mypy only on the Python file Claude just edited.

Reads the hook event from stdin, checks the edited file within a few seconds and
prints only the problems. Exit 2 hands them back to Claude; exit 0 is silent.
Missing tools or timeouts never block (exit 0).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

TIMEOUT = 8
MAX_LINES = 15


def project_of(path: Path) -> Path:
    """Nearest directory with a pyproject.toml (package or repository root)."""
    for parent in path.parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    return path.parent


def run(command: list[str], cwd: Path) -> str:
    try:
        result = subprocess.run(  # noqa: S603
            command, cwd=cwd, capture_output=True, text=True, timeout=TIMEOUT, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if result.returncode == 0:
        return ""
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    return "\n".join(lines[:MAX_LINES])


def main() -> int:
    event = json.load(sys.stdin)
    raw = (event.get("tool_input") or {}).get("file_path", "")
    path = Path(raw)
    if path.suffix != ".py" or not path.is_file():
        return 0
    cwd = project_of(path)
    problems = []
    if shutil.which("ruff"):
        problems.append(run(["ruff", "check", "--output-format=concise", str(path)], cwd))
    in_source = "src" in path.relative_to(cwd).parts if path.is_relative_to(cwd) else False
    if in_source and shutil.which("mypy"):
        command = ["mypy", "--follow-imports=silent", "--no-error-summary", str(path)]
        problems.append(run(command, cwd))
    text = "\n".join(p for p in problems if p)
    if not text:
        return 0
    print(f"{path.name}: bitte beheben\n{text}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
