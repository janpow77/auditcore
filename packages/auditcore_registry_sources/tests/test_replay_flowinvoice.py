"""flowinvoice fraud detection: list check, PEP bulk, VIES, OffeneRegister, verification."""

from __future__ import annotations

import json
from typing import Any

import pytest
from auditcore_entity_matching import legacy as matching_legacy
from replay_support import BY_NAME, FILES, cases, jsonable, plain, same

from auditcore_registry_sources import legacy
from auditcore_registry_sources.sanctions_xml import parse_xml_list

LISTS = (
    ("EU_FSF", "eu_fsf_export.xml", "eu_fsf_xml"),
    ("OFAC_SDN", "ofac_sdn.xml", "ofac_sdn_xml"),
    ("UN_SC", "un_sc_consolidated.xml", "un_sc_xml"),
)


def local_entities() -> list[legacy.LocalEntity]:
    entities = []
    for list_type, name, fmt in LISTS:
        for item in parse_xml_list((FILES / name).read_bytes(), fmt, dates="legacy"):
            entities.append(
                legacy.LocalEntity(
                    name=item["name"],
                    aliases=item.get("aliases") or [],
                    list_type=list_type,
                    entity_type=item.get("entity_type"),
                    sanction_programs=item.get("sanction_programs") or [],
                    vat_ids=item.get("vat_ids") or [],
                )
            )
    return entities


def without(output: Any, *keys: str) -> Any:
    data = plain(output)
    for key in keys:
        data.pop(key, None)
    return data


@pytest.mark.parametrize("case", cases("flowinvoice_local_screen"), ids=lambda c: c["name"])
def test_local_list_check(case: dict[str, Any]) -> None:
    inputs = plain(case["inputs"])
    result = legacy.flowinvoice_check_entity_local(
        inputs["name"], local_entities(), min_score=inputs["min_score"]
    )
    expected = without(case["output"], "check_timestamp")
    assert plain(jsonable(result)) == expected


def test_sanctions_network_mapping() -> None:
    case = BY_NAME["flowinvoice-network-antwort"]
    body = json.loads((FILES / "sanctions_network_search.json").read_text())
    output = plain(case["output"])
    result = legacy.flowinvoice_sanctions_network(body, "Iwan Musterow")
    assert same({"result": result, "requests": output["requests"]}, case["output"])


def test_check_entity_always_fails_on_a_cache_miss() -> None:
    for label in ("antwort", "dns", "http500"):
        exception = BY_NAME[f"flowinvoice-check-entity-{label}"]["exception"]
        assert exception["type"] == "UnboundLocalError"
        assert "SanctionsResult" in exception["message"]
    assert BY_NAME["flowinvoice-network-dns"]["exception"]["type"] == "ConnectError"


def test_pep_download_and_parse() -> None:
    case = BY_NAME["flowinvoice-pep-parse"]
    entries = legacy.flowinvoice_pep_entries((FILES / "peps_targets.simple.csv").read_bytes())
    output = plain(case["output"])
    assert same({"result": entries, "requests": output["requests"]}, case["output"])


@pytest.mark.parametrize("case", cases("flowinvoice_pep_check"), ids=lambda c: c["name"])
def test_pep_check(case: dict[str, Any]) -> None:
    inputs = plain(case["inputs"])
    entries = legacy.flowinvoice_pep_entries((FILES / "peps_targets.simple.csv").read_bytes())
    if inputs.get("load") == "error":
        result = legacy.flowinvoice_pep_check(
            inputs["name"], None, load_error="Datenquelle nicht erreichbar"
        )
    else:
        result = legacy.flowinvoice_pep_check(
            inputs["name"],
            entries,
            country=inputs["country"],
            min_score=inputs["min_score"],
            dataset_size=len(entries),
            last_update="<Ladezeitpunkt>",
        )
    assert same(result, case["output"])


def test_failed_pep_load_is_reported_clean_by_the_source() -> None:
    output = plain(BY_NAME["flowinvoice-pep-load-error"]["output"])
    assert output["is_clean"] is True and output["error_message"]


@pytest.mark.parametrize("case", cases("flowinvoice_pep_normalize"), ids=lambda c: c["name"])
def test_pep_normalisation(case: dict[str, Any]) -> None:
    name = plain(case["inputs"])["name"]
    assert matching_legacy.flowinvoice_pep_normalize_name(name) == plain(case["output"])


@pytest.mark.parametrize("case", cases("flowinvoice_pep_score"), ids=lambda c: c["name"])
def test_pep_score(case: dict[str, Any]) -> None:
    from auditcore_registry_sources.bulk_screening import pep_score

    i = plain(case["inputs"])
    value = pep_score(
        i["query"],
        i["pep_name"],
        legacy._profile("flowinvoice.pep_bulk"),
        country=i["country"],
        entry_countries=i["countries"],
    )
    assert same(value, case["output"])


def test_pep_position_and_original_tests() -> None:
    values = plain(BY_NAME["flowinvoice-pep-position"]["inputs"])["values"]
    assert [legacy.flowinvoice_extract_position(v) for v in values] == plain(
        BY_NAME["flowinvoice-pep-position"]["output"]
    )
    assert plain(BY_NAME["flowinvoice-original-tests"]["output"]) == {
        "test_alias_treffer_weist_getroffenen_namen_aus": "PASS",
        "test_hauptname_ist_nicht_als_alias_markiert": "PASS",
    }
    # The same two regression cases through the reproduction:
    entry = {
        "name": "Erika Beispiel",
        "name_normalized": "erika beispiel",
        "aliases": ["Erika Musterfrau"],
        "aliases_normalized": ["erika musterfrau"],
        "countries": "de",
        "dataset": "peps",
    }
    alias = legacy.flowinvoice_pep_check("Erika Musterfrau", [entry], country="DE")
    assert alias.hit_count == 1 and alias.matches[0].via_alias is True
    assert alias.matches[0].matched_name == "Erika Musterfrau"
    main = legacy.flowinvoice_pep_check(
        "Erika Beispiel", [dict(entry, aliases=[], aliases_normalized=[])]
    )
    assert main.matches[0].via_alias is False


