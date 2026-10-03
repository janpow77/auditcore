"""RK-L: every recorded Flowstat ``_red_flags`` output is reproduced.

Fixture: ``tools/capture_flowstat.py`` executed the unchanged, blob-identical
function of audit_designer@1254591 and audit-portal@ac1ccc7 (pandas 2.1.4,
NumPy 1.26.2) on frames in the normalised column contract. The legacy profile
1254591156d3 reproduces them; version 2026.10.1 computes BL_RF07/BL_RF10 in
whole cents (RK-C12), every decision that differs from the recording is listed
in flowstat_cent_deviations.json (tools/flowstat_cent_deviations.py).
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
CENTS = load_profile("audit_designer.flowstat_belegliste", "2026.10.1")
DEVIATIONS = fixture("flowstat_cent_deviations.json")
RF07 = "BL_RF07_ACCEPTED_MISMATCH"
PARTS = ("projektbetrag", "kuerzungsbetrag", "anerkannter_betrag")


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


# --------------------------------------------------------------------------- 2026.10.1 (RK-C12)


def _expected_in_cents(case: dict[str, Any]) -> list[dict[str, Any]]:
    """Recorded overview minus the BL_RF07 hits that RK-C12 removes in this frame."""
    removed = sum(1 for d in DEVIATIONS["rf07"] if d["frame"] == case["name"] and d["old"] is True)
    out = []
    for entry in decode(case["red_flags"]):
        if entry["code"] == RF07:
            entry = {**entry, "count": entry["count"] - removed}
            if entry["count"] == 0:
                continue
        out.append(entry)
    return out


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_cent_version_counts(case: dict[str, Any]) -> None:
    rows = [decode(row) for row in case["rows"]]
    actual = [dict(s) for s in evaluate(rows, CENTS, columns=case["columns"]).summary]
    expected = _expected_in_cents(case)
    assert [a["code"] for a in actual] == [e["code"] for e in expected]
    for a, e in zip(actual, expected, strict=True):
        if "count" in e:
            assert a == e
        else:  # exact ratio of cent sums: at most the last two binary digits differ
            assert abs(a["share"] - e["share"]) <= 2 * math.ulp(e["share"])


def test_cent_version_profile() -> None:
    assert CENTS.status == "APPROVED" and CENTS.fingerprint != PROFILE.fingerprint
    assert dict(CENTS.source["derived_from"]) == {"profile": PROFILE.id, "version": "1254591156d3"}
    changed = {r.code for r, old in zip(CENTS.rules, PROFILE.rules, strict=True) if r != old}
    assert changed == {RF07, "BL_RF10_VENDOR_CONCENTRATION"}
    assert DEVIATIONS["profile"] == CENTS.reference


def _float_rest(row: dict[str, Any]) -> float:
    def amount(name: str) -> float:
        value = row.get(name)
        return 0.0 if value is None or value != value else float(value)

    return amount(PARTS[0]) - amount(PARTS[1]) - amount(PARTS[2])


def test_rf07_deviations_are_exactly_the_listed_rows() -> None:
    """RK-C12: only the listed rows change, each for the stated reason."""
    listed = {(d["frame"], d["row"]): d for d in DEVIATIONS["rf07"]}
    seen = set()
    for case in CASES:
        rows = [decode(row) for row in case["rows"]]
        result = evaluate(rows, CENTS, columns=case["columns"])
        if RF07 in result.skipped:
            continue
        for index, record in enumerate(result.records):
            rest = _float_rest(rows[index])
            legacy = abs(rest) > 0.01  # float arithmetic of the source (NaN → no hit)
            entry = listed.get((case["name"], index))
            if entry is None:
                assert record.flags[RF07] == legacy, (case["name"], index)
                continue
            seen.add((case["name"], index))
            assert (entry["old"], entry["new"]) == (legacy, record.flags[RF07])
            if entry["new"] is None:
                assert not all(math.isfinite(v) for v in map(decode, entry["values"].values()))
            else:
                assert abs(round(rest * 100)) <= 1 < abs(rest) * 100
    assert seen == set(listed)
    assert len(listed) == 42
    assert sum(1 for d in listed.values() if d["old"] is True and d["new"] is False) == 41


def test_rf10_decisions_are_unchanged() -> None:
    assert DEVIATIONS["rf10_changed_frames"] == []
