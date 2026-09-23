"""Legacy variant ``flowinvoice.fraud_benford`` reproduces the executed source exactly."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from auditcore_statistics import (
    benford_test,
    legacy_flowinvoice_benford,
    recommended_flowinvoice_benford,
)

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "flowinvoice_benford_observed.json").read_text()
)


def decode(value: Any) -> Any:
    if isinstance(value, dict) and "$decimal" in value:
        return Decimal(value["$decimal"])
    if isinstance(value, dict) and value.get("$float") == "nan":
        return float("nan")
    return value


@pytest.mark.parametrize("case", FIXTURE["cases"], ids=lambda c: c["name"])
def test_result_equals_the_source(case: dict[str, Any]) -> None:
    got = legacy_flowinvoice_benford([decode(v) for v in case["amounts"]])
    expected = dict(case["result"])
    got["observed_distribution"] = {str(k): v for k, v in got["observed_distribution"].items()}
    got["expected_distribution"] = {str(k): v for k, v in got["expected_distribution"].items()}
    assert got.pop("profile") == "flowinvoice.fraud_benford"
    assert got == expected


def test_infinite_amounts_are_rejected_instead_of_looping() -> None:
    with pytest.raises(ValueError):
        legacy_flowinvoice_benford([1.0, float("inf")])


def test_differs_from_the_exact_method_on_the_same_data() -> None:
    case = next(c for c in FIXTURE["cases"] if c["name"] == "zufall-00")
    values = [decode(v) for v in case["amounts"]]
    legacy = legacy_flowinvoice_benford(values)
    exact = benford_test(values, digits=1)
    assert legacy["chi_square_statistic"] != round(exact.chi2_statistic, 4)


def test_fixture_scope() -> None:
    assert len(FIXTURE["cases"]) == 65
    assert FIXTURE["source"]["commit"] == "fb2d18568d2eaf64574d131ceae51a936b9aac02"


def test_recommended_variant_is_the_standard_test_with_decided_parameters() -> None:
    case = next(c for c in FIXTURE["cases"] if c["name"] == "zufall-00")
    values = [decode(v) for v in case["amounts"]]
    got = recommended_flowinvoice_benford(values)
    assert got == benford_test(values, digits=1, significance_level=0.05)
    assert got.deviates_at_level is not None
