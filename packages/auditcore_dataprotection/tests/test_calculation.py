"""Corrected calculation contract, each deviation checked against the legacy result.

Behavior-change identifiers (DP-Cnn) refer to ``docs/behavior-changes.md``.
"""

from __future__ import annotations

import copy
from typing import Any

import pytest
from support import all_no, answers, dsgvo, ji

from auditcore_dataprotection import legacy
from auditcore_dataprotection.calculation import (
    CALCULATION_VERSION,
    SCREENING_INCOMPLETE,
    SCREENING_NOT_REQUIRED,
    SCREENING_REQUIRED,
    Answer,
    AnswerValue,
    Scenario,
    assess_risk,
    parse_answer_list,
    parse_answers,
    parse_scenarios,
    prefill_from_activity,
    propose,
    screen,
)
from auditcore_dataprotection.errors import ValidationError

LA = legacy.LegacyAnswer
LS = legacy.LegacyScenario


def scenario(**values: Any) -> dict[str, Any]:
    return {
        "dimension": "vertraulichkeit",
        "description": "Szenario",
        "severity": 4,
        "likelihood": 4,
        **values,
    }


# ------------------------------------------------------------------ DP-C01


def test_c01_empty_answers_are_incomplete_not_no() -> None:
    # DP-C01: legacy treats a missing survey as "no DSFA needed".
    assert legacy.legacy_proposal([], [])["empfehlung"] == "nur_schwellwert"
    proposal = propose(dsgvo(), {})
    assert proposal.recommendation == "unvollstaendig"
    assert proposal.screening.outcome == SCREENING_INCOMPLETE
    assert len(proposal.screening.unanswered) == 18
    assert [i.code for i in proposal.blocking_issues] == ["unanswered_questions"]


def test_c01_explicit_unknown_is_kept_visible() -> None:
    # DP-C01: legacy bool(None) is "no".
    assert legacy.legacy_threshold([LA("art35_3_a", None)]).ergebnis == "keine_pflicht"
    parsed = parse_answers(
        {
            "art35_3_a": None,
            "art35_3_b": "unbekannt",
            "art35_3_c": {"ja": None, "begruendung": "offen"},
        },
        dsgvo(),
    )
    assert {k: a.value for k, a in parsed.items()} == {
        "art35_3_a": AnswerValue.UNKNOWN,
        "art35_3_b": AnswerValue.UNKNOWN,
        "art35_3_c": AnswerValue.UNKNOWN,
    }
    assert parsed["art35_3_c"].justification == "offen"
    result = screen(dsgvo(), {**all_no(), "edsa_01_bewerten": None})
    assert result.outcome == SCREENING_INCOMPLETE
    assert result.unknown == ("edsa_01_bewerten",)
    assert not result.complete


def test_all_no_is_not_required_and_documented() -> None:
    result = screen(dsgvo(), all_no())
    assert result.outcome == SCREENING_NOT_REQUIRED
    assert result.complete and result.fria_required is False
    assert "(Art. 5 Abs. 2 DSGVO)" in result.reasoning
    proposal = propose(dsgvo(), all_no())
    assert proposal.recommendation == "nur_schwellwert"
    assert proposal.issues == ()


# ------------------------------------------------------------------ DP-C02/03/04


def test_c02_unknown_question_keys_are_rejected() -> None:
    # DP-C02: legacy silently skips unknown keys.
    assert legacy.legacy_threshold([LA("erfunden", True)]).punkte == 0
    assert legacy.legacy_answers_from_json({"erfunden": True}) == []
    with pytest.raises(ValidationError, match="Unbekannte Fragen.*erfunden"):
        parse_answers({"erfunden": True}, dsgvo())
    with pytest.raises(ValidationError, match="unbekannte Felder"):
        parse_answers({"art35_3_a": {"ja": True, "extra": 1}}, dsgvo())
    with pytest.raises(ValidationError):
        parse_answers([("art35_3_a", True)], dsgvo())  # type: ignore[arg-type]


