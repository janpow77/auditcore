"""Schema 2 profiles aligned with the EDPB DPIA template 2026 v1.0.

Covers the severity floor, the decision 'verworfen', conditions of a
conditional approval, the consultation ground, EDPB scenario fields, measure
status, the action plan, DPIA master data, hints and the report. Schema 1
profiles must behave exactly as before.
"""

from __future__ import annotations

import copy
import json
from datetime import date
from importlib import resources
from typing import Any

import pytest
from support import (
    ANNA,
    BERT,
    DORA,
    TENANT,
    World,
    complete_activity,
    dsgvo,
    released_register,
    world,
)

from auditcore_dataprotection.calculation import assess_risk, propose
from auditcore_dataprotection.errors import ConflictError, ProfileError, ValidationError
from auditcore_dataprotection.export import assessment_report, render_assessment_html
from auditcore_dataprotection.model import Assessment
from auditcore_dataprotection.rules import (
    DECISION_REJECTED,
    DECISIONS,
    PROFILE_SCHEMA_EDPB,
    load_profile,
    profile_from_dict,
)

VERSION = "2026.10.1"


def edpb() -> Any:
    return load_profile("regulierung.dsgvo", VERSION)


def edpb_ji() -> Any:
    return load_profile("regulierung.hdsig_ji", VERSION)


def raw(profile_id: str = "regulierung.dsgvo") -> dict[str, Any]:
    entry = resources.files("auditcore_dataprotection.profiles").joinpath(
        f"{profile_id}-{VERSION}.json"
    )
    return json.loads(entry.read_text(encoding="utf-8"))


def no_answers(profile: Any) -> dict[str, bool]:
    return {q.key: False for q in profile.questions}


SEVERE_UNLIKELY = {
    "dimension": "vertraulichkeit",
    "description": "Offenlegung der Verfahrensakte",
    "severity": 4,
    "likelihood": 1,
}


def rev(a: Assessment) -> dict[str, int]:
    return {"expected_revision": a.revision}


def started(w: World, profile: Any = None) -> Assessment:
    released_register(w, complete_activity(id="a1"))
    return w.service.start(TENANT, ANNA, "a1", profile or edpb())


def filled(w: World, **extra: Any) -> Assessment:
    a = started(w)
    return w.service.update(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        answers={**no_answers(edpb()), "art35_3_a": True},
        scenarios=[
            {
                "dimension": "vertraulichkeit",
                "description": "Unbefugter Zugriff",
                "severity": 3,
                "likelihood": 4,
                "measures": ["zugriffskontrolle"],
                "risk_source": "Innentäter mit zu weiten Rechten",
                "acceptance_inherent": "nicht_hinnehmbar",
                "acceptance_residual": "hinnehmbar",
            }
        ],
        necessity="N",
        proportionality="V",
        **{
            "dossier": {"team": "Referat III, IT", "umfang": "Vollzug KPAnG ohne Statistik"},
            "measure_status": {"zugriffskontrolle": "umgesetzt"},
            **extra,
        },
    )


# ------------------------------------------------------------------ profile


@pytest.mark.parametrize("profile_id", ["regulierung.dsgvo", "regulierung.hdsig_ji"])
def test_schema2_profiles_load_with_sources_and_derivation(profile_id: str) -> None:
    profile = load_profile(profile_id, VERSION)
    data = raw(profile_id)
    assert profile.schema == PROFILE_SCHEMA_EDPB and profile.edpb
    assert data["derived_from"] == {"id": profile_id, "version": "2026.09.1"}
    assert DECISION_REJECTED in profile.decisions and set(DECISIONS) <= set(profile.decisions)
    assert {s.key for s in profile.sources} >= {"edpb_dpia_template_2026", "wp248", "wp243"}
    assert "Art.-29-Datenschutzgruppe" in profile.criteria_label
    assert "Keine rechtliche Prüfung" in profile.legal_status
    assert all(m.category in profile.measure_categories for m in profile.measures)
    assert [f.key for f in profile.dossier_fields if f.required] == ["team", "umfang"]


