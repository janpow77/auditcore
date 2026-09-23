"""Register content checks, identifiers and the versioned four-eyes lifecycle."""

from __future__ import annotations

from typing import Any

import pytest
from support import (
    ANNA,
    BERT,
    CARL,
    FOREIGN,
    FREMD,
    MAX,
    TENANT,
    actor,
    complete_activity,
    dsgvo,
    register_content,
    world,
)

from auditcore_dataprotection import legacy
from auditcore_dataprotection.errors import (
    AuthorizationError,
    ConflictError,
    FourEyesViolation,
    LockedVersionError,
    NotFoundError,
    StaleRevisionError,
    ValidationError,
)
from auditcore_dataprotection.memory import SequentialIds
from auditcore_dataprotection.model import RegisterStatus
from auditcore_dataprotection.register import (
    MAX_ACTIVITIES,
    activity_changes,
    check_activity,
    check_register,
    content_hash,
    find_activity,
    group_by_department,
    normalize_content,
)

# ------------------------------------------------------------ normalization


def test_uuid_scheme_assigns_ids_once_and_keeps_existing() -> None:
    ids = SequentialIds("t")
    data = normalize_content(register_content({"name": "A"}, {"name": "B", "id": "fest-1"}), ids)
    assert [a["id"] for a in data["taetigkeiten"]] == ["t-activity-1", "fest-1"]
    again = normalize_content(data, ids)
    assert again == data


def test_legacy_scheme_matches_source_identifiers() -> None:
    content = register_content({"name": "Preisaufsicht"}, {"name": "Preisaufsicht"})
    data = normalize_content(content, scheme="legacy")
    expected = legacy.legacy_activities_with_identifiers(content["taetigkeiten"])
    assert [a["id"] for a in data["taetigkeiten"]] == [a["id"] for a in expected]
    assert data["taetigkeiten"][1]["id"].endswith("-2")


def test_c18_duplicate_activity_ids_are_rejected() -> None:
    # DP-C18: legacy keeps duplicated explicit identifiers.
    rows = [{"name": "A", "id": "x"}, {"name": "B", "id": "x"}]
    assert [a["id"] for a in legacy.legacy_activities_with_identifiers(rows)] == ["x", "x"]
    with pytest.raises(ValidationError, match="doppelt"):
        normalize_content(register_content(*rows), scheme="legacy")


@pytest.mark.parametrize("identifier", [" x", "../x", "a" * 65, 5, "ä"])
def test_malformed_identifiers(identifier: Any) -> None:
    with pytest.raises(ValidationError):
        normalize_content(register_content({"name": "A", "id": identifier}), scheme="legacy")


