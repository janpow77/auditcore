"""REST contract of auditcore_sampling.web without an HTTP framework."""

from __future__ import annotations

import csv
import io
import random

import pytest

from auditcore_sampling import METHODS, RECOMMENDED_MUS_METHOD, draw_start, systematic_mus
from auditcore_sampling.web import (
    ContractError,
    allocate,
    calculate_size,
    catalogue,
    export_selection,
    select,
)
from auditcore_sampling.web._validate import MAX_ITEMS

REFERENCE = {
    "method": "portal.mus_poisson",
    "population_value": 475_478.94,
    "materiality": 50_000.0,
    "expected_error_rate": 0.005,
    "confidence_level": 0.95,
}


def _items(count: int = 60, strata: bool = False) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for i in range(count):
        item: dict[str, object] = {"id": f"B-{i + 1}", "value": float((i * 37) % 900 + 10)}
        if strata:
            item["stratum"] = "A" if i % 3 else "B"
        items.append(item)
    return items


def test_catalogue_lists_every_library_method_recommended_first() -> None:
    data = catalogue()
    ids = [m["id"] for m in data["methods"]]
    assert sorted(ids) == sorted(METHODS) and ids[0] == RECOMMENDED_MUS_METHOD
    poisson = data["methods"][0]
    assert poisson["recommended"] and poisson["default_variant"] == "portal"
    assert {"level": 0.95, "factor": 3.0} in poisson["confidence_levels"]
    assert data["decision"]["statement"] == "mus 30"
    assert [a["id"] for a in data["allocation_methods"]] == ["proportional", "equal"]


def test_size_reference_case_with_derivation() -> None:
    result = calculate_size(REFERENCE)
    assert result["sample_size"] == 30 and result["status"] == "RECOMMENDED"
    steps = {s["label"]: s["value"] for s in result["derivation"]}
    assert steps["Erwarteter Fehler"] == pytest.approx(2377.3947)
    assert steps["Präzision"] == pytest.approx(47622.6053)
    assert steps["Stichprobenumfang"] == 30
    assert steps["Stichprobenintervall"] == pytest.approx(475_478.94 / 30)


def test_size_superseded_method_warns_and_srs_derivation() -> None:
    legacy = calculate_size({**REFERENCE, "method": "flowstat.mus_z_attribute"})
    assert legacy["sample_size"] == 1 and legacy["status"] == "SUPERSEDED" and legacy["warnings"]
    srs = calculate_size(
        {
            "method": "portal.srs_normal",
            "population_size": 1000,
            "confidence_level": 0.95,
            "margin_of_error": 0.05,
            "expected_proportion": 0.5,
        }
    )
    assert srs["sample_size"] == 278
    assert srs["derivation"][1]["value"] == pytest.approx(384.16)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"method": "x"}, "Unbekannte Methode"),
        ({"confidence_level": 0.93}, "nicht definiert"),
        ({"materiality": None}, "Pflichtfeld 'materiality'"),
        ({"materiality": True}, "endliche Zahl"),
        ({"expected_error_rate": 1.0}, "Fehlerrate"),
    ],
)
def test_size_rejects_invalid_input(change: dict[str, object], message: str) -> None:
    with pytest.raises(ContractError, match=message) as info:
        calculate_size({**REFERENCE, **change})
    assert info.value.status == 422


def test_size_zero_population_has_no_derivation() -> None:
    result = calculate_size({**REFERENCE, "population_value": 0})
    assert result["sample_size"] == 0 and result["derivation"] == [] and result["warnings"]


def test_allocation() -> None:
    strata = {"A": 70, "B": 30}
    result = allocate({"total_sample_size": 10, "method": "proportional", "strata": strata})
    assert [s["sample_size"] for s in result["strata"]] == [7, 3] and result["allocated"] == 10
    equal = allocate({"total_sample_size": 9, "method": "equal", "strata": {"A": 70, "B": 2}})
    assert [s["sample_size"] for s in equal["strata"]] == [5, 2]
    with pytest.raises(ContractError):
        allocate({"total_sample_size": 9, "method": "neyman", "strata": {"A": 1}})


def test_mus_selection_is_reproducible_and_matches_library() -> None:
    items = _items()
    request = {"method": "mus", "variant": "portal", "items": items, "sample_size": 12, "seed": 42}
    first, second = select(request), select(request)
    assert first == second and first["seed"] == 42 and not first["seed_generated"]
    values = [float(i["value"]) for i in items]  # type: ignore[arg-type]
    interval = sum(values) / 12
    rng = random.Random(42)
    direct = systematic_mus(
        values, sample_size=12, interval=interval, start=draw_start(rng, interval), variant="portal"
    )
    assert [r["position"] for r in first["rows"]] == list(direct.positions)
    assert first["strata"][0]["start"] == direct.start
    assert [r["order"] for r in first["rows"]] == list(range(1, len(first["rows"]) + 1))