def test_schema1_profiles_are_unchanged() -> None:
    old = dsgvo()
    assert not old.edpb and old.decisions == DECISIONS
    assert old.criteria_label == "Kriterien des Europäischen Datenschutzausschusses"
    assert old.severity_floors == () and old.dossier_fields == ()


def test_dsgvo_profile_knows_art_36_5_and_ji_profile_does_not() -> None:
    assert set(edpb().consultation_grounds) == {"hohes_restrisiko", "nationales_recht"}
    assert edpb().consultation_grounds["nationales_recht"][1] == "Art. 36 Abs. 5 DSGVO"
    assert set(edpb_ji().consultation_grounds) == {"hohes_restrisiko"}


@pytest.mark.parametrize(
    "mutate,message",
    [
        (lambda d: d["recommendation"]["decisions"].pop(), "verworfen"),
        (lambda d: d["recommendation"].__setitem__("consultation_grounds", []), "Konsultation"),
        (lambda d: d["risk"]["severity_floors"][0].__setitem__("min_band", "x"), "Mindeststufe"),
        (lambda d: d["risk"]["measures"][0].__setitem__("category", "x"), "Kategorie"),
        (lambda d: d["dossier"]["fields"][0].__setitem__("kind", "zahl"), "Feldart"),
        (lambda d: d.__setitem__("sources", []), "Quellen"),
        (lambda d: d["workflow"].__setitem__("conditions_required_for", ["x"]), "Bedingungen"),
        (lambda d: d.pop("dossier"), "unvollständig"),
    ],
)
def test_schema2_validation_is_strict(mutate: Any, message: str) -> None:
    data = copy.deepcopy(raw())
    mutate(data)
    with pytest.raises(ProfileError, match=message):
        profile_from_dict(data)


# ------------------------------------------------------------ calculation


KP18 = {
    4: ["mittel", "hoch", "hoch", "hoch"],
    3: ["mittel", "mittel", "hoch", "hoch"],
    2: ["mittel", "mittel", "mittel", "mittel"],
    1: ["gering", "gering", "mittel", "mittel"],
}


def test_matrix_follows_dsk_kurzpapier_18() -> None:
    profile = edpb()
    for severity, row in KP18.items():
        assert [profile.matrix_band(severity, lik) for lik in range(1, 5)] == row
    assert profile.band_recommendations == {
        "gering": "freigabe",
        "mittel": "freigabe_mit_auflagen",
        "hoch": "konsultation_aufsichtsbehoerde",
    }


@pytest.mark.parametrize(
    "severity,likelihood,band,recommendation",
    [
        (4, 1, "mittel", "freigabe_mit_auflagen"),
        (4, 2, "hoch", "konsultation_aufsichtsbehoerde"),
        (3, 1, "mittel", "freigabe_mit_auflagen"),
        (1, 4, "mittel", "freigabe_mit_auflagen"),
        (1, 2, "gering", "freigabe"),
        (3, 3, "hoch", "konsultation_aufsichtsbehoerde"),
    ],
)
def test_schema2_bands_come_from_the_matrix(
    severity: int, likelihood: int, band: str, recommendation: str
) -> None:
    scenario = {**SEVERE_UNLIKELY, "severity": severity, "likelihood": likelihood}
    risk = assess_risk(edpb(), [scenario])
    assert risk.scenarios[0].net_band == band and risk.method == "matrix"
    proposal = propose(edpb(), {**no_answers(edpb()), "art35_3_a": True}, [scenario])
    assert proposal.recommendation == recommendation
    assert f"in der Stufe {band}" in proposal.reasoning
    assert proposal.trace[-2]["method"] == "matrix"


def test_schema1_keeps_product_bands() -> None:
    risk = assess_risk(dsgvo(), [SEVERE_UNLIKELY])
    assert risk.scenarios[0].net_band == "gering" and risk.method is None
    proposal = propose(dsgvo(), {**no_answers(dsgvo()), "art35_3_a": True}, [SEVERE_UNLIKELY])
    assert proposal.recommendation == "freigabe"
    assert "method" not in proposal.to_dict()["risk"]


def _profile_with_low_cell() -> Any:
    data = copy.deepcopy(raw())
    data["risk"]["matrix"]["2"]["1"] = "gering"
    return profile_from_dict(data)