@pytest.mark.parametrize(
    "content,message",
    [
        ([], "Zuordnung"),
        ({"deckblatt": []}, "deckblatt"),
        ({"referate": "x"}, "referate"),
        ({"referate": [1]}, "referate"),
        ({"taetigkeiten": {}}, "taetigkeiten"),
        ({"taetigkeiten": ["x"]}, "taetigkeiten"),
        ({"taetigkeiten": [{"name": 5}]}, "Text"),
        ({"taetigkeiten": [{"drittlandtransfer": "nein"}]}, "Ja/Nein"),
        ({"taetigkeiten": [{"anzahl_betroffene": "10"}]}, "ganze Zahl"),
        ({"taetigkeiten": [{"anzahl_betroffene": True}]}, "ganze Zahl"),
        ({"taetigkeiten": [{"anzahl_betroffene": -1}]}, "ganze Zahl"),
        ({"x": object()}, "nicht zulässig"),
        ({"x": float("nan")}, "ungültige Zahl"),
        ({1: "x"}, "Schlüssel"),
    ],
)
def test_content_type_validation(content: Any, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        normalize_content(content, SequentialIds())


def test_size_limits_and_scheme_errors() -> None:
    with pytest.raises(ValidationError, match="Mehr als"):
        normalize_content({"taetigkeiten": [{"name": "a"}] * (MAX_ACTIVITIES + 1)}, SequentialIds())
    with pytest.raises(ValidationError, match="Größe"):
        normalize_content({"blob": "x" * (6 * 1024 * 1024)}, SequentialIds())
    with pytest.raises(ValidationError, match="IdFactory"):
        normalize_content({"taetigkeiten": [{"name": "a"}]})
    with pytest.raises(ValidationError, match="Kennungsschema"):
        normalize_content({}, SequentialIds(), scheme="zufall")
    nested: Any = "x"
    for _ in range(10):
        nested = [nested]
    with pytest.raises(ValidationError, match="verschachtelt"):
        normalize_content({"x": nested}, SequentialIds())


def test_normalization_does_not_mutate_input() -> None:
    content = register_content({"name": "A"})
    normalize_content(content, SequentialIds())
    assert "id" not in content["taetigkeiten"][0]


def test_content_hash_is_canonical() -> None:
    assert content_hash({"a": 1, "b": [1]}) == content_hash({"b": [1], "a": 1})
    assert content_hash({"a": 1}) != content_hash({"a": 2})


# ------------------------------------------------------------ content checks


def test_complete_activity_has_no_issues() -> None:
    assert check_activity(complete_activity(id="a"), dsgvo()) == ()


def test_missing_required_fields_are_blocking_with_reference() -> None:
    issues = check_activity({"id": "a", "name": "A"}, dsgvo())
    blocking = {i.subject.split(":")[1] for i in issues if i.blocking}
    assert {
        "zweck",
        "ermaechtigungsgrundlage",
        "kategorien_betroffene",
        "kategorien_daten",
        "kategorien_empfaenger",
        "speicherdauer",
        "tom",
        "drittlandtransfer",
    } <= blocking
    zweck = next(i for i in issues if i.subject == "a:zweck")
    assert "Art. 30 Abs. 1 lit. b DSGVO" in zweck.message
    notes = {i.code for i in issues if not i.blocking}
    assert {"undecided_flag", "missing_count"} <= notes


def test_conditional_fields() -> None:
    transfer = check_activity(complete_activity(id="a", drittlandtransfer=True), dsgvo())
    assert {i.subject for i in transfer} == {"a:name_empfaenger_drittland", "a:drittland_garantien"}
    processor = check_activity(complete_activity(id="a", auftragsverarbeiter="IT"), dsgvo())
    assert [i.code for i in processor] == ["undecided_flag"]
    no_contract = check_activity(
        complete_activity(id="a", auftragsverarbeiter="IT", avv_besteht=False), dsgvo()
    )
    assert [(i.code, i.blocking) for i in no_contract] == [("missing_contract", False)]
    joint = check_activity(complete_activity(id="a", gemeinsame_verantwortlichkeit=True), dsgvo())
    assert [i.subject for i in joint] == ["a:gemeinsame_verantwortliche"]


def test_register_cover_sheet() -> None:
    issues = check_register({"taetigkeiten": []}, dsgvo())
    assert [i.subject for i in issues] == ["deckblatt:verantwortlicher", "deckblatt:dsb"]
    assert check_register(register_content(complete_activity(id="a")), dsgvo()) == ()


def test_c16_change_detection_is_strict() -> None:
    # DP-C16: legacy hides False/0 -> missing.
    assert legacy.legacy_compare_activity({"drittlandtransfer": False}, {}) == []
    assert legacy.legacy_compare_activity({"anzahl_betroffene": 0}, {}) == []
    assert [c["feld"] for c in activity_changes({"drittlandtransfer": False}, {}, dsgvo())] == [
        "drittlandtransfer"
    ]
    assert [c["feld"] for c in activity_changes({"anzahl_betroffene": 0}, {}, dsgvo())] == [
        "anzahl_betroffene"
    ]
    assert activity_changes({"zweck": None}, {"zweck": ""}, dsgvo()) == ()
    assert activity_changes({"ansprechperson": "A"}, {"ansprechperson": "B"}, dsgvo()) == ()


def test_grouping_follows_source_layout() -> None:
    rows = [{"referat": "Z"}, {"referat": "A"}, {"referat": ""}, {"referat": "Q"}]
    groups = group_by_department(rows, ["A", "Z", "leer"])
    assert [g for g, _ in groups] == ["A", "Z", "Ohne Referat", "Q"]


def test_find_activity_errors() -> None:
    with pytest.raises(NotFoundError, match="noch kein Verzeichnis"):
        find_activity(None, "x")


# ------------------------------------------------------------ lifecycle


def test_draft_lifecycle_and_revisions() -> None:
    w = world()
    first = w.register.save_draft(TENANT, ANNA, register_content(complete_activity()))
    assert (first.version, first.status, first.revision, first.editors) == (
        1,
        RegisterStatus.DRAFT,
        1,
        ("anna",),
    )
    assert first.activities[0]["id"] == "id-activity-1"
    with pytest.raises(StaleRevisionError):
        w.register.save_draft(TENANT, CARL, register_content())
    with pytest.raises(StaleRevisionError):
        w.register.save_draft(TENANT, CARL, register_content(), expected_revision=9)
    second = w.register.save_draft(TENANT, CARL, dict(first.content), expected_revision=1)
    assert (second.version, second.revision, second.editors, second.created_by) == (
        1,
        2,
        ("anna", "carl"),
        "carl",
    )
    third = w.register.save_draft(TENANT, ANNA, dict(first.content), expected_revision=2)
    assert third.editors == ("anna", "carl")
    with pytest.raises(StaleRevisionError, match="keinen offenen Entwurf"):
        w.register.save_draft(
            TENANT, ANNA, register_content(), register_id="anderes", expected_revision=3
        )
    with pytest.raises(ConflictError, match="kein offener Entwurf"):
        w.register.release(TENANT, BERT, expected_revision=3, register_id="anderes")
    assert w.audit.actions() == [
        "register.draft_created",
        "register.draft_saved",
        "register.draft_saved",
    ]
    assert w.audit.events[0].details["content_hash"] == first.content_hash


def test_c13_release_requires_person_who_did_not_edit() -> None:
    # DP-C13: legacy compares only with the last editor; here all editors are excluded.
    w = world()
    draft = w.register.save_draft(TENANT, ANNA, register_content(complete_activity()))
    draft = w.register.save_draft(TENANT, MAX, dict(draft.content), expected_revision=1)
    with pytest.raises(FourEyesViolation, match="Vier-Augen"):
        w.register.release(TENANT, MAX, expected_revision=draft.revision)
    released = w.register.release(TENANT, BERT, expected_revision=draft.revision)
    assert released.status is RegisterStatus.RELEASED and released.released_by == "bert"


def test_c17_incomplete_register_cannot_be_released() -> None:
    # DP-C17: legacy releases without any content check.
    w = world()
    draft = w.register.save_draft(TENANT, ANNA, register_content({"name": "A"}))
    with pytest.raises(ConflictError, match="unvollständig"):
        w.register.release(TENANT, BERT, expected_revision=draft.revision)
    lenient = world(require_complete_release=False)
    draft = lenient.register.save_draft(TENANT, ANNA, register_content({"name": "A"}))
    assert lenient.register.release(TENANT, BERT, expected_revision=draft.revision).locked


def test_release_supersedes_and_keeps_history_immutable() -> None:
    w = world()
    d1 = w.register.save_draft(TENANT, ANNA, register_content(complete_activity()))
    with pytest.raises(StaleRevisionError):
        w.register.release(TENANT, BERT, expected_revision=99)
    r1 = w.register.release(TENANT, BERT, expected_revision=d1.revision)
    with pytest.raises(ConflictError, match="kein offener Entwurf"):
        w.register.release(TENANT, BERT, expected_revision=1)
    assert w.register.effective(TENANT, ANNA) == r1
    changed = dict(r1.content)
    changed["taetigkeiten"] = [{**r1.activities[0], "zweck": "Neu"}]
    d2 = w.register.save_draft(TENANT, ANNA, changed)
    assert (d2.version, d2.predecessor_version) == (2, 1)
    assert w.register.effective(TENANT, ANNA).version == 1  # released wins over draft
    assert w.register.draft(TENANT, ANNA) == d2
    r2 = w.register.release(TENANT, BERT, expected_revision=d2.revision)
    history = w.register.history(TENANT, ANNA)
    assert [(v.version, v.status) for v in history] == [
        (2, RegisterStatus.RELEASED),
        (1, RegisterStatus.SUPERSEDED),
    ]
    assert history[1].content == r1.content
    assert w.register.released(TENANT, ANNA) == r2
    with pytest.raises(LockedVersionError):
        w.registers.replace(history[1], history[1].revision)
    activity, version = w.register.activity(TENANT, ANNA, r2.activities[0]["id"])
    assert activity["zweck"] == "Neu" and version.version == 2
    assert w.audit.events[-1].details["superseded"] == 1


def test_tenant_separation_and_authorization() -> None:
    w = world()
    w.register.save_draft(TENANT, ANNA, register_content(complete_activity()))
    fremd_in_tenant = actor("fremd", "alles", tenants=(FOREIGN,))
    with pytest.raises(AuthorizationError):
        w.register.draft(TENANT, fremd_in_tenant)
    assert w.register.draft(FOREIGN, FREMD) is None
    assert w.register.history(FOREIGN, FREMD) == ()
    assert w.register.effective(FOREIGN, FREMD) is None
    with pytest.raises(NotFoundError):
        w.register.activity(FOREIGN, FREMD, "id-activity-1")
    with pytest.raises(AuthorizationError):
        w.register.release(TENANT, ANNA, expected_revision=1)  # role without release right
    with pytest.raises(AuthorizationError):
        w.register.save_draft(TENANT, BERT, register_content())
    with pytest.raises(AuthorizationError, match="Person"):
        w.register.draft(TENANT, None)  # type: ignore[arg-type]
