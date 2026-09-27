"""REST additions of evaluation/1: periods, sub-samples, groups, 7.7 and attributes."""

from __future__ import annotations

import copy
from typing import cast

import pytest
from starlette.testclient import TestClient

from auditcore_extrapolation.web import (
    ContractError,
    attributes,
    catalogue,
    create_app,
    evaluate,
    export_evaluation,
)

PERIODS_REQUEST: dict[str, object] = {
    "method": "nonstatistical.pps",
    "periods": [{"name": "1. Halbjahr"}, {"name": "2. Halbjahr"}],
    "population_units": 48,
    "strata": [
        {
            "name": "Programm",
            "period": "1. Halbjahr",
            "book_value": 16_930_259,
            "population_size": 34,
        },
        {
            "name": "Programm",
            "period": "2. Halbjahr",
            "book_value": 49_378_264,
            "population_size": 46,
        },
    ],
    "units": [
        *[
            {
                "id": f"a{i}",
                "period": "1. Halbjahr",
                "stratum": "Programm",
                "book_value": 2_000_000,
                "random_error": 44_000,
            }
            for i in range(3)
        ],
        *[
            {
                "id": f"b{i}",
                "period": "2. Halbjahr",
                "stratum": "Programm",
                "book_value": 700_000,
                "random_error": 700_000 * 0.0475 / 3,
            }
            for i in range(3)
        ],
        {
            "id": "H1",
            "period": "2. Halbjahr",
            "stratum": "Programm",
            "book_value": 11_000_000,
            "random_error": 30_000,
            "exhaustive": True,
        },
        {
            "id": "H2",
            "period": "2. Halbjahr",
            "stratum": "Programm",
            "book_value": 10_895_357,
            "random_error": 26_823,
            "exhaustive": True,
        },
    ],
}


def _etc_unit(
    unit: str, lead: float, lead_error: float, partners: float, audited: float, error: float
) -> dict[str, object]:
    return {
        "id": unit,
        "stratum": "Programme",
        "book_value": lead + partners,
        "subsample": {
            "estimator": "ratio",
            "strata": [
                {"name": "Lead-Partner", "book_value": lead},
                {"name": "Projektpartner", "book_value": partners},
            ],
            "units": [
                {
                    "id": f"{unit}-LP",
                    "stratum": "Lead-Partner",
                    "book_value": lead,
                    "random_error": lead_error,
                    "exhaustive": True,
                },
                {
                    "id": f"{unit}-PP",
                    "stratum": "Projektpartner",
                    "book_value": audited,
                    "random_error": error,
                },
            ],
        },
    }


ETC_REQUEST: dict[str, object] = {
    "method": "nonstatistical.ratio",
    "strata": [{"name": "Programme", "book_value": 113_300_285, "population_size": 47}],
    "units": [
        _etc_unit("864", 890_563, 0, 234_567, 37_147, 0),
        _etc_unit("12895", 1_278_327, 0, 834_459, 164_152, 0),
        _etc_unit("6724", 658_748, 5_274, 766_567, 152_024, 23),
        _etc_unit("763", 234_739, 20_327, 666_578, 83_384, 0),
        _etc_unit("65a", 987_329, 0, 245_538, 56_318, 127),
        _etc_unit("3", 1_045_698, 0, 344_765, 101_258, 0),
        _etc_unit("65b", 895_398, 0, 678_927, 97_656, 0),
        _etc_unit("567", 444_584, 0, 1_023_346, 213_216, 1_264),
        _etc_unit("24", 678_927, 0, 789_491, 137_311, 0),
        {
            "id": "HV",
            "stratum": "Programme",
            "book_value": 4_411_965,
            "random_error": 80_328,
            "exhaustive": True,
        },
    ],
}


def _stratum_units(prefix: str, stratum: str, errors: tuple[float, ...]) -> list[dict[str, object]]:
    return [
        {"id": f"{prefix}{i}", "stratum": stratum, "book_value": 1_000, "random_error": error}
        for i, error in enumerate(errors)
    ]


GROUPS_REQUEST: dict[str, object] = {
    "method": "srs.mean_per_unit",
    "confidence_level": 0.8,
    "factor_profile": "kom_2017_tables",
    "strata": [
        {"name": "P1", "group": "Programm 1", "book_value": 500_000, "population_size": 400},
        {"name": "P2", "group": "Programm 2", "book_value": 300_000, "population_size": 250},
    ],
    "units": _stratum_units("a", "P1", (40, 0, 0, 10, 0)) + _stratum_units("b", "P2", (0, 0, 5, 0)),
}


