"""Append-only event log of board changes."""

from __future__ import annotations

import json
import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from .errors import JsonObject

Clock = Callable[[], str]


def utc_now() -> str:
    """Default clock: UTC ISO timestamp with seconds precision."""
    return datetime.now(UTC).isoformat(timespec="seconds")


@dataclass(frozen=True)
class Change:
    """What a command changed; the service turns it into a :class:`BoardEvent`."""

    kind: str
    card_id: str | None = None
    data: JsonObject = field(default_factory=dict)


@dataclass(frozen=True)
class BoardEvent:
    seq: int
    board_id: str
    version: int
    kind: str
    actor: str
    at: str
    card_id: str | None = None
    data: JsonObject = field(default_factory=dict)

    def to_json(self) -> JsonObject:
        return {
            "seq": self.seq,
            "board_id": self.board_id,
            "version": self.version,
            "kind": self.kind,
            "actor": self.actor,
            "at": self.at,
            "card_id": self.card_id,
            "data": self.data,
        }


class EventLog(Protocol):
    def record(
        self, board_id: str, version: int, actor: str, at: str, changes: Sequence[Change]
    ) -> tuple[BoardEvent, ...]: ...

    def since(self, board_id: str, seq: int = 0) -> tuple[BoardEvent, ...]: ...


class InMemoryEventLog:
    """Process-local log; sequence numbers are global and strictly increasing."""

    def __init__(self) -> None:
        self._events: list[BoardEvent] = []
        self._lock = threading.Lock()

    def record(
        self, board_id: str, version: int, actor: str, at: str, changes: Sequence[Change]
    ) -> tuple[BoardEvent, ...]:
        with self._lock:
            start = len(self._events)
            new = tuple(
                BoardEvent(start + i + 1, board_id, version, c.kind, actor, at, c.card_id, c.data)
                for i, c in enumerate(changes)
            )
            self._events.extend(new)
        return new

    def since(self, board_id: str, seq: int = 0) -> tuple[BoardEvent, ...]:
        return tuple(e for e in self._events if e.board_id == board_id and e.seq > seq)


class JsonLinesEventLog(InMemoryEventLog):
    """Log persisted as one JSON object per line (appended, never rewritten)."""

    def __init__(self, path: Path) -> None:
        super().__init__()
        self._path = path
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    self._events.append(_event_from_line(line))

    def record(
        self, board_id: str, version: int, actor: str, at: str, changes: Sequence[Change]
    ) -> tuple[BoardEvent, ...]:
        new = super().record(board_id, version, actor, at, changes)
        with self._path.open("a", encoding="utf-8") as handle:
            for event in new:
                handle.write(json.dumps(event.to_json(), ensure_ascii=False) + "\n")
        return new


def _event_from_line(line: str) -> BoardEvent:
    raw = json.loads(line)
    if not isinstance(raw, dict):
        raise ValueError("event line is not an object")
    data = raw.get("data")
    card_id = raw.get("card_id")
    return BoardEvent(
        seq=int(raw["seq"]),
        board_id=str(raw["board_id"]),
        version=int(raw["version"]),
        kind=str(raw["kind"]),
        actor=str(raw["actor"]),
        at=str(raw["at"]),
        card_id=None if card_id is None else str(card_id),
        data=data if isinstance(data, dict) else {},
    )
