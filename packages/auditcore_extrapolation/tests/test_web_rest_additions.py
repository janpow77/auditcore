"""REST additions: exclusions (7.10), groups over periods, /attributes variants, /negative-units."""

from __future__ import annotations

import copy
from typing import cast

import pytest

from auditcore_extrapolation.web import ContractError, attributes, evaluate, negative_units

BASE: dict[str, object] = {
    "method": "mus.standard",
    "confidence_level": 0.9,
    "factor_profile": "kom_2017_tables",
    "periods": [{"name": "H1"}, {"name": "H2"}],
    "strata": [
        {"name": "P1", "period": "H1", "group": "Programm 1", "book_value": 200_000},
        {"name": "P2", "period": "H1", "group": "Programm 2", "book_value": 200_000},
        {"name": "P1", "period": "H2", "group": "Programm 1", "book_value": 200_000},
        {"name": "P2", "period": "H2", "group": "Programm 2", "book_value": 200_000},
    ],
    "units": [
        {"id": f"{p}{s}{i}", "period": p, "stratum": s, "book_value": 1_000, "random_error": e}
        for p in ("H1", "H2")
        for s in ("P1", "P2")
        for i, e in enumerate((10, 0, 0, 5))
    ],
}


def test_groups_over_periods() -> None:
    result = evaluate(BASE)
    groups = cast(list[dict[str, object]], result["groups"])
    assert [g["name"] for g in groups] == ["Programm 1", "Programm 2"]
    total = sum(
        cast(float, cast(dict[str, object], g["projection"])["projected_random_error"])
        for g in groups
    )
    projection = cast(dict[str, object], result["projection"])
    assert projection["projected_random_error"] == pytest.approx(total)


def test_exclusions_extend_to_the_original_population() -> None:
    request = {
        "method": "nonstatistical.pps",
        "strata": [
            {
                "name": "Programm",
                "book_value": 3_909_572_424,
                "population_size": 3_851,
                "excluded_exhaustive_book_value": 290_309_600,
                "excluded_exhaustive_units": 1,
            }
        ],
        "units": [
            *[
                {
                    "id": f"s{i}",
                    "stratum": "Programm",
                    "book_value": 1_000_000,
                    "random_error": 1_000_000 * 0.52 / 23,
                }
                for i in range(23)
            ],
            *[
                {
                    "id": f"h{i}",
                    "stratum": "Programm",
                    "book_value": 1_697_136_654 / 7,
                    "random_error": 60,
                    "exhaustive": True,
                }
                for i in range(7)
            ],
        ],
    }
    result = evaluate(request)
    assert cast(dict[str, object], result["projection"])["projected_random_error"] == pytest.approx(
        50_020_779, abs=1
    )
    assert cast(dict[str, object], result["total_error_rate"])["book_value"] == 4_199_882_024
    broken = copy.deepcopy(request)
    cast(list[dict[str, object]], broken["strata"])[0]["excluded_units"] = -1
    with pytest.raises(ContractError):
        evaluate(broken)


def test_attribute_variants() -> None:
    base = {"deviations": 0, "sample_size": 59, "confidence_level": 0.95, "tolerable_rate": 0.05}
    discovery = cast(dict[str, object], attributes({**base, "approach": "discovery"})["attributes"])
    assert discovery["conclusion"] == "criterion_met"
    stop = cast(
        dict[str, object],
        attributes({**base, "approach": "stop_or_go", "deviations": 1, "sample_size": 93})[
            "attributes"
        ],
    )
    assert stop["conclusion"] == "stop"
    normal = cast(
        dict[str, object], attributes({**base, "factor_profile": "kom_2017_tables"})["attributes"]
    )
    assert normal["approach"] == "normal"
    with pytest.raises(ContractError, match="approach"):
        attributes({**base, "approach": "median"})


def test_negative_units_endpoint() -> None:
    reply = negative_units(
        {
            "approach": 3,
            "units": [
                {"id": "X", "new_expenditure": 100_000},
                {
                    "id": "Y",
                    "new_expenditure": 25_000,
                    "current_corrections": 700,
                    "previous_corrections": 4_300,
                },
                {"id": "Z", "new_expenditure": 10_000, "previous_corrections": 15_000},
            ],
            "checks": [{"id": "Z", "corrected_amount": 12_000, "decided_amount": 15_000}],
        }
    )
    population = cast(dict[str, object], reply["population"])
    assert population["positive_total"] == 134_300 and population["net_declared"] == 115_000
    assert cast(dict[str, object], reply["review"])["disclose"] is True
    with pytest.raises(ContractError, match="Variante"):
        negative_units({"approach": 5, "units": [{"id": "X", "new_expenditure": 1}]})