def test_floor_depends_on_severity_before_measures() -> None:
    profile = _profile_with_low_cell()
    reduced = {**SEVERE_UNLIKELY, "measures": ["pseudonymisierung"]}
    scenario = assess_risk(profile, [reduced]).scenarios[0]
    assert (scenario.net_severity, scenario.net_likelihood) == (2, 1)
    assert scenario.net_band == "mittel" and "Fn. 9" in scenario.edpb["net_floor"]
    proposal = propose(profile, {**no_answers(profile), "art35_3_a": True}, [reduced])
    assert proposal.recommendation == "freigabe_mit_auflagen"
    assert "Schwere vor Maßnahmen" in proposal.reasoning and proposal.trace[-2]["floored"] == [1]


def test_explicit_justified_residual_severity_lifts_the_floor() -> None:
    profile = _profile_with_low_cell()
    explicit = {
        **SEVERE_UNLIKELY,
        "residual_severity": 2,
        "residual_justification": "Nur Pseudonyme verlassen das System.",
    }
    scenario = assess_risk(profile, [explicit]).scenarios[0]
    assert scenario.net_band == "gering" and scenario.edpb["net_floor"] is None


def test_screening_names_article_29_working_party() -> None:
    answers = {**no_answers(edpb()), "edsa_01_bewerten": True, "edsa_03_ueberwachung": True}
    assert "Art.-29-Datenschutzgruppe" in propose(edpb(), answers).screening.reasoning
    assert "Europäischen Datenschutzausschusses erfüllt" in (
        propose(
            dsgvo(), {**no_answers(dsgvo()), **{k: v for k, v in answers.items()}}
        ).screening.reasoning
    )


def test_edpb_scenario_fields_only_in_schema2() -> None:
    scenario = {
        **SEVERE_UNLIKELY,
        "risk_source": "Angreifer",
        "acceptance_inherent": "nicht_hinnehmbar",
        "acceptance_residual": "hinnehmbar",
    }
    result = assess_risk(edpb(), [scenario]).scenarios[0]
    assert result.edpb["risk_source"] == "Angreifer"
    assert result.edpb["acceptance_inherent_title"] == "nicht hinnehmbar"
    assert result.edpb["acceptance_residual_title"] == "hinnehmbar"
    with pytest.raises(ValidationError, match="Schema 2"):
        assess_risk(dsgvo(), [scenario])
    with pytest.raises(ValidationError, match="unbekannte Bewertung"):
        assess_risk(edpb(), [{**SEVERE_UNLIKELY, "acceptance_residual": "egal"}])
    with pytest.raises(ValidationError, match="unbekannte Felder"):
        assess_risk(edpb(), [{**SEVERE_UNLIKELY, "acceptance": "hinnehmbar"}])


# ---------------------------------------------------------------- workflow


def test_documentation_is_validated_and_stored() -> None:
    w = world()
    a = filled(
        w, action_plan=[{"activity": "MFA einführen", "responsible": "IT", "due": "2026-12-01"}]
    )
    assert a.dossier == {"team": "Referat III, IT", "umfang": "Vollzug KPAnG ohne Statistik"}
    assert a.measure_status == {"zugriffskontrolle": {"status": "umgesetzt", "note": ""}}
    assert a.action_plan == (
        {"activity": "MFA einführen", "responsible": "IT", "due": "2026-12-01"},
    )
    s = w.service
    for kwargs, message in [
        ({"dossier": {"unbekannt": "x"}}, "Unbekanntes Feld"),
        ({"dossier": {"beginn": "morgen"}}, "Datum"),
        ({"dossier": {"veroeffentlichung": "vielleicht"}}, "unbekannte Auswahl"),
        ({"measure_status": {"zugriffskontrolle": "fertig"}}, "unbekannter Stand"),
        ({"measure_status": {"x": "umgesetzt"}}, "Unbekannte Maßnahme"),
        ({"action_plan": [{"activity": "x"}]}, "responsible"),
    ]:
        with pytest.raises(ValidationError, match=message):
            s.update(TENANT, ANNA, a.assessment_id, **rev(a), **kwargs)


