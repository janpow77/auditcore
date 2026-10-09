"""In-memory reference adapters for transfers, operational decisions and the central register.

Tenant-scoped like :mod:`.memory`; for tests and single-process consumers.
:class:`FakeCentralRegister` answers deterministically and never opens a
network connection.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from .central_register import (
    RECEIPT_CONFLICT,
    RECEIPT_TAKEN_OVER,
    Receipt,
    TransferRecord,
)
from .operation_model import OperationalDecision


class InMemoryTransferRepository:
    """Transfer records keyed by tenant and version key."""

    def __init__(self) -> None:
        self._data: dict[str, dict[str, TransferRecord]] = {}

    def get(self, tenant_id: str, key: str) -> TransferRecord | None:
        """Record of one version key or None."""
        return self._data.get(tenant_id, {}).get(key)

    def put(self, record: TransferRecord) -> None:
        """Insert or replace the record of its key."""
        self._data.setdefault(record.tenant_id, {})[record.key] = record

    def latest(self, tenant_id: str, register_id: str) -> TransferRecord | None:
        """Record of the highest version of a register."""
        found = [r for r in self._data.get(tenant_id, {}).values() if r.register_id == register_id]
        return max(found, key=lambda r: r.version, default=None)


class InMemoryOperationRepository:
    """Append-only operational decisions."""

    def __init__(self) -> None:
        self._data: list[OperationalDecision] = []

    def add(self, decision: OperationalDecision) -> None:
        """Store a decision."""
        self._data.append(decision)

    def list_for_activity(
        self, tenant_id: str, register_id: str, activity_id: str
    ) -> Sequence[OperationalDecision]:
        """Decisions of one activity of the tenant, newest first."""
        found = [
            d
            for d in self._data
            if d.tenant_id == tenant_id
            and d.register_id == register_id
            and d.activity_id == activity_id
        ]
        return list(reversed(found))


@dataclass
class FakeCentralRegister:
    """Deterministic central register: one entry per key, optional conflict or silence."""

    answer: str = RECEIPT_TAKEN_OVER
    entries: dict[str, Mapping[str, object]] = field(default_factory=dict)
    calls: int = 0

    def submit(self, key: str, payload: Mapping[str, object]) -> Receipt:
        """Store the payload once per key and answer with the configured receipt."""
        self.calls += 1
        if self.answer == RECEIPT_CONFLICT:
            return Receipt(RECEIPT_CONFLICT, message="Abweichender Eintrag im Hausverzeichnis.")
        self.entries.setdefault(key, payload)
        central_id = f"HV-{list(self.entries).index(key) + 1:05d}"
        if self.answer == RECEIPT_TAKEN_OVER:
            return Receipt(RECEIPT_TAKEN_OVER, central_id=central_id)
        return Receipt(self.answer)
