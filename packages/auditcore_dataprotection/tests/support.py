"""Test wiring: real services with the in-memory reference adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from auditcore_dataprotection.assessment import AssessmentService
from auditcore_dataprotection.memory import (
    FixedClock,
    InMemoryAssessmentRepository,
    InMemoryRegisterRepository,
    ListAuditSink,
    RoleAuthorizer,
    SequentialIds,
)
from auditcore_dataprotection.model import Actor, Permission
from auditcore_dataprotection.register import RegisterService
from auditcore_dataprotection.rules import RuleProfile, load_profile

TENANT = "mandant-1"
FOREIGN = "mandant-2"

ROLES = {
    "fach": frozenset(
        {
            Permission.REGISTER_READ,
            Permission.REGISTER_EDIT,
            Permission.ASSESSMENT_READ,
            Permission.ASSESSMENT_EDIT,
            Permission.ASSESSMENT_DECIDE,
        }
    ),
    "leitung": frozenset(
        {
            Permission.REGISTER_READ,
            Permission.REGISTER_RELEASE,
            Permission.ASSESSMENT_READ,
            Permission.ASSESSMENT_RELEASE,
        }
    ),
    "dsb": frozenset({Permission.ASSESSMENT_READ, Permission.ASSESSMENT_DPO_STATEMENT}),
    "alles": frozenset(Permission),
}


def actor(name: str, *roles: str, tenants: tuple[str, ...] = (TENANT,)) -> Actor:
    return Actor(name, frozenset(tenants), frozenset(roles))


ANNA = actor("anna", "fach")
CARL = actor("carl", "fach")
BERT = actor("bert", "leitung")
DORA = actor("dora", "dsb")
MAX = actor("max", "alles")
FREMD = actor("fremd", "alles", tenants=(FOREIGN,))


def dsgvo() -> RuleProfile:
    return load_profile("regulierung.dsgvo", "2026.09.1")


def ji() -> RuleProfile:
    return load_profile("regulierung.hdsig_ji", "2026.09.1")


def complete_activity(**extra: Any) -> dict[str, Any]:
    return {
        "name": "Preisaufsicht",
        "referat": "Referat III – KPAnG-Vollzug",
        "zweck": "Vollzug des Kraftstoffpreisanpassungsgesetzes",
        "ermaechtigungsgrundlage": "KPAnG",
        "kategorien_betroffene": "Betreiber",
        "kategorien_daten": "Preisdaten",
        "kategorien_empfaenger": "keine",
        "speicherdauer": "10 Jahre",
        "tom": "Rollenkonzept",
        "drittlandtransfer": False,
        "besondere_kategorien": False,
        "daten_art10": False,
        "anzahl_betroffene": 250,
        **extra,
    }


def register_content(*activities: dict[str, Any]) -> dict[str, Any]:
    return {
        "deckblatt": {
            "verantwortlicher": {"name": "Behörde"},
            "dsb": {"name": "Beauftragte"},
        },
        "referate": ["Referat III – KPAnG-Vollzug", "Referat Z"],
        "taetigkeiten": list(activities),
    }


@dataclass
class World:
    registers: InMemoryRegisterRepository
    assessments: InMemoryAssessmentRepository
    audit: ListAuditSink
    clock: FixedClock
    ids: SequentialIds
    register: RegisterService
    service: AssessmentService


def world(**options: Any) -> World:
    registers = InMemoryRegisterRepository()
    assessments = InMemoryAssessmentRepository()
    audit = ListAuditSink()
    clock = FixedClock()
    ids = SequentialIds()
    authorizer = RoleAuthorizer(ROLES)
    register = RegisterService(
        registers,
        authorizer,
        audit,
        clock,
        ids,
        dsgvo(),
        **{
            k: v
            for k, v in options.items()
            if k in {"identifier_scheme", "require_complete_release"}
        },
    )
    service = AssessmentService(
        assessments,
        registers,
        authorizer,
        audit,
        clock,
        ids,
        **{
            k: v
            for k, v in options.items()
            if k in {"require_consultation_record", "resolve_profile"}
        },
    )
    return World(registers, assessments, audit, clock, ids, register, service)


def released_register(w: World, *activities: dict[str, Any]) -> None:
    draft = w.register.save_draft(TENANT, ANNA, register_content(*activities))
    w.register.release(TENANT, BERT, expected_revision=draft.revision)


def all_no() -> dict[str, bool]:
    return {q.key: False for q in dsgvo().questions}


def answers(**yes: bool) -> dict[str, bool]:
    return {**all_no(), **yes}


SCENARIO = {
    "dimension": "vertraulichkeit",
    "description": "Unbefugter Zugriff",
    "severity": 3,
    "likelihood": 4,
    "measures": ["zugriffskontrolle"],
}
