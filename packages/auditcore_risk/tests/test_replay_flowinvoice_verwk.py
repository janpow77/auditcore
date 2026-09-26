"""RK-L: VerwK point scores of flowinvoice (intermediate-body RBVK, ex-ante) are reproduced.

Fixture: ``tools/capture_flowinvoice_verwk_scores.py`` traced the unchanged,
blob-verified scoring functions of flowinvoice@fb2d185 (Python 3.12 like
``Dockerfile.verwk``) on three demo-generator data sets and 60 synthetic
Mittelabruf frames.
"""

from __future__ import annotations

from typing import Any

import pytest
from conftest import decode, fixture

from auditcore_risk import ProfileError, evaluate, load_profile

FIXTURE = fixture("flowinvoice_verwk_scores_observed.json")
V = "fb2d18568d2e"
RBVK = load_profile("flowinvoice.rbvk_intermediate_body", V)
HEUR = load_profile("flowinvoice.exante_heuristik", V)
BASIS = load_profile("flowinvoice.exante_basis", V)
LABEL_TO_CODE = {r.label: r.code for r in BASIS.rules}


def legacy_stage(score: int) -> str:
    return "keine_pruefung" if score < 8 else "teilpruefung" if score < 19 else "vollpruefung"


@pytest.mark.parametrize("case", FIXTURE["rbvk"], ids=lambda c: str(id(c)))
def test_rbvk_points_criteria_and_stage(case: dict[str, Any]) -> None:
    result = evaluate([decode(case["record"])], RBVK)
    assessment = result.records[0].assessment
    assert assessment is not None
    assert {code[1:]: value for code, value in assessment["criteria"].items()} == case["flags"]
    assert assessment["score"] == case["score"]
    assert assessment["stage"] == legacy_stage(case["score"])


def test_exante_indicators() -> None:
    rows = FIXTURE["exante_features"]
    result = evaluate([decode(r["record"]) for r in rows], BASIS)
    for record, row in zip(result.records, rows, strict=True):
        expected = {LABEL_TO_CODE[label]: bool(v) for label, v in row["indicators"].items()}
        assert dict(record.flags) == expected


def test_exante_score_class_and_detail_with_supplied_weights() -> None:
    for run in FIXTURE["exante"]:
        points = {LABEL_TO_CODE[label]: w for label, w in run["weights"].items()}
        for row in run["rows"]:
            record = {
                "brutto": 0,
                "laufzeit_monate": 0,
                "erw_ma": 0,
                "fpgq": 0,
                "grp_v": 2,
                "an_risiko": 0,
            }
            # indicators as captured; the score step only reads them
            flags = {LABEL_TO_CODE[label]: bool(v) for label, v in row["indicators"].items()}
            got = evaluate([_record_for(flags, record)], BASIS, points=points)
            assessment = got.records[0].assessment
            assert assessment is not None
            assert assessment["score"] == row["score"]
            assert assessment["stage"] == row["class"]
            assert assessment["detail"] == row["detail"]
        if run["fallback"]:
            assert points == {r.code: r.points for r in BASIS.rules}


def _record_for(flags: dict[str, bool], base: dict[str, Any]) -> dict[str, Any]:
    """A record whose indicators equal ``flags`` (inverse of the seven predicates)."""
    record = dict(base)
    if flags["E1"]:
        record["brutto"] = 2_000_000
    elif flags["E2"]:
        record["brutto"] = 700_000
    record["laufzeit_monate"] = 30 if flags["E3"] else 12
    record["erw_ma"] = 5 if flags["E4"] else 1
    record["fpgq"] = 20 if flags["E5"] else 1
    record["grp_v"] = 1 if flags["E6"] else 2
    record["an_risiko"] = 0.5 if flags["E7"] else 0.1
    return record


def test_heuristik_scores() -> None:
    for run in FIXTURE["exante"]:
        rows = run["heuristik"]
        result = evaluate([decode(r["record"]) for r in rows], HEUR)
        for record, row in zip(result.records, rows, strict=True):
            assert record.assessment is not None
            assert record.assessment["score"] == row["score"]


def test_points_override_rules() -> None:
    with pytest.raises(ProfileError):
        evaluate([{}], RBVK, points={r.code: 1 for r in RBVK.rules})
    with pytest.raises(ProfileError):
        evaluate([{}], BASIS, points={"E1": 5})


def test_fixture_scope() -> None:
    assert len(FIXTURE["rbvk"]) == 777
    assert len(FIXTURE["exante_features"]) == 125
    assert len(FIXTURE["exante"]) == 3
    assert FIXTURE["source"]["commit"] == "fb2d18568d2eaf64574d131ceae51a936b9aac02"
    assert FIXTURE["environment"]["python"].startswith("3.12")


def test_calibrated_weights_are_applied_unchanged() -> None:
    """Calibrated weights (not in the fixture: all demo runs fell back) are applied as given."""
    weights = {"E1": 25, "E2": 0, "E3": 3, "E4": 0, "E5": 12, "E6": 7, "E7": 0}
    record = {
        "brutto": 2_000_000,
        "laufzeit_monate": 30,
        "erw_ma": 2,
        "fpgq": 20,
        "grp_v": 1,
        "an_risiko": 0.9,
    }
    assessment = evaluate([record], BASIS, points=weights).records[0].assessment
    assert assessment is not None
    assert assessment["score"] == 25 + 3 + 12 + 7
    assert assessment["stage"] == "mittel"
    assert assessment["detail"] == [
        "Budget > 1 Mio € (+25)",
        "Geplante Laufzeit > 24 M (+3)",
        "FPG-Fehlerquote historisch hoch (> 15 %) (+12)",
        "Erstantragsteller (+7)",
    ]
