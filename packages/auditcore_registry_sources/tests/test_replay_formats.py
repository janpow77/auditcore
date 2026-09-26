"""List formats: audit-portal and flowinvoice parsers are reproduced exactly."""

from __future__ import annotations

from typing import Any
from xml.etree.ElementTree import ParseError  # noqa: S405 - exception type only

import pytest
from replay_support import BY_NAME, FILES, cases, plain, same

from auditcore_registry_sources import legacy
from auditcore_registry_sources.sanctions_xml import (
    parse_date_legacy,
    parse_xml_list,
    serialize_xml_list,
    to_simple_row,
)

FORMAT = {
    "eu_fsf_export.xml": "eu_fsf_xml",
    "ofac_sdn.xml": "ofac_sdn_xml",
    "un_sc_consolidated.xml": "un_sc_xml",
    "kaputt.xml": "eu_fsf_xml",
}


@pytest.mark.parametrize("case", cases("portal_parse_csv"), ids=lambda c: c["name"])
def test_portal_csv_parser(case: dict[str, Any]) -> None:
    data = (FILES / plain(case["inputs"])["file"]).read_bytes()
    assert same(legacy.portal_parse_sanctions_csv(data), case["output"])


@pytest.mark.parametrize(
    "case",
    cases("portal_parse_xml") + cases("flowinvoice_parse_xml"),
    ids=lambda c: c["name"],
)
def test_xml_parsers(case: dict[str, Any]) -> None:
    name = plain(case["inputs"])["file"]
    data = (FILES / name).read_bytes()
    if case["exception"]:
        with pytest.raises(ParseError) as error:
            parse_xml_list(data, FORMAT[name], dates="legacy")
        assert str(error.value) == case["exception"]["message"]
    else:
        assert same(parse_xml_list(data, FORMAT[name], dates="legacy"), case["output"])


@pytest.mark.parametrize("name", ["eu_fsf_export.xml", "ofac_sdn.xml", "un_sc_consolidated.xml"])
def test_portal_and_flowinvoice_parsers_are_identical(name: str) -> None:
    assert BY_NAME[f"portal-xml-{name}"]["output"] == BY_NAME[f"flowinvoice-xml-{name}"]["output"]


@pytest.mark.parametrize("case", cases("portal_simple_row"), ids=lambda c: c["name"])
def test_simple_rows(case: dict[str, Any]) -> None:
    name = case["name"].removeprefix("portal-row-").rsplit("-", 1)[0]
    index = int(case["name"].rsplit("-", 1)[1])
    parsed = parse_xml_list((FILES / name).read_bytes(), FORMAT[name], dates="legacy")[index]
    assert same(to_simple_row(parsed), case["output"])


@pytest.mark.parametrize("case", cases("portal_serialize"), ids=lambda c: c["name"])
def test_serialisation(case: dict[str, Any]) -> None:
    name = plain(case["inputs"])["file"]
    parsed = parse_xml_list((FILES / name).read_bytes(), FORMAT[name], dates="legacy")
    assert same(serialize_xml_list(parsed), case["output"])


@pytest.mark.parametrize(
    "case",
    cases("portal_parse_date") + cases("flowinvoice_parse_date"),
    ids=lambda c: c["name"],
)
def test_dates(case: dict[str, Any]) -> None:
    assert same(parse_date_legacy(plain(case["inputs"])["value"]), case["output"])


@pytest.mark.parametrize("case", cases("flowinvoice_to_list"), ids=lambda c: c["name"])
def test_to_list(case: dict[str, Any]) -> None:
    assert same(legacy.flowinvoice_to_list(plain(case["inputs"])["value"]), case["output"])


def test_fixture_files_are_the_ones_the_originals_saw() -> None:
    import hashlib

    from replay_support import OBSERVED

    for name, digest in OBSERVED["fixture_files"].items():
        assert hashlib.sha256((FILES / name).read_bytes()).hexdigest() == digest, name
    assert {s["repository"] for s in OBSERVED["sources"]} == {
        "janpow77/audit_designer",
        "janpow77/flowworkshop",
        "janpow77/audit-portal",
        "janpow77/flowsearch",
        "janpow77/osint",
        "janpow77/riskanalysis",
        "janpow77/flowinvoice",
    }
    assert len(OBSERVED["cases"]) == 456
