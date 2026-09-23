"""Reader corrections and limits; each correction is shown next to the legacy behavior."""

from __future__ import annotations

import io
import zipfile

import pytest
from conftest import FIXTURES, load

from auditcore_funding_sources import flowsearch, tables, workshop
from auditcore_funding_sources.errors import SourceFormatError

FILES = FIXTURES / "files"


def test_fs_w04_title_rows_no_longer_abort_the_file() -> None:
    legacy = {c["name"]: c for c in load("flowworkshop")["cases"]}
    crashed = [
        c for c in legacy.values() if "semikolon_titelzeilen.csv" in c["name"] and c["exception"]
    ]
    assert crashed and crashed[0]["exception"]["type"] == "ParserError"
    rows = workshop.parse_file((FILES / "semikolon_titelzeilen.csv").read_bytes(), "x.csv")
    assert [r.get("beneficiary_name") for r in rows] == [
        "Beispiel GmbH",
        "Müller & Söhne KG",
        None,
        "Ohne Kosten e.V.",
    ]


def test_fs_w02_text_typing_keeps_leading_zero_legacy_drops_it() -> None:
    content = (FILES / "semikolon_ohne_titel.csv").read_bytes()
    legacy = workshop.parse_file(content, "x.csv")
    text = workshop.parse_file(content, "x.csv", typing="text")
    assert legacy[0]["plz"] == "1067" and text[0]["plz"] == "01067"


def test_fs_w03_gaps_change_the_raw_value_and_hash_in_legacy_only() -> None:
    content = (FILES / "zahlen_spalte.csv").read_bytes()
    legacy = workshop.parse_file(content, "x.csv")
    text = workshop.parse_file(content, "x.csv", typing="text")
    assert legacy[0]["cost_total_raw"] == "150000.0" and text[0]["cost_total_raw"] == "150000"
    assert workshop.compute_record_hash(legacy[0], "s") != workshop.compute_record_hash(
        text[0], "s"
    )


def test_fs_w08_strict_header_detection_keeps_a_numeric_first_row() -> None:
    content = (FILES / "erste_zeile_numerisch.csv").read_bytes()
    legacy = workshop.parse_file(content, "x.csv")
    strict = workshop.parse_file(content, "x.csv", header_detection="strict")
    assert [r.get("beneficiary_name") for r in legacy] == [None]
    assert [r["beneficiary_name"] for r in strict] == ["A GmbH", "B GmbH"]


def test_limits_and_formats() -> None:
    with pytest.raises(SourceFormatError):
        tables.read_csv(b"a;b\n1;2\n", limits=tables.Limits(max_bytes=3))
    with pytest.raises(SourceFormatError):
        tables.read_csv(b"Name;Betrag;Ort\nA;1;X\nB;2;Y;zu;viele\n")
    with pytest.raises(SourceFormatError):
        tables.read_table(b"%PDF", "liste.pdf")
    with pytest.raises(SourceFormatError):
        tables.read_csv("text")  # type: ignore[arg-type]
    with pytest.raises(SourceFormatError):
        tables.read_xlsx(b"kein xlsx")


def test_xlsx_text_typing() -> None:
    table = tables.read_xlsx((FILES / "titelzeilen.xlsx").read_bytes(), typing="text")
    first = dict(zip(table.headers, table.rows[0], strict=True))
    assert first["PLZ"] == "1067" and first["Gesamtkosten"] == "125000.5"
    assert first["Datum des Beginns"] == "2024-02-01T00:00:00"


def test_fs_s03_zip_member_size_is_limited() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("liste.csv", b"0" * 5000)
    with pytest.raises(SourceFormatError):
        flowsearch.extract_from_zip(buffer.getvalue(), max_member_bytes=100)
    assert flowsearch.extract_from_zip(buffer.getvalue()) == b"0" * 5000
    with pytest.raises(SourceFormatError):
        flowsearch.extract_from_zip(b"kein zip")


def test_readers_do_not_mutate_or_share_state() -> None:
    content = (FILES / "fonds_gemischt.csv").read_bytes()
    first = workshop.parse_file(content, "x.csv")
    first[0]["beneficiary_name"] = "verändert"
    assert workshop.parse_file(content, "x.csv")[0]["beneficiary_name"] == "A GmbH"
