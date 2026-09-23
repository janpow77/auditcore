"""RK-L: every recorded original output of riskanalysis red_flags is reproduced.

Fixture: ``tools/capture_riskanalysis.py`` executed the unchanged,
blob-verified source (riskanalysis@b5c523b) with pandas 3.0.5, NumPy 2.5.1 and
rapidfuzz 3.14.5: the 24 frames of the 26 original tests, boundary frames per
rule and seeded random frames.
"""

from __future__ import annotations

import math
from typing import Any

import pytest
from conftest import decode, fixture

from auditcore_risk import evaluate, load_profile

FIXTURE = fixture("riskanalysis_observed.json")
CASES = FIXTURE["cases"]
PROFILE = load_profile("riskanalysis.legacy", "b5c523bf7eaa")
CODES = FIXTURE["constants"]["RED_FLAG_CODES"]


def records(case: dict[str, Any]) -> list[dict[str, Any]]:
    return [decode(row) for row in case["rows"]]


def assert_same_float(actual: float, expected: Any) -> None:
    expected = decode(expected)
    if isinstance(expected, float) and math.isnan(expected):
        assert math.isnan(actual)
    else:
        assert actual == expected


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_flags_codes_and_scores(case: dict[str, Any]) -> None:
    assert case["exception"] is None
    result = evaluate(records(case), PROFILE, columns=case["columns"])
    for code in CODES:
        observed = case["flags"][code.lower()]
        assert [r.flags[code] for r in result.records] == observed, code
    assert [list(r.codes) for r in result.records] == case["red_flag_codes"]
    for record, expected in zip(result.records, case["name_match"], strict=True):
        assert_same_float(record.values["name_match"], expected)


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_summary(case: dict[str, Any]) -> None:
    result = evaluate(records(case), PROFILE, columns=case["columns"])
    assert [dict(s) for s in result.summary] == case["summary"]


def test_near_threshold_scalars() -> None:
    rule = PROFILE.rule("RF02")
    for item in FIXTURE["near_threshold"]:
        amount = decode(item["input"])
        result = evaluate(
            [{"bruttobetrag": amount, "Name": None, "zahlungsempfaenger": None}], PROFILE
        )
        assert result.records[0].flags[rule.code] is item["output"], amount


def test_placeholder_identifier_semantics() -> None:
    ids = decode(FIXTURE["hat_echte_vergabe"]["input"])
    expected = FIXTURE["hat_echte_vergabe"]["output"]
    rows = [
        {"bruttobetrag": 30_000.0, "vergabenummer": v, "Name": None, "zahlungsempfaenger": None}
        for v in ids
    ]
    result = evaluate(rows, PROFILE)
    # RF08 = no genuine identifier (all rows are > 25 T€ and relevant)
    assert [not r.flags["RF08"] for r in result.records] == expected


def test_fixture_scope_and_environment() -> None:
    assert len(CASES) == 173
    assert sum(1 for c in CASES if c["name"].startswith("orig-")) == 24
    assert FIXTURE["environment"]["pandas"] == "3.0.5"
    assert FIXTURE["environment"]["numpy"] == "2.5.1"
    assert FIXTURE["environment"]["rapidfuzz"] == "3.14.5"
    assert FIXTURE["source"]["commit"] == "b5c523bf7eaa326153778d9751f176f03d4d56ed"
    assert sum(len(c["rows"]) for c in CASES) > 2500
