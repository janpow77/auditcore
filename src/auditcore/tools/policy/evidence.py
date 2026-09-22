"""Bind policy records to actual artifact bytes and explicit applicability facts."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict
from pathlib import Path

from auditcore.tools.policy.models import ApplicabilityContext

_GENERATED_DIRECTORIES = {
    ".git",
    ".auditcore",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".tox",
    ".nox",
    "node_modules",
}
_ROOT_BUILD_DIRECTORIES = {"build", "dist"}
_GENERATED_FILES = {".coverage", "coverage.xml", "coverage.json"}


def _unreadable_directory(error: OSError) -> None:
    raise error


def artifact_source_digest(root: Path) -> str:
    """Hash all artifact files, including resources/config; exclude generated state.

    Evidence and logs belong under .auditcore. Symlinked directories and external
    file links are rejected; internal file links include their target bytes.
    """
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Artifact root must be an existing nonsymlink directory")
    root = root.resolve()
    rows: list[tuple[str, str]] = []
    for directory, names, filenames in os.walk(
        root, followlinks=False, onerror=_unreadable_directory
    ):
        parent = Path(directory)
        names[:] = sorted(
            name
            for name in names
            if name not in _GENERATED_DIRECTORIES
            and not name.endswith(".egg-info")
            and not (parent == root and name in _ROOT_BUILD_DIRECTORIES)
        )
        for name in names:
            if (parent / name).is_symlink():
                raise ValueError("Artifact source contains a symlinked directory")
        for name in sorted(filenames):
            if name in _GENERATED_FILES or name.endswith((".pyc", ".pyo")):
                continue
            path = parent / name
            if path.is_symlink() and not path.resolve().is_relative_to(root):
                raise ValueError("Artifact source contains an external symlinked file")
            if not path.is_file():
                raise ValueError("Artifact source contains a nonregular file")
            rows.append(
                (path.relative_to(root).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest())
            )
    if not rows:
        raise ValueError("Artifact contains no reviewable files")
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def evidence_binding(root: Path, artifact: str, context: ApplicabilityContext) -> dict[str, str]:
    """Return identity/digests only; this helper never certifies a requirement."""
    if not artifact or artifact == "UNKNOWN":
        raise ValueError("Evidence requires an explicit artifact identity")
    context_bytes = json.dumps(
        asdict(context), sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode()
    return {
        "artifact": artifact,
        "artifact_source_digest": artifact_source_digest(root),
        "context_digest": hashlib.sha256(context_bytes).hexdigest(),
    }
