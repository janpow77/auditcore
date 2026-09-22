"""Shared tooling I/O, evidence and safe process execution."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def now() -> str:
    """Return a timezone-aware timestamp."""
    return datetime.now(UTC).isoformat()


def serializable(value: Any) -> Any:
    """Convert tool models to JSON-compatible values."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return serializable(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {str(k): serializable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [serializable(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    return value


def digest(value: bytes | str) -> str:
    """Return a SHA-256 digest."""
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def write_json(path: Path, value: Any) -> None:
    """Atomically replace JSON, with private permissions for inventory data."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".auditcore-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(serializable(value), handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def read_json(path: Path) -> Any:
    """Read JSON without executing input."""
    return json.loads(path.read_text(encoding="utf-8"))


def run(command: list[str], cwd: Path | None = None, timeout: int = 120) -> str:
    """Run an argument vector; redact subprocess output from raised errors."""
    try:
        result = subprocess.run(
            command, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"Command unavailable or timed out: {command[0]}") from exc
    if result.returncode:
        raise RuntimeError(f"Command failed: {command[0]}, exit={result.returncode}")
    return result.stdout


def safe_path(root: Path, relative: str) -> Path:
    """Resolve an input path and reject escape or symlink traversal."""
    candidate = root / relative
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("Relative path required")
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError("Path escapes repository")
    current = candidate
    while current != root:
        if current.is_symlink():
            raise ValueError("Symlink traversal is forbidden")
        current = current.parent
    return candidate


def emit(value: Any, output: Path | None = None) -> None:
    """Print a JSON report and optionally persist it atomically."""
    if output:
        write_json(output, value)
    print(json.dumps(serializable(value), indent=2, ensure_ascii=False))
