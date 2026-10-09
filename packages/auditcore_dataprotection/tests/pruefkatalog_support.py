"""Wiring for the acceptance tests of the VVT/DSFA review catalogue (synthetic data only)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from auditcore_dataprotection.assessment import AssessmentService
from auditcore_dataprotection.central_register import CentralRegisterService
from auditcore_dataprotection.memory import (
    FixedClock,
    InMemoryAssessmentRepository,
    InMemoryRegisterRepository,
    ListAuditSink,
    RoleAuthorizer,
    SequentialIds,
)
from auditcore_dataprotection.memory_records import (
    FakeCentralRegister,
    InMemoryOperationRepository,
    InMemoryTransferRepository,
)
from auditcore_dataprotection.model import Actor, Permission
from auditcore_dataprotection.operation import OperationService
from auditcore_dataprotection.register import RegisterService
from auditcore_dataprotection.rules import RuleProfile, load_profile
from auditcore_dataprotection.workspace import ActivityWorkspace

TENANT = "mandant-1"
VERSION = "2026.10.4"

_EDIT = {
    Permission.REGISTER_READ,
    Permission.REGISTER_EDIT,
    Permission.ASSESSMENT_READ,
    Permission.ASSESSMENT_EDIT,
    Permission.ASSESSMENT_DECIDE,
    Permission.CHECKLIST_EDIT,
}
ROLES = {
    "entwicklung": frozenset(_EDIT),
    "fach": frozenset(_EDIT),
    "leitung": frozenset(
        {
            Permission.REGISTER_READ,
            Permission.REGISTER_RELEASE,
            Permission.ASSESSMENT_READ,
            Permission.ASSESSMENT_RELEASE,
            Permission.CENTRAL_REGISTER_TRANSFER,
        }
    ),
    "dsb": frozenset({Permission.ASSESSMENT_READ, Permission.ASSESSMENT_DPO_STATEMENT}),
    "zentral": frozenset({Permission.REGISTER_READ, Permission.CENTRAL_REGISTER_CONFIRM}),
    "entscheidung": frozenset(
        {Permission.REGISTER_READ, Permission.ASSESSMENT_READ, Permission.OPERATION_DECIDE}
    ),
    # Technical administration: everything technical, but no subject-matter decision.
    "admin": frozenset(set(Permission) - {Permission.OPERATION_DECIDE}),
}


def person(name: str, role: str, tenant: str = TENANT) -> Actor:
    return Actor(name, frozenset({tenant}), frozenset({role}))


DEV = person("dev", "entwicklung")
FACH = person("fach", "fach")
LEITUNG = person("leitung", "leitung")
DSB = person("dsb", "dsb")
ZENTRAL = person("zentral", "zentral")
CHEF = person("chef", "entscheidung")
ADMIN = person("admin", "admin")


def hdsig() -> RuleProfile:
    return load_profile("auditcore.hdsig_ji", VERSION)


def gdpr() -> RuleProfile:
    return load_profile("auditcore.dsgvo", VERSION)


def cover() -> dict[str, Any]:
    return {
        "deckblatt": {"verantwortlicher": {"name": "Beispielbehörde"}, "dsb": {"name": "DSB"}},
        "referate": ["Referat A"],
    }


@dataclass
class Kat:
    profile: RuleProfile
    registers: InMemoryRegisterRepository
    assessments_repo: InMemoryAssessmentRepository
    audit: ListAuditSink
    clock: FixedClock
    register: RegisterService
    assessments: AssessmentService
    workspace: ActivityWorkspace
    operations: OperationService
    central: CentralRegisterService
    fake_central: FakeCentralRegister


def kat(profile: RuleProfile | None = None) -> Kat:
    rules = profile or hdsig()
    registers = InMemoryRegisterRepository()
    assessments_repo = InMemoryAssessmentRepository()
    audit = ListAuditSink()
    clock = FixedClock()
    ids = SequentialIds()
    authorizer = RoleAuthorizer(ROLES)
    register = RegisterService(registers, authorizer, audit, clock, ids, rules)
    assessments = AssessmentService(assessments_repo, registers, authorizer, audit, clock, ids)
    transfers = InMemoryTransferRepository()
    decisions = InMemoryOperationRepository()
    workspace = ActivityWorkspace(
        register, assessments_repo, authorizer, clock, rules, transfers, decisions, assessments
    )
    operations = OperationService(workspace, decisions, authorizer, audit, clock, ids)
    fake = FakeCentralRegister()
    central = CentralRegisterService(transfers, authorizer, audit, clock, fake)
    return Kat(
        rules,
        registers,
        assessments_repo,
        audit,
        clock,
        register,
        assessments,
        workspace,
        operations,
        central,
        fake,
    )


def full_activity(**extra: Any) -> dict[str, Any]:
    """Synthetic, complete controller activity under the selected regime."""
    return {
        "name": "Verfolgung von Ordnungswidrigkeiten (Beispiel)",
        "referat": "Referat A",
        "rechtsregime": "hdsig_ji",
        "rolle": "verantwortlicher",
        "verantwortliche_stelle": "Beispielbehörde",
        "zweck": "Verfolgung und Ahndung von Ordnungswidrigkeiten nach Fachgesetz X",
        "ermaechtigungsgrundlage": "§ 1 Fachgesetz X (synthetisch)",
        "kategorien_betroffene": "Betroffene des Verfahrens",
        "kategorien_daten": "Stammdaten, Verfahrensdaten",
        "kategorien_empfaenger": "Gerichte",
        "uebermittlungen": [{"empfaenger": "Amtsgericht", "rechtsgrundlage": "§ 69 OWiG"}],
        "profiling": False,
        "speicherdauer": "5 Jahre nach Abschluss",
        "tom": "Rollenkonzept, Verschlüsselung",
        "drittlandtransfer": False,
        "besondere_kategorien": False,
        "daten_art10": True,
        "anzahl_betroffene": 300,
        **extra,
    }


def new_register(world: Kat, *activities: dict[str, Any]) -> str:
    """Save a draft with the activities and return the first activity id."""
    version = world.register.save_draft(TENANT, FACH, {**cover(), "taetigkeiten": list(activities)})
    return str(version.activities[0]["id"])
