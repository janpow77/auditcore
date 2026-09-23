"""Original versus migrated regulierung connectors (same 30 scenarios, same payloads).

``regulierung_migrated_observed.json`` was captured with
``tools/capture_regulierung_connectors.py --migrated`` from the local
integration branch (patch ``docs/migrations/regulierung-price.patch``) with
the built wheels installed. Stored domain rows must be identical; every other
difference is listed here with its contract number.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from support import FIXTURES, OBSERVED

MIGRATED = json.loads((FIXTURES / "regulierung_migrated_observed.json").read_text("utf-8"))
OLD = {s["scenario"]: s for s in OBSERVED["scenarios"]}
NEW = {s["scenario"]: s for s in MIGRATED["scenarios"]}

#: scenarios whose run result differs on purpose (status, count, error text)
RESULT_CHANGES = {
    "bundesbank-ok": "PS-C02",
    "bundesbank-ok-existing-day": "PS-C02",
    "bundesbank-empty": "PS-C03",
    "bundesbank-http-500": "PS-C11",
    "bundesbank-not-json": "PS-C11",
    "eia-ok": "PS-C04/PS-C05",
    "eia-http-403": "PS-C11",
    "eu-oil-404": "PS-C11",
    "overpass-ok": "PS-C06",
    "overpass-ok-existing": "PS-C06",
    "overpass-remark": "PS-C07",
    "overpass-504": "PS-C11",
    "overpass-not-json": "PS-C11",
}
#: scenarios with more requests because of the bounded retry (PS-C10)
RETRIED = {"bundesbank-http-500", "overpass-429", "overpass-504"}


def _domain_rows(scenario: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in scenario["rows"]:
        if row["$type"] == "ExternalApiLauf":
            continue
        rows.append(
            {
                k: float(v["$decimal"]) if isinstance(v, dict) and "$decimal" in v else v
                for k, v in row.items()
            }
        )
    return rows


def test_same_scenarios_and_payloads() -> None:
    assert MIGRATED["scope"] == "MIGRATED_CONSUMER"
    assert set(NEW) == set(OLD) and len(NEW) == 30
    assert MIGRATED["payload_sha256"].items() >= OBSERVED["payload_sha256"].items()


@pytest.mark.parametrize("name", sorted(OLD))
def test_stored_domain_rows_are_identical(name: str) -> None:
    assert _domain_rows(NEW[name]) == _domain_rows(OLD[name])


@pytest.mark.parametrize("name", sorted(OLD))
def test_result_changes_are_documented(name: str) -> None:
    old, new = OLD[name]["result"], NEW[name]["result"]
    if name in RESULT_CHANGES:
        assert old != new
        if isinstance(old, dict) and old["status"] == "fehler":
            assert new["status"] == "fehler"
        elif isinstance(old, dict):
            assert new["status"] == "teilweise" and new["fehlermeldung"]
            assert new["paket_sha256"] == old["paket_sha256"] or name == "eia-ok"
    else:
        assert old == new
    extra = len(NEW[name]["requests"]) - len(OLD[name]["requests"])
    assert extra == (1 if name in RETRIED else 0)
    for request in NEW[name]["requests"]:
        assert not set(request["params"]) & {"apikey", "api_key", "password", "token"}