def test_generated_seed_is_returned_and_reproduces_the_draw() -> None:
    request = {"method": "srs", "items": _items(), "sample_size": 5}
    drawn = select(request)
    assert drawn["seed_generated"] and 0 <= drawn["seed"] < 2**53
    again = select({**request, "seed": drawn["seed"]})
    assert again["rows"] == drawn["rows"] and again["items_sha256"] == drawn["items_sha256"]


def test_portal_variant_reports_excluded_values_and_flowstat_counts_hits() -> None:
    items = [
        {"id": "a", "value": 1000.0},
        {"id": "b", "value": -50.0},
        {"id": "c", "value": 0},
        {"id": "d", "value": None},
        {"id": "e", "value": 10.0},
    ]
    portal = select({"method": "mus", "variant": "portal", "items": items, "sample_size": 4,
                     "seed": 1})
    assert portal["strata"][0]["excluded_negative"] == ["b"]
    assert portal["strata"][0]["excluded_zero_or_missing"] == ["c", "d"]
    flowstat = select({"method": "mus", "variant": "flowstat", "items": items, "sample_size": 4,
                       "seed": 1})
    assert flowstat["rows"][0]["id"] == "a" and flowstat["rows"][0]["hits"] >= 3


def test_stratified_selection_uses_allocation_per_stratum() -> None:
    result = select({"method": "srs", "items": _items(60, strata=True), "sample_size": 12,
                     "allocation": "proportional", "seed": 5})
    sizes = {s["stratum"]: s["sample_size"] for s in result["strata"]}
    assert sizes == {"B": 4, "A": 8} and result["selected"] == 12
    assert all(r["stratum"] == "A" for r in result["rows"] if r["order"] > 4)
    with pytest.raises(ContractError, match="allocation"):
        select({"method": "srs", "items": _items(10, strata=True), "sample_size": 2, "seed": 1})
    mixed = _items(4, strata=True) + [{"id": "x", "value": 1.0}]
    with pytest.raises(ContractError, match="jedes Element"):
        select({"method": "srs", "items": mixed, "sample_size": 2, "seed": 1,
                "allocation": "equal"})


@pytest.mark.parametrize(
    "request_body",
    [
        {"method": "mus", "items": [{"value": 1.0}], "sample_size": 1, "seed": 1},
        {"method": "srs", "items": [], "sample_size": 1},
        {"method": "srs", "items": [{"value": "12"}], "sample_size": 1},
        {"method": "srs", "items": [{"value": 1.0}], "sample_size": 2},
        {"method": "srs", "items": [{"value": 1.0}], "sample_size": 1, "seed": -1},
        {"method": "srs", "items": [{"value": 1.0}], "sample_size": 1, "seed": 2**63},
    ],
)
def test_selection_rejects_invalid_requests(request_body: dict[str, object]) -> None:
    with pytest.raises(ContractError):
        select(request_body)


def test_selection_limits_population_size() -> None:
    with pytest.raises(ContractError) as info:
        select({"method": "srs", "items": [{"value": 1}] * (MAX_ITEMS + 1), "sample_size": 1})
    assert info.value.status == 413


def test_csv_export_is_spreadsheet_safe_and_reproduced() -> None:
    items = [{"id": "=HYPERLINK(1)", "value": 1234.5}, {"id": "B-2", "value": 20.25}]
    request = {"method": "srs", "items": items, "sample_size": 2, "seed": 3}
    exported = export_selection({**request, "format": "csv"})
    assert exported.filename == "stichprobe-srs-seed-3.csv"
    text = exported.content.decode("utf-8")
    assert text.startswith("\ufeffLfd. Nr.;Position;Kennung;Wert;Schicht;Treffer\r\n")
    rows = list(csv.reader(io.StringIO(text.lstrip("\ufeff")), delimiter=";"))
    by_id = {r[2]: r for r in rows[1:]}
    assert by_id["'=HYPERLINK(1)"][3] == "1234,5" and by_id["B-2"][3] == "20,25"
    assert [r[1] for r in rows[1:]] == [str(r["position"]) for r in select(request)["rows"]]


def test_json_export_and_seed_requirement() -> None:
    request = {"method": "srs", "items": _items(5), "sample_size": 2, "seed": 9}
    exported = export_selection({**request, "format": "json"})
    assert exported.media_type == "application/json" and b'"seed": 9' in exported.content
    with pytest.raises(ContractError, match="Seed"):
        export_selection({**request, "seed": None, "format": "csv"})
    with pytest.raises(ContractError, match="format"):
        export_selection({**request, "format": "xlsx"})
