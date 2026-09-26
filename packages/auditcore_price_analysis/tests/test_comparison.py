"""Deviation, traffic light and group statistics against the observed legacy cases."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from replay import decode, load_fixture

from auditcore_price_analysis import (
    ProfileError,
    comparison_profile_from_dict,
    delta_pct,
    group_statistics,
    load_comparison_profile,
    traffic_light,
)

CP = load_comparison_profile("regulierung.hpp.vergleich", "2026.09.1")
CASES = {c["id"]: c for c in load_fixture()["cases"]}


def with_threshold(value: Any) -> Any:
    raw = {**CP.raw, "traffic_light": {**CP.raw["traffic_light"], "threshold_pct": str(value)}}
    return comparison_profile_from_dict(raw)


#: documented divergences (PA-L11): reference ≤ 0 is unknown, exact half-up rounding
DELTA_DIVERGES = {
    "delta-004": None,
    "delta-005": None,
    "delta-006": None,
    "delta-007": Decimal("0.3"),
    "delta-008": Decimal("0.4"),
    "delta-009": Decimal("0.1"),
}
#: documented divergences (PA-L12): no positive median, float artifacts at the limits
LIGHT_DIVERGES = {
    "compliance-009": None,
    "compliance-010": None,
    "compliance-012": "gruen",
    "compliance-015": "gelb",
}
#: documented divergences (PA-L13): empty group unknown, exact half-up rounding
STATS_DIVERGES = {"cluster-001", "cluster-006", "cluster-007", "cluster-008"}


@pytest.mark.parametrize("case_id", sorted(k for k in CASES if k.startswith("delta-")))
def test_delta(case_id: str) -> None:
    case = CASES[case_id]
    value, reference = decode(case["args"])
    new = delta_pct(value, reference, CP)
    if case_id in DELTA_DIVERGES:
        assert new == DELTA_DIVERGES[case_id]
    else:
        assert new is not None and float(new) == case["ok"]


@pytest.mark.parametrize("case_id", sorted(k for k in CASES if k.startswith("compliance-")))
def test_traffic_light(case_id: str) -> None:
    case = CASES[case_id]
    value, median = decode(case["args"])
    threshold = decode(case["kwargs"]).get("schwelle_pct", 20)
    if threshold < 0:  # PA-L12: a negative threshold is no valid profile
        with pytest.raises(ProfileError):
            with_threshold(threshold)
        return
    new = traffic_light(value, median, with_threshold(threshold))
    assert new == LIGHT_DIVERGES.get(case_id, case["ok"])


@pytest.mark.parametrize("case_id", sorted(k for k in CASES if k.startswith("cluster-")))
def test_statistics(case_id: str) -> None:
    case = CASES[case_id]
    stats = group_statistics(decode(case["args"])[0], CP)
    legacy = case["ok"]
    assert stats.count == legacy["count"]
    if case_id in STATS_DIVERGES:
        return
    view = stats.to_dict()
    for key in ("median", "mean", "stddev", "min", "max"):
        assert float(view[key]) == legacy[key], key


def test_statistics_divergences_are_exactly_rounding_or_empty() -> None:
    empty = group_statistics([], CP)
    assert empty.count == 0 and empty.median is None and empty.stddev is None
    assert group_statistics([2.675, 2.675], CP).median == Decimal("2.68")
    assert group_statistics([0.125, 0.135], CP).minimum == Decimal("0.13")
    assert group_statistics([1.005, 1.015, 1.025], CP).maximum == Decimal("1.03")


def test_missing_values_are_not_skipped_or_zero() -> None:
    from auditcore_price_analysis import PriceAnalysisError

    with pytest.raises(PriceAnalysisError):
        group_statistics([100, None], CP)
    assert delta_pct(None, 100, CP) is None and traffic_light(100, None, CP) is None


def test_sample_standard_deviation_is_a_named_variant() -> None:
    raw = {**CP.raw, "statistics": {**CP.raw["statistics"], "stddev": "sample"}}
    sample = comparison_profile_from_dict(raw)
    assert group_statistics([100, 200], sample).stddev == Decimal("70.71")
    assert group_statistics([100], sample).stddev is None
    assert group_statistics([100, 200], CP).stddev == Decimal("50.00")
