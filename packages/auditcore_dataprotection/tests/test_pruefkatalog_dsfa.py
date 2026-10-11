"""Prüfkatalog VVT/DSFA, Abschnitt 12: Vorprüfung, DSFA und Konsultation (T-07 bis T-16)."""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest
from pruefkatalog_support import (
    CHEF,
    DSB,
    FACH,
    LEITUNG,
    TENANT,
    full_activity,
    hdsig,
    kat,
    new_register,
)

from auditcore_dataprotection.calculation import finalize_consultation, propose
from auditcore_dataprotection.errors import ConflictError, ValidationError
from auditcore_dataprotection.operation import DecisionRequest
from auditcore_dataprotection.operation_model import UrgentStart
from auditcore_dataprotection.screening import screen

LOW = [
    {"dimension": "vertraulichkeit", "description": "Fehlversand", "severity": 1, "likelihood": 1}
]


def all_no(**override: object) -> dict[str, object]:
    return {**{k: False for k in hdsig().question_keys}, **override}


def released_world(**activity: Any) -> tuple[Any, str]:
    world = kat()
    activity_id = new_register(world, full_activity(**activity))
    draft = world.register.draft(TENANT, FACH)
    assert draft is not None
    world.register.release(TENANT, LEITUNG, expected_revision=draft.revision)
    return world, activity_id


@pytest.mark.parametrize("value", [None, "", "unbekannt"], ids=["none", "leer", "unklar"])
def test_t07_offene_antwort_wird_nie_nein(value: object) -> None:
    profile = hdsig()
    answers = all_no(gesamt_01_sonstiges_hohes_risiko=value)
    if value == "":
        answers.pop("gesamt_01_sonstiges_hohes_risiko")
    result = screen(profile, answers)
    assert result.outcome == "unvollstaendig"


def test_t08_zwingende_fallgruppe_nicht_heruntergerechnet() -> None:
    profile = hdsig()
    hard = next(q.key for q in profile.questions if q.effect == "hart")
    assert screen(profile, all_no(**{hard: True})).outcome == "pflicht"


def test_t09_ein_gewichtiges_merkmal_ohne_typische_fallgruppe() -> None:
    result = screen(hdsig(), all_no(gesamt_01_sonstiges_hohes_risiko=True))
    assert result.outcome == "pflicht"


def _assessment_for(world: Any, activity_id: str, answers: dict[str, object]) -> Any:
    started = world.assessments.start(TENANT, FACH, activity_id, world.profile)
    return world.assessments.update(
        TENANT, FACH, started.assessment_id, expected_revision=started.revision, answers=answers
    )


def test_t10_keine_dsfa_ohne_eigene_begruendung_abgelehnt() -> None:
    world, activity_id = released_world()
    assessment = _assessment_for(world, activity_id, all_no())
    assert assessment.proposal["recommendation"] == "nur_schwellwert"
    with pytest.raises(ValidationError, match="eigene"):
        world.assessments.decide(
            TENANT,
            FACH,
            assessment.assessment_id,
            expected_revision=assessment.revision,
            decision="nur_schwellwert",
        )
    decided = world.assessments.decide(
        TENANT,
        FACH,
        assessment.assessment_id,
        expected_revision=assessment.revision,
        decision="nur_schwellwert",
        justification="Nur Stammdaten weniger Verfahrensbeteiligter, keine Bewertung, "
        "keine Zusammenführung; Risiken wurden einzeln geprüft.",
    )
    axes = world.workspace.evaluate(TENANT, FACH, activity_id).axes
    assert decided.decision_justification
    assert axes.necessity.value == "nicht_erforderlich_begruendet"


def test_t10_keine_dsfa_bei_unklarer_vorpruefung_unmoeglich() -> None:
    world, activity_id = released_world()
    assessment = _assessment_for(world, activity_id, all_no(gesamt_01_sonstiges_hohes_risiko=None))
    with pytest.raises(ConflictError, match="vollständige"):
        world.assessments.decide(
            TENANT,
            FACH,
            assessment.assessment_id,
            expected_revision=assessment.revision,
            decision="nur_schwellwert",
            justification="x" * 80,
        )


def test_t11_nur_angelegte_dsfa_ist_nicht_abgeschlossen() -> None:
    world, activity_id = released_world()
    _assessment_for(world, activity_id, all_no(gesamt_01_sonstiges_hohes_risiko=True))
    result = world.workspace.evaluate(TENANT, FACH, activity_id)
    assert result.axes.necessity.value == "erforderlich"
    assert result.axes.dpia_work.value == "nicht_begonnen"
    assert "GATE-03" in {g.id for g in result.gates}


