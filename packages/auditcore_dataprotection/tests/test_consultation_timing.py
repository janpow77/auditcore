"""DP-C21: consultation notice only after the final assessment (user decision A5).

Profile version 2026.10.2 gives the notice on the prior consultation of the
supervisory authority (Art. 36 Abs. 1 DSGVO, Erwägungsgrund 94 DSGVO) only
once the assessment is final and only if the net risk after measures is still
high. Before that the proposal carries at most a preliminary, clearly marked
notice. Profiles 2026.09.1 and 2026.10.1 and the legacy contract are unchanged.
"""

from __future__ import annotations

import copy
import json
from datetime import date
from importlib import resources
from typing import Any

import pytest
from support import ANNA, BERT, DORA, TENANT, World, complete_activity, released_register, world

from auditcore_dataprotection.calculation import finalize_consultation, propose
from auditcore_dataprotection.errors import ConflictError, ProfileError, ValidationError
from auditcore_dataprotection.export import assessment_report, render_assessment_html
from auditcore_dataprotection.model import Assessment
from auditcore_dataprotection.rules import (
    CONSULTATION_TIMING_FINAL,
    DECISION_REJECTED,
    NOTICE_NONE,
    NOTICE_NOT_REQUIRED,
    NOTICE_PRELIMINARY,
    NOTICE_REQUIRED,
    RECOMMENDATION_CONSULTATION,
    load_profile,
    profile_from_dict,
)

VERSION = "2026.10.2"
CONSULT = RECOMMENDATION_CONSULTATION

#: Gross 4 × 4 = 16, matrix band hoch.
HIGH_GROSS = {
    "dimension": "vertraulichkeit",
    "description": "Offenlegung der Verfahrensakte",
    "severity": 4,
    "likelihood": 4,
}
#: Measures lower both axes by two: net 2 × 2, band mittel (not hoch).
LOWERED = {**HIGH_GROSS, "measures": ["pseudonymisierung", "verschluesselung"]}
#: Measures lower the likelihood by one only: net 4 × 3, band still hoch.
STILL_HIGH = {**HIGH_GROSS, "measures": ["protokollierung"]}


def a5(profile_id: str = "auditcore.dsgvo") -> Any:
    return load_profile(profile_id, VERSION)


def raw(profile_id: str = "auditcore.dsgvo", version: str = VERSION) -> dict[str, Any]:
    entry = resources.files("auditcore_dataprotection.profiles").joinpath(
        f"{profile_id}-{version}.json"
    )
    return json.loads(entry.read_text(encoding="utf-8"))


def all_no(profile: Any) -> dict[str, bool]:
    return {q.key: False for q in profile.questions}


def required_answers(profile: Any) -> dict[str, bool]:
    return {**all_no(profile), "art35_3_a": True}


def rev(a: Assessment) -> dict[str, int]:
    return {"expected_revision": a.revision}


def assessed(w: World, scenario: dict[str, Any], profile: Any = None) -> Assessment:
    rules = profile or a5()
    released_register(w, complete_activity(id="a1"))
    a = w.service.start(TENANT, ANNA, "a1", rules)
    return w.service.update(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        answers=required_answers(rules),
        scenarios=[scenario],
        necessity="Erforderlich für den gesetzlichen Vollzug.",
        proportionality="Mildere Mittel geprüft.",
        dossier={"team": "Referat III, IT", "umfang": "Vollzug ohne Statistik"},
    )


def with_dpo(w: World, a: Assessment) -> Assessment:
    return w.service.record_dpo_statement(
        TENANT, DORA, a.assessment_id, **rev(a), vote="zugestimmt", statement="Keine Einwände."
    )


# ------------------------------------------------------------------ profile


@pytest.mark.parametrize("profile_id", ["auditcore.dsgvo", "auditcore.hdsig_ji"])
def test_profile_cites_legal_basis_and_decision(profile_id: str) -> None:
    profile = a5(profile_id)
    notice = profile.consultation_notice
    assert notice is not None and notice.timing == CONSULTATION_TIMING_FINAL
    assert "Art. 36 Abs. 1 DSGVO" in notice.legal_basis
    assert "Erwägungsgrund 94 DSGVO" in notice.legal_basis
    assert "A5" in notice.decision_reference and "23.09.2026" in notice.decision_reference
    assert notice.preliminary_text.startswith("Vorläufiger Hinweis:")
    assert "voraussichtlich erforderlich" in notice.preliminary_text
    assert "abschließende Bewertung" in notice.final_text
    assert raw(profile_id)["derived_from"] == {"id": profile_id, "version": "2026.10.1"}
    if profile_id == "auditcore.hdsig_ji":
        assert "§ 64 HDSIG" in notice.legal_basis


def test_profile_differs_from_2026_10_1_only_by_notice_and_identity() -> None:
    new, old = raw(), raw(version="2026.10.1")
    notice = new["recommendation"].pop("consultation_notice")
    assert notice["timing"] == CONSULTATION_TIMING_FINAL
    for key in ("version", "derived_from", "legal_status"):
        new.pop(key), old.pop(key)
    assert new == old