@pytest.mark.parametrize("value", ["false", "true", "0", 0, 1, 2.0, [], "Ja"])
def test_c03_truthy_values_are_rejected(value: Any) -> None:
    # DP-C03: legacy bool("false") is True.
    assert legacy.legacy_answers_from_json({"art35_3_a": "false"})[0].ja is True
    with pytest.raises(ValidationError, match="ja/nein"):
        parse_answers({"art35_3_a": value}, dsgvo())
    with pytest.raises(ValidationError):
        parse_answers({"art35_3_a": {"ja": value}}, dsgvo())


def test_accepted_answer_forms() -> None:
    parsed = parse_answers(
        {
            "art35_3_a": True,
            "art35_3_b": "nein",
            "art35_3_c": {"value": "ja", "justification": "J"},
            "dsk_01_telemetrie": Answer(AnswerValue.NO),
            "dsk_02_beschaeftigte": AnswerValue.YES,
        },
        dsgvo(),
    )
    assert [a.value for a in parsed.values()] == [
        AnswerValue.YES,
        AnswerValue.NO,
        AnswerValue.YES,
        AnswerValue.NO,
        AnswerValue.YES,
    ]
    assert parsed["art35_3_c"].to_dict() == {"value": "ja", "justification": "J"}
    with pytest.raises(ValidationError, match="Text"):
        parse_answers({"art35_3_a": {"ja": True, "begruendung": 5}}, dsgvo())


def test_c04_duplicate_criteria_are_rejected() -> None:
    # DP-C04: legacy counts the same criterion twice and reaches the threshold.
    duplicate = [LA("edsa_01_bewerten", True), LA("edsa_01_bewerten", True)]
    assert legacy.legacy_threshold(duplicate).ergebnis == "pflicht"
    with pytest.raises(ValidationError, match="mehrfach"):
        parse_answer_list([("edsa_01_bewerten", True), ("edsa_01_bewerten", True)], dsgvo())
    assert (
        parse_answer_list([("edsa_01_bewerten", True)], dsgvo())["edsa_01_bewerten"].value
        is AnswerValue.YES
    )


# ------------------------------------------------------------------ screening


def test_point_threshold_edges() -> None:
    one = screen(dsgvo(), answers(edsa_01_bewerten=True))
    two = screen(dsgvo(), answers(edsa_01_bewerten=True, edsa_05_umfang=True))
    assert (one.outcome, one.points) == (SCREENING_NOT_REQUIRED, 1)
    assert (two.outcome, two.points) == (SCREENING_REQUIRED, 2)
    assert two.point_criteria == ("edsa_01_bewerten", "edsa_05_umfang")
    assert "Ab 2 Kriterien" in two.reasoning


def test_hard_trigger_decides_even_with_open_questions() -> None:
    result = screen(dsgvo(), {"art35_3_a": True})
    assert result.outcome == SCREENING_REQUIRED
    assert result.hard_triggers == ("art35_3_a",)
    assert len(result.unanswered) == 17 and not result.complete
    proposal = propose(dsgvo(), {"art35_3_a": True}, [scenario()])
    assert proposal.recommendation == "konsultation_aufsichtsbehoerde"
    assert "unanswered_questions" in [i.code for i in proposal.blocking_issues]


def test_results_are_in_profile_order_not_input_order() -> None:
    result = screen(dsgvo(), {"dsk_03_biometrie": True, "art35_3_a": True})
    assert result.hard_triggers == ("art35_3_a", "dsk_03_biometrie")
    assert "2 Muss-Kriterien" in result.reasoning


def test_fria_marker_three_valued() -> None:
    assert screen(dsgvo(), answers(ki_01_hochrisiko=True)).fria_required is True
    assert (
        "Grundrechte-Folgenabschätzung" in screen(dsgvo(), answers(ki_01_hochrisiko=True)).reasoning
    )
    assert screen(dsgvo(), all_no()).fria_required is False
    open_fria = {k: v for k, v in all_no().items() if k != "ki_01_hochrisiko"}
    assert screen(dsgvo(), open_fria).fria_required is None


