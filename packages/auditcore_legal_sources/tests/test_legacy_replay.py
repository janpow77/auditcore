"""Every recorded original output of both applications is reproduced exactly."""

from __future__ import annotations

import asyncio
import copy
import json
from pathlib import Path
from typing import Any

import pytest

from auditcore_legal_sources import legacy
from auditcore_legal_sources.profile import load_profile

DATA = json.loads(
    (Path(__file__).parent / "fixtures" / "legacy_harvesters_observed.json").read_text()
)
CASES = DATA["cases"]
AUDITDATABASE = load_profile("auditdatabase.esi", "2026.09.2")
DESIGNER = load_profile("audit_designer.vp_ai", "2026.09.2")
PURE = {
    "parse_date",
    "detect_funding_period",
    "detect_fund",
    "is_relevant",
    "normalize_document",
    "content_hash",
    "dip_normalize",
    "celex_type",
    "eurlex_normalize",
    "designer_dip_drucksache",
    "designer_dip_vorgang",
}


def plain(value: Any) -> Any:
    """Same JSON encoding as the capture tool."""
    from datetime import datetime

    if isinstance(value, datetime):
        return {"$datetime": value.isoformat()}
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [plain(v) for v in value]
    return value


def revive(value: Any) -> Any:
    from conftest import revive as inner

    return inner(value)


def run(case: dict[str, Any]) -> Any:
    op, i, designer = case["operation"], case["inputs"], case["variant"] == "designer"
    if op == "parse_date":
        return legacy.legacy_parse_date(revive(i["value"]))
    if op == "detect_funding_period":
        if designer:
            return legacy.designer_detect_funding_period(i["text"], i.get("publication_date"))
        return legacy.legacy_detect_funding_period(i["text"])
    if op == "detect_fund":
        return legacy.legacy_detect_fund(i["text"])
    if op == "is_relevant":
        return legacy.legacy_is_relevant(i["text"], ["EFRE", "Vergabe"])
    if op == "normalize_document":
        return legacy.legacy_normalize_document("probe", i)
    if op == "content_hash":
        return legacy.legacy_content_hash(i["content"], i["abstract"], i["title"])
    if op == "dip_normalize":
        return legacy.legacy_dip_normalize(i)
    if op == "celex_type":
        return legacy.legacy_celex_type(i["celex"])
    if op == "eurlex_normalize":
        return legacy.legacy_eurlex_normalize(i, designer=designer)
    if op == "designer_dip_drucksache":
        return legacy.designer_dip_drucksache(i["item"], i["query"])
    if op == "designer_dip_vorgang":
        return legacy.designer_dip_vorgang(i["item"], i["query"])
    raise AssertionError(op)


@pytest.mark.parametrize(
    "case",
    [c for c in CASES if c["operation"] in PURE],
    ids=[f"{c['variant']}-{c['name']}" for c in CASES if c["operation"] in PURE],
)
def test_pure_output_is_reproduced(case: dict[str, Any]) -> None:
    assert case["exception"] is None
    assert plain(run(case)) == case["output"]


def _dip_route(keyword: str | None) -> tuple[int, Any]:
    """Same synthetic answers as the capture tool (tools/capture_legacy_harvesters.py)."""
    from capture_routes import drucksache

    if keyword == "ESF":
        return 500, {"errors": "synthetic"}
    if keyword == "ESF+":
        raise RuntimeError("synthetic transport failure")
    if keyword == "EFRE":
        return 200, {"documents": [drucksache(1), drucksache(2), drucksache(1)]}
    if keyword == "Strukturfonds":
        return 200, {"documents": [drucksache(2), drucksache(3)]}
    if keyword == "Kohäsionspolitik":
        raise ValueError("invalid json")
    return 200, {"documents": []}


@pytest.mark.parametrize("limit", [200, 2])
def test_dip_harvest_flow_is_reproduced(limit: int) -> None:
    case = next(c for c in CASES if c["name"] == f"dip-harvest-limit-{limit}")
    calls: list[dict[str, Any]] = []

    async def fetch(url: str, params: dict[str, Any]) -> tuple[int, Any]:
        calls.append({"url": url, "params": copy.deepcopy(params)})
        return _dip_route(params.get("f.titel"))

    result = asyncio.run(
        legacy.legacy_dip_harvest(fetch, AUDITDATABASE.dip_keywords, "TEST-KEY", limit)
    )
    expected = case["output"]["result"]
    assert result["documents"] == expected["documents"]
    assert result["success"] is expected["success"] is True
    assert [(c["url"], c["params"]) for c in calls] == [
        (c["url"], c["params"]) for c in case["output"]["calls"]
    ]


def test_dip_all_failing_reports_success_like_the_source() -> None:
    case = next(c for c in CASES if c["name"] == "dip-harvest-all-failing")

    async def fetch(url: str, params: dict[str, Any]) -> tuple[int, Any]:
        return 503, {}

    result = asyncio.run(legacy.legacy_dip_harvest(fetch, AUDITDATABASE.dip_keywords, "k"))
    assert result["success"] is case["output"]["result"]["success"] is True
    assert result["documents"] == case["output"]["result"]["documents"] == []
    assert case["output"]["calls"] == len(AUDITDATABASE.dip_keywords)


def test_dip_vorgang_defect_is_recorded() -> None:
    case = next(c for c in CASES if c["name"] == "dip-get-vorgang")
    assert case["exception"]["type"] == "AttributeError"
    assert next(c for c in CASES if c["name"] == "dip-test-connection")["output"] is False


def test_eurlex_sparql_parse_is_reproduced() -> None:
    case = next(c for c in CASES if c["name"] == "eurlex-execute-sparql")
    payload = {"results": {"bindings": case["inputs"]["bindings"]}}
    assert legacy.legacy_sparql_rows(payload) == case["output"]


def test_eurlex_harvest_is_reproduced() -> None:
    case = next(c for c in CASES if c["name"] == "eurlex-harvest")

    async def execute(query: str) -> list[dict[str, str]]:
        if "Delegierte" in query:
            raise RuntimeError("synthetic SPARQL timeout")
        if "Durchführung" in query:
            return [{"celex": "32023R0002", "title": "Durchführungs-VO ESF", "date": "2023-01-02"}]
        return [
            {"celex": "32021R1060", "title": "Dublette"},
            {"celex": "32022R0001", "title": "Kohäsion 2021/1060", "date": "2022-05-04"},
        ]

    result = asyncio.run(legacy.legacy_eurlex_harvest(AUDITDATABASE, execute))
    assert plain(result["documents"]) == case["output"]["documents"]
    assert result["success"] is case["output"]["success"] is True


def test_eurlex_update_query_is_reproduced() -> None:
    from datetime import datetime

    case = next(c for c in CASES if c["name"] == "eurlex-update-query")
    assert legacy.legacy_update_query(AUDITDATABASE, datetime(2024, 1, 31)) == case["output"]


def test_designer_profile_differs_and_is_not_merged() -> None:
    assert DESIGNER.eurlex_queries != AUDITDATABASE.eurlex_queries
    assert DESIGNER.dip_keywords != AUDITDATABASE.dip_keywords
    assert DESIGNER.eurlex_update_query_template is None


def test_fixture_size() -> None:
    assert len(CASES) == 176
