"""Reference implementations of the ports for tests, replays and simple consumers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from .errors import CheckpointConflict
from .model import JSON, Checkpoint, HarvestRecord, SinkReceipt


@dataclass
class MemoryStateStore:
    """Compare-and-set checkpoint store in memory."""

    checkpoints: dict[str, Checkpoint] = field(default_factory=dict)

    def load(self, source_id: str) -> Checkpoint | None:
        """Stored checkpoint or ``None``."""
        return self.checkpoints.get(source_id)

    def save(self, checkpoint: Checkpoint, expected: Checkpoint | None) -> None:
        """Store only if the current value is ``expected``."""
        if self.checkpoints.get(checkpoint.source_id) != expected:
            raise CheckpointConflict("Checkpoint wurde parallel geändert.")
        self.checkpoints[checkpoint.source_id] = checkpoint


@dataclass
class ListSink:
    """Idempotent in-memory sink keyed by ``(source_id, record_id)``.

    ``fail_on_page`` simulates a storage failure for contract tests.
    """

    records: dict[tuple[str, str], HarvestRecord] = field(default_factory=dict)
    deliveries: int = 0
    fail_on_page: int | None = None

    def deliver(self, records: Sequence[HarvestRecord], *, run_id: str, page: int) -> SinkReceipt:
        """Store new or changed records; unchanged ones are duplicates."""
        self.deliveries += 1
        if self.fail_on_page is not None and page == self.fail_on_page:
            self.fail_on_page = None
            raise OSError("simulierter Speicherfehler")
        accepted: list[tuple[str, str]] = []
        duplicates: list[tuple[str, str]] = []
        for record in records:
            stored = self.records.get(record.key)
            if stored is not None and stored.content_hash == record.content_hash:
                duplicates.append(record.key)
            else:
                self.records[record.key] = record
                accepted.append(record.key)
        return SinkReceipt(tuple(accepted), tuple(duplicates))


@dataclass
class FixedClock:
    """Deterministic clock; ``monotonic`` follows slept time."""

    current: datetime = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)
    elapsed: float = 0.0

    def now(self) -> datetime:
        """Current fixed time."""
        return self.current + timedelta(seconds=self.elapsed)

    def monotonic(self) -> float:
        """Seconds since start."""
        return self.elapsed


@dataclass
class ClockSleeper:
    """Advances a :class:`FixedClock` instead of waiting; records every sleep."""

    clock: FixedClock
    sleeps: list[float] = field(default_factory=list)

    def sleep(self, seconds: float) -> None:
        """Record and advance time."""
        self.sleeps.append(seconds)
        self.clock.elapsed += seconds


@dataclass
class StaticCredentials:
    """Credentials from a mapping ``{(source_id, name): value}``."""

    values: Mapping[tuple[str, str], str] = field(default_factory=dict)

    def get(self, source_id: str, name: str) -> str | None:
        """Configured value or ``None``."""
        return self.values.get((source_id, name))


@dataclass
class ListEvents:
    """Collects events; asserts in tests that no secret leaks."""

    events: list[Mapping[str, JSON]] = field(default_factory=list)

    def emit(self, event: Mapping[str, JSON]) -> None:
        """Store the event."""
        self.events.append(dict(event))
