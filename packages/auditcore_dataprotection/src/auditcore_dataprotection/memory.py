"""In-memory reference adapters for tests and simple single-process consumers.

They implement the repository contract of :mod:`auditcore_dataprotection.ports`
literally: tenant-scoped storage, revision checks, refusal to change locked
records and ``mark_superseded`` as the only change of a released record.
They are not transactional and not persistent; production consumers provide
database adapters that enforce the same rules (ideally also in the database).
"""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta

from .errors import ConflictError, LockedVersionError, NotFoundError, StaleRevisionError
from .model import (
    Actor,
    Assessment,
    AssessmentStatus,
    AuditEvent,
    Permission,
    RegisterStatus,
    RegisterVersion,
)


class InMemoryRegisterRepository:
    """Register versions keyed by ``(tenant_id, register_id, version)``."""

    def __init__(self) -> None:
        self._data: dict[str, dict[tuple[str, int], RegisterVersion]] = {}

    def _tenant(self, tenant_id: str) -> dict[tuple[str, int], RegisterVersion]:
        return self._data.setdefault(tenant_id, {})

    def get_draft(self, tenant_id: str, register_id: str) -> RegisterVersion | None:
        """Open draft of the register, if any."""
        for version in self.list_versions(tenant_id, register_id):
            if version.status is RegisterStatus.DRAFT:
                return version
        return None

    def get_released(self, tenant_id: str, register_id: str) -> RegisterVersion | None:
        """Currently released version, if any."""
        for version in self.list_versions(tenant_id, register_id):
            if version.status is RegisterStatus.RELEASED:
                return version
        return None

    def list_versions(self, tenant_id: str, register_id: str) -> Sequence[RegisterVersion]:
        """All versions, newest first."""
        found = [
            copy.deepcopy(v)
            for (rid, _), v in self._data.get(tenant_id, {}).items()
            if rid == register_id
        ]
        return sorted(found, key=lambda v: v.version, reverse=True)

    def add(self, version: RegisterVersion) -> None:
        """Store a new version; duplicates are a conflict."""
        store = self._tenant(version.tenant_id)
        key = (version.register_id, version.version)
        if key in store:
            raise ConflictError("Diese Fassung des Verzeichnisses existiert bereits.")
        if version.status is RegisterStatus.DRAFT and self.get_draft(
            version.tenant_id, version.register_id
        ):
            raise ConflictError("Es gibt bereits einen offenen Entwurf.")
        store[key] = copy.deepcopy(version)

    def replace(self, version: RegisterVersion, expected_revision: int) -> None:
        """Replace a draft after the revision check."""
        store = self._data.get(version.tenant_id, {})
        key = (version.register_id, version.version)
        current = store.get(key)
        if current is None:
            raise NotFoundError("Fassung des Verzeichnisses nicht gefunden")
        if current.revision != expected_revision:
            raise StaleRevisionError("Die Fassung wurde inzwischen geändert.")
        if current.locked:
            raise LockedVersionError(
                "Freigegebene Fassungen des Verzeichnisses sind unveränderlich."
            )
        if version.revision <= current.revision:
            raise StaleRevisionError("Die neue Revision muss größer sein.")
        store[key] = copy.deepcopy(version)

    def mark_superseded(
        self, tenant_id: str, register_id: str, version: int, expected_revision: int
    ) -> None:
        """Mark a released version as superseded."""
        store = self._data.get(tenant_id, {})
        current = store.get((register_id, version))
        if current is None:
            raise NotFoundError("Fassung des Verzeichnisses nicht gefunden")
        if current.revision != expected_revision:
            raise StaleRevisionError("Die Fassung wurde inzwischen geändert.")
        if current.status is not RegisterStatus.RELEASED:
            raise ConflictError("Nur eine freigegebene Fassung kann abgelöst werden.")
        store[(register_id, version)] = replace(
            current, status=RegisterStatus.SUPERSEDED, revision=current.revision + 1
        )