def test_documentation_is_refused_for_schema1() -> None:
    w = world()
    a = started(w, dsgvo())
    with pytest.raises(ValidationError, match="Schema 2"):
        w.service.update(TENANT, ANNA, a.assessment_id, **rev(a), dossier={"team": "x"})


def test_documentation_change_resets_review() -> None:
    w = world()
    a = filled(w)
    a = w.service.decide(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        decision=a.proposal["recommendation"],
        conditions=["MFA vor Start"],
    )
    a = w.service.record_dpo_statement(
        TENANT, DORA, a.assessment_id, **rev(a), vote="zugestimmt", statement="ok"
    )
    a = w.service.update(
        TENANT, ANNA, a.assessment_id, **rev(a), dossier={"team": "neu", "umfang": "u"}
    )
    assert a.decision is None and a.dpo_vote is None and a.conditions == ()


def test_status_and_plan_changes_keep_the_review() -> None:
    w = world()
    a = filled(w)
    a = w.service.decide(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        decision="freigabe_mit_auflagen",
        conditions=["MFA vor Start"],
    )
    a = w.service.record_dpo_statement(
        TENANT, DORA, a.assessment_id, **rev(a), vote="zugestimmt", statement="ok"
    )
    a = w.service.update(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        measure_status={"zugriffskontrolle": "teilweise_umgesetzt"},
        action_plan=[{"activity": "MFA", "responsible": "IT", "measure": "zugriffskontrolle"}],
    )
    assert a.decision == "freigabe_mit_auflagen" and a.dpo_vote == "zugestimmt"
    assert a.conditions == ("MFA vor Start",)
    assert a.measure_status["zugriffskontrolle"]["status"] == "teilweise_umgesetzt"


def test_switch_back_to_schema1_is_refused() -> None:
    w = world()
    a = filled(w)
    with pytest.raises(ValidationError, match="nicht möglich"):
        w.service.update(TENANT, ANNA, a.assessment_id, **rev(a), profile=dsgvo())
    a = w.service.decide(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        decision="freigabe_mit_auflagen",
        conditions=["MFA"],
    )
    a = w.service.record_dpo_statement(
        TENANT, DORA, a.assessment_id, **rev(a), vote="zugestimmt", statement="ok"
    )
    released = w.service.release(TENANT, BERT, a.assessment_id, **rev(a))
    with pytest.raises(ValidationError, match="nicht möglich"):
        w.service.reassess(TENANT, ANNA, released.assessment_id, profile=dsgvo())


def test_conditional_approval_requires_conditions() -> None:
    w = world()
    a = filled(w)
    assert a.proposal["recommendation"] == "freigabe_mit_auflagen"
    with pytest.raises(ValidationError, match="Bedingung"):
        w.service.decide(TENANT, ANNA, a.assessment_id, **rev(a), decision="freigabe_mit_auflagen")
    with pytest.raises(ValidationError, match="keine Bedingungen"):
        w.service.decide(
            TENANT,
            ANNA,
            a.assessment_id,
            **rev(a),
            decision="konsultation_aufsichtsbehoerde",
            justification="x" * 60,
            conditions=["y"],
        )
    a = w.service.decide(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        decision="freigabe_mit_auflagen",
        conditions=[" Mehrfaktor-Anmeldung aktiv ", ""],
    )
    assert a.conditions == ("Mehrfaktor-Anmeldung aktiv",)


def test_rejected_needs_justification_and_no_consultation() -> None:
    w = world()
    a = started(w)
    a = w.service.update(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        answers={**no_answers(edpb()), "art35_3_a": True},
        scenarios=[{**SEVERE_UNLIKELY, "likelihood": 4}],
        necessity="N",
        proportionality="V",
        dossier={"team": "T", "umfang": "U"},
    )
    assert a.proposal["consultation_required"] is True
    with pytest.raises(ValidationError, match="begründen"):
        w.service.decide(TENANT, ANNA, a.assessment_id, **rev(a), decision=DECISION_REJECTED)
    a = w.service.decide(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        decision=DECISION_REJECTED,
        justification="Das Restrisiko ist nicht beherrschbar; die Verarbeitung unterbleibt.",
    )
    a = w.service.record_dpo_statement(
        TENANT, DORA, a.assessment_id, **rev(a), vote="zugestimmt", statement="ok"
    )
    assert w.service.release_blockers(a) == ()
    released = w.service.release(TENANT, BERT, a.assessment_id, **rev(a))
    assert released.decision == DECISION_REJECTED
    html = render_assessment_html(assessment_report(released, edpb()))
    assert "noch nicht dokumentiert" not in html