def test_periods_through_the_contract() -> None:
    result = evaluate(PERIODS_REQUEST)
    assert result["design"] == "periods"
    projection = cast(dict[str, object], result["projection"])
    assert projection["projected_random_error"] == pytest.approx(864_435, abs=1)
    extra = cast(dict[str, object], projection["extra"])
    assert [p["name"] for p in cast(list[dict[str, object]], extra["periods"])] == [
        "1. Halbjahr",
        "2. Halbjahr",
    ]
    assert {s["period"] for s in cast(list[dict[str, object]], projection["strata"])} == {
        "1. Halbjahr",
        "2. Halbjahr",
    }
    assert cast(dict[str, object], extra["coverage"])["population_units"] == 48
    assert cast(dict[str, object], result["confidence_recalculation"])["applicable"] is False


def test_period_errors() -> None:
    broken = copy.deepcopy(PERIODS_REQUEST)
    cast(list[dict[str, object]], broken["units"])[0]["period"] = "3. Quartal"
    with pytest.raises(ContractError, match="ohne gültigen Zeitraum"):
        evaluate(broken)
    no_list = copy.deepcopy(PERIODS_REQUEST)
    del no_list["periods"], no_list["population_units"]
    with pytest.raises(ContractError, match="setzt die Liste 'periods' voraus"):
        evaluate(no_list)
    conservative = copy.deepcopy(PERIODS_REQUEST) | {
        "method": "mus.conservative",
        "confidence_level": 0.9,
        "factor_profile": "kom_2017_tables",
    }
    with pytest.raises(ContractError, match="konservativen"):
        evaluate(conservative)
    grouped = copy.deepcopy(PERIODS_REQUEST)
    cast(list[dict[str, object]], grouped["strata"])[0]["group"] = "A"
    with pytest.raises(ContractError, match="braucht jede Schicht"):
        evaluate(grouped)
    with pytest.raises(ContractError, match="population_units"):
        evaluate({**GROUPS_REQUEST, "population_units": 5})


def test_subsamples_through_the_contract() -> None:
    result = evaluate(ETC_REQUEST)
    subsamples = cast(list[dict[str, object]], result["subsamples"])
    assert len(subsamples) == 9
    assert sum(cast(float, s["projected_error"]) for s in subsamples) == pytest.approx(
        32_337.4, abs=0.5
    )
    projection = cast(dict[str, object], result["projection"])
    assert projection["projected_random_error"] == pytest.approx(357_616, abs=1)


def test_subsample_errors() -> None:
    mixed = copy.deepcopy(ETC_REQUEST)
    cast(list[dict[str, object]], mixed["units"])[0]["random_error"] = 5
    with pytest.raises(ContractError, match="schließen sich aus"):
        evaluate(mixed)
    mismatch = copy.deepcopy(ETC_REQUEST)
    cast(list[dict[str, object]], mismatch["units"])[0]["book_value"] = 1
    with pytest.raises(ContractError, match="Summe der Teilschichten"):
        evaluate(mismatch)
    unknown = copy.deepcopy(ETC_REQUEST)
    sub = cast(dict[str, object], cast(list[dict[str, object]], unknown["units"])[0]["subsample"])
    sub["estimator"] = "median"
    with pytest.raises(ContractError, match="estimator"):
        evaluate(unknown)


def test_three_stages_and_no_fourth() -> None:
    invoices = [
        {
            "id": f"r{i}",
            "stratum": "Rechnungen",
            "book_value": 100,
            "random_error": 10 if i == 0 else 0,
        }
        for i in range(30)
    ]
    partner = {
        "id": "PP1",
        "stratum": "Partner",
        "book_value": 50_000,
        "subsample": {
            "estimator": "ratio",
            "strata": [{"name": "Rechnungen", "book_value": 50_000}],
            "units": invoices,
        },
    }
    operation = {
        "id": "V1",
        "stratum": "Programm",
        "book_value": 200_000,
        "subsample": {
            "estimator": "ratio",
            "strata": [{"name": "Partner", "book_value": 200_000}],
            "units": [partner],
        },
    }
    request = {
        "method": "nonstatistical.ratio",
        "strata": [{"name": "Programm", "book_value": 1_000_000, "population_size": 20}],
        "units": [operation, {"id": "V2", "stratum": "Programm", "book_value": 100_000}],
    }
    result = evaluate(request)
    subsamples = cast(list[dict[str, object]], result["subsamples"])
    assert [s["unit_id"] for s in subsamples] == ["PP1", "V1"]
    assert subsamples[0]["projected_error"] == pytest.approx(50_000 * 10 / 3000)
    assert subsamples[1]["projected_error"] == pytest.approx(200_000 * 10 / 3000)
    deeper = copy.deepcopy(request)
    inner = cast(list[dict[str, object]], deeper["units"])[0]
    stage2 = cast(list[dict[str, object]], cast(dict[str, object], inner["subsample"])["units"])[0]
    stage3 = cast(list[dict[str, object]], cast(dict[str, object], stage2["subsample"])["units"])[0]
    stage3["subsample"] = {
        "estimator": "ratio",
        "strata": [{"name": "X", "book_value": 100}],
        "units": [{"id": "x", "stratum": "X", "book_value": 100}],
    }
    with pytest.raises(ContractError, match="höchstens drei Stufen"):
        evaluate(deeper)


