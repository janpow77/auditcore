"""Every recorded original output is reproduced exactly (legacy contract)."""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest
from conftest import LEGACY, normalise, revive

from auditcore_procurement import company_sources, prechecks, ted

PROFILE = prechecks.load_profile("procurement.hvtg-legacy", "2026.09.1")
CASES = [c for c in LEGACY["cases"] if c["operation"] != "constant"]


def run(case: dict[str, Any]) -> Any:
    op, i = case["operation"], case["inputs"]
    if op == "normalize_notice":
        return ted.normalize_notice(i)
    if op == "normalize_notices":
        return ted.normalize_notices(i)
    if op == "parse_ted_file":
        return list(ted.parse_ted_file(bytes.fromhex(i["bytes_hex"]), i["file_name"]))
    if op == "to_iso_date":
        return ted.to_iso_date(i["value"])
    if op == "build_ted_query":
        if case["name"] == "query-date-object":
            return ted.build_ted_query(date_from=date(2024, 1, 2))
        return ted.build_ted_query(**i)
    raise AssertionError(op)


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_ted_normalisation_and_query(case: dict[str, Any]) -> None:
    assert case["exception"] is None
    assert normalise(run(case)) == case["output"]


def test_constants_are_identical() -> None:
    constants = {c["name"]: c["output"] for c in LEGACY["cases"] if c["operation"] == "constant"}
    assert list(ted.DEFAULT_FIELDS) == constants["default-fields"]
    assert constants["field-aliases"] == ted.FIELD_ALIASES
    assert list(ted.FIELD_ALIASES) == list(constants["field-aliases"])


@pytest.mark.parametrize("case", LEGACY["prechecks"], ids=[c["name"] for c in LEGACY["prechecks"]])
def test_prechecks_legacy_mode(case: dict[str, Any]) -> None:
    result = prechecks.run_prechecks(PROFILE, *revive(case["args"]), mode="legacy")
    result["timestamp"] = "<wall-clock>"
    assert normalise(result) == case["output"]


def test_ruleset_equals_profile() -> None:
    rules = LEGACY["ruleset"]
    for category, tiers in rules["threshold_rules"].items():
        assert [
            {"max": t.maximum, "procedure": t.procedure, "min_bids": t.min_bids}
            for t in PROFILE.tiers[category]
        ] == [
            {
                "max": None if v["max"] is None else float(v["max"]),
                "procedure": v["procedure"],
                "min_bids": v["min_bids"],
            }
            for v in tiers.values()
        ]
        assert [t.name for t in PROFILE.tiers[category]] == list(tiers)
    assert {k: list(v) for k, v in PROFILE.required_documents.items()} == rules[
        "required_documents_by_procedure"
    ]


CLIENTS = LEGACY["clients"]


def _response(case: dict[str, Any]) -> tuple[int, Any]:
    """Status and body the fake session delivered to the original client."""
    from tools_inputs import CLIENT_INPUTS

    return CLIENT_INPUTS[(case["source"], case["name"])]


@pytest.mark.parametrize(
    "case", CLIENTS, ids=[f"{c['variant']}-{c['source']}-{c['name']}" for c in CLIENTS]
)
def test_company_clients_legacy(case: dict[str, Any]) -> None:
    status, body = _response(case)
    if case["source"] == "ted":
        request = company_sources.ted_company_request('Beispiel "GmbH"', "DE", case["variant"])
        output = company_sources.legacy_ted_company_parse(status, body, "DE", case["variant"])
    else:
        request = company_sources.had_request("Kita", case["name"] != "none", case["variant"])
        output = company_sources.legacy_had_parse(status, body, case["variant"])
    assert normalise(output) == case["output"]
    call = case["calls"][0]
    assert call["method"] == request["method"] and call["url"] == request["url"]
    for key in ("params", "json", "headers", "timeout"):
        assert call.get(key) == normalise(request.get(key))
