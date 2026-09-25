"""Excel- und PDF-Bericht der Prozessanalyse – Übernahme von ``bpmn_export.py`` (audit_designer).

Quelle: ``janpow77/audit_designer@eff41a4c``
``backend/app/modules/flowstat/services/bpmn_export.py`` (Blob ``ebc5b0ab``).
Framework-frei: Die Tabelleninhalte entstehen ohne Zusatzbibliothek
(:func:`analysis_sheets`), die Dateien schreiben die Extras ``excel``
(openpyxl, ohne pandas) und ``pdf`` (reportlab). Zellwerte, Blattreihenfolge,
Kopfzeilenformat, Spaltenbreiten und PDF-Aufbau entsprechen dem Original mit
pandas 2.1.4, openpyxl 3.1.2 und reportlab 4.0.8.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Any

from ..optional import require_module
from .analyzer import BpmnAnalyzer, PersonnelRateLookup, ProcessAnalysis

_OVERVIEW_LABELS = (
    "Prozessname",
    "Anzahl Tasks",
    "",
    "--- Kosten ---",
    "Gesamtkosten pro Durchlauf",
    "Durchschnittliche Kosten pro Task",
    "Jährliche Gesamtkosten",
    "Anzahl Tasks mit Kosten",
    "",
    "--- Zeit ---",
    "Summe Bearbeitungszeit (Minuten)",
    "Summe Bearbeitungszeit (Stunden)",
    "Durchschnittliche Dauer pro Task (Min)",
    "Anzahl Tasks mit Zeitangabe",
    "",
    "--- Aufwand ---",
    "Gesamtaufwand (Personentage)",
    "Jährlicher Gesamtaufwand (PT)",
    "",
    "--- Frequenz ---",
    "Durchläufe pro Jahr",
    "",
    "--- Ressourcen ---",
    "Anzahl Prozessverantwortliche",
    "Anzahl Abteilungen",
    "Anzahl Systeme",
    "Anzahl Tasks mit Verantwortlichem",
)
TASK_COLUMNS = (
    "Task ID",
    "Task Name",
    "Task Typ",
    "Prozessverantwortlicher",
    "Abteilung",
    "Prozesstyp",
    "Personal/Rollen",
    "Personaleinsatz (Anzahl)",
    "Systeme",
    "Dokumente",
    "Dauer",
    "Zeiteinheit",
    "Kosten (EUR)",
    "Aufwand (PT)",
    "Frequenz/Jahr",
    "Dokumentation",
    "Rechtsgrundlagen",
    "Interne Notizen",
)
COST_COLUMNS = (
    "Task Name",
    "Kosten pro Durchlauf (EUR)",
    "Frequenz/Jahr",
    "Jährliche Kosten (EUR)",
    "Anteil an Gesamtkosten (%)",
)


@dataclass
class Sheet:
    """Ein Tabellenblatt: Kopfzeile, Zeilen und Formatangaben wie im Original."""

    name: str
    header: list[str]
    rows: list[list[Any]]
    header_styled: bool = True
    auto_width: bool = False


def _overview(a: ProcessAnalysis) -> Sheet:
    values: list[Any] = [
        a.diagram_name,
        a.total_tasks,
        "",
        "",
        f"{a.total_cost:.2f} EUR",
        f"{a.avg_task_cost:.2f} EUR",
        f"{a.annual_cost:.2f} EUR",
        a.tasks_with_cost,
        "",
        "",
        f"{a.total_duration_minutes:.2f}",
        f"{a.total_duration_minutes / 60:.2f}",
        f"{a.avg_task_duration_minutes:.2f}",
        a.tasks_with_duration,
        "",
        "",
        f"{a.total_person_days:.2f}",
        f"{a.annual_person_days:.2f}",
        "",
        "",
        a.annual_frequency,
        "",
        "",
        len(a.unique_owners),
        len(a.unique_departments),
        len(a.unique_systems),
        a.tasks_with_owner,
    ]
    rows = [list(pair) for pair in zip(_OVERVIEW_LABELS, values, strict=True)]
    return Sheet("Prozessübersicht", ["Kennzahl", "Wert"], rows)


def _value(value: Any) -> Any:
    return value if value is not None else ""


def _task_row(task: dict[str, Any]) -> list[Any]:
    texts = ("process_owner", "process_department", "process_type", "resources_personnel")
    later = ("resources_systems", "resources_documents", "duration_estimated", "duration_unit")
    return [
        task["task_id"],
        task["task_name"],
        task["task_type"],
        *(task[key] or "" for key in texts),
        _value(task["personnel_count"]),
        *(task[key] or "" for key in later),
        _value(task["cost_estimate"]),
        _value(task["effort_person_days"]),
        _value(task["frequency"]),
        task["documentation"] or "",
        task.get("legal_basis") or "",
        task.get("internal_note") or "",
    ]


def _tasks(a: ProcessAnalysis) -> Sheet:
    rows = [_task_row(task) for task in a.tasks]
    return Sheet("Tasks", list(TASK_COLUMNS) if rows else [], rows, auto_width=True)


def _resources(a: ProcessAnalysis) -> Sheet:
    rows: list[list[Any]] = []
    for title, values in (
        ("Prozessverantwortliche", a.unique_owners),
        ("Abteilungen", a.unique_departments),
        ("Systeme/Tools", a.unique_systems),
    ):
        if rows:
            rows.append(["", ""])
        rows.append([title, ""])
        rows += [["", value] for value in values]
    return Sheet("Ressourcen", ["Kategorie", "Wert"], rows)


def _costs(a: ProcessAnalysis) -> Sheet:
    rows = []
    for task in a.tasks:
        if task["cost_estimate"] is None:
            continue
        frequency = task["frequency"] or a.annual_frequency
        annual = task["cost_estimate"] * frequency
        share = annual / a.annual_cost * 100 if a.annual_cost > 0 else 0
        rows.append([task["task_name"], task["cost_estimate"], frequency, round(annual, 2), round(share, 2)])
    # pandas sort_values(ascending=False) behält bei gleichen Werten die Reihenfolge (kleine Tabellen).
    rows.sort(key=lambda row: -row[3])
    return Sheet("Kostenanalyse", list(COST_COLUMNS) if rows else [], rows, auto_width=True)


def _esi(esi: dict[str, Any]) -> Sheet:
    if not esi.get("requirements_parsed"):
        note = [
            [
                "Keine ESI-Kernanforderungen im Prozess definiert",
                "Fügen Sie ESI-Anforderungen im BPMN-Editor hinzu (Process-Element -> ESI-Profil)",
            ]
        ]
        return Sheet("ESI-Anforderungen", ["Hinweis", "Information"], note, header_styled=False, auto_width=True)
    rows: list[list[Any]] = [
        ["ESI-Profil", esi.get("profile") or "ESI"],
        ["Anzahl Kernanforderungen", esi.get("total_requirements", 0)],
        ["Anzahl Bewertungskriterien", esi.get("total_criteria", 0)],
        ["", ""],
        ["--- Anforderungen (roh) ---", ""],
    ]
    rows += [[code, ", ".join(criteria) or "(keine)"] for code, criteria in esi["requirements_parsed"].items()]
    return Sheet("ESI-Anforderungen", ["Kategorie", "Wert"], rows, auto_width=True)


def analysis_sheets(analysis: ProcessAnalysis, esi: dict[str, Any]) -> list[Sheet]:
    """Die fünf Blätter des Originalberichts in Originalreihenfolge."""
    return [_overview(analysis), _tasks(analysis), _resources(analysis), _costs(analysis), _esi(esi)]


def _write_sheet(workbook: Any, styles: Any, sheet: Sheet) -> None:
    target = workbook.create_sheet(sheet.name)
    thin = styles.Side(style="thin")
    for column, title in enumerate(sheet.header, start=1):
        cell = target.cell(row=1, column=column, value=title)
        cell.font = styles.Font(bold=True)
        cell.border = styles.Border(left=thin, right=thin, top=thin, bottom=thin)
        cell.alignment = styles.Alignment(horizontal="center", vertical="top")
    for row_index, row in enumerate(sheet.rows, start=2):
        for column, value in enumerate(row, start=1):
            if value not in (None, ""):
                target.cell(row=row_index, column=column, value=value)
    if sheet.header_styled:
        for cell in target[1]:
            cell.fill = styles.PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
            cell.font = styles.Font(color="FFFFFF", bold=True)
            cell.alignment = styles.Alignment(horizontal="center", vertical="center")
    if sheet.auto_width:
        for cells in target.columns:
            length = max((len(str(c.value)) for c in cells if c.value), default=0)
            target.column_dimensions[cells[0].column_letter].width = min(length + 2, 50)


def write_workbook(sheets: list[Sheet]) -> BytesIO:
    """Schreibt Blätter wie ``pandas.DataFrame.to_excel`` plus Formatierung des Originals."""
    openpyxl = require_module("openpyxl", "excel")
    styles = require_module("openpyxl.styles", "excel")
    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)
    for sheet in sheets:
        _write_sheet(workbook, styles, sheet)
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return output


class BpmnExcelExporter:
    """Excel-Bericht wie im Original (``db_session`` → ``personnel_rate``)."""

    def __init__(
        self, xml_content: str | bytes, diagram_name: str, personnel_rate: PersonnelRateLookup | None = None
    ) -> None:
        self.analyzer = BpmnAnalyzer(xml_content, personnel_rate=personnel_rate)
        self.analysis = self.analyzer.analyze_process(diagram_name)

    def sheets(self) -> list[Sheet]:
        """Die fünf Blätter des Berichts."""
        return analysis_sheets(self.analysis, self.analyzer.extract_esi_requirements())

    def create_excel_report(self) -> BytesIO:
        """Excel-Bericht als ``BytesIO``."""
        return write_workbook(self.sheets())


def export_bpmn_to_excel(
    xml_content: str | bytes, diagram_name: str, personnel_rate: PersonnelRateLookup | None = None
) -> BytesIO:
    """Excel-Bericht (Extra ``excel``)."""
    return BpmnExcelExporter(xml_content, diagram_name, personnel_rate).create_excel_report()


def export_bpmn_to_pdf(
    xml_content: str | bytes, diagram_name: str, personnel_rate: PersonnelRateLookup | None = None
) -> BytesIO:
    """Mehrseitiger PDF-Bericht wie im Original (Extra ``pdf``)."""
    from .pdf import build_pdf

    analysis = BpmnAnalyzer(xml_content, personnel_rate=personnel_rate).analyze_process(diagram_name)
    return build_pdf(analysis, diagram_name)
