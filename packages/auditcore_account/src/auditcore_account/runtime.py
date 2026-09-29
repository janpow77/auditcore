"""Gemeinsame Laufzeit: injizierbare Uhr, Revision und Ereignisse ohne Feldwerte."""

from collections.abc import Callable
from datetime import UTC, datetime

from .errors import require
from .models import Actor, Event
from .repository import Repository, State


class Runtime:
    def __init__(self, repository: Repository, clock: Callable[[], datetime] | None = None) -> None:
        self.repository = repository
        self.clock = clock or (lambda: datetime.now(UTC))

    def now(self) -> datetime:
        value = self.clock()
        require(value.tzinfo is not None, "invalid_clock", "Zeitzone der Uhr erforderlich.")
        return value

    def event(
        self,
        state: State,
        actor: Actor,
        operation: str,
        target: str,
        tenant: str = "",
        fields: tuple[str, ...] = (),
    ) -> None:
        state.events.append(Event(actor.account_id, tenant, operation, target, fields, self.now()))


def revision(actual: int, expected: int) -> None:
    require(actual == expected, "conflict", "Die Daten wurden inzwischen geändert.")
