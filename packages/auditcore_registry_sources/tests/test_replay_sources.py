"""flowsearch clients, UBO/KMU engine, OSINT register sources and riskanalysis demo."""

from __future__ import annotations

import json
from typing import Any

import pytest
from replay_support import BY_NAME, FILES, cases, plain, same

from auditcore_registry_sources import legacy


def recorded(case: dict[str, Any]) -> tuple[Any, list[dict[str, Any]]]:
    output = plain(case["output"])
    return case["output"], output["requests"]


RESPONSES = {
    "api-shape": "opensanctions_match_{}.json",
    "wrapped-shape": "opensanctions_match_{}_wrapped.json",
    "wrapped-with-key": "opensanctions_match_{}_wrapped.json",
}


@pytest.mark.parametrize("case", cases("flowsearch_check_sanctions"), ids=lambda c: c["name"])
def test_flowsearch_sanctions(case: dict[str, Any]) -> None:
    inputs = plain(case["inputs"])
    output = plain(case["output"])
    label = inputs["case"]
    if label in RESPONSES:
        body = json.loads((FILES / RESPONSES[label].format("sanctions")).read_text())
        result = legacy.flowsearch_check_sanctions(body)
    else:
        result = legacy.flowsearch_check_sanctions(None, error=output["result"]["error"])
    assert same({"result": result, "requests": output["requests"]}, case["output"])
    for request in output["requests"]:
        assert request["json"] == legacy.flowsearch_sanctions_payload(inputs["name"], "DE")
        assert request["authorization"] is None  # the source sends no key at all


@pytest.mark.parametrize("case", cases("flowsearch_check_person"), ids=lambda c: c["name"])
def test_flowsearch_pep(case: dict[str, Any]) -> None:
    inputs = plain(case["inputs"])
    output = plain(case["output"])
    label = inputs["case"]
    if label in RESPONSES:
        body = json.loads((FILES / RESPONSES[label].format("pep")).read_text())
        result = legacy.flowsearch_check_person(body, name=inputs["name"])
    else:
        result = legacy.flowsearch_check_person(
            None, name=inputs["name"], error=output["result"]["error"]
        )
    assert same({"result": result, "requests": output["requests"]}, case["output"])
    for request in output["requests"]:
        assert request["json"] == legacy.flowsearch_pep_payload(
            inputs["name"], inputs.get("date_of_birth"), inputs.get("nationality")
        )
        expected = "Bearer geheim-nicht-echt" if inputs["api_key"] else None
        assert (
            request["authorization"]
            == expected
            == legacy.flowsearch_pep_authorization(
                "geheim-nicht-echt" if inputs["api_key"] else None
            )
        )


def test_documented_api_shape_finds_nothing_in_the_source() -> None:
    sanctions = plain(BY_NAME["flowsearch-sanctions-api-shape"]["output"])["result"]
    pep = plain(BY_NAME["flowsearch-pep-api-shape"]["output"])["result"]
    assert sanctions["found"] is False and sanctions["matches"] == []
    # Candidates above 0.7 are listed, but without name, topics or PEP type.
    assert pep["is_pep"] is False and pep["pep_category"] == "None"
    assert {m["name"] for m in pep["matches"]} == {""}
    assert {m["pep_type"] for m in pep["matches"]} == {"Unknown"}


SIMPLE = {
    "flowsearch_assess_risk": lambda i: legacy.flowsearch_assess_risk(
        i["pep_type"], i["score"], i["positions"]
    ),
    "flowsearch_pep_type": lambda i: legacy.flowsearch_pep_type(i["topics"], i["positions"]),
    "flowsearch_pep_category": lambda i: legacy.flowsearch_pep_category(i["matches"]),
    "flowsearch_entity_type": lambda i: legacy.flowsearch_entity_type(i["name"]),
    "flowsearch_share": lambda i: legacy.flowsearch_share(i["officer"]),
    "flowsearch_handelsregister_search": lambda i: legacy.flowsearch_handelsregister_search(
        i["name"], i["location"]
    ),
    "flowsearch_ubo": lambda i: legacy.flowsearch_ubo(i["structure"]),
    "flowsearch_kmu": lambda i: legacy.flowsearch_kmu(i["company"]),
}


@pytest.mark.parametrize("case", [c for op in SIMPLE for c in cases(op)], ids=lambda c: c["name"])
def test_flowsearch_functions(case: dict[str, Any]) -> None:
    assert same(SIMPLE[case["operation"]](plain(case["inputs"])), case["output"])


def test_openregister_endpoint_does_not_exist() -> None:
    case = BY_NAME["flowsearch-openregister-search-404"]
    output = plain(case["output"])
    result = legacy.flowsearch_openregister_error(output["result"]["error"])
    assert same({"result": result, "requests": output["requests"]}, case["output"])
    assert "404" in result["error"]


OSINT_FILES = {
    "osint-zer-gleich": ("zer_status.json", "zer_register.json"),
    "osint-zer-abweichend": ("zer_status_abweichend.json", "zer_register.json"),
}


@pytest.mark.parametrize("case", cases("osint_zer"), ids=lambda c: c["name"])
def test_osint_zer(case: dict[str, Any]) -> None:
    status, register = OSINT_FILES[case["name"]]
    result = legacy.osint_zer((FILES / status).read_bytes(), (FILES / register).read_bytes())
    assert same(result, case["output"])


@pytest.mark.parametrize("case", cases("osint_ihk"), ids=lambda c: c["name"])
def test_osint_ihk(case: dict[str, Any]) -> None:
    name = plain(case["inputs"])["file"]
    if name is None:
        assert case["exception"]["type"] == "OSError"  # no recorded answer: download failed
        return
    assert same(legacy.osint_ihk((FILES / name).read_bytes()), case["output"])


def test_osint_hwk_and_chambers() -> None:
    html = (FILES / "zdh_handwerkskammern.html").read_bytes()
    ihk = (FILES / "ihk_locations.json").read_bytes()
    assert same(legacy.osint_hwk(html), BY_NAME["osint-hwk"]["output"])
    assert same(legacy.osint_kammern(ihk, html), BY_NAME["osint-kammern"]["output"])


def test_riskanalysis_demo_is_documented_not_ported() -> None:
    observed = [plain(c["output"]) for c in cases("riskanalysis_screen")]
    assert len(observed) == 6
    assert {o["status"] for o in observed} == {"kein Treffer", "möglicher Treffer"}
    assert plain(BY_NAME["riskanalysis-screen-0"]["output"])["score"] == 100.0
