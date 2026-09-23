"""DPIA workflow against the recorded legacy transcript and the corrected contract.

Guards that remain unchanged must fire in the same order with the same German
text as the original service; the corrected outcomes (DP-Cnn) are asserted
together with the recorded legacy behavior.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from typing import Any

import pytest
from support import (
    ANNA,
    BERT,
    CARL,
    DORA,
    FOREIGN,
    FREMD,
    MAX,
    SCENARIO,
    TENANT,
    World,
    actor,
    answers,
    complete_activity,
    dsgvo,
    ji,
    register_content,
    released_register,
    world,
)

from auditcore_dataprotection.assessment import AssessmentService
from auditcore_dataprotection.errors import (
    AuthorizationError,
    ConflictError,
    DataProtectionError,
    FourEyesViolation,
    LockedVersionError,
    NotFoundError,
    ProfileError,
    StaleRevisionError,
    TenantMismatchError,
    ValidationError,
)
from auditcore_dataprotection.memory import (
    DenyAllAuthorizer,
    FixedClock,
    InMemoryAssessmentRepository,
    InMemoryRegisterRepository,
    ListAuditSink,
    SequentialIds,
)
from auditcore_dataprotection.model import Assessment, AssessmentStatus
from auditcore_dataprotection.rules import load_profile, profile_from_dict


def steps(legacy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {s["name"]: s for s in legacy["workflow"]["steps"]}


def legacy_message(legacy: dict[str, Any], name: str) -> str:
    exception = steps(legacy)[name]["exception"]
    assert exception is not None, name
    return str(exception["message"])


def raises(error: type[Exception], call: Any) -> str:
    with pytest.raises(error) as caught:
        call()
    return str(caught.value)


def ready(w: World, **activity: Any) -> Assessment:
    released_register(w, complete_activity(id="a1", **activity))
    started = w.service.start(TENANT, ANNA, "a1", dsgvo())
    return w.service.update(
        TENANT,
        ANNA,
        started.assessment_id,
        expected_revision=started.revision,
        answers=answers(art35_3_a=True, edsa_01_bewerten=True),
        scenarios=[SCENARIO],
    )


def rev(a: Assessment) -> dict[str, int]:
    return {"expected_revision": a.revision}


# ------------------------------------------------------ unchanged guards


def test_guard_sequence_and_messages_match_legacy(legacy: dict[str, Any]) -> None:
    w = world()
    s = w.service
    a = ready(w)
    aid = a.assessment_id
    assert a.proposal["recommendation"] == "freigabe_mit_auflagen"
    assert (
        steps(legacy)["dsfa-save-1"]["output"]["vorschlag"]["empfehlung"] == "freigabe_mit_auflagen"
    )

    assert raises(ConflictError, lambda: s.release(TENANT, BERT, aid, **rev(a))) == legacy_message(
        legacy, "dsfa-release-before-decision"
    )
    assert raises(
        ValidationError,
        lambda: s.decide(TENANT, ANNA, aid, **rev(a), decision="freigabe", justification="zu kurz"),
    ) == legacy_message(legacy, "dsfa-decide-deviation-short")
    deviated = s.decide(TENANT, ANNA, aid, **rev(a), decision="freigabe", justification="x" * 50)
    assert (deviated.deviation, deviated.deviation_justification) == (True, "x" * 50)
    a = s.decide(TENANT, ANNA, aid, **rev(deviated), decision="freigabe_mit_auflagen")
    assert (a.deviation, a.deviation_justification, a.decided_by) == (False, None, "anna")

    assert raises(ConflictError, lambda: s.release(TENANT, BERT, aid, **rev(a))) == legacy_message(
        legacy, "dsfa-release-before-dsb"
    )
    assert raises(
        ConflictError,
        lambda: s.record_dpo_conclusion(TENANT, ANNA, aid, **rev(a), conclusion="Folgerung"),
    ) == legacy_message(legacy, "dsfa-conclusion-before-statement")
    assert raises(
        ValidationError,
        lambda: s.record_dpo_statement(TENANT, DORA, aid, **rev(a), vote="ja", statement="Text"),
    ) == legacy_message(legacy, "dsfa-statement-unknown-vote")
    assert raises(
        ValidationError,
        lambda: s.record_dpo_statement(
            TENANT, DORA, aid, **rev(a), vote="abgelehnt", statement="  "
        ),
    ) == legacy_message(legacy, "dsfa-statement-empty")
    a = s.record_dpo_statement(
        TENANT,
        DORA,
        aid,
        **rev(a),
        vote="abgelehnt",
        statement="Das Risiko ist nicht ausreichend gemindert.",
    )
    assert a.status is AssessmentStatus.DPO_INVOLVED
    assert raises(ConflictError, lambda: s.release(TENANT, BERT, aid, **rev(a))) == legacy_message(
        legacy, "dsfa-release-missing-necessity"
    )

    # Editing texts after the DPO statement resets decision and statement (DP-C10),
    # therefore the necessity is recorded here before the decision is repeated.
    a = s.update(
        TENANT,
        ANNA,
        aid,
        **rev(a),
        necessity="N",
        proportionality="V",
        data_subject_view="Nicht eingeholt.",
    )
    assert a.decision is None and a.dpo_vote is None
    a = s.decide(TENANT, ANNA, aid, **rev(a), decision="freigabe_mit_auflagen")
    a = s.record_dpo_statement(TENANT, DORA, aid, **rev(a), vote="abgelehnt", statement="Nein.")
    assert raises(ConflictError, lambda: s.release(TENANT, BERT, aid, **rev(a))) == legacy_message(
        legacy, "dsfa-release-rejected-without-conclusion"
    )
    assert raises(
        ValidationError,
        lambda: s.record_dpo_conclusion(TENANT, ANNA, aid, **rev(a), conclusion="zu kurz"),
    ) == legacy_message(legacy, "dsfa-conclusion-short")
    a = s.record_dpo_conclusion(TENANT, ANNA, aid, **rev(a), conclusion="f" * 50)
    assert raises(ConflictError, lambda: s.release(TENANT, BERT, aid, **rev(a))) == legacy_message(
        legacy, "dsfa-release-without-leadership"
    )
    a = s.record_dpo_conclusion(
        TENANT, ANNA, aid, **rev(a), conclusion="f" * 50, presented_to_leadership="Behördenleitung"
    )
    assert a.leadership_presented_to == "Behördenleitung" and a.leadership_presented_at

    released = s.release(TENANT, BERT, aid, **rev(a))
    assert released.status is AssessmentStatus.RELEASED and released.locked
    assert released.released_by == "bert"
    locked = legacy_message(legacy, "dsfa-decide-locked")
    assert (
        raises(
            LockedVersionError,
            lambda: s.decide(TENANT, ANNA, aid, **rev(released), decision="freigabe"),
        )
        == locked
    )
    assert raises(
        LockedVersionError,
        lambda: s.record_dpo_statement(
            TENANT, DORA, aid, **rev(released), vote="zugestimmt", statement="x"
        ),
    ) == legacy_message(legacy, "dsfa-statement-locked")
    assert (
        raises(
            LockedVersionError,
            lambda: s.update(TENANT, ANNA, aid, **rev(released), necessity="neu"),
        )
        == locked
    )


def test_self_release_is_refused_like_legacy(legacy: dict[str, Any]) -> None:
    w = world()
    a = ready(w)
    a = w.service.update(
        TENANT, ANNA, a.assessment_id, **rev(a), necessity="N", proportionality="V"
    )
    a = w.service.decide(TENANT, ANNA, a.assessment_id, **rev(a), decision="freigabe_mit_auflagen")
    a = w.service.record_dpo_statement(
        TENANT, DORA, a.assessment_id, **rev(a), vote="zugestimmt", statement="Keine Einwände."
    )
    self_releaser = actor("anna", "fach", "leitung")
    message = raises(
        FourEyesViolation,
        lambda: w.service.release(TENANT, self_releaser, a.assessment_id, **rev(a)),
    )
    expected = legacy_message(legacy, "dsfa-release-self")
    assert message.startswith("Vier-Augen-Prinzip verletzt: Die Kennung 'anna' hat")
    assert expected.startswith("Vier-Augen-Prinzip verletzt: Die Kennung 'anna' hat")


def test_missing_register_and_activity_messages_match_legacy(legacy: dict[str, Any]) -> None:
    w = world()
    assert raises(
        NotFoundError, lambda: w.service.start(TENANT, ANNA, "egal", dsgvo())
    ) == legacy_message(legacy, "dsfa-without-register")
    released_register(w, complete_activity(id="a1"))
    assert raises(
        NotFoundError, lambda: w.service.start(TENANT, ANNA, "unbekannt", dsgvo())
    ) == legacy_message(legacy, "dsfa-unknown-activity")


def test_conditional_agreement_requires_conclusion(legacy: dict[str, Any]) -> None:
    w = world()
    a = ready(w)
    a = w.service.update(
        TENANT, ANNA, a.assessment_id, **rev(a), necessity="N", proportionality="V"
    )
    a = w.service.decide(TENANT, ANNA, a.assessment_id, **rev(a), decision="freigabe_mit_auflagen")
    a = w.service.record_dpo_statement(
        TENANT,
        DORA,
        a.assessment_id,
        **rev(a),
        vote="zugestimmt_mit_auflagen",
        statement="Auflage.",
    )
    assert raises(
        ConflictError, lambda: w.service.release(TENANT, BERT, a.assessment_id, **rev(a))
    ) == legacy_message(legacy, "dsfa-conditional-release-no-conclusion")
    a = w.service.record_dpo_conclusion(
        TENANT, ANNA, a.assessment_id, **rev(a), conclusion="Auflage umgesetzt."
    )
    assert w.service.release(TENANT, BERT, a.assessment_id, **rev(a)).locked


def test_missing_scenario_guard_matches_legacy_wording(legacy: dict[str, Any]) -> None:
    w = world()
    released_register(w, complete_activity(id="a1"))
    a = w.service.start(TENANT, ANNA, "a1", dsgvo())
    a = w.service.update(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        answers=answers(edsa_01_bewerten=True),
        necessity="N",
        proportionality="V",
    )
    a = w.service.decide(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        decision="freigabe",
        justification="Nach Prüfung liegt nur ein Kriterium vor, kein hohes Risiko.",
    )
    # Deviation "freigabe" against "nur_schwellwert" means a DSFA; scenarios are then required.
    a = w.service.record_dpo_statement(
        TENANT, DORA, a.assessment_id, **rev(a), vote="zugestimmt", statement="Einverstanden."
    )
    message = raises(
        ConflictError, lambda: w.service.release(TENANT, BERT, a.assessment_id, **rev(a))
    )
    assert (
        message.split("(")[0]
        == legacy_message(legacy, "dsfa-conditional-release-no-scenario").split("(")[0]
    )


# ------------------------------------------------------ corrected behavior


def test_c01_empty_survey_cannot_be_decided_or_released(legacy: dict[str, Any]) -> None:
    # DP-C01: legacy released an assessment with empty answers as "nur_schwellwert".
    assert steps(legacy)["dsfa-empty-release"]["output"]["status"] == "freigegeben"
    assert steps(legacy)["dsfa-empty-release"]["output"]["antworten"] == {}
    w = world()
    released_register(w, complete_activity(id="a1"))
    a = w.service.start(TENANT, ANNA, "a1", dsgvo())
    assert a.proposal["recommendation"] == "unvollstaendig"
    message = raises(
        ConflictError,
        lambda: w.service.decide(
            TENANT, ANNA, a.assessment_id, **rev(a), decision="nur_schwellwert"
        ),
    )
    assert "unvollständig" in message
    a = w.service.record_dpo_statement(
        TENANT, DORA, a.assessment_id, **rev(a), vote="zugestimmt", statement="Keine Einwände."
    )
    blockers = w.service.release_blockers(a)
    assert any("Schwellwertanalyse ist unvollständig" in b for b in blockers)
    with pytest.raises(ConflictError):
        w.service.release(TENANT, BERT, a.assessment_id, **rev(a))


def test_c01_all_no_path_releases_without_dpia_content() -> None:
    w = world()
    released_register(w, complete_activity(id="a1"))
    a = w.service.start(TENANT, ANNA, "a1", dsgvo())
    a = w.service.update(TENANT, ANNA, a.assessment_id, **rev(a), answers=answers())
    a = w.service.decide(TENANT, ANNA, a.assessment_id, **rev(a), decision="nur_schwellwert")
    a = w.service.record_dpo_statement(
        TENANT, DORA, a.assessment_id, **rev(a), vote="zugestimmt", statement="Keine Einwände."
    )
    assert w.service.release(TENANT, BERT, a.assessment_id, **rev(a)).locked


def test_c09_unknown_decision_value_is_rejected(legacy: dict[str, Any]) -> None:
    # DP-C09: legacy stored "irgendwas" as decision.
    assert steps(legacy)["dsfa-decide-unknown-value"]["output"]["entscheidung"] == "irgendwas"
    w = world()
    a = ready(w)
    message = raises(
        ValidationError,
        lambda: w.service.decide(
            TENANT, ANNA, a.assessment_id, **rev(a), decision="irgendwas", justification="y" * 50
        ),
    )
    assert "Unbekannte Entscheidung" in message


def test_c10_content_change_resets_decision_and_dpo(legacy: dict[str, Any]) -> None:
    # DP-C10: legacy kept the DPO vote after the answers changed.
    kept = steps(legacy)["dsfa-save-content-after-statement"]["output"]
    assert kept["dsb_votum"] == "abgelehnt" and kept["entscheidung"] == "freigabe_mit_auflagen"
    w = world()
    a = ready(w)
    a = w.service.decide(TENANT, ANNA, a.assessment_id, **rev(a), decision="freigabe_mit_auflagen")
    a = w.service.record_dpo_statement(
        TENANT, DORA, a.assessment_id, **rev(a), vote="abgelehnt", statement="Nein."
    )
    same = w.service.update(TENANT, ANNA, a.assessment_id, **rev(a))
    assert same.decision == "freigabe_mit_auflagen" and same.dpo_vote == "abgelehnt"
    changed = w.service.update(
        TENANT,
        ANNA,
        same.assessment_id,
        **rev(same),
        answers=answers(art35_3_a=True, edsa_05_umfang=True),
    )
    assert changed.status is AssessmentStatus.DRAFT
    assert (changed.decision, changed.dpo_vote, changed.dpo_by) == (None, None, None)
    assert w.audit.events[-1].details["review_reset"] is True


def test_c11_consultation_must_be_documented(legacy: dict[str, Any]) -> None:
    # DP-C11: legacy released a "konsultation" result without any consultation record.
    assert steps(legacy)["dsfa-conditional-release"]["output"]["status"] == "freigegeben"
    w = world()
    released_register(w, complete_activity(id="a1"))
    a = w.service.start(TENANT, ANNA, "a1", dsgvo())
    a = w.service.update(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        answers=answers(art35_3_c=True),
        scenarios=[{**SCENARIO, "severity": 4, "likelihood": 4, "measures": []}],
        necessity="N",
        proportionality="V",
    )
    assert a.proposal["consultation_required"] is True
    a = w.service.decide(
        TENANT, ANNA, a.assessment_id, **rev(a), decision="konsultation_aufsichtsbehoerde"
    )
    a = w.service.record_dpo_statement(
        TENANT, DORA, a.assessment_id, **rev(a), vote="zugestimmt", statement="Konsultation nötig."
    )
    message = raises(
        ConflictError, lambda: w.service.release(TENANT, BERT, a.assessment_id, **rev(a))
    )
    assert "Aufsichtsbehörde" in message and "Art. 36 Abs. 1 DSGVO" in message
    with pytest.raises(ValidationError):
        w.service.record_consultation(
            TENANT,
            ANNA,
            a.assessment_id,
            **rev(a),
            authority=" ",
            result="r",
            consulted_on=date(2026, 9, 1),
        )
    with pytest.raises(ValidationError):
        w.service.record_consultation(
            TENANT,
            ANNA,
            a.assessment_id,
            **rev(a),
            authority="HBDI",
            result="r",
            consulted_on="2026",
        )  # type: ignore[arg-type]
    a = w.service.record_consultation(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        authority="HBDI",
        result="Keine Einwände",
        consulted_on=date(2026, 9, 1),
    )
    assert a.consultation is not None and a.consultation.recorded_by == "anna"
    assert w.service.release(TENANT, BERT, a.assessment_id, **rev(a)).locked

    lenient = world(require_consultation_record=False)
    released_register(lenient, complete_activity(id="a1"))
    b = lenient.service.start(TENANT, ANNA, "a1", dsgvo())
    b = lenient.service.update(
        TENANT,
        ANNA,
        b.assessment_id,
        **rev(b),
        answers=answers(art35_3_c=True),
        scenarios=[{**SCENARIO, "severity": 4, "likelihood": 4, "measures": []}],
        necessity="N",
        proportionality="V",
    )
    b = lenient.service.decide(
        TENANT, ANNA, b.assessment_id, **rev(b), decision="konsultation_aufsichtsbehoerde"
    )
    b = lenient.service.record_dpo_statement(
        TENANT, DORA, b.assessment_id, **rev(b), vote="zugestimmt", statement="ok"
    )
    assert lenient.service.release(TENANT, BERT, b.assessment_id, **rev(b)).locked


def test_c12_tenant_binding(legacy: dict[str, Any]) -> None:
    # DP-C12: legacy loaded a DSFA of tenant 1 for a request of tenant 2.
    observed = steps(legacy)["dsfa-foreign-tenant-load"]["output"]
    assert observed["mandant_id"] != observed["requested_by_tenant"]
    w = world()
    a = ready(w)
    with pytest.raises(NotFoundError):
        w.service.get(FOREIGN, FREMD, a.assessment_id)
    with pytest.raises(NotFoundError):
        w.service.decide(FOREIGN, FREMD, a.assessment_id, **rev(a), decision="freigabe")
    with pytest.raises(AuthorizationError):
        w.service.get(TENANT, FREMD, a.assessment_id)  # actor not member of tenant
    assert w.service.versions(FOREIGN, FREMD, "a1") == ()
    assert w.service.overview(FOREIGN, FREMD) == ()
    assert w.service.review_required(FOREIGN, FREMD) == ()


def test_c12_repository_returning_foreign_record_is_detected() -> None:
    w = world()
    a = ready(w)

    class Leaky(InMemoryAssessmentRepository):
        def get(self, tenant_id: str, assessment_id: str) -> Assessment | None:
            return replace(a, tenant_id="anderer")

    w.service.assessments = Leaky()
    with pytest.raises(TenantMismatchError):
        w.service.get(TENANT, ANNA, a.assessment_id)


def test_c13_all_editors_and_decider_are_excluded_from_release() -> None:
    # DP-C13: legacy compared the releaser only with the last editor.
    w = world()
    a = ready(w)
    a = w.service.update(TENANT, MAX, a.assessment_id, **rev(a), necessity="N", proportionality="V")
    a = w.service.update(TENANT, ANNA, a.assessment_id, **rev(a), data_subject_view="Sicht")
    a = w.service.decide(TENANT, CARL, a.assessment_id, **rev(a), decision="freigabe_mit_auflagen")
    a = w.service.record_dpo_statement(
        TENANT, DORA, a.assessment_id, **rev(a), vote="zugestimmt", statement="ok"
    )
    assert a.editors == ("anna", "max", "carl")
    for person in (MAX, actor("carl", "leitung")):
        with pytest.raises(FourEyesViolation):
            w.service.release(TENANT, person, a.assessment_id, **rev(a))
    assert w.service.release(TENANT, BERT, a.assessment_id, **rev(a)).released_by == "bert"


def test_c14_dpo_statement_is_attributed_and_dpo_cannot_release(legacy: dict[str, Any]) -> None:
    # DP-C14: legacy recorded the DPO statement without a person.
    assert not any(
        "dsb" in k and ("von" in k or "by" in k)
        for k in legacy["workflow"]["exports"]["report_record"]
    )
    w = world()
    a = ready(w)
    a = w.service.update(
        TENANT, ANNA, a.assessment_id, **rev(a), necessity="N", proportionality="V"
    )
    a = w.service.decide(TENANT, ANNA, a.assessment_id, **rev(a), decision="freigabe_mit_auflagen")
    dpo_and_lead = actor("dora", "dsb", "leitung")
    a = w.service.record_dpo_statement(
        TENANT, dpo_and_lead, a.assessment_id, **rev(a), vote="zugestimmt", statement="ok"
    )
    assert a.dpo_by == "dora" and a.dpo_at is not None
    message = raises(
        FourEyesViolation,
        lambda: w.service.release(TENANT, dpo_and_lead, a.assessment_id, **rev(a)),
    )
    assert "Art. 38" in message
    with pytest.raises(AuthorizationError):
        w.service.record_dpo_statement(
            TENANT, ANNA, a.assessment_id, **rev(a), vote="zugestimmt", statement="ok"
        )


# ------------------------------------------------------ lifecycle


def test_happy_path_with_audit_trail() -> None:
    w = world()
    a = ready(w)
    a = w.service.update(
        TENANT, ANNA, a.assessment_id, **rev(a), necessity="N", proportionality="V"
    )
    a = w.service.decide(TENANT, ANNA, a.assessment_id, **rev(a), decision="freigabe_mit_auflagen")
    a = w.service.record_dpo_statement(
        TENANT, DORA, a.assessment_id, **rev(a), vote="zugestimmt", statement="ok"
    )
    assert w.service.release_blockers(a) == ()
    released = w.service.release(TENANT, BERT, a.assessment_id, **rev(a))
    events = [e for e in w.audit.events if e.entity == "assessment"]
    assert [e.action for e in events] == [
        "assessment.created",
        "assessment.updated",
        "assessment.updated",
        "assessment.decided",
        "assessment.dpo_statement",
        "assessment.released",
    ]
    assert [e.actor_id for e in events] == ["anna", "anna", "anna", "anna", "dora", "bert"]
    assert all(e.tenant_id == TENANT and e.entity_id == released.assessment_id for e in events)
    assert events[-1].details["recommendation"] == "freigabe_mit_auflagen"
    assert released.profile_fingerprint == dsgvo().fingerprint
    assert released.register_version == 1 and released.activity_snapshot["id"] == "a1"
    with pytest.raises(LockedVersionError):
        w.assessments.replace(replace(released, necessity="x", revision=99), released.revision)


def _release(w: World, a: Assessment) -> Assessment:
    a = w.service.update(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        answers=answers(art35_3_a=True),
        scenarios=[SCENARIO],
        necessity="N",
        proportionality="V",
    )
    a = w.service.decide(
        TENANT, ANNA, a.assessment_id, **rev(a), decision=a.proposal["recommendation"]
    )
    a = w.service.record_dpo_statement(
        TENANT, DORA, a.assessment_id, **rev(a), vote="zugestimmt", statement="ok"
    )
    return w.service.release(TENANT, BERT, a.assessment_id, **rev(a))


def test_register_change_review_and_reassessment(legacy: dict[str, Any]) -> None:
    w = world()
    released_register(w, complete_activity(id="a1"), complete_activity(id="a2", name="Zweite"))
    first = _release(w, w.service.start(TENANT, ANNA, "a1", dsgvo()))
    second = _release(w, w.service.start(TENANT, ANNA, "a2", dsgvo()))
    assert w.service.review_required(TENANT, ANNA) == ()
    with pytest.raises(ConflictError, match="Nur eine freigegebene"):
        w.service.reassess(TENANT, ANNA, w.service.start(TENANT, CARL, "a1", dsgvo()).assessment_id)

    fresh = world()
    released_register(fresh, complete_activity(id="a1"), complete_activity(id="a2", name="Zweite"))
    first = _release(fresh, fresh.service.start(TENANT, ANNA, "a1", dsgvo()))
    second = _release(fresh, fresh.service.start(TENANT, ANNA, "a2", dsgvo()))
    w = fresh
    current = w.register.released(TENANT, ANNA)
    assert current is not None
    content = dict(current.content)
    content["taetigkeiten"] = [
        {
            **current.activities[0],
            "zweck": "Erweitert",
            "ansprechperson": "B",
            "anzahl_betroffene": 20000,
        },
    ]
    draft = w.register.save_draft(TENANT, ANNA, content)
    # Like legacy (changes-draft-over-release): an unreleased draft triggers nothing.
    assert steps(legacy)["changes-draft-over-release"]["output"] == []
    assert w.service.review_required(TENANT, ANNA) == ()
    w.register.release(TENANT, BERT, expected_revision=draft.revision)
    items = {i.activity_id: i for i in w.service.review_required(TENANT, ANNA)}
    assert items["a2"].reason == "Die Tätigkeit ist im Verzeichnis nicht mehr enthalten."
    assert [d["feld"] for d in items["a1"].differences] == ["zweck", "anzahl_betroffene"]
    legacy_reason = steps(legacy)["changes-after-release"]["output"][0]["grund"]
    assert items["a1"].reason == legacy_reason
    assert w.service.get(TENANT, ANNA, first.assessment_id).status is AssessmentStatus.RELEASED

    successor = w.service.reassess(TENANT, ANNA, first.assessment_id)
    assert (successor.version, successor.predecessor_id, successor.register_version) == (
        2,
        first.assessment_id,
        2,
    )
    assert [c["feld"] for c in successor.changes_to_predecessor] == ["zweck", "anzahl_betroffene"]
    assert successor.decision is None and successor.dpo_vote is None
    assert dict(successor.answers) == dict(first.answers)
    assert raises(
        ConflictError, lambda: w.service.reassess(TENANT, ANNA, first.assessment_id)
    ) == legacy_message(legacy, "reassessment-again")
    assert (
        raises(NotFoundError, lambda: w.service.reassess(TENANT, ANNA, second.assessment_id))
        == "Verarbeitungstätigkeit mit ID a2 nicht gefunden"
    )
    assert raises(
        ConflictError, lambda: w.service.start(TENANT, ANNA, "a1", dsgvo())
    ) == legacy_message(legacy, "reassessment-again")

    released2 = _release(w, successor)
    old = w.service.get(TENANT, ANNA, first.assessment_id)
    assert old.status is AssessmentStatus.SUPERSEDED and old.necessity == first.necessity
    assert released2.status is AssessmentStatus.RELEASED
    assert [v.version for v in w.service.versions(TENANT, ANNA, "a1")] == [2, 1]
    assert w.service.open_version(TENANT, ANNA, "a1") is None


def test_overview_and_department_filter() -> None:
    w = world()
    released_register(
        w,
        complete_activity(id="k", referat="Referat III – KPAnG-Vollzug"),
        complete_activity(id="z", name="Z", referat="Referat Z"),
        complete_activity(id="o", name="Ohne", referat=""),
    )
    w.service.start(TENANT, ANNA, "k", dsgvo())
    rows = w.service.overview(TENANT, ANNA)
    assert [r["id"] for r in rows] == ["k", "z", "o"]
    assert rows[0]["dsfa"]["status"] == "entwurf" and rows[1]["dsfa"] is None
    assert [r["id"] for r in w.service.overview(TENANT, ANNA, department="kpang")] == ["k", "o"]
    assert [r["position"] for r in w.service.overview(TENANT, ANNA, department="referat z")] == [
        2,
        3,
    ]
    prefill = w.service.prefill(TENANT, ANNA, "k", dsgvo())
    assert prefill == {}


def test_stale_revision_and_profile_integrity() -> None:
    w = world()
    a = ready(w)
    with pytest.raises(StaleRevisionError):
        w.service.update(TENANT, ANNA, a.assessment_id, expected_revision=a.revision - 1)
    changed = profile_from_dict(
        {
            **__import__("json").loads(
                __import__("importlib")
                .resources.files("auditcore_dataprotection.profiles")
                .joinpath("regulierung.dsgvo-2026.09.1.json")
                .read_text(encoding="utf-8")
            ),
            "legal_status": "geändert",
        }
    )
    tampered = AssessmentService(
        w.assessments,
        w.registers,
        w.service.authorizer,
        w.audit,
        w.clock,
        w.ids,
        resolve_profile=lambda _id, _version: changed,
    )
    with pytest.raises(ProfileError, match="Fingerprint"):
        tampered.decide(TENANT, ANNA, a.assessment_id, **rev(a), decision="freigabe_mit_auflagen")


def test_profile_switch_recalculates_with_ji_texts() -> None:
    w = world()
    a = ready(w)
    switched = w.service.update(TENANT, ANNA, a.assessment_id, **rev(a), profile=ji())
    assert switched.profile_id == "regulierung.hdsig_ji"
    assert switched.proposal["regime"] == "hdsig_ji"
    assert "§ 62 Abs. 1 HDSIG" in switched.proposal["reasoning"]


def test_update_validates_and_follows_register() -> None:
    w = world()
    a = ready(w)
    with pytest.raises(ValidationError):
        w.service.update(TENANT, ANNA, a.assessment_id, **rev(a), answers={"x": True})
    with pytest.raises(ValidationError):
        w.service.update(TENANT, ANNA, a.assessment_id, **rev(a), necessity=5)  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        w.service.decide(
            TENANT, ANNA, a.assessment_id, **rev(a), decision="freigabe", justification=None
        )  # type: ignore[arg-type]
    draft = w.register.save_draft(
        TENANT, ANNA, register_content(complete_activity(id="a1", zweck="Z2"))
    )
    w.register.release(TENANT, BERT, expected_revision=draft.revision)
    followed = w.service.update(TENANT, ANNA, a.assessment_id, **rev(a))
    assert followed.activity_snapshot["zweck"] == "Z2" and followed.register_version == 2


def test_deny_all_and_missing_actor() -> None:
    w = world()
    ready(w)
    denied = AssessmentService(
        InMemoryAssessmentRepository(),
        InMemoryRegisterRepository(),
        DenyAllAuthorizer(),
        ListAuditSink(),
        FixedClock(),
        SequentialIds(),
    )
    for call in (
        lambda: denied.get(TENANT, MAX, "x"),
        lambda: denied.start(TENANT, MAX, "a1", dsgvo()),
        lambda: denied.review_required(TENANT, MAX),
        lambda: w.service.get(TENANT, None, "x"),  # type: ignore[arg-type]
    ):
        with pytest.raises(AuthorizationError):
            call()
    assert issubclass(AuthorizationError, DataProtectionError)
    assert load_profile("regulierung.dsgvo", "2026.09.1") == dsgvo()
