"""RK-C12: BL_RF07 (balance) and BL_RF10 (top share) compute in whole cents."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from auditcore_risk import ProfileError, evaluate, load_profile, profile_from_dict
from auditcore_risk.columns import evaluate_columns

FLOWSTAT = load_profile("audit_designer.flowstat_belegliste", "2026.10.1")
LEGACY = load_profile("audit_designer.flowstat_belegliste", "1254591156d3")
RF07, RF10 = "BL_RF07_ACCEPTED_MISMATCH", "BL_RF10_VENDOR_CONCENTRATION"
BALANCE = ["projektbetrag", "kuerzungsbetrag", "anerkannter_betrag"]
SHARE = ["projektbetrag", "rechnungssteller"]


def _rows(columns: list[str], *values: tuple[object, ...]) -> list[dict[str, object]]:
    return [dict(zip(columns, row, strict=True)) for row in values]


def _both(rows: list[dict[str, object]], columns: list[str]) -> tuple[Any, Any]:
    records = evaluate(rows, FLOWSTAT, columns=columns)
    lists = {c: [r.get(c) for r in rows] for c in columns}
    return records, evaluate_columns(lists, FLOWSTAT)


def test_balance_compares_whole_cents() -> None:
    rows = _rows(
        BALANCE,
        (100.0, 0.0, 99.99),  # float: 0.010000000000005116 > 0.01, cents: 1
        (100.0, 0.0, 99.98),
        (2.675, None, 2.68),  # 2.675 → 268 cents (ROUND_HALF_UP of the decimal value)
        (float("inf"), 0.0, float("inf")),
        (10_000_000_000.01, 0.0, 0.0),
        (10_000_000_000.0, 6e9, 6e9),  # subtrahends above 10 Mrd. €
        ("12.345", "0", 12.35),
    )
    records, columns = _both(rows, BALANCE)
    flags = [r.flags[RF07] for r in records.records]
    assert flags == [False, True, False, None, None, None, False]
    assert columns.record_flags(RF07) == flags
    hit = records.records[1].hits[0]
    assert dict(hit.evidence) == {"difference": 0.02, "difference_cents": 2}
    assert "= 0,02 (Toleranz 0.01, in ganzen Cent)" in hit.reason
    assert "nicht prüfbar" in records.records[3].undetermined[RF07]
    legacy = evaluate(rows, LEGACY, columns=BALANCE)  # float arithmetic of the source
    assert [r.flags[RF07] for r in legacy.records] == [True, True, False, False, True, True, False]
    legacy_columns = evaluate_columns({c: [r.get(c) for r in rows] for c in BALANCE}, LEGACY)
    assert legacy_columns.record_flags(RF07) == [r.flags[RF07] for r in legacy.records]


@settings(deadline=None)
@given(st.lists(st.tuples(*[st.integers(-(10**9), 10**9)] * 3), max_size=20))
def test_balance_equals_integer_arithmetic(cents: list[tuple[int, int, int]]) -> None:
    rows = _rows(BALANCE, *[tuple(c / 100 for c in row) for row in cents])
    records, columns = _both(rows, BALANCE)
    expected = [abs(a - b - c) > 1 for a, b, c in cents]
    assert [r.flags[RF07] for r in records.records] == expected
    assert columns.record_flags(RF07) == expected


def _share(rows: list[dict[str, object]]) -> tuple[Any, Any]:
    records, columns = _both(rows, SHARE)
    left = next(d for d in records.dataset if d.code == RF10)
    right = next(d for d in columns.dataset if d.code == RF10)
    assert (left.triggered, left.value, left.reason) == (right.triggered, right.value, right.reason)
    assert dict(left.evidence) == dict(right.evidence)
    return left, columns


def test_share_uses_cent_sums() -> None:
    finding, _ = _share(_rows(SHARE, (0.105, "A"), (0.095, "B")))  # 11 and 10 cents
    assert finding.triggered and finding.value == 11 / 21
    assert dict(finding.evidence) == {
        "group": "A",
        "group_sum": 0.11,
        "total": 0.21,
        "group_sum_cents": 11,
        "total_cents": 21,
    }
    tie, _ = _share(_rows(SHARE, (5.0, None), (5.0, "B"), ("x", "C")))
    assert tie.evidence["group"] is None and tie.value == 0.5 and tie.triggered


def test_share_without_decidable_total() -> None:
    finding, _ = _share(_rows(SHARE, (1.0, "A"), (float("inf"), "B"), (2e10, "C")))
    assert not finding.triggered and finding.value is None
    assert finding.reason.startswith("Betrag in Zeile 1:")
    empty, _ = _share(_rows(SHARE, (0.0, "A"), (-1.0, "B")))
    assert empty.reason == "Gesamtsumme nicht positiv." and empty.value is None


def _profile_with(tolerance: object) -> dict[str, Any]:
    raw = files("auditcore_risk.profile_data").joinpath(
        "audit_designer.flowstat_belegliste-2026.10.1.json"
    )
    data: dict[str, Any] = json.loads(raw.read_text(encoding="utf-8"))
    rule = next(r for r in data["rules"] if r["code"] == RF07)
    rule["params"]["tolerance"] = tolerance
    return data


def test_tolerance_must_be_whole_cents() -> None:
    assert profile_from_dict(_profile_with(1.5)).rule(RF07).params["tolerance"] == 1.5
    for bad in (0.005, -0.01, 2e10):
        with pytest.raises(ProfileError, match="ganzen Cent"):
            profile_from_dict(_profile_with(bad))
    legacy = _profile_with(0.005)
    for rule in legacy["rules"]:
        rule["params"].pop("arithmetic", None)
    assert profile_from_dict(legacy).rule(RF07).params["tolerance"] == 0.005
    for rule in legacy["rules"]:
        if rule["code"] == RF10:
            rule["params"]["arithmetic"] = "float"
    with pytest.raises(ProfileError, match="arithmetic"):
        profile_from_dict(legacy)
