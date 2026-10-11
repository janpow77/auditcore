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
from ..central_register import CentralRegisterPort, CentralRegisterService, TransferRepository
from ..memory import InMemoryAssessmentRepository, InMemoryRegisterRepository, ListAuditSink
from ..operation import OperationService
from ..operation_model import OperationRepository
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
from ..workspace import ActivityWorkspace


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
    workspace: ActivityWorkspace | None = None
    operations: OperationService | None = None
    central: CentralRegisterService | None = None


def create_backend(
    profile: RuleProfile,
    storage: Storage,
    authorizer: Authorizer,
    *,
    clock: Clock | None = None,
    ids: IdFactory | None = None,
    transfers: TransferRepository | None = None,
    decisions: OperationRepository | None = None,
    central_port: CentralRegisterPort | None = None,
) -> Backend:
    """Library services over the consumer's storage and authorizer.

    ``transfers`` and ``decisions`` enable the central register takeover and the
    operational decision; ``central_port`` is the explicitly configured
    connection to the central register (no hidden network access).
    """
    active_clock = clock or SystemClock()
    active_ids = ids or UuidIds()
    registers = RegisterService(
        storage.registers, authorizer, storage.audit, active_clock, active_ids, profile
    )
    assessments = AssessmentService(
        storage.assessments, storage.registers, authorizer, storage.audit, active_clock, active_ids
    )
    workspace = ActivityWorkspace(
        registers,
        storage.assessments,
        authorizer,
        active_clock,
        profile,
        transfers,
        decisions,
        assessments,
    )
    operations = (
        None
        if decisions is None
        else OperationService(
            workspace, decisions, authorizer, storage.audit, active_clock, active_ids
        )
    )
    central = (
        None
        if transfers is None
        else CentralRegisterService(
            transfers, authorizer, storage.audit, active_clock, central_port
        )
    )
    return Backend(profile, registers, assessments, workspace, operations, central)