class InMemoryAssessmentRepository:
    """Assessments keyed by ``(tenant_id, assessment_id)``."""

    def __init__(self) -> None:
        self._data: dict[str, dict[str, Assessment]] = {}

    def get(self, tenant_id: str, assessment_id: str) -> Assessment | None:
        """Assessment of the tenant or None."""
        found = self._data.get(tenant_id, {}).get(assessment_id)
        return copy.deepcopy(found) if found is not None else None

    def list_for_activity(
        self, tenant_id: str, register_id: str, activity_id: str
    ) -> Sequence[Assessment]:
        """All versions of one activity, newest first."""
        found = [
            copy.deepcopy(a)
            for a in self._data.get(tenant_id, {}).values()
            if a.register_id == register_id and a.activity_id == activity_id
        ]
        return sorted(found, key=lambda a: a.version, reverse=True)

    def list_for_register(self, tenant_id: str, register_id: str) -> Sequence[Assessment]:
        """All assessments of one register."""
        found = [
            copy.deepcopy(a)
            for a in self._data.get(tenant_id, {}).values()
            if a.register_id == register_id
        ]
        return sorted(found, key=lambda a: (a.activity_id, -a.version))

    def add(self, assessment: Assessment) -> None:
        """Store a new assessment; duplicates are a conflict."""
        store = self._data.setdefault(assessment.tenant_id, {})
        if assessment.assessment_id in store:
            raise ConflictError("Diese Folgenabschätzung existiert bereits.")
        if any(
            a.register_id == assessment.register_id
            and a.activity_id == assessment.activity_id
            and a.version == assessment.version
            for a in store.values()
        ):
            raise ConflictError("Diese Fassung der Folgenabschätzung existiert bereits.")
        store[assessment.assessment_id] = copy.deepcopy(assessment)

    def replace(self, assessment: Assessment, expected_revision: int) -> None:
        """Replace an open assessment after the revision check."""
        store = self._data.get(assessment.tenant_id, {})
        current = store.get(assessment.assessment_id)
        if current is None:
            raise NotFoundError("Folgenabschätzung nicht gefunden")
        if current.revision != expected_revision:
            raise StaleRevisionError("Die Fassung wurde inzwischen geändert.")
        if current.locked:
            raise LockedVersionError("Freigegebene Fassungen sind unveränderlich.")
        if (
            assessment.activity_id != current.activity_id
            or assessment.register_id != current.register_id
            or assessment.version != current.version
        ):
            raise ConflictError("Tätigkeit, Verzeichnis und Fassungsnummer sind unveränderlich.")
        if assessment.revision <= current.revision:
            raise StaleRevisionError("Die neue Revision muss größer sein.")
        store[assessment.assessment_id] = copy.deepcopy(assessment)

    def mark_superseded(self, tenant_id: str, assessment_id: str, expected_revision: int) -> None:
        """Mark a released assessment as superseded."""
        store = self._data.get(tenant_id, {})
        current = store.get(assessment_id)
        if current is None:
            raise NotFoundError("Folgenabschätzung nicht gefunden")
        if current.revision != expected_revision:
            raise StaleRevisionError("Die Fassung wurde inzwischen geändert.")
        if current.status is not AssessmentStatus.RELEASED:
            raise ConflictError("Nur eine freigegebene Fassung kann abgelöst werden.")
        store[assessment_id] = replace(
            current, status=AssessmentStatus.SUPERSEDED, revision=current.revision + 1
        )


@dataclass
class ListAuditSink:
    """Collects audit events in memory."""

    events: list[AuditEvent] = field(default_factory=list)

    def record(self, event: AuditEvent) -> None:
        """Append the event."""
        self.events.append(event)

    def actions(self) -> list[str]:
        """Recorded action names in order."""
        return [e.action for e in self.events]


@dataclass
class FixedClock:
    """Deterministic clock; each call advances by ``step``."""

    start: datetime = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)
    step: timedelta = timedelta(minutes=1)

    def __post_init__(self) -> None:
        if self.start.tzinfo is None:
            raise ValueError("FixedClock benötigt eine zeitzonenbewusste Startzeit.")
        self._current = self.start

    def now(self) -> datetime:
        """Current time; advances by one step per call."""
        self._current = self._current + self.step
        return self._current


@dataclass
class SequentialIds:
    """Readable deterministic identifiers ``<prefix>-<kind>-<n>``."""

    prefix: str = "id"
    _counter: int = 0

    def new_id(self, kind: str) -> str:
        """Next sequential identifier for the kind."""
        self._counter += 1
        return f"{self.prefix}-{kind}-{self._counter}"


class RoleAuthorizer:
    """Tenant membership plus a role that grants the permission."""

    def __init__(self, role_permissions: Mapping[str, frozenset[Permission]]) -> None:
        self._roles = {role: frozenset(p) for role, p in role_permissions.items()}

    def authorize(self, actor: Actor, permission: Permission, tenant_id: str) -> bool:
        """Allow if the actor belongs to the tenant and holds a granting role."""
        if tenant_id not in actor.tenant_ids:
            return False
        return any(permission in self._roles.get(role, frozenset()) for role in actor.roles)


class DenyAllAuthorizer:
    """Refuses everything; a safe default for wiring errors."""

    def authorize(self, actor: Actor, permission: Permission, tenant_id: str) -> bool:
        """Deny every operation."""
        return False
