"""Transactional ast-grep and LibCST codemods guarded by auditcore-refactor."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


class CodemodError(RuntimeError):
    """A codemod was unsafe, failed, or could not be verified."""


@dataclass(frozen=True)
class CodemodResult:
    """Result of one verified codemod execution."""

    engine: str
    recipe: str
    changed_files: tuple[str, ...]
    verification: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return {
            "status": "VERIFIED",
            "engine": self.engine,
            "recipe": self.recipe,
            "changed_files": list(self.changed_files),
            "verification": self.verification,
        }


def _run(command: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=900, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise CodemodError(f"Befehl nicht ausführbar: {command[0]}") from error


def _tracked_state(root: Path) -> list[str]:
    process = _run(["git", "status", "--porcelain", "--untracked-files=all"], root)
    if process.returncode:
        raise CodemodError("Git-Status konnte nicht gelesen werden")
    return [line[3:] for line in process.stdout.splitlines() if len(line) > 3]


def _copy_repository(root: Path, target: Path) -> None:
    def ignore(_directory: str, names: list[str]) -> set[str]:
        excluded = {
            ".git",
            ".auditcore",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            ".venv",
            "__pycache__",
            "build",
            "dist",
            "node_modules",
            "venv",
        }
        return {name for name in names if name in excluded or name.endswith(".egg-info")}

    shutil.copytree(root, target, ignore=ignore, dirs_exist_ok=True, symlinks=True)


def _changed_files(root: Path, transformed: Path) -> tuple[str, ...]:
    command = ["git", "diff", "--no-index", "--name-only", "--", str(root), str(transformed)]
    process = subprocess.run(command, capture_output=True, text=True, check=False)
    if process.returncode not in (0, 1):
        raise CodemodError("Codemod-Änderungen konnten nicht bestimmt werden")
    prefix = str(transformed) + os.sep
    return tuple(sorted(line[len(prefix) :] for line in process.stdout.splitlines() if line.startswith(prefix)))


def _apply_verified(root: Path, transformed: Path, changed: tuple[str, ...]) -> None:
    for relative in changed:
        source, target = transformed / relative, root / relative
        if source.is_symlink():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.unlink(missing_ok=True)
            target.symlink_to(os.readlink(source))
        elif source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        elif target.exists():
            target.unlink()


def _verification(transformed: Path) -> dict[str, object]:
    process = _run(["auditcore-refactor", "verify", str(transformed)], transformed)
    try:
        result = json.loads(process.stdout)
    except json.JSONDecodeError as error:
        raise CodemodError("auditcore-refactor verify lieferte kein JSON") from error
    if process.returncode or not isinstance(result, dict) or result.get("status") != "PASS":
        raise CodemodError("auditcore-refactor verify hat die Codemod-Änderung blockiert")
    return result


def run(engine: str, recipe: str, repository: Path) -> CodemodResult:
    """Run a codemod in a copy and publish its changes only after verification."""
    root = repository.resolve()
    if not (root / ".git").exists() and _run(["git", "rev-parse", "--git-dir"], root).returncode:
        raise CodemodError("Codemods benötigen ein Git-Repository")
    dirty = _tracked_state(root)
    if dirty:
        raise CodemodError("Arbeitsbaum ist nicht sauber: " + ", ".join(dirty[:5]))
    verification_config = root / "auditcore-verification.json"
    if not verification_config.is_file():
        raise CodemodError("auditcore-verification.json fehlt")

    recipe_path = Path(recipe)
    if engine == "ast-grep":
        rule = recipe_path if recipe_path.is_absolute() else root / recipe_path
        if not rule.is_file() or not rule.resolve().is_relative_to(root):
            raise CodemodError("ast-grep-Regel muss eine Datei im Repository sein")
        relative_recipe = rule.resolve().relative_to(root).as_posix()
        command = ["ast-grep", "scan", "--rule", relative_recipe, "--update-all", "."]
    elif engine == "libcst":
        if not recipe or any(part.startswith("_") for part in recipe.split(".")):
            raise CodemodError("Ungültiges LibCST-Codemod-Modul")
        relative_recipe = recipe
        command = ["python", "-m", "libcst.tool", "codemod", recipe, "."]
    else:
        raise CodemodError(f"Unbekannte Codemod-Engine: {engine}")

    with tempfile.TemporaryDirectory(prefix="auditcore-codemod-") as temporary:
        transformed = Path(temporary) / "repository"
        _copy_repository(root, transformed)
        process = _run(command, transformed)
        if process.returncode:
            raise CodemodError(f"{engine} fehlgeschlagen (Exit {process.returncode})")
        changed = _changed_files(root, transformed)
        if not changed:
            raise CodemodError("Codemod hat keine Dateien geändert")
        verification = _verification(transformed)
        _apply_verified(root, transformed, changed)
    return CodemodResult(engine, relative_recipe, changed, verification)