def test_t12_geplante_massnahme_nicht_als_wirksam() -> None:
    world, activity_id = released_world(
        schutzmassnahmen=[{"key": "verschluesselung", "state": "geplant"}]
    )
    assessment = _assessment_for(world, activity_id, all_no(gesamt_01_sonstiges_hohes_risiko=True))
    scenario = {
        "dimension": "vertraulichkeit",
        "description": "Offenlegung",
        "severity": 3,
        "likelihood": 4,
        "measures": ["verschluesselung"],
    }
    world.assessments.update(
        TENANT,
        FACH,
        assessment.assessment_id,
        expected_revision=assessment.revision,
        scenarios=[scenario],
    )
    result = world.workspace.evaluate(TENANT, FACH, activity_id)
    assert result.unproven_measures == ("verschluesselung",)
    assert "GATE-06" in {g.id for g in result.gates}


def _dpia_done(world: Any, activity_id: str, answers: dict[str, object]) -> Any:
    assessment = _assessment_for(world, activity_id, answers)
    assessment = world.assessments.update(
        TENANT,
        FACH,
        assessment.assessment_id,
        expected_revision=assessment.revision,
        scenarios=LOW,
        necessity="Erforderlich für die Verfolgung",
        proportionality="Datensparsam, kein milderes Mittel",
    )
    return assessment


def test_t13_ohne_dsb_beteiligung_kein_abschluss() -> None:
    world, activity_id = released_world()
    assessment = _dpia_done(world, activity_id, all_no(gesamt_01_sonstiges_hohes_risiko=True))
    world.assessments.decide(
        TENANT,
        FACH,
        assessment.assessment_id,
        expected_revision=assessment.revision,
        decision=assessment.proposal["recommendation"],
    )
    result = world.workspace.evaluate(TENANT, FACH, activity_id)
    assert result.axes.dpia_work.value != "fachlich_abgeschlossen"
    assert "GATE-04" in {g.id for g in result.gates}


def test_t14_paragraf_64_nr_2_eigenstaendig_trotz_niedrigem_restrisiko() -> None:
    profile = hdsig()
    proposal = propose(profile, all_no(hdsig_64_1_nr2_form=True), LOW).to_dict()
    assert proposal["recommendation"] != "konsultation_aufsichtsbehoerde"  # Restrisiko gering
    assert proposal["screening"]["consultation_grounds"] == ["form_hochriskant"]
    final = finalize_consultation(profile, proposal, proposal["recommendation"])
    assert final["consultation_required"] is True
    assert "§ 64 Abs. 1 Satz 1 Nr. 2 HDSIG" in final["consultation_notice"]["text"]
    rejected = finalize_consultation(profile, proposal, "verworfen")
    assert rejected["consultation_required"] is False


def test_t15_kein_allgemeiner_override_waehrend_konsultation() -> None:
    world, activity_id = released_world(konsultation_eingeleitet_am="2026-09-01")
    _dpia_done(world, activity_id, all_no(hdsig_64_1_nr2_form=True))
    request = DecisionRequest(
        activity_id,
        "fuer_definierten_umfang_erteilt",
        "produktion",
        "1.0",
        "Pilot Referat A",
        "Betrieb soll trotz laufender Konsultation beginnen, weil es eilt.",
    )
    with pytest.raises(ConflictError, match="GATE-05"):
        world.operations.decide(TENANT, CHEF, request)
    sloppy = UrgentStart("eilt", "2026-09-01", "")
    with pytest.raises(ValidationError, match="Dringlichkeit"):
        world.operations.decide(
            TENANT, CHEF, DecisionRequest(**{**request.__dict__, "urgent": sloppy})
        )
    urgent = UrgentStart(
        "Gefahr erheblicher Rechtsverluste Dritter bei weiterem Zuwarten (synthetisch).",
        "2026-09-01",
        "Ergebnis der Konsultation binnen Frist umsetzen",
    )
    with pytest.raises(ConflictError, match="GATE-04") as refused:  # andere Sperren bleiben
        world.operations.decide(
            TENANT, CHEF, DecisionRequest(**{**request.__dict__, "urgent": urgent})
        )
    assert "GATE-05" not in str(refused.value)


def test_t16_dsb_einwaende_bleiben_sichtbar_keine_fingierte_zustimmung() -> None:
    world, activity_id = released_world()
    assessment = _dpia_done(world, activity_id, all_no(gesamt_01_sonstiges_hohes_risiko=True))
    stated = world.assessments.record_dpo_statement(
        TENANT,
        DSB,
        assessment.assessment_id,
        expected_revision=assessment.revision,
        vote="abgelehnt",
        statement="Löschkonzept fehlt; Zugriffsrechte zu weit.",
    )
    assert stated.dpo_vote == "abgelehnt"
    assert "Löschkonzept" in (stated.dpo_statement or "")
    result = world.workspace.evaluate(TENANT, FACH, activity_id)
    assert result.axes.operation.value == "nicht_beantragt"
    assert date(2026, 9, 1) <= world.clock.now().date()
