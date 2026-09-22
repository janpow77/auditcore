"""Optional Excel output (``pip install 'auditcore_dataprotection[excel]'``).

openpyxl is imported lazily. Every text cell is written as literal text:
the source application stored a text such as ``=1+1`` as a formula, which a
spreadsheet program evaluates when the file is opened. That is corrected
here for the legacy-compatible layouts and the new-contract workbooks alike.
"""

from __future__ import annotations

import io
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime
from typing import Any

from .legacy import REGIME_DSGVO, legacy_profile
from .register import group_by_department

MAX_ROWS = 100_000
MAX_TEXT = 32_767


class ExportDependencyError(ImportError):
    """The optional renderer dependency is not installed."""


def _openpyxl() -> Any:
    try:
        import openpyxl
    except ImportError as exc:  # pragma: no cover - exercised without the extra
        raise ExportDependencyError(
            "Excel-Ausgabe benötigt openpyxl: pip install 'auditcore_dataprotection[excel]'"
        ) from exc
    return openpyxl


def _put(ws: Any, row: int, column: int, value: Any) -> Any:
    """Write a value; strings are always literal text, never formulas."""
    if isinstance(value, str) and len(value) > MAX_TEXT:
        value = value[:MAX_TEXT]
    cell = ws.cell(row=row, column=column, value=value)
    if isinstance(value, str) and cell.data_type == "f":
        cell.data_type = "s"
    return cell


def _yes_no(value: Any) -> str:
    if value is True:
        return "Ja"
    if value is False:
        return "Nein"
    return ""


def _to_bytes(workbook: Any) -> bytes:
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def legacy_register_workbook(document: Mapping[str, Any], tenant_label: str) -> Any:
    """Layout of ``baue_verarbeitungsverzeichnis_workbook`` (cover sheet, one section
    per department); returns an openpyxl ``Workbook``."""
    openpyxl = _openpyxl()
    from openpyxl.styles import Font

    content = document.get("inhalt") or {}
    cover = content.get("deckblatt") or {}
    activities: list[Mapping[str, Any]] = list(content.get("taetigkeiten") or [])
    groups = group_by_department(activities, list(content.get("referate") or []))

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Vorblatt"
    title_font = Font(bold=True, size=14)
    heading_font = Font(bold=True, size=11)
    _put(
        ws, 1, 1, "Verzeichnis von Verarbeitungstätigkeiten (Art. 30 Abs. 1 DS-GVO)"
    ).font = title_font
    _put(ws, 2, 1, tenant_label).font = heading_font
    _legacy_cover(ws, document, cover)
    _legacy_activity_sheet(wb, groups)
    return wb


def _legacy_cover(ws: Any, document: Mapping[str, Any], cover: Mapping[str, Any]) -> None:
    """Status line, controller and DPO block of the legacy cover sheet."""
    from openpyxl.styles import Font

    label_font = Font(bold=True, size=10)
    controller = cover.get("verantwortlicher") or {}
    dpo = cover.get("dsb") or {}
    status = document.get("status")
    status_text = {
        "entwurf": "ENTWURF - noch nicht freigegeben",
        "freigegeben": "FREIGEGEBEN",
        "abgeloest": "ABGELÖST (historische Fassung)",
    }.get(str(status), status)
    created_at = document.get("erstellt_am")
    released_at = document.get("freigegeben_am")
    line = (
        f"Status: {status_text} — Fassung {document.get('version')}, "
        f"erstellt von {document.get('ersteller')} am "
        f"{created_at.strftime('%d.%m.%Y') if isinstance(created_at, datetime) else '—'}"
    )
    if document.get("freigeber") and isinstance(released_at, datetime):
        line += f", freigegeben von {document.get('freigeber')} am " + released_at.strftime(
            "%d.%m.%Y"
        )
    _put(ws, 3, 1, line)
    row = 5
    _put(ws, row, 1, "Verantwortlicher").font = label_font
    _put(ws, row, 4, "Datenschutzbeauftragte/r").font = label_font
    row += 1
    controller_lines = [
        controller.get("name", ""),
        controller.get("dienststelle", ""),
        f"{controller.get('strasse', '')}, {controller.get('plz', '')} "
        f"{controller.get('ort', '')}".strip(", "),
        f"{controller.get('telefon', '')} · {controller.get('email', '')}".strip(" ·"),
    ]
    dpo_name = " ".join(
        filter(None, [dpo.get("anrede", ""), dpo.get("titel", ""), dpo.get("name", "")])
    )
    dpo_lines = [
        dpo_name or "—",
        f"{dpo.get('strasse', '')}, {dpo.get('plz', '')} {dpo.get('ort', '')}".strip(", "),
        f"{dpo.get('telefon', '')} · {dpo.get('email', '')}".strip(" ·"),
    ]
    for i in range(max(len(controller_lines), len(dpo_lines))):
        if i < len(controller_lines):
            _put(ws, row + i, 1, controller_lines[i] or "—")
        if i < len(dpo_lines):
            _put(ws, row + i, 4, dpo_lines[i] or "—")
    ws.column_dimensions["A"].width = 45
    ws.column_dimensions["D"].width = 45


