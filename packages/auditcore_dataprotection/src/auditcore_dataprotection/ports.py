"""Interfaces the consumer application implements.

The library contains no database, session, HTTP or identity code. Consumers
provide persistence (inside their own transaction), authorization, audit
storage, time and identifier generation through these protocols. Reference
in-memory implementations live in :mod:`auditcore_dataprotection.memory`.

Repository contract, verified by ``tests/test_ports_contract.py``:

* every read and write is scoped by ``tenant_id``; an object of another
  tenant must behave as if it did not exist;
* ``replace`` compares the stored ``revision`` with ``expected_revision`` and
  raises :class:`~auditcore_dataprotection.errors.StaleRevisionError` on
  mismatch; it refuses any change to a locked (released/superseded) record
  with :class:`~auditcore_dataprotection.errors.LockedVersionError`;
* ``mark_superseded`` is the only allowed change of a released record.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol, runtime_checkable

from .model import Actor, Assessment, AuditEvent, Permission, RegisterVersion


@runtime_checkable
class Authorizer(Protocol):
    """Decides whether an actor may perform an operation in a tenant."""

    def authorize(self, actor: Actor, permission: Permission, tenant_id: str) -> bool:
        """True if the actor may perform the operation inside the tenant."""
        ...


@runtime_checkable
class AuditSink(Protocol):
    """Persists audit events."""

    def record(self, event: AuditEvent) -> None:
        """Persist an audit event in the same transaction as the change."""
        ...


@runtime_checkable
class Clock(Protocol):
    """Source of the current time."""

    def now(self) -> datetime:
        """Timezone-aware current time."""
        ...


@runtime_checkable
class IdFactory(Protocol):
    """Generates unique identifiers."""

    def new_id(self, kind: str) -> str:
        """Unique identifier for ``"activity"`` or ``"assessment"``."""
        ...


@runtime_checkable
class RegisterRepository(Protocol):
    """Tenant-scoped storage of register versions."""

    def get_draft(self, tenant_id: str, register_id: str) -> RegisterVersion | None:
        """Open draft of the register, if any."""
        ...

    def get_released(self, tenant_id: str, register_id: str) -> RegisterVersion | None:
        """Currently released version, if any."""
        ...

    def list_versions(self, tenant_id: str, register_id: str) -> Sequence[RegisterVersion]:
        """All versions, newest first."""
        ...

    def add(self, version: RegisterVersion) -> None:
        """Store a new version."""
        ...

    def replace(self, version: RegisterVersion, expected_revision: int) -> None:
        """Replace a draft; raises on stale revision or locked record."""
        ...

    def mark_superseded(
        self, tenant_id: str, register_id: str, version: int, expected_revision: int
    ) -> None:
        """Mark a released version as superseded."""
        ...


@runtime_checkable
class AssessmentRepository(Protocol):
    """Tenant-scoped storage of assessment versions."""

    def get(self, tenant_id: str, assessment_id: str) -> Assessment | None:
        """Assessment of the tenant or None."""
        ...

    def list_for_activity(
        self, tenant_id: str, register_id: str, activity_id: str
    ) -> Sequence[Assessment]:
        """All versions of one activity's assessments, newest first."""
        ...

    def list_for_register(self, tenant_id: str, register_id: str) -> Sequence[Assessment]:
        """All assessments of one register."""
        ...

    def add(self, assessment: Assessment) -> None:
        """Store a new assessment."""
        ...

    def replace(self, assessment: Assessment, expected_revision: int) -> None:
        """Replace an open assessment; raises on stale revision or locked record."""
        ...

    def mark_superseded(self, tenant_id: str, assessment_id: str, expected_revision: int) -> None:
        """Mark a released assessment as superseded."""
        ...
