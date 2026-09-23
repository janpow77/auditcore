"""RK-L: flowinvoice fraud_detection (manager score, TED, duplicates) is reproduced.

Fixture: ``tools/capture_flowinvoice_fraud.py`` executed the unchanged,
blob-verified modules of flowinvoice@fb2d185; see its docstring for which
parts (SQL selection) were not executed.
"""

from __future__ import annotations

from typing import Any

import pytest
from conftest import fixture

from auditcore_risk import (
    InputError,
    assess_contractor,
    load_fraud_profile,
    score_signals,
)
from auditcore_risk.fraud import exact_duplicates, fuzzy_duplicates

FIXTURE = fixture("flowinvoice_fraud_observed.json")
V = "fb2d18568d2e"
SIGNALS = load_fraud_profile("flowinvoice.fraud_signals", V, "signal_score")
TED = load_fraud_profile("flowinvoice.ted_contractor", V, "ted_contractor")
DUP = load_fraud_profile("flowinvoice.duplicates", V, "duplicates")


@pytest.mark.parametrize("case", FIXTURE["manager"], ids=lambda c: c["name"])
def test_manager_score_level_blockers_warnings(case: dict[str, Any]) -> None:
    if case["exception"] is not None:
        assert case["exception"]["type"] == "TypeError"
        with pytest.raises(InputError):
            score_signals(case["signals"], SIGNALS)
        return
    got = score_signals(case["signals"], SIGNALS)
    assert got.score == case["risk_score"]
    assert got.level == case["risk_level"]
    assert sorted(got.blockers) == case["blockers"]
    assert sorted(got.warnings) == case["warnings"]
    assert list(got.checks_performed) == case["checks_performed"]


@pytest.mark.parametrize("case", FIXTURE["ted"], ids=lambda c: c["name"])
def test_ted_statistics_flags_and_legitimacy(case: dict[str, Any]) -> None:
    got = assess_contractor(case["notices"], TED)
    assert got.total_contracts == case["total_contracts"]
    assert dict(got.statistics) == case["statistics"]
    assert [dict(f) for f in got.red_flags] == case["red_flags"]
    assert dict(got.legitimacy_score) == case["legitimacy_score"]


def _plain(matches: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": m.candidate_id,
            "match_type": m.match_type,
            "confidence": m.confidence,
            "details": dict(m.details),
        }
        for m in matches
    ]


def _candidates(case: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {**c, "original_filename": f"r{i}.pdf", "project_id": "p1"}
        for i, c in enumerate(case["candidates"])
    ]


@pytest.mark.parametrize("case", FIXTURE["duplicates"], ids=lambda c: c["name"])
def test_duplicate_matching(case: dict[str, Any]) -> None:
    candidates = _candidates(case)
    assert _plain(exact_duplicates(case["invoice"], candidates, DUP)) == case["exact"]
    assert _plain(fuzzy_duplicates(case["invoice"], candidates, DUP)) == case["fuzzy"]


def test_fixture_scope() -> None:
    assert len(FIXTURE["manager"]) == 268
    assert sum(1 for c in FIXTURE["manager"] if c["exception"]) == 23
    assert len(FIXTURE["ted"]) == 129
    assert len(FIXTURE["duplicates"]) == 250
    assert FIXTURE["source"]["commit"] == "fb2d18568d2eaf64574d131ceae51a936b9aac02"