def test_ji_regime_texts_and_references() -> None:
    result = screen(ji(), answers(art35_3_a=True))
    assert "(§ 62 Abs. 1 HDSIG)" in result.reasoning
    assert "strengerer Maßstab" in result.reasoning
    assert ji().question("art35_3_a").reference in result.reasoning
    proposal = propose(ji(), answers(art35_3_a=True), [scenario(severity=1, likelihood=1)])
    assert proposal.recommendation_text == ji().recommendation_texts["freigabe"]
    assert "§ 62 Abs. 3 HDSIG" in proposal.recommendation_text
    assert proposal.consultation_reference == "§ 64 HDSIG"
    assert proposal.regime == "hdsig_ji"
    legacy_text = legacy.legacy_proposal(
        [LA("art35_3_a", True)], [LS("vertraulichkeit", "x", 1, 1)], "hdsig_ji"
    )
    assert legacy_text["empfehlung_text"] == proposal.recommendation_text


# ------------------------------------------------------------------ risk


@pytest.mark.parametrize(
    "severity,likelihood,band",
    [
        (1, 4, "gering"),
        (1, 5, None),
        (2, 2, "gering"),
        (1, 1, "gering"),
        (3, 3, "mittel"),
        (5, 2, None),
        (2, 5, None),
        (3, 4, "hoch"),
        (4, 4, "hoch"),
    ],
)
def test_risk_band_edges(severity: int, likelihood: int, band: str | None) -> None:
    if band is None:
        with pytest.raises(ValidationError, match="Skala"):
            assess_risk(dsgvo(), [scenario(severity=severity, likelihood=likelihood)])
        return
    result = assess_risk(dsgvo(), [scenario(severity=severity, likelihood=likelihood)])
    assert result.scenarios[0].gross_band == band
    assert result.gross_maximum == severity * likelihood


def test_band_boundaries_via_products() -> None:
    profile = dsgvo()
    assert (profile.band(4), profile.band(5), profile.band(9), profile.band(10)) == (
        "gering",
        "mittel",
        "mittel",
        "hoch",
    )


def test_measure_cap_two_and_floor_one() -> None:
    all_measures = [m.key for m in dsgvo().measures]
    result = assess_risk(dsgvo(), [scenario(measures=all_measures)])
    row = result.scenarios[0]
    assert (row.reduction_severity, row.reduction_likelihood) == (2, 2)
    assert (row.net_severity, row.net_likelihood, row.net) == (2, 2, 4)
    low = assess_risk(dsgvo(), [scenario(severity=1, likelihood=2, measures=["verschluesselung"])])
    assert (low.scenarios[0].net_severity, low.scenarios[0].net_likelihood) == (1, 1)
    legacy_row = legacy.legacy_risk([LS("vertraulichkeit", "x", 4, 4, tuple(all_measures))])
    assert legacy_row["netto_hoechstwert"] == result.net_maximum


def test_c05_duplicate_and_unknown_measures_are_rejected() -> None:
    # DP-C05: legacy applies a duplicated measure repeatedly and ignores unknown keys.
    doubled = legacy.legacy_risk([LS("vertraulichkeit", "x", 4, 4, ("protokollierung",) * 2)])
    assert doubled["szenarien"][0]["netto_wahrscheinlichkeit"] == 2
    assert (
        legacy.legacy_risk([LS("vertraulichkeit", "x", 4, 4, ("UNKNOWN",))])["netto_hoechstwert"]
        == 16
    )
    with pytest.raises(ValidationError, match="mehrfach"):
        parse_scenarios([scenario(measures=["protokollierung", "protokollierung"])], dsgvo())
    with pytest.raises(ValidationError, match="unbekannte Maßnahmen"):
        parse_scenarios([scenario(measures=["UNKNOWN"])], dsgvo())
    with pytest.raises(ValidationError, match="Liste"):
        parse_scenarios([scenario(measures="protokollierung")], dsgvo())


