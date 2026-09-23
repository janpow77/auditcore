"""RK-L: every recorded Flowstat ``_red_flags`` output is reproduced.

Fixture: ``tools/capture_flowstat.py`` executed the unchanged, blob-identical
function of audit_designer@1254591 and audit-portal@ac1ccc7 (pandas 2.1.4,
NumPy 1.26.2) on frames in the normalised column contract.
"""

from __future__ import annotations

import math
from typing import Any

import pytest
from conftest import decode, fixture

from auditcore_risk import evaluate, load_profile

FIXTURE = fixture("flowstat_observed.json")
CASES = FIXTURE["cases"]
PROFILE = load_profile("audit_designer.flowstat_belegliste", "1254591156d3")


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_counts_and_share(case: dict[str, Any]) -> None:
    rows = [decode(row) for row in case["rows"]]
    result = evaluate(rows, PROFILE, columns=case["columns"])
    actual = [dict(s) for s in result.summary]
    expected = decode(case["red_flags"])
    assert [a["code"] for a in actual] == [e["code"] for e in expected]
    for a, e in zip(actual, expected, strict=True):
        if "count" in e:
            assert a == e
        else:
            # RK-C06: exact (fsum) instead of numpy-pairwise/Kahan summation; the share
            # may differ in the last binary digit, the decision (≥ 0.5) is identical.
            assert math.isclose(a["share"], e["share"], rel_tol=1e-12, abs_tol=0.0)


def test_share_differences_are_last_digit_only() -> None:
    differing = 0
    for case in CASES:
        rows = [decode(row) for row in case["rows"]]
        result = evaluate(rows, PROFILE, columns=case["columns"])
        for a, e in zip(result.summary, decode(case["red_flags"]), strict=True):
            if "share" in e and a["share"] != e["share"]:
                differing += 1
                assert abs(a["share"] - e["share"]) <= 2 * math.ulp(e["share"])
    assert differing <= 5


def test_fixture_scope_and_sources() -> None:
    assert len(CASES) == 112
    assert FIXTURE["environment"]["pandas"] == "2.1.4"
    assert {s["repository"] for s in FIXTURE["sources"]} == {
        "janpow77/audit_designer",
        "janpow77/audit-portal",
    }
    assert {s["git_blob"] for s in FIXTURE["sources"]} == {
        "d03738cb7e250e3cd838c88157992e0b4093ef35"
    }
