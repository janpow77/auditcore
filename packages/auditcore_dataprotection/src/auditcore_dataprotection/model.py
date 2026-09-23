"""Immutable records, actors, permissions and audit events.

Records are frozen dataclasses. Services never mutate a stored record; they
build a replacement and hand it to the repository port together with the
revision they read, so lost updates are detected (optimistic concurrency).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any

from .calculation import Answer, Scenario

DEFAULT_REGISTER = "verarbeitungsverzeichnis"


class Permission(StrEnum):
    """Operations the authorizer port must allow for an actor and tenant."""

    REGISTER_READ = "register.read"
    REGISTER_EDIT = "register.edit"
    REGISTER_RELEASE = "register.release"
    ASSESSMENT_READ = "assessment.read"
    ASSESSMENT_EDIT = "assessment.edit"
    ASSESSMENT_DECIDE = "assessment.decide"
    ASSESSMENT_DPO_STATEMENT = "assessment.dpo_statement"
    ASSESSMENT_RELEASE = "assessment.release"


@dataclass(frozen=True)
class Actor:
    """Authenticated person as established by the consumer application."""

    id: str
    tenant_ids: frozenset[str] = frozenset()
    roles: frozenset[str] = frozenset()


class RegisterStatus(StrEnum):
    """Status of a register version."""

    DRAFT = "entwurf"
    RELEASED = "freigegeben"
    SUPERSEDED = "abgeloest"


class AssessmentStatus(StrEnum):
    """Status of an assessment version."""

    DRAFT = "entwurf"
    DPO_INVOLVED = "dsb_beteiligung"
    RELEASED = "freigegeben"
    SUPERSEDED = "abgeloest"


def frozen_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    """Read-only shallow view; nested values are validated JSON data."""
    return MappingProxyType(dict(value))


@dataclass(frozen=True)
class RegisterVersion:
    """One version of a record of processing activities (Art. 30 GDPR)."""

    tenant_id: str
    register_id: str
    version: int
    status: RegisterStatus
    content: Mapping[str, Any]
    content_hash: str
    created_by: str
    created_at: datetime
    editors: tuple[str, ...]
    revision: int = 1
    released_by: str | None = None
    released_at: datetime | None = None
    predecessor_version: int | None = None

    @property
    def locked(self) -> bool:
        """True once the version is released or superseded."""
        return self.status is not RegisterStatus.DRAFT

    @property
    def activities(self) -> tuple[Mapping[str, Any], ...]:
        """Activities of this version."""
        return tuple(self.content.get("taetigkeiten") or ())


@dataclass(frozen=True)
class Consultation:
    """Prior consultation of the supervisory authority (Art. 36 GDPR / § 64 HDSIG)."""

    authority: str
    result: str
    consulted_on: str
    recorded_by: str
    recorded_at: datetime
    ground: str | None = None


@dataclass(frozen=True)
class Assessment:
    """One version of a DPIA for exactly one activity version of a register."""

    tenant_id: str
    assessment_id: str
    register_id: str
    activity_id: str
    activity_name: str
    version: int
    status: AssessmentStatus
    profile_id: str
    profile_version: str
    profile_fingerprint: str
    register_version: int
    activity_snapshot: Mapping[str, Any]
    answers: Mapping[str, Answer]
    scenarios: tuple[Scenario, ...]
    proposal: Mapping[str, Any]
    created_by: str
    created_at: datetime
    updated_at: datetime
    editors: tuple[str, ...]
    revision: int = 1
    necessity: str = ""
    proportionality: str = ""
    data_subject_view: str = ""
    decision: str | None = None
    deviation: bool = False
    deviation_justification: str | None = None
    decided_by: str | None = None
    decided_at: datetime | None = None
    dpo_vote: str | None = None
    dpo_statement: str | None = None
    dpo_by: str | None = None
    dpo_at: datetime | None = None
    dpo_conclusion: str | None = None
    dpo_conclusion_by: str | None = None
    leadership_presented_to: str | None = None
    leadership_presented_at: datetime | None = None
    consultation: Consultation | None = None
    released_by: str | None = None
    released_at: datetime | None = None
    predecessor_id: str | None = None
    changes_to_predecessor: tuple[Mapping[str, Any], ...] = ()
    # Schema 2 (EDPB template 2026 v1.0); empty for schema 1 profiles.
    dossier: Mapping[str, str] = field(default_factory=dict)
    measure_status: Mapping[str, Mapping[str, str]] = field(default_factory=dict)
    action_plan: tuple[Mapping[str, str], ...] = ()
    conditions: tuple[str, ...] = ()

    @property
    def locked(self) -> bool:
        """True once the version is released or superseded."""
        return self.status in (AssessmentStatus.RELEASED, AssessmentStatus.SUPERSEDED)


@dataclass(frozen=True)
class AuditEvent:
    """Attributable change; persisted by the consumer's audit trail."""

    tenant_id: str
    actor_id: str
    action: str
    entity: str
    entity_id: str
    version: int
    at: datetime
    details: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReviewItem:
    """A released assessment whose activity changed or disappeared (Art. 35 Abs. 11)."""

    tenant_id: str
    assessment_id: str
    activity_id: str
    activity_name: str
    assessment_version: int
    register_version: int
    reason: str
    differences: tuple[Mapping[str, Any], ...]