@pytest.mark.parametrize(
    "field,value",
    [
        ("residual_severity", 0),
        ("residual_likelihood", 5),
        ("residual_severity", -1),
        ("residual_severity", True),
        ("severity", "3"),
        ("likelihood", 2.9),
        ("severity", None),
    ],
)
def test_c06_values_outside_scale_are_rejected(field: str, value: Any) -> None:
    # DP-C06: legacy accepts explicit residual 0/9 and truncates floats/strings.
    net_zero = legacy.legacy_preview(
        {"art35_3_a": True},
        [
            {
                "schwere": 4,
                "wahrscheinlichkeit": 4,
                "netto_schwere": 0,
                "netto_wahrscheinlichkeit": 0,
            }
        ],
    )
    assert net_zero["empfehlung"] == "freigabe"
    assert (
        legacy.legacy_scenarios_from_json([{"schwere": 2.9, "wahrscheinlichkeit": 1}])[0].schwere
        == 2
    )
    with pytest.raises(ValidationError):
        parse_scenarios([scenario(**{field: value})], dsgvo())


def test_scenario_structure_is_validated() -> None:
    for bad in (
        scenario(dimension="UNKNOWN"),
        scenario(description=" "),
        scenario(extra=1),
        scenario(residual_justification=3),
        "kein-dict",
    ):
        with pytest.raises(ValidationError):
            parse_scenarios([bad], dsgvo())
    with pytest.raises(ValidationError, match="Liste"):
        parse_scenarios(scenario(), dsgvo())  # type: ignore[arg-type]
    parsed = parse_scenarios([Scenario("integritaet", "D", 2, 2)], dsgvo())
    assert parsed[0].dimension == "integritaet"


def test_c07_explicit_residual_needs_justification() -> None:
    # DP-C07: legacy takes explicit residual values without any reasoning.
    result = assess_risk(dsgvo(), [scenario(residual_severity=1, residual_likelihood=1)])
    assert result.net_maximum == 1
    assert result.scenarios[0].explicit_residual == ("severity", "likelihood")
    assert [(i.code, i.blocking) for i in result.issues] == [
        ("residual_without_justification", True)
    ]
    justified = assess_risk(
        dsgvo(), [scenario(residual_severity=1, residual_justification="Nachweis")]
    )
    assert justified.issues == ()
    assert justified.scenarios[0].net_likelihood == 4


def test_residual_above_gross_is_a_visible_note() -> None:
    result = assess_risk(
        dsgvo(),
        [
            scenario(
                severity=2, likelihood=2, residual_severity=3, residual_justification="Neubewertung"
            )
        ],
    )
    assert [(i.code, i.blocking) for i in result.issues] == [("residual_above_gross", False)]


def test_c08_required_without_scenarios_is_incomplete() -> None:
    # DP-C08: legacy recommends consultation when no scenario is recorded.
    assert (
        legacy.legacy_proposal([LA("art35_3_a", True)], [])["empfehlung"]
        == "konsultation_aufsichtsbehoerde"
    )
    proposal = propose(dsgvo(), answers(art35_3_a=True), [])
    assert proposal.recommendation == "unvollstaendig"
    assert proposal.consultation_required is False
    assert [i.code for i in proposal.blocking_issues] == ["risk_assessment_missing"]
    assert "(Art. 35 Abs. 7 lit. c DSGVO)" in proposal.recommendation_text


@pytest.mark.parametrize(
    "severity,likelihood,measures,expected,consult",
    [
        (4, 4, [], "konsultation_aufsichtsbehoerde", True),
        (2, 5 - 0, ["menschliche_aufsicht"], None, False),
        (3, 4, ["zugriffskontrolle"], "freigabe_mit_auflagen", False),
        (3, 3, ["verschluesselung"], "freigabe", False),
        (2, 5, [], None, False),
    ],
)
def test_recommendation_thresholds(
    severity: int, likelihood: int, measures: list[str], expected: str | None, consult: bool
) -> None:
    if expected is None:
        with pytest.raises(ValidationError):
            propose(
                dsgvo(),
                answers(art35_3_a=True),
                [scenario(severity=severity, likelihood=likelihood, measures=measures)],
            )
        return
    proposal = propose(
        dsgvo(),
        answers(art35_3_a=True),
        [scenario(severity=severity, likelihood=likelihood, measures=measures)],
    )
    assert proposal.recommendation == expected
    assert proposal.consultation_required is consult
    legacy_result = legacy.legacy_proposal(
        [LA("art35_3_a", True)],
        [LS("vertraulichkeit", "Szenario", severity, likelihood, tuple(measures))],
    )
    assert legacy_result["empfehlung"] == expected
    assert legacy_result["begruendung"] == proposal.reasoning


