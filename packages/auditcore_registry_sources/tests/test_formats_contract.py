"""List format contract (REG-C03..REG-C06): no silent empties, no invented precision."""

from __future__ import annotations

import pytest
from replay_support import FILES

from auditcore_registry_sources import FormatError, parse_targets_simple_csv, xml_entries
from auditcore_registry_sources.opensanctions_csv import (
    SIMPLE_CSV_COLUMNS,
    entry_to_row,
    serialize_targets_simple_csv,
)


def test_csv_entries_issues_and_hash() -> None:
    data = (FILES / "eu_fsf_targets.simple.csv").read_bytes()
    parsed = parse_targets_simple_csv(data, list_key="eu_fsf")
    assert parsed.columns == SIMPLE_CSV_COLUMNS
    assert len(parsed.entries) == 8 and parsed.rows_seen == 10
    assert [(i.row, i.reason) for i in parsed.issues] == [(6, "Kennung fehlt"), (7, "Name fehlt")]
    assert not parsed.complete
    lodz = next(e for e in parsed.entries if e.entry_id == "eu-fsf-demo-0008")
    assert lodz.name == "Łódź Beispiel Sp. z o.o." and lodz.dataset == "eu_fsf"
    assert parsed.entries[0].aliases == (
        "Ivan Petrovich Musterov",
        "Иван Петрович Мустеров",
        "Ivan Musterov",
    )
    assert len(parsed.content_sha256) == 64


@pytest.mark.parametrize(
    ("name", "message"),
    [
        ("leer_nur_kopf.csv", "keine verwertbaren Einträge"),
        ("falsches_format.csv", "Pflichtspalten fehlen"),
        ("latin1_minimal.csv", "nicht UTF-8"),
    ],
)
def test_reg_c03_bad_deliveries_are_errors(name: str, message: str) -> None:
    with pytest.raises(FormatError, match=message):
        parse_targets_simple_csv((FILES / name).read_bytes(), list_key="x")


def test_csv_round_trip() -> None:
    parsed = parse_targets_simple_csv(
        (FILES / "un_sc_targets.simple.csv").read_bytes(), list_key="un_sc"
    )
    again = parse_targets_simple_csv(
        serialize_targets_simple_csv(entry_to_row(e) for e in parsed.entries), list_key="un_sc"
    )
    assert [e.to_dict() | {"dataset": ""} for e in again.entries] == [
        e.to_dict() | {"dataset": ""} for e in parsed.entries
    ]


def test_reg_c04_xml_keeps_year_precision_and_all_values() -> None:
    eu = xml_entries((FILES / "eu_fsf_export.xml").read_bytes(), format="eu_fsf_xml", list_key="eu")
    first = next(e for e in eu.entries if e.entry_id == "990001")
    assert first.birth_date == "1961-04-12"
    assert first.countries == "RU;BY"
    jorgen = next(e for e in eu.entries if e.entry_id == "990003")
    assert jorgen.birth_date == "1975"  # the originals turn this into 1975-01-01
    anna = next(e for e in eu.entries if e.entry_id == "990004")
    assert anna.birth_date == "1980-07;1981-01-01"
    assert [(i.reason, i.entry_id) for i in eu.issues] == [("Name fehlt", "990005")]
    ofac = xml_entries((FILES / "ofac_sdn.xml").read_bytes(), format="ofac_sdn_xml", list_key="o")
    ivan = ofac.entries[0]
    assert ivan.birth_date == "12 Apr 1961" and ivan.countries == "Russia;Belarus"
    assert ivan.schema == "Person"
    un = xml_entries(
        (FILES / "un_sc_consolidated.xml").read_bytes(), format="un_sc_xml", list_key="u"
    )
    iwan = un.entries[0]
    assert iwan.birth_date == "1961"
    assert iwan.countries == "Russian Federation;Belarus"


def test_broken_xml_is_a_format_error() -> None:
    with pytest.raises(FormatError, match="nicht lesbar"):
        xml_entries((FILES / "kaputt.xml").read_bytes(), format="eu_fsf_xml", list_key="eu")
    with pytest.raises(FormatError, match="Unbekanntes"):
        xml_entries(b"<x/>", format="xyz", list_key="eu")


def test_entity_expansion_is_refused() -> None:
    bomb = (
        b'<?xml version="1.0"?><!DOCTYPE l [<!ENTITY a "aaaa"><!ENTITY b "&a;&a;&a;">]>'
        b"<CONSOLIDATED_LIST><ENTITIES><ENTITY><DATAID>1</DATAID><FIRST_NAME>&b;</FIRST_NAME>"
        b"</ENTITY></ENTITIES></CONSOLIDATED_LIST>"
    )
    with pytest.raises(FormatError):
        xml_entries(bomb, format="un_sc_xml", list_key="u")
