"""Flat tables of register and overview workbooks (no spreadsheet dependency).

The tables are rendered by :mod:`.excel` with ``auditcore_reporting``; they
contain plain cell values only.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime
from typing import Any

MAX_ROWS = 100_000

#: Value of one worksheet cell as the reporting renderer accepts it.
CellValue = str | int | float | date | None
#: ``(sheet name, header, rows)`` of one worksheet.
Table = tuple[str, Sequence[str], Sequence[Sequence[object]]]


def yes_no(value: object) -> str:
    """``Ja``/``Nein`` for explicit flags, empty for anything else."""
    if value is True:
        return "Ja"
    if value is False:
        return "Nein"
    return ""


def cell_value(value: object) -> CellValue:
    """Plain cell value for the reporting renderer; lists joined, flags as Ja/Nein."""
    if isinstance(value, datetime) and value.tzinfo is not None:
        return value.isoformat()  # Excel kennt keine Zeitzonen; Angabe bleibt eindeutig
    if isinstance(value, bool):
        return yes_no(value)
    if value is None or isinstance(value, (str, int, float, date)):
        return value
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value)
    return str(value)


def _register_info(report: Mapping[str, Any]) -> list[list[object]]:
    meta = report["meta"]
    cover = report.get("cover") or {}
    info: list[list[object]] = [
        ["Verzeichnis", meta.get("register_id")],
        ["Fassung", meta.get("version")],
        ["Status", meta.get("status")],
        ["Inhaltsprüfsumme (SHA-256)", meta.get("content_hash")],
        ["Erstellt von", meta.get("created_by")],
        ["Bearbeitet von", ", ".join(meta.get("editors") or [])],
        ["Freigegeben von", meta.get("released_by") or ""],
        ["Profil", f"{meta.get('profile_id')} {meta.get('profile_version')}"],
    ]
    for part in ("verantwortlicher", "dsb"):
        for key, value in (cover.get(part) or {}).items():
            info.append([f"{part}.{key}", value])
    return info


def register_tables(report: Mapping[str, Any]) -> list[Table]:
    """Cover sheet, activities and review notes of a register report."""
    info = _register_info(report)
    columns = report["columns"]
    header = ["Referat", "Kennung", *[c["title"] for c in columns]]
    rows = [
        [group["name"], activity.get("id"), *[activity.get(c["key"]) for c in columns]]
        for group in report["departments"]
        for activity in group["activities"]
    ]
    if len(rows) > MAX_ROWS:
        raise ValueError("Zu viele Zeilen für die Arbeitsmappe.")
    issues = [[i["code"], i["message"], i["blocking"], i["subject"]] for i in report["issues"]]
    return [
        ("Vorblatt", ["Angabe", "Wert"], info),
        ("Verarbeitungstätigkeiten", header, rows),
        ("Prüfhinweise", ["Code", "Hinweis", "Blockiert Freigabe", "Bezug"], issues),
    ]


OVERVIEW_HEADER = (
    "Nr.",
    "Kennung",
    "Verarbeitungstätigkeit",
    "Referat",
    "Zweck",
    "Fassung des Verzeichnisses",
    "Folgenabschätzung",
    "Fassung",
    "Entscheidung",
    "Freigegeben am",
    "Überprüfung erforderlich",
)


def _overview_line(row: Mapping[str, Any]) -> list[object]:
    dsfa = row.get("dsfa") or {}
    return [
        row.get("position"),
        row.get("id"),
        row.get("name"),
        row.get("referat"),
        row.get("zweck"),
        row.get("vvt_version"),
        dsfa.get("status") or "noch nicht begonnen",
        dsfa.get("version"),
        dsfa.get("entscheidung"),
        dsfa.get("freigegeben_am"),
        dsfa.get("pruefung_erforderlich"),
    ]


def overview_tables(
    rows: Sequence[Mapping[str, Any]], tenant_label: str, generated_at: datetime
) -> list[Table]:
    """Activities with their newest assessment and the date of the overview."""
    lines = [_overview_line(row) for row in rows]
    if len(lines) > MAX_ROWS:
        raise ValueError("Zu viele Zeilen für die Arbeitsmappe.")
    return [
        ("Folgenabschätzungen", list(OVERVIEW_HEADER), lines),
        ("Stand", ["Angabe", "Wert"], [["Mandant", tenant_label], ["Stand", generated_at]]),
    ]