@pytest.mark.parametrize(
    "profile_id,version", [("regulierung.dsgvo", "2026.09.1"), ("auditcore.dsgvo", "2026.10.1")]
)
def test_earlier_profiles_keep_the_immediate_notice(profile_id: str, version: str) -> None:
    profile = load_profile(profile_id, version)
    assert profile.consultation_notice is None
    proposal = propose(profile, required_answers(profile), [STILL_HIGH])
    assert proposal.recommendation == CONSULT and proposal.consultation_required is True
    assert proposal.recommendation_text == profile.recommendation_texts[CONSULT]
    assert "consultation_notice" not in proposal.to_dict()
    assert finalize_consultation(profile, proposal.to_dict(), CONSULT) == proposal.to_dict()


def test_invalid_notice_sections_are_rejected() -> None:
    data = raw()
    broken = copy.deepcopy(data)
    broken["recommendation"]["consultation_notice"]["timing"] = "sofort"
    with pytest.raises(ProfileError, match="Zeitpunkt"):
        profile_from_dict(broken)
    broken = copy.deepcopy(data)
    broken["recommendation"]["consultation_notice"]["final_text"] = " "
    with pytest.raises(ProfileError, match="unvollständig"):
        profile_from_dict(broken)
    broken = copy.deepcopy(data)
    del broken["recommendation"]["consultation_notice"]["legal_basis"]
    with pytest.raises(ProfileError):
        profile_from_dict(broken)


# ------------------------------------------------------------ calculation


def test_proposal_gives_at_most_a_preliminary_notice() -> None:
    profile = a5()
    proposal = propose(profile, required_answers(profile), [STILL_HIGH])
    assert proposal.recommendation == CONSULT
    assert proposal.consultation_required is False
    notice = proposal.consultation_notice
    assert notice is not None
    assert notice["status"] == NOTICE_PRELIMINARY and notice["final"] is False
    assert proposal.recommendation_text == profile.consultation_notice.preliminary_text
    assert {"step": "consultation_notice", "status": NOTICE_PRELIMINARY} in proposal.trace


def test_high_gross_lowered_by_measures_gives_no_notice() -> None:
    profile = a5()
    proposal = propose(profile, required_answers(profile), [LOWERED])
    assert proposal.risk is not None
    assert proposal.risk.gross_band == "hoch" and proposal.risk.net_band == "mittel"
    assert proposal.recommendation == "freigabe_mit_auflagen"
    assert proposal.consultation_notice == {
        "timing": CONSULTATION_TIMING_FINAL,
        "final": False,
        "status": NOTICE_NONE,
        "text": "",
        "legal_basis": profile.consultation_notice.legal_basis,
    }
    final = finalize_consultation(profile, proposal.to_dict(), "freigabe_mit_auflagen")
    assert final["consultation_required"] is False
    assert final["consultation_notice"]["status"] == NOTICE_NOT_REQUIRED
    assert final["consultation_notice"]["final"] is True
    assert final["consultation_notice"]["net_risk_high"] is False


def test_incomplete_proposals_never_get_a_final_notice() -> None:
    profile = a5()
    no_scenario = propose(profile, required_answers(profile), [])
    assert no_scenario.recommendation == "unvollstaendig"
    assert no_scenario.consultation_notice is not None
    assert no_scenario.consultation_notice["status"] == NOTICE_NONE
    with pytest.raises(ValidationError, match="vollständige Bewertung"):
        finalize_consultation(profile, no_scenario.to_dict(), CONSULT)
    # A hard trigger with open questions still proposes; the notice stays preliminary.
    partial = propose(profile, {"art35_3_a": True}, [STILL_HIGH])
    assert partial.recommendation == CONSULT and not partial.screening.complete
    assert partial.consultation_notice is not None
    assert partial.consultation_notice["status"] == NOTICE_PRELIMINARY
    assert partial.consultation_required is False


# --------------------------------------------------------------- workflow


def test_high_net_risk_gives_final_notice_at_decision_and_blocks_release() -> None:
    w = world()
    a = assessed(w, STILL_HIGH)
    assert a.proposal["consultation_notice"]["status"] == NOTICE_PRELIMINARY
    assert a.proposal["consultation_required"] is False
    a = w.service.decide(TENANT, ANNA, a.assessment_id, **rev(a), decision=CONSULT)
    notice = a.proposal["consultation_notice"]
    assert notice["final"] is True and notice["status"] == NOTICE_REQUIRED
    assert notice["net_risk_high"] is True
    assert a.proposal["consultation_required"] is True
    assert a.proposal["recommendation_text"] == a5().consultation_notice.final_text
    assert w.audit.events[-1].details["consultation_notice"] == NOTICE_REQUIRED
    a = with_dpo(w, a)
    with pytest.raises(ConflictError, match="Art. 36 Abs. 1 DSGVO"):
        w.service.release(TENANT, BERT, a.assessment_id, **rev(a))
    a = w.service.record_consultation(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        authority="HBDI",
        result="Keine Bedenken bei Umsetzung der Maßnahmen.",
        consulted_on=date(2026, 9, 23),
        ground="hohes_restrisiko",
    )
    released = w.service.release(TENANT, BERT, a.assessment_id, **rev(a))
    assert released.locked


