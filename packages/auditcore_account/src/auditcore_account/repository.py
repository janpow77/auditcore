"""Transaktionsport und threadsichere Referenzablage für Tests und Einbettung."""

from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager
from copy import deepcopy
from dataclasses import dataclass, field
from threading import RLock
from typing import Protocol

from .models import Account, Asset, Event, Grant, Membership, Role, Settings, Tenant


@dataclass
class State:
    accounts: dict[str, Account] = field(default_factory=dict)
    tenants: dict[str, Tenant] = field(default_factory=dict)
    memberships: dict[str, Membership] = field(default_factory=dict)
    roles: dict[str, Role] = field(default_factory=dict)
    settings: dict[tuple[str, str], Settings] = field(default_factory=dict)
    grants: dict[str, Grant] = field(default_factory=dict)
    assets: dict[str, Asset] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)


class Repository(Protocol):
    """Adapter sichert atomaren Commit, Rollback und serialisierte konkurrierende Zugriffe."""

    def transaction(self) -> AbstractContextManager[State]: ...


class MemoryRepository:
    """Flüchtige Referenz; keine produktive Datenbank und kein impliziter Dateizugriff."""

    def __init__(self) -> None:
        self._state = State()
        self._lock = RLock()

    @contextmanager
    def transaction(self) -> Iterator[State]:
        with self._lock:
            draft = deepcopy(self._state)
            yield draft
            self._state = deepcopy(draft)

    def snapshot(self) -> State:
        with self._lock:
            return deepcopy(self._state)
