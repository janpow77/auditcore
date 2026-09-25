"""PDF-Aufbau des Originalberichts (Extra ``pdf``, reportlab)."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from ..optional import require_module
from .analyzer import ProcessAnalysis


def _table_style(colors: Any, platypus: Any) -> Any:
    return platypus.TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]
    )


class _Builder:
    def __init__(self, analysis: ProcessAnalysis) -> None:
        self.analysis = analysis
        self.colors = require_module("reportlab.lib.colors", "pdf")
        self.platypus = require_module("reportlab.platypus", "pdf")
        self.mm = require_module("reportlab.lib.units", "pdf").mm
        self.styles = require_module("reportlab.lib.styles", "pdf").getSampleStyleSheet()

    def table(self, rows: list[list[Any]], widths: list[float]) -> Any:
        """Tabelle im Stil des Originals."""
        table = self.platypus.Table(rows, colWidths=[w * self.mm for w in widths], repeatRows=1)
        table.setStyle(_table_style(self.colors, self.platypus))
        return table

    def overview(self) -> list[Any]:
        """Kennzahlentabelle."""
        a = self.analysis
        rows = [
            ["Kennzahl", "Wert"],
            ["Anzahl Tasks", str(a.total_tasks)],
            ["Gesamtkosten je Durchlauf", f"{a.total_cost:,.2f} EUR"],
            ["Jährliche Gesamtkosten", f"{a.annual_cost:,.2f} EUR"],
            ["Bearbeitungszeit", f"{a.total_duration_minutes:,.2f} Minuten"],
            ["Gesamtaufwand", f"{a.total_person_days:,.2f} Personentage"],
            ["Jährliche Durchläufe", str(a.annual_frequency)],
        ]
        return [self.table(rows, [90, 80]), self.platypus.Spacer(1, 8 * self.mm)]

    @staticmethod
    def _task_row(task: dict[str, Any]) -> list[str]:
        duration = " ".join(
            value
            for value in (str(task.get("duration_estimated") or ""), str(task.get("duration_unit") or ""))
            if value
        )
        cost = f"{float(task['cost_estimate']):,.2f} EUR" if task.get("cost_estimate") is not None else ""
        return [
            str(task.get("task_name") or task.get("task_id") or ""),
            str(task.get("task_type") or ""),
            str(task.get("process_owner") or ""),
            str(task.get("process_department") or ""),
            duration,
            cost,
        ]

    def tasks(self) -> list[Any]:
        """Aufgabentabelle."""
        rows = [["Task", "Typ", "Verantwortlich", "Abteilung", "Dauer", "Kosten"]]
        rows += [self._task_row(task) for task in self.analysis.tasks]
        return [self.platypus.Paragraph("Tasks", self.styles["Heading2"]), self.table(rows, [62, 30, 45, 42, 34, 34])]

    def legal(self) -> list[Any]:
        """Verzeichnis der Rechtsgrundlagen (entfällt ohne Angaben)."""
        rows = [
            [str(task.get("task_name") or task.get("task_id") or ""), str(basis)]
            for task in self.analysis.tasks
            if (basis := (task.get("legal_basis") or "").strip())
        ]
        if not rows:
            return []
        paragraph, body = self.platypus.Paragraph, self.styles["BodyText"]
        table = self.table(
            [["Aufgabe", "Rechtsgrundlage"]] + [[paragraph(n, body), paragraph(b, body)] for n, b in rows], [80, 167]
        )
        return [self.platypus.Spacer(1, 8 * self.mm), paragraph("Rechtsgrundlagen", self.styles["Heading2"]), table]

    def resources(self) -> list[Any]:
        """Ressourcenübersicht auf neuer Seite (entfällt ohne Angaben)."""
        a = self.analysis
        if not (a.unique_owners or a.unique_departments or a.unique_systems):
            return []
        paragraph, body = self.platypus.Paragraph, self.styles["BodyText"]
        return [
            self.platypus.PageBreak(),
            paragraph("Ressourcenübersicht", self.styles["Heading2"]),
            paragraph("<b>Verantwortliche:</b> " + (", ".join(a.unique_owners) or "–"), body),
            paragraph("<b>Abteilungen:</b> " + (", ".join(a.unique_departments) or "–"), body),
            paragraph("<b>Systeme:</b> " + (", ".join(a.unique_systems) or "–"), body),
        ]


def build_pdf(analysis: ProcessAnalysis, diagram_name: str) -> BytesIO:
    """PDF-Bericht als ``BytesIO`` (Querformat A4)."""
    builder = _Builder(analysis)
    pagesizes = require_module("reportlab.lib.pagesizes", "pdf")
    mm = builder.mm
    output = BytesIO()
    document = builder.platypus.SimpleDocTemplate(
        output,
        pagesize=pagesizes.landscape(pagesizes.A4),
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f"Prozessanalyse – {diagram_name}",
    )
    story: list[Any] = [
        builder.platypus.Paragraph(f"Prozessanalyse: {diagram_name}", builder.styles["Title"]),
        builder.platypus.Spacer(1, 5 * mm),
        *builder.overview(),
        *builder.tasks(),
        *builder.legal(),
        *builder.resources(),
    ]
    document.build(story)
    output.seek(0)
    return output
