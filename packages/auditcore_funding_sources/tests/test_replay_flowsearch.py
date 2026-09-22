"""Every recorded flowsearch output is reproduced exactly (separate profile)."""

from __future__ import annotations

from typing import Any

import pytest
from conftest import FIXTURES, encode, load, revive

from auditcore_funding_sources import flowsearch as fs

DATA = load("flowsearch")
CASES = DATA["cases"]
MAPPINGS = revive(DATA["constants"])["fallback_mapping"]


def run(case: dict[str, Any]) -> Any:
    op, i = case["operation"], revive(case["inputs"])
    if op == "flowsearch.parse_amount":
        return fs.parse_amount(i["value"])
    if op == "flowsearch.parse_date":
        return fs.parse_date(i["value"])
    if op == "flowsearch.normalize_name":
        return fs.normalize_name(i["value"])
    if op == "flowsearch.parse_location":
        return fs.parse_location(i["value"])
    if op == "flowsearch.truncate":
        return fs.truncate(i["value"], i["max"])
    if op == "flowsearch.extract_mapped_field":
        return fs.extract_mapped_field(i["record"], i["columns"], i["field"], MAPPINGS)
    if op == "flowsearch.parse_csv":
        return fs.parse_csv((FIXTURES / "files" / i["file"]).read_bytes(), i["mapping"])
    if op == "flowsearch.parse_excel":
        return fs.parse_excel((FIXTURES / "files" / i["file"]).read_bytes(), i["mapping"])
    if op == "flowsearch.extract_from_zip":
        if i["file"] == "(no table)":
            import io
            import zipfile

            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w") as zf:
                zf.writestr(zipfile.ZipInfo("a.txt", date_time=(2026, 9, 1, 0, 0, 0)), "x")
            return fs.extract_from_zip(buffer.getvalue())
        return fs.extract_from_zip((FIXTURES / "files" / i["file"]).read_bytes())
    if op == "flowsearch.import_record":
        mappings = {
            "_fallback": MAPPINGS,
            "test_quelle": {
                "delimiter": ";",
                "skip_rows": 1,
                "header_row": 2,
                "columns": {
                    "beneficiary_name": "Begünstigter",
                    "project_name": "Vorhaben",
                    "total_cost": "Gesamtkosten",
                    "eu_contribution": "EU-Beitrag",
                    "location": "Ort",
                    "start_date": "Beginn",
                },
            },
        }
        values = fs.record_values(i["record"], i["source"], mappings)
        if values is not None:
            values.pop("defaulted")
        return values
    raise AssertionError(op)


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_recorded_output(case: dict[str, Any]) -> None:
    if case["exception"]:
        with pytest.raises(Exception) as caught:
            run(case)
        assert type(caught.value).__name__ == case["exception"]["type"]
        assert str(caught.value) == case["exception"]["message"]
    else:
        assert encode(run(case)) == case["output"]


def test_record_values_report_defaulted_amounts() -> None:
    source = {"source_key": "q", "bundesland": "Hessen", "fonds": "EFRE"}
    mappings = {"q": {"columns": {"beneficiary_name": "N", "total_cost": "K"}}}
    values = fs.record_values({"N": "A GmbH", "K": "keine Angabe"}, source, mappings)
    assert values is not None
    assert values["total_amount"] == 0.0 and "total_cost" in values["defaulted"]


def test_fixture_is_complete() -> None:
    assert len(CASES) == 112
    assert DATA["source"]["checkout_clean"] is True