def test_lowered_risk_releases_without_consultation() -> None:
    w = world()
    a = assessed(w, LOWERED)
    assert a.proposal["recommendation"] == "freigabe_mit_auflagen"
    a = w.service.decide(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        decision="freigabe_mit_auflagen",
        conditions=["Pseudonymisierung vor Start aktiv"],
    )
    assert a.proposal["consultation_notice"]["status"] == NOTICE_NOT_REQUIRED
    assert a.proposal["consultation_required"] is False
    a = with_dpo(w, a)
    assert w.service.release_blockers(a) == ()
    assert w.service.release(TENANT, BERT, a.assessment_id, **rev(a)).locked


def test_voluntary_consultation_decision_still_requires_the_record() -> None:
    w = world()
    a = assessed(w, LOWERED)
    a = w.service.decide(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        decision=CONSULT,
        justification="Wir konsultieren freiwillig, weil das Vorhaben öffentlich umstritten ist.",
    )
    assert a.proposal["consultation_notice"]["status"] == NOTICE_NOT_REQUIRED
    a = with_dpo(w, a)
    assert any("Aufsichtsbehörde" in r for r in w.service.release_blockers(a))


def test_rejected_processing_needs_no_consultation() -> None:
    w = world()
    a = assessed(w, STILL_HIGH)
    a = w.service.decide(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        decision=DECISION_REJECTED,
        justification="Das Restrisiko ist nicht beherrschbar; die Verarbeitung unterbleibt.",
    )
    notice = a.proposal["consultation_notice"]
    assert notice["status"] == NOTICE_NOT_REQUIRED and notice["net_risk_high"] is True
    assert notice["text"] == a5().consultation_notice.rejected_text
    assert a.proposal["consultation_required"] is False
    a = with_dpo(w, a)
    assert w.service.release_blockers(a) == ()


def test_incomplete_assessment_cannot_be_decided_finally() -> None:
    w = world()
    released_register(w, complete_activity(id="a1"))
    a = w.service.start(TENANT, ANNA, "a1", a5())
    a = w.service.update(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        answers={"art35_3_a": True},
        scenarios=[STILL_HIGH],
    )
    assert a.proposal["recommendation"] == CONSULT
    with pytest.raises(ConflictError, match="nicht abschließend"):
        w.service.decide(TENANT, ANNA, a.assessment_id, **rev(a), decision=CONSULT)
    stored = w.service.get(TENANT, ANNA, a.assessment_id)
    assert stored.decision is None
    assert stored.proposal["consultation_notice"]["status"] == NOTICE_PRELIMINARY
    assert stored.proposal["consultation_required"] is False


def test_content_change_returns_to_the_preliminary_notice() -> None:
    w = world()
    a = assessed(w, STILL_HIGH)
    a = w.service.decide(TENANT, ANNA, a.assessment_id, **rev(a), decision=CONSULT)
    # Saving unchanged content keeps the decision and the final notice.
    a = w.service.update(TENANT, ANNA, a.assessment_id, **rev(a))
    assert a.decision == CONSULT
    assert a.proposal["consultation_notice"]["status"] == NOTICE_REQUIRED
    # A substantive change removes the decision; the notice is preliminary again.
    a = w.service.update(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        scenarios=[{**STILL_HIGH, "description": "Offenlegung durch Fehlversand"}],
    )
    assert a.decision is None
    assert a.proposal["consultation_notice"]["status"] == NOTICE_PRELIMINARY
    assert a.proposal["consultation_required"] is False


def test_report_marks_the_preliminary_and_the_final_notice() -> None:
    w = world()
    profile = a5()
    a = assessed(w, STILL_HIGH)
    report = assessment_report(a, profile)
    assert report["proposal"]["consultation_notice"]["status"] == NOTICE_PRELIMINARY
    html = render_assessment_html(report)
    assert "Hinweis zur Konsultation (vorläufig)" in html
    assert "noch nicht dokumentiert" not in html
    a = w.service.decide(TENANT, ANNA, a.assessment_id, **rev(a), decision=CONSULT)
    html = render_assessment_html(assessment_report(a, profile))
    assert "(vorläufig)" not in html and "noch nicht dokumentiert" in html


def test_schema1_report_has_no_notice_key() -> None:
    w = world()
    profile = load_profile("regulierung.dsgvo", "2026.09.1")
    released_register(w, complete_activity(id="a1"))
    a = w.service.start(TENANT, ANNA, "a1", profile)
    assert "consultation_notice" not in assessment_report(a, profile)["proposal"]
