"""RK-L: the flowinvoice ``RiskChecker`` (identical in audit-portal) is reproduced.

Fixture: ``tools/capture_flowinvoice_risk_checker.py`` executed the unchanged,
blob-verified ``RiskChecker.assess`` of flowinvoice@fb2d185 on 338 requests
(boundary cases per check and 250 seeded random requests).
"""

from __future__ import annotations

from typing import Any

import pytest
from conftest import fixture

from auditcore_risk import evaluate, flatten_record, load_profile

FIXTURE = fixture("flowinvoice_risk_checker_observed.json")
CASES = FIXTURE["cases"]
PROFILE = load_profile("flowinvoice.risk_checker", "fb2d18568d2e")


def assess(request: dict[str, Any]) -> dict[str, Any]:
    result = evaluate([flatten_record(request)], PROFILE)
    assessment = result.records[0].assessment
    assert assessment is not None
    return dict(assessment)


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_findings_score_and_summary(case: dict[str, Any]) -> None:
    assert case["exception"] is None
    got = assess(case["request"])
    expected = [
        {
            "code": f["indicator"],
            "severity": f["severity"],
            "description": f["description"],
            "evidence": f["evidence"],
            "recommendation": f["recommendation"],
        }
        for f in case["findings"]
    ]
    assert got["findings"] == expected
    assert got["score"] == case["risk_score"]
    assert got["highest_severity"] == case["highest_severity"]
    assert got["summary"] == case["summary"]
    assert got["source_version"] == case["assessment_version"]


def test_constants_equal_the_executed_source() -> None:
    c = FIXTURE["constants"]
    assert PROFILE.rule("HIGH_AMOUNT").params["absolute_gt"] == c["HIGH_AMOUNT_ABSOLUTE"]
    assert PROFILE.rule("HIGH_AMOUNT").params["sigma"] == c["HIGH_AMOUNT_SIGMA"]
    assert (
        PROFILE.rule("VENDOR_CLUSTERING").params["ratio_gt"] == c["VENDOR_CONCENTRATION_THRESHOLD"]
    )
    assert PROFILE.rule("ROUND_AMOUNT").params["min_amount"] == c["ROUND_AMOUNT_THRESHOLD"]
    split = PROFILE.rule("SPLIT_INVOICE").params
    assert list(split["thresholds"]) == c["SPLIT_INVOICE_THRESHOLDS"]
    assert split["proximity"] == c["SPLIT_INVOICE_PROXIMITY"]
    assert split["min_items"] == c["SPLIT_INVOICE_MIN_INVOICES"]
    assert split["window_days"] == c["SPLIT_INVOICE_TIME_WINDOW_DAYS"]


def test_fixture_scope() -> None:
    assert len(CASES) == 338
    assert FIXTURE["source"]["commit"] == "fb2d18568d2eaf64574d131ceae51a936b9aac02"
    indicators = {f["indicator"] for c in CASES for f in c["findings"]}
    assert indicators == {r.code for r in PROFILE.rules}
