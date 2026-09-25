"""Services behind the REST interface and the storage protocol they need.

The web module keeps no data itself. A consumer passes a :class:`Storage`
(register and assessment repositories plus the audit sink, see
:mod:`auditcore_dataprotection.ports`), its authorizer and the explicitly
chosen rule profile; :func:`create_backend` wires the library services.
:class:`InMemoryStorage` is only for demos, tests and single-process tools.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol, runtime_checkable

from ..assessment import AssessmentService
from ..memory import InMemoryAssessmentRepository, InMemoryRegisterRepository, ListAuditSink
from ..ports import (
    AssessmentRepository,
    AuditSink,
    Authorizer,
    Clock,
    IdFactory,
    RegisterRepository,
)
from ..register import RegisterService
from ..rules import RuleProfile


@runtime_checkable
class Storage(Protocol):
    """Persistence of the consumer: repositories and audit trail in one transaction scope."""

    @property
    def registers(self) -> RegisterRepository:
        """Tenant-scoped register versions."""
        ...

    @property
    def assessments(self) -> AssessmentRepository:
        """Tenant-scoped assessment versions."""
        ...

    @property
    def audit(self) -> AuditSink:
        """Audit events of every change."""
        ...


@dataclass
class InMemoryStorage:
    """Reference storage in memory; not persistent, not transactional."""

    registers: InMemoryRegisterRepository = field(default_factory=InMemoryRegisterRepository)
    assessments: InMemoryAssessmentRepository = field(default_factory=InMemoryAssessmentRepository)
    audit: ListAuditSink = field(default_factory=ListAuditSink)


class SystemClock:
    """Current UTC time."""

    def now(self) -> datetime:
        """Timezone-aware current time."""
        return datetime.now(UTC)


class UuidIds:
    """Random UUIDs as identifiers of activities and assessments."""

    def new_id(self, kind: str) -> str:
        """New identifier; ``kind`` is not part of the value."""
        return str(uuid.uuid4())


@dataclass(frozen=True)
class Backend:
    """Profile and services of one REST interface instance."""

    profile: RuleProfile
    registers: RegisterService
    assessments: AssessmentService


def create_backend(
    profile: RuleProfile,
    storage: Storage,
    authorizer: Authorizer,
    *,
    clock: Clock | None = None,
    ids: IdFactory | None = None,
) -> Backend:
    """Library services over the consumer's storage and authorizer."""
    active_clock = clock or SystemClock()
    active_ids = ids or UuidIds()
    registers = RegisterService(
        storage.registers, authorizer, storage.audit, active_clock, active_ids, profile
    )
    assessments = AssessmentService(
        storage.assessments, storage.registers, authorizer, storage.audit, active_clock, active_ids
    )
    return Backend(profile=profile, registers=registers, assessments=assessments)
