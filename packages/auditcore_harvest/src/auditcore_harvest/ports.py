"""Ports the consumer (or a test) provides: transport, credentials, state, sink, time, events.

The core owns no network client, database, ORM, tenant context or scheduler.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from .model import Checkpoint, HarvestRecord, SinkReceipt


@dataclass(frozen=True)
class Response:
    """Transport-neutral response."""

    status: int
    body: bytes
    headers: Mapping[str, str] = field(default_factory=dict)
    url: str = ""

    def header(self, name: str) -> str | None:
        """Case-insensitive header lookup."""
        wanted = name.lower()
        for key, value in self.headers.items():
            if key.lower() == wanted:
                return value
        return None

    def text(self, encoding: str = "utf-8") -> str:
        """Decoded body; undecodable bytes are replaced, never raise."""
        return self.body.decode(encoding, errors="replace")


@runtime_checkable
class Transport(Protocol):
    """Performs exactly one request; retries and paging belong to the engine."""

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
        data: bytes | None = None,
        timeout: float,
    ) -> Response:
        """Return the response or raise :class:`~auditcore_harvest.errors.TransportError`."""
        ...


@runtime_checkable
class CredentialProvider(Protocol):
    """Supplies secrets by source and name; the core never stores or logs them."""

    def get(self, source_id: str, name: str) -> str | None:
        """Secret value or ``None`` if not configured."""
        ...


@runtime_checkable
class StateStore(Protocol):
    """Persists checkpoints with compare-and-set semantics."""

    def load(self, source_id: str) -> Checkpoint | None:
        """Last confirmed checkpoint or ``None``."""
        ...

    def save(self, checkpoint: Checkpoint, expected: Checkpoint | None) -> None:
        """Store if the current value equals ``expected``; else raise ``CheckpointConflict``."""
        ...


@runtime_checkable
class Sink(Protocol):
    """Receives records; must be idempotent per ``(source_id, record_id, content_hash)``."""

    def deliver(self, records: Sequence[HarvestRecord], *, run_id: str, page: int) -> SinkReceipt:
        """Process the batch and confirm every record as accepted or duplicate."""
        ...


@runtime_checkable
class Clock(Protocol):
    """Time source for timestamps, deadlines and rate limiting."""

    def now(self) -> datetime:
        """Timezone-aware current time."""
        ...

    def monotonic(self) -> float:
        """Monotonic seconds for intervals."""
        ...


@runtime_checkable
class Sleeper(Protocol):
    """Waiting is injectable so tests and schedulers stay deterministic."""

    def sleep(self, seconds: float) -> None:
        """Block for ``seconds``."""
        ...


@runtime_checkable
class EventSink(Protocol):
    """Receives bounded, secret-free run events."""

    def emit(self, event: Mapping[str, Any]) -> None:
        """Handle one event."""
        ...
