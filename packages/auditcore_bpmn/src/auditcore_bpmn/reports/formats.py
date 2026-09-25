"""Ausgabeformate für Berichtszeilen: CSV, MyST-Markdown und Excel (Extra ``excel``)."""

from __future__ import annotations

import csv
import io
from collections.abc import Mapping, Sequence
from typing import Any

from ..optional import require_module


def _columns(rows: Sequence[Mapping[str, Any]], columns: Mapping[str, str] | None) -> dict[str, str]:
    return dict(columns) if columns else {key: key for key in (rows[0] if rows else {})}


def to_csv(rows: Sequence[Mapping[str, Any]], columns: Mapping[str, str] | None = None, *, delimiter: str = ";") -> str:
    """CSV (UTF-8, Standard-Trennzeichen Semikolon), Kopfzeile aus ``columns`` oder den Schlüsseln."""
    selected = _columns(rows, columns)
    output = io.StringIO()
    writer = csv.writer(output, delimiter=delimiter, lineterminator="\n")
    writer.writerow(list(selected.values()))
    for row in rows:
        writer.writerow(["" if row.get(key) is None else row.get(key) for key in selected])
    return output.getvalue()


def _cell(value: Any) -> str:
    return ("" if value is None else str(value)).replace("|", "\\|").replace("\n", " ")


def to_myst(
    rows: Sequence[Mapping[str, Any]],
    columns: Mapping[str, str] | None = None,
    *,
    title: str | None = None,
    target: str | None = None,
) -> str:
    """Tabelle als MyST-Markdown (Pipe-Tabelle, optional mit Überschrift und Sprungmarke)."""
    selected = _columns(rows, columns)
    lines = [f"({target})="] if target else []
    if title:
        lines += [f"## {title}", ""]
    lines.append("| " + " | ".join(_cell(v) for v in selected.values()) + " |")
    lines.append("|" + "|".join("---" for _ in selected) + "|")
    lines += ["| " + " | ".join(_cell(row.get(key)) for key in selected) + " |" for row in rows]
    return "\n".join(lines) + "\n"


def to_xlsx(tables: Mapping[str, Sequence[Mapping[str, Any]]]) -> bytes:
    """Mehrere Tabellen als Excel-Mappe (Extra ``excel``)."""
    openpyxl = require_module("openpyxl", "excel")
    styles = require_module("openpyxl.styles", "excel")
    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)
    for name, rows in tables.items():
        sheet = workbook.create_sheet(name[:31])
        columns = list(rows[0].keys()) if rows else []
        sheet.append(columns)
        for cell in sheet[1]:
            cell.font = styles.Font(bold=True, color="FFFFFF")
            cell.fill = styles.PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        for row in rows:
            sheet.append(["" if row.get(c) is None else row.get(c) for c in columns])
        for cells in sheet.columns:
            length = max((len(str(c.value)) for c in cells if c.value), default=0)
            sheet.column_dimensions[cells[0].column_letter].width = min(length + 2, 60)
    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()
