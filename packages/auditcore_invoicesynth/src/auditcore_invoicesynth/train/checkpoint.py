"""Atomare, geprüfte Checkpoints (Plan 2c „Strom-/Wiederaufnahmefestigkeit“).

Ablauf je Checkpoint: in ``checkpoint-<Schritt>.tmp/`` schreiben, jede Datei
mit ``fsync``, ``CHECKSUMS.sha256`` und ``meta.json`` anlegen, Verzeichnis
synchronisieren, dann atomar in ``checkpoint-<Schritt>/`` umbenennen. Beim Start
wird der **neueste vollständige** Checkpoint mit gültigen Prüfsummen gewählt;
unvollständige oder beschädigte Verzeichnisse werden nach ``rejected/``
verschoben (Nachweis), nicht gelöscht. Lauf-ID, Datensatz-Hash und
Konfigurations-Hash müssen beim Wiederaufnehmen übereinstimmen.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from auditcore_common.hashing import sha256_file

CHECKSUMS = "CHECKSUMS.sha256"
META = "meta.json"
_NAME = re.compile(r"checkpoint-(\d{8})")


class ResumeMismatch(ValueError):
    """Checkpoint gehört zu einem anderen Lauf, Datensatz oder einer anderen Konfiguration."""


@dataclass(frozen=True)
class Checkpoint:
    step: int
    path: Path
    meta: dict[str, Any]


def _fsync_file(path: Path) -> None:
    with path.open("rb") as handle:
        os.fsync(handle.fileno())


def _fsync_dir(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _files(directory: Path) -> list[Path]:
    return sorted(p for p in directory.rglob("*") if p.is_file() and p.name != CHECKSUMS)


class CheckpointPolicy:
    """Checkpoint alle ``every_steps`` Optimiererschritte **oder** ``every_seconds``."""

    def __init__(
        self, every_steps: int, every_seconds: float, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self.every_steps = every_steps
        self.every_seconds = every_seconds
        self.clock = clock
        self.last = clock()

    def due(self, step: int) -> bool:
        return step % self.every_steps == 0 or self.clock() - self.last >= self.every_seconds

    def saved(self) -> None:
        self.last = self.clock()


class CheckpointManager:
    def __init__(
        self,
        run_dir: Path,
        *,
        run_id: str,
        dataset_hash: str,
        config_hash: str,
        save_total_limit: int = 3,
    ) -> None:
        self.run_dir = Path(run_dir)
        self.run_id = run_id
        self.dataset_hash = dataset_hash
        self.config_hash = config_hash
        self.save_total_limit = save_total_limit
        self.run_dir.mkdir(parents=True, exist_ok=True)

    @property
    def rejected_dir(self) -> Path:
        return self.run_dir / "rejected"

    def _reject(self, path: Path, reason: str) -> None:
        self.rejected_dir.mkdir(exist_ok=True)
        target = self.rejected_dir / path.name
        number = 1
        while target.exists():
            target = self.rejected_dir / f"{path.name}.{number}"
            number += 1
        shutil.move(str(path), target)
        (target.parent / (target.name + ".reason")).write_text(reason + "\n", encoding="utf-8")

    def identity(self) -> dict[str, str]:
        return {
            "run_id": self.run_id,
            "dataset_hash": self.dataset_hash,
            "config_hash": self.config_hash,
        }

    def save(self, step: int, write: Callable[[Path], None], state: dict[str, Any]) -> Path:
        """``write`` legt die Zustandsdateien im temporären Verzeichnis ab."""
        final = self.run_dir / f"checkpoint-{step:08d}"
        temporary = final.with_name(final.name + ".tmp")
        if temporary.exists():
            self._reject(temporary, "unvollständiger Checkpoint vor erneutem Schreiben")
        temporary.mkdir()
        write(temporary)
        meta = {**self.identity(), "step": step, "state": state}
        (temporary / META).write_text(json.dumps(meta, sort_keys=True, indent=2) + "\n")
        lines = []
        for path in _files(temporary):
            _fsync_file(path)
            lines.append(f"{sha256_file(path)}  {path.relative_to(temporary).as_posix()}\n")
        (temporary / CHECKSUMS).write_text("".join(lines), encoding="utf-8")
        _fsync_file(temporary / CHECKSUMS)
        _fsync_dir(temporary)
        if final.exists():
            self._reject(final, "älterer Checkpoint gleicher Nummer ersetzt")
        os.replace(temporary, final)
        _fsync_dir(self.run_dir)
        self._prune()
        return final

    def _complete(self) -> list[tuple[int, Path]]:
        found = []
        for path in self.run_dir.iterdir():
            match = _NAME.fullmatch(path.name)
            if match and path.is_dir():
                found.append((int(match[1]), path))
        return sorted(found)

    def _prune(self) -> None:
        complete = self._complete()
        for _, path in complete[: max(0, len(complete) - self.save_total_limit)]:
            shutil.rmtree(path)

    @staticmethod
    def verify(path: Path) -> str | None:
        """Fehlerbeschreibung oder ``None`` bei gültigen Prüfsummen."""
        listing = path / CHECKSUMS
        if not listing.is_file() or not (path / META).is_file():
            return "Prüfsummen- oder Metadatei fehlt"
        expected = {}
        for line in listing.read_text(encoding="utf-8").splitlines():
            digest, _, name = line.partition("  ")
            expected[name] = digest
        actual = {p.relative_to(path).as_posix(): sha256_file(p) for p in _files(path)}
        if expected != actual:
            return "Prüfsummen stimmen nicht"
        return None

    def latest(self) -> Checkpoint | None:
        """Neuester vollständiger, gültiger Checkpoint dieses Laufs (sonst ``None``)."""
        for path in sorted(self.run_dir.glob("checkpoint-*.tmp")):
            self._reject(path, "unvollständig (Abbruch während des Schreibens)")
        for step, path in reversed(self._complete()):
            problem = self.verify(path)
            if problem is not None:
                self._reject(path, problem)
                continue
            meta = json.loads((path / META).read_text(encoding="utf-8"))
            for key, value in self.identity().items():
                if meta.get(key) != value:
                    raise ResumeMismatch(f"{key} des Checkpoints {path.name} passt nicht zum Lauf")
            return Checkpoint(step, path, meta)
        return None