def _legacy_activity_sheet(wb: Any, groups: Any) -> None:
    """One section per department with header row, values and auto filter."""
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    columns = list(legacy_profile(REGIME_DSGVO).register_columns)
    heading_font = Font(bold=True, size=11)
    label_font = Font(bold=True, size=10)
    head_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    department_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    ws2 = wb.create_sheet("Verarbeitungstätigkeiten")
    widths = {
        "name": 28,
        "zweck": 34,
        "ermaechtigungsgrundlage": 30,
        "ansprechperson": 20,
        "kategorien_betroffene": 30,
        "kategorien_daten": 30,
        "kategorien_empfaenger": 26,
        "name_empfaenger": 20,
        "drittlandtransfer": 14,
        "name_empfaenger_drittland": 20,
        "avv_besteht": 14,
        "auftragsverarbeiter": 26,
        "gemeinsame_verantwortlichkeit": 16,
        "gemeinsame_verantwortliche": 26,
        "speicherdauer": 26,
        "loeschfrist_rechtsgrundlage": 32,
        "anmerkungen": 34,
    }
    count = len(columns)
    for index, (name, _) in enumerate(columns, start=1):
        ws2.column_dimensions[get_column_letter(index)].width = widths.get(name, 20)
    r = 1
    if not groups:
        _put(ws2, r, 1, "Noch keine Verarbeitungstätigkeit erfasst.")
    for department, rows in groups:
        ws2.merge_cells(start_row=r, start_column=1, end_row=r, end_column=count)
        cell = _put(ws2, r, 1, f"Referat: {department}")
        cell.font = heading_font
        cell.fill = department_fill
        r += 1
        for c, (_, label) in enumerate(columns, start=1):
            cell = _put(ws2, r, c, label)
            cell.font = label_font
            cell.fill = head_fill
            cell.alignment = Alignment(wrap_text=True, vertical="top")
        header = r
        r += 1
        for activity in rows:
            for c, (name, _) in enumerate(columns, start=1):
                value = activity.get(name)
                if isinstance(value, bool):
                    value = _yes_no(value)
                cell = _put(ws2, r, c, value or "")
                cell.alignment = Alignment(wrap_text=True, vertical="top")
            r += 1
        ws2.auto_filter.ref = f"A{header}:{get_column_letter(count)}{r - 1}"
        r += 1
    ws2.freeze_panes = "A2"


def _date(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%d.%m.%Y %H:%M")
    return "–"


def legacy_overview_workbook(
    rows: Sequence[Mapping[str, Any]], tenant_label: str, generated_at: datetime
) -> Any:
    """Layout of ``baue_uebersicht_workbook``; ``generated_at`` replaces ``datetime.now()``."""
    openpyxl = _openpyxl()
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    profile = legacy_profile(REGIME_DSGVO)
    status_texts = profile.status_texts
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Folgenabschätzungen"
    _put(ws, 1, 1, "Datenschutz-Folgenabschätzungen je Verarbeitungstätigkeit").font = Font(
        bold=True, size=14
    )
    _put(ws, 2, 1, tenant_label or "")
    _put(ws, 3, 1, f"Stand: {generated_at.strftime('%d.%m.%Y %H:%M')}").font = Font(
        size=9, italic=True
    )
    columns = [
        ("Nr.", 6),
        ("Verarbeitungstätigkeit", 42),
        ("Referat", 16),
        ("Zweck", 46),
        ("Fassung des Verzeichnisses", 12),
        ("Folgenabschätzung", 18),
        ("Fassung", 8),
        ("Entscheidung", 30),
        ("Freigegeben am", 18),
    ]
    head = 5
    for i, (title, width) in enumerate(columns, start=1):
        cell = _put(ws, head, i, title)
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", start_color="D9E1F2", end_color="D9E1F2")
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        ws.column_dimensions[get_column_letter(i)].width = width
    for line, entry in enumerate(rows, start=head + 1):
        if line - head > MAX_ROWS:
            raise ValueError("Zu viele Zeilen für die Übersicht.")
        dsfa = entry.get("dsfa") or {}
        released = dsfa.get("freigegeben_am")
        values = [
            entry.get("position"),
            entry.get("name"),
            entry.get("referat"),
            entry.get("zweck"),
            entry.get("vvt_version"),
            status_texts.get(dsfa.get("status", ""), "noch nicht begonnen"),
            dsfa.get("version"),
            dsfa.get("entscheidung"),
            _date(released) if released else "",
        ]
        for column, value in enumerate(values, start=1):
            _put(ws, line, column, value).alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = ws.cell(row=head + 1, column=1)
    ws2 = wb.create_sheet("Bewertungsmaßstab")
    _put(ws2, 1, 1, "Maßstab der Risikobewertung").font = Font(bold=True, size=12)
    r = 3
    for title, levels in (
        ("Schwere des Schadens", profile.severity_levels),
        ("Eintrittswahrscheinlichkeit", profile.likelihood_levels),
    ):
        _put(ws2, r, 1, title).font = Font(bold=True)
        r += 1
        for level, text in levels.items():
            _put(ws2, r, 1, level)
            _put(ws2, r, 2, text)
            r += 1
        r += 1
    _put(ws2, r, 1, "Maßnahmen nach Artikel 32 DSGVO").font = Font(bold=True)
    r += 1
    for measure in profile.measures:
        _put(ws2, r, 1, measure.title)
        _put(ws2, r, 2, measure.legal_basis)
        r += 1
    ws2.column_dimensions["A"].width = 30
    ws2.column_dimensions["B"].width = 80
    return wb


def _cell_value(value: Any) -> Any:
    if isinstance(value, datetime) and value.tzinfo is not None:
        return value.isoformat()  # Excel kennt keine Zeitzonen; Angabe bleibt eindeutig
    if value is None or isinstance(value, (str, int, float, datetime, date)):
        return value
    if isinstance(value, bool):
        return _yes_no(value)
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value)
    return str(value)