def test_rejected_follows_a_rejecting_dpo_without_leadership_submission() -> None:
    w = world()
    a = filled(w)
    a = w.service.decide(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        decision=DECISION_REJECTED,
        justification="Die Datenschutzbeauftragte rät ab; die Verarbeitung unterbleibt.",
    )
    a = w.service.record_dpo_statement(
        TENANT, DORA, a.assessment_id, **rev(a), vote="abgelehnt", statement="Nicht vertretbar."
    )
    assert w.service.release_blockers(a) == ()


def test_rejected_is_unknown_in_schema1() -> None:
    w = world()
    a = started(w, dsgvo())
    a = w.service.update(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        answers={**no_answers(dsgvo()), "art35_3_a": True},
        scenarios=[SEVERE_UNLIKELY],
    )
    with pytest.raises(ValidationError, match="Unbekannte Entscheidung"):
        w.service.decide(
            TENANT,
            ANNA,
            a.assessment_id,
            **rev(a),
            decision=DECISION_REJECTED,
            justification="x" * 60,
        )


def test_consultation_ground_required_in_schema2() -> None:
    w = world()
    a = filled(w)
    with pytest.raises(ValidationError, match="Grund der Konsultation"):
        w.service.record_consultation(
            TENANT,
            ANNA,
            a.assessment_id,
            **rev(a),
            authority="HBDI",
            result="keine Bedenken",
            consulted_on=date(2026, 9, 1),
        )
    a = w.service.record_consultation(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        authority="HBDI",
        result="keine Bedenken",
        consulted_on=date(2026, 9, 1),
        ground="nationales_recht",
    )
    assert a.consultation is not None and a.consultation.ground == "nationales_recht"
    assert w.audit.events[-1].details["ground"] == "nationales_recht"
    for ground, message in [(["x"], "Grund der Konsultation"), ("hohes_restrisiko", "kein hohes")]:
        with pytest.raises(ValidationError, match=message):
            w.service.record_consultation(
                TENANT,
                ANNA,
                a.assessment_id,
                **rev(a),
                authority="HBDI",
                result="r",
                consulted_on=date(2026, 9, 1),
                ground=ground,
            )


def test_required_master_data_blocks_release() -> None:
    w = world()
    a = filled(w)
    a = w.service.update(TENANT, ANNA, a.assessment_id, **rev(a), dossier={"team": "T"})
    a = w.service.decide(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        decision="freigabe_mit_auflagen",
        conditions=["MFA"],
    )
    a = w.service.record_dpo_statement(
        TENANT, DORA, a.assessment_id, **rev(a), vote="zugestimmt", statement="ok"
    )
    blockers = w.service.release_blockers(a)
    assert len(blockers) == 1 and "Umfang der Abschätzung" in blockers[0]
    with pytest.raises(ConflictError, match="Umfang"):
        w.service.release(TENANT, BERT, a.assessment_id, **rev(a))


def test_hints_follow_the_template() -> None:
    w = world()
    a = filled(w, measure_status={"zugriffskontrolle": "geplant"})
    hints = w.service.hints(a)
    assert any("nicht im Maßnahmenplan" in h for h in hints)
    assert any("Abschnitt 2.3" in h for h in hints)
    a = w.service.update(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        action_plan=[{"activity": "MFA", "responsible": "IT", "measure": "zugriffskontrolle"}],
    )
    assert not any("nicht im Maßnahmenplan" in h for h in w.service.hints(a))
    w2 = world()
    b = started(w2, dsgvo())
    assert w2.service.hints(b) == ()