def test_consultation_from_net_ten() -> None:
    nine = propose(dsgvo(), answers(art35_3_a=True), [scenario(severity=3, likelihood=3)])
    twelve = propose(dsgvo(), answers(art35_3_a=True), [scenario(severity=3, likelihood=4)])
    assert (nine.recommendation, nine.consultation_required) == ("freigabe_mit_auflagen", False)
    assert (twelve.recommendation, twelve.consultation_required) == (
        "konsultation_aufsichtsbehoerde",
        True,
    )
    assert twelve.consultation_reference == "Art. 36 Abs. 1 DSGVO"


def test_proposal_names_profile_and_serialises() -> None:
    profile = dsgvo()
    proposal = propose(profile, answers(art35_3_a=True), [scenario(measures=["verschluesselung"])])
    data = proposal.to_dict()
    assert data["profile"] == {
        "id": "regulierung.dsgvo",
        "version": "2026.09.1",
        "fingerprint": profile.fingerprint,
    }
    assert data["calculation"] == CALCULATION_VERSION
    assert data["screening"]["complete"] is True
    assert data["risk"]["scenarios"][0]["measure_titles"] == [
        "Verschlüsselung bei Übertragung und Speicherung"
    ]
    steps = [t["step"] for t in data["trace"]]
    assert steps[0] == "criterion" and steps[-1] == "recommendation" and "risk" in steps


def test_inputs_are_not_mutated() -> None:
    raw_answers = {"art35_3_a": {"ja": True, "begruendung": "B"}}
    raw_scenarios = [scenario(measures=["verschluesselung"])]
    before = copy.deepcopy((raw_answers, raw_scenarios))
    propose(dsgvo(), raw_answers, raw_scenarios)
    assert (raw_answers, raw_scenarios) == before


# ------------------------------------------------------------------ prefill


@pytest.mark.parametrize(
    "count,large",
    [
        (9999, False),
        (10000, True),
        (10001, True),
        ("10000", True),
        (True, False),
        ("1e4", False),
        (-1, False),
        (None, False),
        (2.5, False),
    ],
)
def test_prefill_count_is_strict(count: Any, large: bool) -> None:
    suggestions = prefill_from_activity(
        dsgvo(), {"besondere_kategorien": True, "anzahl_betroffene": count}
    )
    assert suggestions["edsa_04_sensible_daten"].value is True
    assert ("edsa_05_umfang" in suggestions) is large
    assert ("art35_3_b" in suggestions) is large


def test_prefill_texts_and_flags() -> None:
    # Legacy says "über dem Anhaltswert" although the code uses >=; new text is exact.
    old = legacy.legacy_prefill({"anzahl_betroffene": 10000})
    assert "über dem Anhaltswert" in old["edsa_05_umfang"]["grund"]
    new = prefill_from_activity(dsgvo(), {"anzahl_betroffene": 10000})
    assert new["edsa_05_umfang"].reason == (
        "Das Verzeichnis nennt 10.000 betroffene Personen und erreicht damit den "
        "Anhaltswert von 10.000 oder liegt darüber."
    )
    # Only explicit True flags count (legacy bool(["x"]) / bool("false") are true).
    assert "edsa_04_sensible_daten" in legacy.legacy_prefill({"besondere_kategorien": "false"})
    assert prefill_from_activity(dsgvo(), {"besondere_kategorien": "false"}) == {}
    assert prefill_from_activity(dsgvo(), {"daten_art10": True})[
        "edsa_04_sensible_daten"
    ].reason.endswith("Artikel 10 DSGVO aus.")
    transfer = prefill_from_activity(dsgvo(), {"drittlandtransfer": True})
    assert transfer["edsa_06_abgleich"].value is False
    assert prefill_from_activity(dsgvo(), {}) == {}
