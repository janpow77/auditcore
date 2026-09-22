"""Framework catalogue cases (verwaltung-app-framework docs/pruefkatalog.md) for the library.

T-03 rights revocation, T-09 export scope, T-14 protocol content. The other
applicable cases are covered by the workflow, register, export and
architecture tests and mapped in ``tools/policy_proof.py``.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from support import TENANT, complete_activity, dsgvo, register_content

import auditcore_dataprotection
from auditcore_dataprotection.assessment import AssessmentService
from auditcore_dataprotection.errors import AuthorizationError
from auditcore_dataprotection.export import register_report
from auditcore_dataprotection.memory import (
    FixedClock,
    InMemoryAssessmentRepository,
    InMemoryRegisterRepository,
    ListAuditSink,
    SequentialIds,
)
from auditcore_dataprotection.model import Actor, Permission
from auditcore_dataprotection.register import RegisterService


@dataclass
class RevocableAuthorizer:
    """Consumer-like authorizer whose decisions change at runtime."""

    revoked: set[str] = field(default_factory=set)

    def authorize(self, actor: Actor, permission: Permission, tenant_id: str) -> bool:
        return actor.id not in self.revoked and tenant_id in actor.tenant_ids


def test_t03_revoked_rights_apply_to_the_next_operation() -> None:
    authorizer = RevocableAuthorizer()
    repo = InMemoryRegisterRepository()
    audit = ListAuditSink()
    service = RegisterService(repo, authorizer, audit, FixedClock(), SequentialIds(), dsgvo())
    anna = Actor("anna", frozenset({TENANT}))
    draft = service.save_draft(TENANT, anna, register_content(complete_activity()))
    authorizer.revoked.add("anna")
    with pytest.raises(AuthorizationError):
        service.save_draft(
            TENANT, anna, register_content(complete_activity()), expected_revision=draft.revision
        )
    with pytest.raises(AuthorizationError):
        service.history(TENANT, anna)
    assessments = AssessmentService(
        InMemoryAssessmentRepository(), repo, authorizer, audit, FixedClock(), SequentialIds()
    )
    with pytest.raises(AuthorizationError):
        assessments.start(TENANT, anna, draft.activities[0]["id"], dsgvo())
    assert [e.action for e in audit.events] == ["register.draft_created"]


def test_t09_register_export_contains_exactly_the_version_with_metadata() -> None:
    service = RegisterService(
        InMemoryRegisterRepository(),
        RevocableAuthorizer(),
        ListAuditSink(),
        FixedClock(),
        SequentialIds(),
        dsgvo(),
    )
    anna = Actor("anna", frozenset({TENANT}))
    activities = [complete_activity(name=f"T{i}") for i in range(3)]
    draft = service.save_draft(TENANT, anna, register_content(*activities))
    report = register_report(draft, dsgvo())
    exported = [a for group in report["departments"] for a in group["activities"]]
    assert len(exported) == 3
    assert [a["name"] for a in exported] == ["T0", "T1", "T2"]
    meta = report["meta"]
    assert meta["version"] == draft.version and meta["content_hash"] == draft.content_hash
    assert meta["profile_id"] == "regulierung.dsgvo" and meta["tenant_id"] == TENANT


def test_t14_library_writes_no_logs_and_audit_events_carry_no_content() -> None:
    package = Path(auditcore_dataprotection.__file__).parent
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names] + [getattr(node, "module", "") or ""]
                assert not any(n.split(".")[0] == "logging" for n in names), path.name
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id != "print", path.name
    audit = ListAuditSink()
    service = RegisterService(
        InMemoryRegisterRepository(),
        RevocableAuthorizer(),
        audit,
        FixedClock(),
        SequentialIds(),
        dsgvo(),
    )
    secret_text = "Geheimer Freitext der Fachabteilung"
    service.save_draft(
        TENANT,
        Actor("anna", frozenset({TENANT})),
        register_content(complete_activity(anmerkungen=secret_text)),
    )
    event = audit.events[0]
    assert secret_text not in repr(event)
    assert set(event.details) == {"content_hash"}