def test_ji_hints_skip_areas_without_catalogue_measures() -> None:
    w = world()
    a = started(w, edpb_ji())
    a = w.service.update(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        scenarios=[{**SEVERE_UNLIKELY, "measures": ["zugriffskontrolle"]}],
        measure_status={
            "zugriffskontrolle": "umgesetzt",
            "loeschkonzept": "umgesetzt",
            "menschliche_aufsicht": "umgesetzt",
            "pseudonymisierung": "umgesetzt",
        },
    )
    assert not any("Abschnitt 2.3" in h for h in w.service.hints(a))


def test_reassessment_carries_documentation() -> None:
    w = world()
    a = filled(w)
    a = w.service.decide(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        decision="freigabe_mit_auflagen",
        conditions=["MFA"],
    )
    a = w.service.record_dpo_statement(
        TENANT, DORA, a.assessment_id, **rev(a), vote="zugestimmt", statement="ok"
    )
    released = w.service.release(TENANT, BERT, a.assessment_id, **rev(a))
    assert any(e.details.get("conditions") == ["MFA"] for e in w.audit.events)
    follow = w.service.reassess(TENANT, ANNA, released.assessment_id)
    assert follow.dossier == released.dossier and follow.measure_status == released.measure_status
    assert follow.conditions == () and follow.decision is None
    assert assessment_report(follow, edpb())["edpb"]["occasion"].startswith("Neubewertung")


# ------------------------------------------------------------------ report


def test_report_keeps_layout_and_adds_template_details() -> None:
    w = world()
    a = filled(w)
    a = w.service.decide(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        decision="freigabe_mit_auflagen",
        conditions=["MFA vor Start"],
    )
    report = assessment_report(a, edpb())
    section = report["edpb"]
    assert section["occasion"] == "Erstmalige Abschätzung der Verarbeitungstätigkeit"
    assert "DSK-Kurzpapiers Nr. 18" in section["method"]
    assert {s["key"] for s in section["sources"]} >= {"edpb_dpia_template_2026", "wp248"}
    assert section["measures"][0]["category_title"] == "Sicherheit der Verarbeitung"
    assert report["decision"]["decision_title"] == "Freigabe mit Auflagen"
    html = render_assessment_html(report)
    for heading in (
        "1. Gegenstand der Verarbeitung",
        "2. Schwellwertanalyse",
        "3. Notwendigkeit und Verhältnismäßigkeit",
        "4. Risiken und vorgesehene Maßnahmen",
        "5. Vorschlag, Entscheidung und Beteiligung",
    ):
        assert heading in html
    assert "Maßnahmen nach Bereichen und Umsetzungsstand" in html
    assert "Bedingungen vor Beginn der Verarbeitung" in html and "MFA vor Start" in html
    assert "Grundlagen der Abschätzung" in html and "Risikoquelle: Innentäter" in html
    assert "Risiko vor Maßnahmen nicht hinnehmbar" in html and "Restrisiko hinnehmbar" in html
    assert "Methode: Schwere und Eintrittswahrscheinlichkeit" in html


def test_schema1_report_has_no_template_section() -> None:
    w = world()
    a = started(w, dsgvo())
    a = w.service.update(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        answers={**no_answers(dsgvo()), "art35_3_a": True},
        scenarios=[{**SEVERE_UNLIKELY, "likelihood": 4}],
    )
    a = w.service.record_consultation(
        TENANT,
        ANNA,
        a.assessment_id,
        **rev(a),
        authority="HBDI",
        result="r",
        consulted_on=date(2026, 9, 1),
    )
    report = assessment_report(a, dsgvo())
    assert "edpb" not in report
    assert "decision_title" not in report["decision"] and "conditions" not in report["decision"]
    assert "ground" not in report["consultation"]
    html = render_assessment_html(report)
    assert "Grundlagen der Abschätzung" not in html and "Anlass der Abschätzung" not in html


def test_screening_only_needs_no_dpia_master_data() -> None:
    w = world()
    a = started(w)
    a = w.service.update(TENANT, ANNA, a.assessment_id, **rev(a), answers=no_answers(edpb()))
    a = w.service.decide(TENANT, ANNA, a.assessment_id, **rev(a), decision="nur_schwellwert")
    a = w.service.record_dpo_statement(
        TENANT, DORA, a.assessment_id, **rev(a), vote="zugestimmt", statement="ok"
    )
    assert w.service.release_blockers(a) == ()
