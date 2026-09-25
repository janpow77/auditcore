"""Storage protocol of the review log; the library ships only an in-memory store.

The log is append-only. A run is written once; every decision, second review
and the creation itself are events with a run-wide sequence number. The
review state is derived from the events, never stored beside them, so the
log is the single source of truth. Persistent stores (database, files,
document store) are the consumer's; they implement :class:`ReviewStore`,
including the compare-and-append of :meth:`ReviewStore.append`, which is
what makes concurrent reviewers safe.
"""

from __future__ import annotations

import threading
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol, TypedDict

from ._types import ActorView, RunRequestRecord, RunResultRecord


class SequenceConflict(Exception):
    """The log of a run changed since the caller read it."""

    def __init__(self, expected: int, actual: int) -> None:
        super().__init__(f"expected sequence {expected}, found {actual}")
        self.expected = expected
        self.actual = actual


class EventView(TypedDict):
    """JSON view of a log entry."""

    run_id: str
    sequence: int
    type: str
    at: str
    actor: ActorView
    hit_id: str | None
    data: dict[str, object]


@dataclass(frozen=True)
class ReviewEvent:
    """One entry of the review log (Protokoll)."""

    run_id: str
    sequence: int
    type: str
    at: str
    actor: ActorView
    hit_id: str | None = None
    data: Mapping[str, object] = field(default_factory=dict)

    def to_dict(self) -> EventView:
        """JSON view."""
        return {
            "run_id": self.run_id,
            "sequence": self.sequence,
            "type": self.type,
            "at": self.at,
            "actor": {"id": self.actor["id"], "display_name": self.actor["display_name"]},
            "hit_id": self.hit_id,
            "data": dict(self.data),
        }


@dataclass(frozen=True)
class StoredRun:
    """A screening run as written once: request, result views and metadata."""

    run_id: str
    created_at: str
    created_by: ActorView
    kind: str
    request: RunRequestRecord
    result: RunResultRecord


class ReviewStore(Protocol):
    """What the review service needs from a persistent store."""

    def add_run(self, run: StoredRun, first_event: ReviewEvent) -> None:
        """Store a new run together with its creation event (sequence 1)."""
        ...

    def get_run(self, run_id: str) -> StoredRun | None:
        """The run, or ``None`` if unknown (or not visible to the consumer's caller)."""
        ...

    def list_runs(self) -> Sequence[StoredRun]:
        """All visible runs, newest first."""
        ...

    def events(self, run_id: str) -> Sequence[ReviewEvent]:
        """Events of a run in sequence order."""
        ...

    def append(self, event: ReviewEvent, *, expected_sequence: int) -> None:
        """Append atomically if the run's last sequence equals ``expected_sequence``.

        Raise :class:`SequenceConflict` otherwise. ``event.sequence`` is
        ``expected_sequence + 1``.
        """
        ...


class InMemoryReviewStore:
    """Thread-safe store for tests, demos and single-process use; nothing persists."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._runs: dict[str, StoredRun] = {}
        self._events: dict[str, list[ReviewEvent]] = {}

    def add_run(self, run: StoredRun, first_event: ReviewEvent) -> None:
        """Store a new run; a duplicate id is a programming error."""
        with self._lock:
            if run.run_id in self._runs:
                raise ValueError(f"Prüflauf {run.run_id} existiert bereits.")
            self._runs[run.run_id] = run
            self._events[run.run_id] = [first_event]

    def get_run(self, run_id: str) -> StoredRun | None:
        """The run or ``None``."""
        with self._lock:
            return self._runs.get(run_id)

    def list_runs(self) -> Sequence[StoredRun]:
        """Runs, newest first."""
        with self._lock:
            return sorted(self._runs.values(), key=lambda r: r.created_at, reverse=True)

    def events(self, run_id: str) -> Sequence[ReviewEvent]:
        """A copy of the events of the run."""
        with self._lock:
            return tuple(self._events.get(run_id, ()))

    def append(self, event: ReviewEvent, *, expected_sequence: int) -> None:
        """Compare-and-append under the store lock."""
        with self._lock:
            log = self._events.get(event.run_id)
            if log is None:
                raise KeyError(event.run_id)
            actual = log[-1].sequence if log else 0
            if actual != expected_sequence or event.sequence != expected_sequence + 1:
                raise SequenceConflict(expected_sequence, actual)
            log.append(event)