VIES = {
    "live-de-ungueltig": "vies_de_000000000_live.xml",
    "gueltig-ns2": "vies_valid_ns2.xml",
    "gueltig-de-ohne-name": "vies_valid_de_ohne_name.xml",
    "ohne-praefix": "vies_ohne_praefix.xml",
    "fault": "vies_fault.xml",
    "formatfehler": "vies_valid_ns2.xml",
    "kleinbuchstaben": "vies_valid_ns2.xml",
}


@pytest.mark.parametrize("case", cases("flowinvoice_vies"), ids=lambda c: c["name"])
def test_vies_legacy(case: dict[str, Any]) -> None:
    inputs = plain(case["inputs"])
    output = without(case["output"], "requests")["result"]
    output.pop("request_date")
    if inputs["case"] == "timeout":
        result = legacy.flowinvoice_validate_vat(inputs["vat_id"], error=output["error_message"])
    else:
        text = (FILES / VIES[inputs["case"]]).read_text()
        result = legacy.flowinvoice_validate_vat(inputs["vat_id"], response_text=text)
    assert result == output


def test_vies_legacy_rejects_every_real_answer() -> None:
    for label in ("live-de-ungueltig", "gueltig-ns2", "gueltig-de-ohne-name", "fault"):
        assert plain(BY_NAME[f"flowinvoice-vies-{label}"]["output"])["result"]["is_valid"] is False
    assert plain(BY_NAME["flowinvoice-vies-ohne-praefix"]["output"])["result"]["is_valid"] is True


REGISTER = {
    "registriert": ("offeneregister_datasette.json", 200),
    "liquidation": ("offeneregister_liquidation.json", 200),
    "dissolved": ("offeneregister_dissolved.json", 200),
    "removed": ("offeneregister_removed.json", 200),
    "leer": ("offeneregister_leer.json", 200),
    "http502": ("offeneregister_leer.json", 502),
    "apostroph": ("offeneregister_datasette.json", 200),
    "umlaut": ("offeneregister_datasette.json", 200),
    "sonderzeichen": ("offeneregister_datasette.json", 200),
    "zu-lang": ("offeneregister_datasette.json", 200),
}


def legacy_sql(name: str) -> dict[str, str]:
    """The SQL text the source builds from the name (kept out of the shipped library)."""
    search = name.replace("'", "''")
    return {
        "sql": "SELECT * FROM companies WHERE name LIKE '%" + search + "%' LIMIT 5",
        "_shape": "objects",
    }


@pytest.mark.parametrize("case", cases("flowinvoice_offeneregister"), ids=lambda c: c["name"])
def test_register_legacy(case: dict[str, Any]) -> None:
    import urllib.parse

    inputs = plain(case["inputs"])
    output = plain(case["output"])
    file_name, status = REGISTER[inputs["case"]]
    accepted = legacy.flowinvoice_register_accepts(inputs["name"])
    assert accepted == bool(output["requests"])
    result = (
        legacy.flowinvoice_register_company(status, json.loads((FILES / file_name).read_text()))
        if accepted
        else None
    )
    assert same({"result": result, "requests": output["requests"]}, case["output"])
    for request in output["requests"]:
        query = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(request["url"]).query))
        assert query == legacy_sql(inputs["name"])


@pytest.mark.parametrize("case", cases("flowinvoice_names_match"), ids=lambda c: c["name"])
def test_names_match_legacy(case: dict[str, Any]) -> None:
    i = plain(case["inputs"])
    result = {
        "match": legacy.flowinvoice_names_match(i["a"], i["b"]),
        "a": legacy.flowinvoice_normalize_company_name(i["a"]),
        "b": legacy.flowinvoice_normalize_company_name(i["b"]),
    }
    assert same(result, case["output"])


@pytest.mark.parametrize("case", cases("flowinvoice_verify_company"), ids=lambda c: c["name"])
def test_verify_company_legacy(case: dict[str, Any]) -> None:
    i = plain(case["inputs"])
    output = plain(case["output"])["result"]
    vat = None
    if output["vat_validation"] is not None:
        vat = dict(output["vat_validation"])
        vat.pop("request_date")
        if i["files"].get("vies") == "vies_fault.xml":
            expected_vat = legacy.flowinvoice_validate_vat(i["vat_id"], error=vat["error_message"])
        else:
            text = (FILES / i["files"]["vies"]).read_text()
            expected_vat = legacy.flowinvoice_validate_vat(i["vat_id"], response_text=text)
        assert expected_vat == vat
    register = None
    if "register" in i["files"]:
        register = legacy.flowinvoice_register_company(
            200, json.loads((FILES / i["files"]["register"]).read_text())
        )
    result = legacy.flowinvoice_verify_company(
        i["name"], vat=vat, register=register, country=i["country"]
    )
    if result["vat_validation"] is not None:
        output["vat_validation"].pop("request_date")
    assert result == output
