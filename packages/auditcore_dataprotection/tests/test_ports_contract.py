"""Repository contract of ``ports.py``; reusable against consumer adapters.

``check_register_repository`` and ``check_assessment_repository`` take a
factory, so a consumer can run the same assertions against its database
adapter inside a test transaction.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime

import pytest

from auditcore_dataprotection.errors import (
    ConflictError,
    LockedVersionError,
    NotFoundError,
    StaleRevisionError,
)
from auditcore_dataprotection.memory import (
    FixedClock,
    InMemoryAssessmentRepository,
    InMemoryRegisterRepository,
    ListAuditSink,
    RoleAuthorizer,
    SequentialIds,
)
from auditcore_dataprotection.model import (
    Actor,
    Assessment,
    AssessmentStatus,
    Permission,
    RegisterStatus,
    RegisterVersion,
)
from auditcore_dataprotection.ports import (
    AssessmentRepository,
    AuditSink,
    Authorizer,
    Clock,
    IdFactory,
    RegisterRepository,
)

NOW = datetime(2026, 9, 1, tzinfo=UTC)


def register(
    tenant: str = "t1", version: int = 1, status: RegisterStatus = RegisterStatus.DRAFT
) -> RegisterVersion:
    return RegisterVersion(
        tenant, "vvt", version, status, {"taetigkeiten": []}, "h", "anna", NOW, ("anna",)
    )


def assessment(
    tenant: str = "t1",
    ident: str = "a1",
    version: int = 1,
    status: AssessmentStatus = AssessmentStatus.DRAFT,
) -> Assessment:
    return Assessment(
        tenant,
        ident,
        "vvt",
        "act",
        "Name",
        version,
        status,
        "p",
        "1",
        "f",
        1,
        {},
        {},
        (),
        {},
        "anna",
        NOW,
        NOW,
        ("anna",),
    )


def check_register_repository(factory: Callable[[], RegisterRepository]) -> None:
    repo = factory()
    repo.add(register())
    assert repo.get_draft("t2", "vvt") is None
    assert repo.list_versions("t2", "vvt") == []
    with pytest.raises(ConflictError):
        repo.add(register())
    stored = repo.get_draft("t1", "vvt")
    assert stored is not None and stored.revision == 1
    with pytest.raises(StaleRevisionError):
        repo.replace(replace(stored, revision=2), expected_revision=5)
    with pytest.raises(StaleRevisionError):
        repo.replace(replace(stored, revision=1), expected_revision=1)
    with pytest.raises(NotFoundError):
        repo.replace(replace(stored, tenant_id="t2", revision=2), expected_revision=1)
    repo.replace(replace(stored, status=RegisterStatus.RELEASED, revision=2), expected_revision=1)
    released = repo.get_released("t1", "vvt")
    assert released is not None and repo.get_draft("t1", "vvt") is None
    with pytest.raises(LockedVersionError):
        repo.replace(replace(released, content={"x": 1}, revision=3), expected_revision=2)
    with pytest.raises(StaleRevisionError):
        repo.mark_superseded("t1", "vvt", 1, expected_revision=1)
    repo.mark_superseded("t1", "vvt", 1, expected_revision=2)
    superseded = repo.list_versions("t1", "vvt")[0]
    assert superseded.status is RegisterStatus.SUPERSEDED and superseded.revision == 3
    assert superseded.content == {"taetigkeiten": []}
    with pytest.raises(ConflictError):
        repo.mark_superseded("t1", "vvt", 1, expected_revision=3)
    with pytest.raises(NotFoundError):
        repo.mark_superseded("t2", "vvt", 1, expected_revision=3)
    repo.add(register(version=2))
    with pytest.raises(ConflictError):
        repo.add(register(version=3))  # second open draft
    assert [v.version for v in repo.list_versions("t1", "vvt")] == [2, 1]


def check_assessment_repository(factory: Callable[[], AssessmentRepository]) -> None:
    repo = factory()
    repo.add(assessment())
    assert repo.get("t2", "a1") is None
    assert repo.list_for_register("t2", "vvt") == []
    with pytest.raises(ConflictError):
        repo.add(assessment())
    with pytest.raises(ConflictError):
        repo.add(assessment(ident="a2"))  # same activity version
    stored = repo.get("t1", "a1")
    assert stored is not None
    with pytest.raises(StaleRevisionError):
        repo.replace(replace(stored, revision=2), expected_revision=9)
    with pytest.raises(ConflictError):
        repo.replace(replace(stored, version=5, revision=2), expected_revision=1)
    with pytest.raises(NotFoundError):
        repo.replace(replace(stored, tenant_id="t2", revision=2), expected_revision=1)
    with pytest.raises(ConflictError):
        repo.mark_superseded("t1", "a1", expected_revision=1)  # not released
    repo.replace(replace(stored, status=AssessmentStatus.RELEASED, revision=2), expected_revision=1)
    released = repo.get("t1", "a1")
    assert released is not None
    with pytest.raises(LockedVersionError):
        repo.replace(replace(released, necessity="neu", revision=3), expected_revision=2)
    repo.mark_superseded("t1", "a1", expected_revision=2)
    after = repo.get("t1", "a1")
    assert after is not None and after.status is AssessmentStatus.SUPERSEDED
    assert after.revision == 3
    repo.add(assessment(ident="a3", version=2))
    assert [a.version for a in repo.list_for_activity("t1", "vvt", "act")] == [2, 1]
    assert repo.list_for_activity("t2", "vvt", "act") == []


def test_in_memory_register_repository_contract() -> None:
    check_register_repository(InMemoryRegisterRepository)


def test_in_memory_assessment_repository_contract() -> None:
    check_assessment_repository(InMemoryAssessmentRepository)


def test_returned_records_are_copies() -> None:
    repo = InMemoryRegisterRepository()
    repo.add(register())
    stored = repo.get_draft("t1", "vvt")
    assert stored is not None
    stored.content["taetigkeiten"].append({"name": "x"})  # type: ignore[attr-defined]
    fresh = repo.get_draft("t1", "vvt")
    assert fresh is not None and fresh.content == {"taetigkeiten": []}


def test_reference_adapters_satisfy_protocols() -> None:
    assert isinstance(InMemoryRegisterRepository(), RegisterRepository)
    assert isinstance(InMemoryAssessmentRepository(), AssessmentRepository)
    assert isinstance(ListAuditSink(), AuditSink)
    assert isinstance(FixedClock(), Clock)
    assert isinstance(SequentialIds(), IdFactory)
    assert isinstance(RoleAuthorizer({}), Authorizer)


def test_clock_ids_and_authorizer() -> None:
    clock = FixedClock()
    first, second = clock.now(), clock.now()
    assert first.tzinfo is not None and second > first
    with pytest.raises(ValueError):
        FixedClock(start=datetime(2026, 1, 1))
    ids = SequentialIds("x")
    assert (ids.new_id("activity"), ids.new_id("assessment")) == ("x-activity-1", "x-assessment-2")
    auth = RoleAuthorizer({"r": frozenset({Permission.REGISTER_READ})})
    member = Actor("a", frozenset({"t1"}), frozenset({"r"}))
    assert auth.authorize(member, Permission.REGISTER_READ, "t1")
    assert not auth.authorize(member, Permission.REGISTER_EDIT, "t1")
    assert not auth.authorize(member, Permission.REGISTER_READ, "t2")
    assert not auth.authorize(
        Actor("a", frozenset({"t1"}), frozenset({"x"})), Permission.REGISTER_READ, "t1"
    )