def _sheet(wb: Any, title: str, header: Sequence[str], rows: Iterable[Sequence[Any]]) -> None:
    from openpyxl.styles import Font

    ws = wb.create_sheet(title[:31])
    for column, label in enumerate(header, start=1):
        _put(ws, 1, column, label).font = Font(bold=True)
    for line, values in enumerate(rows, start=2):
        if line - 1 > MAX_ROWS:
            raise ValueError("Zu viele Zeilen für die Arbeitsmappe.")
        for column, value in enumerate(values, start=1):
            v = _cell_value(value)
            if isinstance(v, bool):
                v = _yes_no(v)
            _put(ws, line, column, v)
    ws.freeze_panes = "A2"


def render_register_xlsx(report: Mapping[str, Any]) -> bytes:
    """Register report (see :func:`~auditcore_dataprotection.export.register_report`) as XLSX."""
    openpyxl = _openpyxl()
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    meta = report["meta"]
    cover = report.get("cover") or {}
    info = [
        ("Verzeichnis", meta.get("register_id")),
        ("Fassung", meta.get("version")),
        ("Status", meta.get("status")),
        ("Inhaltsprüfsumme (SHA-256)", meta.get("content_hash")),
        ("Erstellt von", meta.get("created_by")),
        ("Bearbeitet von", ", ".join(meta.get("editors") or [])),
        ("Freigegeben von", meta.get("released_by") or ""),
        ("Profil", f"{meta.get('profile_id')} {meta.get('profile_version')}"),
    ]
    for part in ("verantwortlicher", "dsb"):
        for key, value in (cover.get(part) or {}).items():
            info.append((f"{part}.{key}", value))
    _sheet(wb, "Vorblatt", ["Angabe", "Wert"], info)
    columns = report["columns"]
    header = ["Referat", "Kennung", *[c["title"] for c in columns]]
    rows = []
    for group in report["departments"]:
        for activity in group["activities"]:
            rows.append(
                [group["name"], activity.get("id"), *[activity.get(c["key"]) for c in columns]]
            )
    _sheet(wb, "Verarbeitungstätigkeiten", header, rows)
    _sheet(
        wb,
        "Prüfhinweise",
        ["Code", "Hinweis", "Blockiert Freigabe", "Bezug"],
        [[i["code"], i["message"], i["blocking"], i["subject"]] for i in report["issues"]],
    )
    return _to_bytes(wb)


def render_overview_xlsx(
    rows: Sequence[Mapping[str, Any]], tenant_label: str, generated_at: datetime
) -> bytes:
    """Overview of activities and their newest assessment as XLSX."""
    openpyxl = _openpyxl()
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    header = [
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
    ]
    lines = []
    for row in rows:
        dsfa = row.get("dsfa") or {}
        lines.append(
            [
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
        )
    _sheet(wb, "Folgenabschätzungen", header, lines)
    _sheet(wb, "Stand", ["Angabe", "Wert"], [["Mandant", tenant_label], ["Stand", generated_at]])
    return _to_bytes(wb)
