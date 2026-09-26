"""Documentation mode of profile 2026.10.3 (user decision of 24.09.2026).

The library documents: open checks, including a missing statement of the
DPO, never prevent the release; they are recorded with it. Rights and the
four-eyes principle still apply. Profiles up to 2026.10.2 keep blocking.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest
from support import (
    ANNA,
    BERT,
    MAX,
    TENANT,
    World,
    complete_activity,
    released_register,
    world,
)

from auditcore_dataprotection.errors import (
    AuthorizationError,
    ConflictError,
    FourEyesViolation,
    ValidationError,
)
from auditcore_dataprotection.export import assessment_report, render_assessment_html
from auditcore_dataprotection.model import Assessment
from auditcore_dataprotection.rules import load_profile


def doc() -> Any:
    return load_profile("auditcore.dsgvo", "2026.10.3")


def rev(a: Assessment) -> dict[str, int]:
    return {"expected_revision": a.revision}


def started(w: World, profile: Any = None) -> Assessment:
    released_register(w, complete_activity(id="a1"))
    return w.service.start(TENANT, ANNA, "a1", profile or doc())


def test_profile_2026_10_3_documents_and_earlier_versions_block() -> None:
    assert doc().documentation_mode and doc().release_mode == "dokumentation"
    for version in ("2026.10.1", "2026.10.2"):
        assert not load_profile("auditcore.dsgvo", version).documentation_mode
    assert load_profile("auditcore.hdsig_ji", "2026.10.3").documentation_mode


def test_empty_assessment_can_be_released_and_open_points_are_recorded() -> None:
    w = world()
    a = started(w)
    assert w.service.release_blockers(a) == ()
    points = w.service.open_points(a)
    assert any("über den Vorschlag zu entscheiden" in p for p in points)
    assert any("eingeholt wurde" in p for p in points)
    released = w.service.release(TENANT, BERT, a.assessment_id, **rev(a))
    assert released.status.value == "freigegeben"
    assert released.release_open_points == points
    assert w.audit.events[-1].details["open_points"] == len(points)


def test_dpo_request_is_enough_and_the_statement_may_follow_or_not() -> None:
    w = world()
    a = started(w)
    a = w.service.record_dpo_request(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        requested_from="Behördliche Datenschutzbeauftragte",
        requested_on=date(2026, 9, 24),
    )
    assert a.dpo_requested_on == "2026-09-24" and a.dpo_requested_by == "anna"
    points = w.service.open_points(a)
    assert any("liegt noch nicht vor; eingeholt am 2026-09-24" in p for p in points)
    assert not any("eingeholt wurde (" in p for p in points)
    released = w.service.release(TENANT, BERT, a.assessment_id, **rev(a))
    html = render_assessment_html(assessment_report(released, doc()))
    assert "Stellungnahme eingeholt" in html and "am 2026-09-24 bei" in html
    assert "Bei der Freigabe offen" in html


def test_incomplete_survey_and_deviation_without_reason_can_be_decided() -> None:
    w = world()
    a = started(w)
    assert a.proposal["recommendation"] == "unvollstaendig"
    a = w.service.decide(TENANT, ANNA, a.assessment_id, **rev(a), decision="freigabe_mit_auflagen")
    assert a.decision == "freigabe_mit_auflagen" and a.conditions == ()
    points = w.service.open_points(a)
    assert any("Begründung von mindestens" in p for p in points)
    assert any("Bedingungen" in p for p in points)


def test_rights_four_eyes_and_dpo_self_release_still_apply() -> None:
    w = world()
    a = started(w)
    with pytest.raises(AuthorizationError):
        w.service.release(TENANT, ANNA, a.assessment_id, **rev(a))
    a = w.service.record_dpo_request(
        TENANT, MAX, a.assessment_id, **rev(a), requested_from="DSB", requested_on=date(2026, 9, 24)
    )
    with pytest.raises(FourEyesViolation):
        w.service.release(TENANT, MAX, a.assessment_id, **rev(a))
    w2 = world()
    b = started(w2)
    b = w2.service.record_dpo_statement(
        TENANT, MAX, b.assessment_id, **rev(b), vote="abgelehnt", statement="Nicht vertretbar."
    )
    with pytest.raises(FourEyesViolation, match="berät"):
        w2.service.release(TENANT, MAX, b.assessment_id, **rev(b))
    assert w2.service.release_blockers(b) == ()
    assert any("Behördenleitung" in p for p in w2.service.open_points(b))


def test_consultation_ground_mismatch_is_recorded_not_refused() -> None:
    w = world()
    a = started(w)
    a = w.service.record_consultation(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        authority="HBDI",
        result="r",
        consulted_on=date(2026, 9, 1),
        ground="hohes_restrisiko",
    )
    assert any("kein hohes Restrisiko" in p for p in w.service.open_points(a))


def test_dpo_request_only_in_documentation_mode() -> None:
    w = world()
    a = started(w, load_profile("auditcore.dsgvo", "2026.10.2"))
    with pytest.raises(ValidationError, match="Dokumentationsmodus"):
        w.service.record_dpo_request(
            TENANT,
            ANNA,
            a.assessment_id,
            **rev(a),
            requested_from="DSB",
            requested_on=date(2026, 9, 24),
        )
    with pytest.raises(ConflictError):
        w.service.release(TENANT, BERT, a.assessment_id, **rev(a))


def test_content_change_resets_the_dpo_request() -> None:
    w = world()
    a = started(w)
    a = w.service.record_dpo_request(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        requested_from="DSB",
        requested_on=date(2026, 9, 24),
    )
    a = w.service.decide(TENANT, ANNA, a.assessment_id, **rev(a), decision="freigabe")
    a = w.service.update(TENANT, ANNA, a.assessment_id, **rev(a), necessity="neu")
    assert a.dpo_requested_on is None and a.decision is None