def test_groups_and_recalculation_through_the_contract() -> None:
    result = evaluate({**GROUPS_REQUEST, "system_assessment": 1})
    assert result["design"] == "groups"
    groups = cast(list[dict[str, object]], result["groups"])
    assert [g["name"] for g in groups] == ["Programm 1", "Programm 2"]
    assert all("total_error_rate" in g and g["observations"] in (5, 4) for g in groups)
    recalculation = cast(dict[str, object], result["confidence_recalculation"])
    assert recalculation["required_level"] == 0.6
    with pytest.raises(ContractError, match="schließen sich aus"):
        evaluate({**GROUPS_REQUEST, "system_assessment": 1, "required_confidence_level": 0.7})
    partial = copy.deepcopy(GROUPS_REQUEST)
    cast(list[dict[str, object]], partial["strata"])[1]["group"] = ""
    with pytest.raises(ContractError, match="braucht jede Schicht"):
        evaluate(partial)


def test_inconclusive_result_is_recalculated() -> None:
    request = {
        "method": "srs.mean_per_unit",
        "confidence_level": 0.9,
        "factor_profile": "kom_2017_tables",
        "required_confidence_level": 0.6,
        "strata": [{"name": "S", "book_value": 100_000, "population_size": 100}],
        "units": _stratum_units("u", "S", (0, 0, 0, 0, 0, 0, 0, 0, 0, 150)),
    }
    result = evaluate(request)
    ter = cast(dict[str, object], result["total_error_rate"])
    assert ter["conclusion"] == "inconclusive"
    recalculation = cast(dict[str, object], result["confidence_recalculation"])
    assert recalculation["applicable"] is True
    level = cast(float, recalculation["confidence_level"])
    assert 0 < level < 0.9 and recalculation["supports_not_material"] == (level >= 0.6)
    csv_text = export_evaluation({**request, "format": "csv"}).content.decode("utf-8")
    assert "Neu berechnetes Konfidenzniveau" in csv_text


def test_attributes_endpoint_and_catalogue() -> None:
    reply = attributes(
        {
            "deviations": 3,
            "sample_size": 150,
            "confidence_level": 0.95,
            "factor_profile": "kom_2017_tables",
            "tolerable_rate": 0.05,
        }
    )
    result = cast(dict[str, object], reply["attributes"])
    assert result["upper_limit"] == pytest.approx(0.0424, abs=5e-5)
    with pytest.raises(ContractError):
        attributes(
            {
                "deviations": 3,
                "sample_size": 2,
                "confidence_level": 0.95,
                "factor_profile": "kom_2017_tables",
                "tolerable_rate": 0.05,
            }
        )
    client = TestClient(create_app("/api"))
    assert client.post("/api/attributes", json={"deviations": 0}).status_code == 422
    listing = catalogue()
    assert [d["id"] for d in cast(list[dict[str, object]], listing["designs"])] == [
        "single",
        "periods",
        "groups",
    ]
    assert len(cast(list[object], listing["system_assessment"])) == 4
    methods = {m["id"]: m for m in cast(list[dict[str, object]], listing["methods"])}
    assert (
        methods["mus.conservative"]["periods"] is False and methods["srs.ratio"]["periods"] is True
    )


def test_period_export_lists_the_periods() -> None:
    content = export_evaluation({**PERIODS_REQUEST, "format": "csv"}).content.decode("utf-8")
    assert "Zeitraum 1. Halbjahr: hochgerechneter Fehler" in content
