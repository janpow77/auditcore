"""Storage port with an in-memory and a file-system implementation.

``save`` takes the version the caller loaded (``expected_version``; None for a
new board) and fails with ``VERSION_CONFLICT`` if someone else saved meanwhile.
"""

from __future__ import annotations

import os
import re
import tempfile
import threading
from pathlib import Path
from typing import Protocol

from .errors import KanbanError
from .model import Board
from .serialization import dumps, loads

BOARD_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$"
_BOARD_ID_RE = re.compile(BOARD_ID_PATTERN)


def check_board_id(board_id: str) -> str:
    """Board ids are file-name safe (no path separators, no dots)."""
    if not _BOARD_ID_RE.match(board_id):
        raise KanbanError("VALIDATION_ERROR", "Ungültige Board-ID")
    return board_id


def _conflict() -> KanbanError:
    return KanbanError("VERSION_CONFLICT", "Das Board wurde inzwischen geändert")


class BoardStore(Protocol):
    def get(self, board_id: str) -> Board | None: ...

    def save(self, board: Board, expected_version: int | None) -> None: ...

    def list(self) -> list[Board]: ...

    def delete(self, board_id: str) -> bool: ...


def _check_version(current: Board | None, expected_version: int | None) -> None:
    if current is None and expected_version is not None:
        raise _conflict()
    if current is not None and current.version != expected_version:
        raise _conflict()


class InMemoryBoardStore:
    """Thread-safe store for tests, demos and single-process consumers."""

    def __init__(self) -> None:
        self._boards: dict[str, Board] = {}
        self._lock = threading.Lock()

    def get(self, board_id: str) -> Board | None:
        return self._boards.get(board_id)

    def save(self, board: Board, expected_version: int | None) -> None:
        with self._lock:
            _check_version(self._boards.get(board.id), expected_version)
            self._boards[board.id] = board

    def list(self) -> list[Board]:
        return list(self._boards.values())

    def delete(self, board_id: str) -> bool:
        with self._lock:
            return self._boards.pop(board_id, None) is not None


class FileSystemBoardStore:
    """One JSON document per board in ``root``; writes are atomic (temp file + rename)."""

    def __init__(self, root: Path) -> None:
        self.root = root
        root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _path(self, board_id: str) -> Path:
        return self.root / f"{check_board_id(board_id)}.json"

    def get(self, board_id: str) -> Board | None:
        path = self._path(board_id)
        if not path.is_file():
            return None
        return loads(path.read_text(encoding="utf-8"))

    def save(self, board: Board, expected_version: int | None) -> None:
        path = self._path(board.id)
        with self._lock:
            _check_version(self.get(board.id), expected_version)
            handle, temporary = tempfile.mkstemp(dir=self.root, prefix=".tmp-", suffix=".json")
            try:
                with os.fdopen(handle, "w", encoding="utf-8") as stream:
                    stream.write(dumps(board) + "\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, path)
            except BaseException:
                Path(temporary).unlink(missing_ok=True)
                raise

    def list(self) -> list[Board]:
        return [loads(p.read_text(encoding="utf-8")) for p in sorted(self.root.glob("*.json"))
                if not p.name.startswith(".")]

    def delete(self, board_id: str) -> bool:
        path = self._path(board_id)
        with self._lock:
            if not path.is_file():
                return False
            path.unlink()
            return True
