"""Legacy report and workbook layouts reproduce the recorded original exports."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from conftest import revive

from auditcore_dataprotection.legacy import legacy_report_html

openpyxl = pytest.importorskip("openpyxl")

from auditcore_dataprotection.excel import (  # noqa: E402
    legacy_overview_workbook,
    legacy_register_workbook,
)

TENANT = "Synthetische Testbehörde"


def cells(workbook: Any) -> dict[str, Any]:
    """Same projection as the capture tool's ``workbook_cells``."""
    sheets = []
    for sheet in workbook.worksheets:
        found = []
        for row in sheet.iter_rows():
            for cell in row:
                if cell.value is None:
                    continue
                value = cell.value
                if isinstance(value, datetime):
                    value = {"$datetime": value.isoformat()}
                found.append(
                    {
                        "ref": cell.coordinate,
                        "value": value,
                        "type": cell.data_type,
                        "bold": bool(cell.font and cell.font.bold),
                    }
                )
        sheets.append(
            {
                "title": sheet.title,
                "cells": found,
                "merged": sorted(str(r) for r in sheet.merged_cells.ranges),
                "freeze_panes": sheet.freeze_panes,
                "auto_filter": sheet.auto_filter.ref,
            }
        )
    return {"sheets": sheets}


def corrected(expected: dict[str, Any], formula_refs: list[tuple[str, str]]) -> dict[str, Any]:
    """The original stored the text '=1+1' as a formula; the only intended difference."""
    found = [
        (s["title"], c["ref"]) for s in expected["sheets"] for c in s["cells"] if c["type"] == "f"
    ]
    assert found == formula_refs
    for sheet in expected["sheets"]:
        for cell in sheet["cells"]:
            if cell["type"] == "f":
                assert cell["value"] == "=1+1"
                cell["type"] = "s"
    return expected


def test_report_html_is_identical(legacy: dict[str, Any]) -> None:
    exports = legacy["workflow"]["exports"]
    assert legacy_report_html(revive(exports["report_record"]), TENANT) == exports["report_html"]


def test_reassessment_report_html_is_identical(legacy: dict[str, Any]) -> None:
    exports = legacy["workflow"]["exports"]
    record = revive(exports["reassessment_record"])
    assert legacy_report_html(record, "") == exports["reassessment_report_html"]


def test_register_workbook_matches_except_corrected_formula(legacy: dict[str, Any]) -> None:
    exports = legacy["workflow"]["exports"]
    document = revive(exports["register_workbook_document"])
    observed = cells(legacy_register_workbook(document, TENANT))
    expected = corrected(exports["register_workbook"], [("Verarbeitungstätigkeiten", "B8")])
    assert observed == expected


def test_formula_text_is_literal_after_round_trip(legacy: dict[str, Any], tmp_path: Any) -> None:
    document = revive(legacy["workflow"]["exports"]["register_workbook_document"])
    path = tmp_path / "vvt.xlsx"
    legacy_register_workbook(document, TENANT).save(path)
    cell = openpyxl.load_workbook(path)["Verarbeitungstätigkeiten"]["B8"]
    assert cell.value == "=1+1" and cell.data_type == "s"


def test_empty_register_workbook_is_identical(legacy: dict[str, Any]) -> None:
    document = {
        "inhalt": {},
        "version": 9,
        "status": "entwurf",
        "ersteller": "anna",
        "erstellt_am": datetime(2026, 9, 2, tzinfo=UTC),
        "freigeber": None,
        "freigegeben_am": None,
    }
    observed = cells(legacy_register_workbook(document, TENANT))
    assert observed == legacy["workflow"]["exports"]["register_workbook_empty"]


def test_overview_workbook_is_identical(legacy: dict[str, Any]) -> None:
    exports = legacy["workflow"]["exports"]
    stand = exports["overview_workbook"]["sheets"][0]["cells"][2]["value"]
    generated_at = datetime.strptime(stand, "Stand: %d.%m.%Y %H:%M")
    rows = revive(exports["overview_rows"])
    observed = cells(legacy_overview_workbook(rows, TENANT, generated_at))
    assert observed == corrected(exports["overview_workbook"], [("Folgenabschätzungen", "D8")])
