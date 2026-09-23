"""PDF-Ausgabe der Synopse (Extra ``pdf-render``: reportlab).

Übernommen aus audit_designer ``app/modules/ecohesion/services/research_pdf.py``
(``render_pdf``), mit dem der ECOHESION-Vergleich ``comparison.pdf`` erzeugt.
Aufbau, Beschriftungen, Zeitstempel (Europe/Berlin), Seitenrahmen und
Schriftwahl (DejaVuSans, sonst Helvetica) wie im Original. Kopf- und Fußzeile
sind Parameter; die Vorgaben sind die charakterisierten ECOHESION-Texte.
Statt ``ResearchResult`` dient ``SynopsisReport`` als Datenvertrag;
``synopsis_report`` baut ihn aus einem Vergleichsergebnis wie der Worker.
"""

from __future__ import annotations

import io
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

from auditcore_documents.errors import DependencyError
from auditcore_documents.model import ComparisonResult
from auditcore_documents.synopsis import synopsis_extra, synopsis_records

DEFAULT_FONT_FILE = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
DEFAULT_HEADER = "ECOHESION · Recherche & Auswertung"
DEFAULT_FOOTER = "ecohesion.flowaudit.de"

LABELS = {
    "q": "Suchbegriff",
    "country": "Land",
    "country_code": "Land",
    "country_name": "Land",
    "level": "Regionale Ebene",
    "metric": "Kennzahl",
    "nuts_code": "Regionskennung",
    "name": "Name",
    "value": "Wert",
    "value_label": "Ergebnis",
    "project_count": "Anzahl der Vorhaben",
    "total_volume": "Gesamtvolumen",
    "bundesland": "Bundesland",
    "beneficiary_name": "Empfänger",
    "project_name": "Vorhaben",
    "cost_total": "Gesamtkosten",
    "fonds": "Fonds",
    "location": "Ort",
    "source_key": "Quellenkennung",
    "summary": "Zusammenfassung",
    "total": "Gesamt",
    "total_label": "Gesamtergebnis",
    "normalised_name": "Normalisierter Name",
    "name_similarity": "Namensähnlichkeit (0–100)",
    "beneficiary_matches": "Treffer in Begünstigtenverzeichnissen",
    "state_aid_matches": "Treffer im Beihilferegister",
    "beneficiary_names": "Namen in Begünstigtenverzeichnissen",
    "state_aid_names": "Namen im Beihilferegister",
    "beneficiary_records": "Begünstigtenverzeichnis",
    "state_aid_records": "Beihilferegister",
    "company_name": "Empfänger",
    "kosten": "Gesamtkosten des Vorhabens (EUR)",
    "aid_amount_eur": "Beihilfebetrag (EUR)",
    "aid_measure_title": "Maßnahme",
    "granting_date": "Gewährungsdatum",
    "source_url": "Originalquelle",
    "source_filename": "Quelldatei",
    "source_sheet": "Tabellenblatt",
    "source_row_number": "Zeile",
}
PARAM_DISPLAY = {
    "country": {"DE": "Deutschland", "AT": "Österreich"},
    "level": {"1": "Bundesländer", "3": "Kreise und vergleichbare Regionen"},
    "metric": {"count": "Anzahl der Vorhaben", "value": "Gesamtkosten der Vorhaben"},
}


@dataclass
class SynopsisReport:
    """Flacher Berichtsinhalt (entspricht dem genutzten Teil von ``ResearchResult``)."""

    tool: str
    rows: list[dict[str, Any]] = field(default_factory=list)
    total: int = 0
    columns: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    truncated: bool = False
    notes: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)
    methodology: str | None = None
    limitations: str | None = None
    data_sources: list[dict[str, Any]] = field(default_factory=list)
    source_findings: list[dict[str, Any]] = field(default_factory=list)


def synopsis_report(
    result: ComparisonResult, *, generated_at: datetime | None = None
) -> SynopsisReport:
    """Berichtsinhalt wie im ECOHESION-Worker (``tool="document-comparison"``)."""
    columns, rows = synopsis_records(result)
    extra = synopsis_extra(result)
    return SynopsisReport(
        tool="document-comparison",
        rows=list(rows),
        columns=columns,
        total=len(rows),
        notes=extra["notes"],
        extra=extra["extra"],
        generated_at=generated_at or datetime.now(UTC),
    )


def _reportlab() -> dict[str, Any]:
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except ImportError as exc:
        raise DependencyError(
            "Die PDF-Ausgabe benötigt das Extra 'pdf-render' (reportlab)."
        ) from exc
    return {
        "colors": colors,
        "TA_LEFT": TA_LEFT,
        "A4": A4,
        "ParagraphStyle": ParagraphStyle,
        "pdfmetrics": pdfmetrics,
        "TTFont": TTFont,
        "Paragraph": Paragraph,
        "SimpleDocTemplate": SimpleDocTemplate,
        "Spacer": Spacer,
    }


def render_synopsis_pdf(
    title: str,
    report: SynopsisReport,
    params: Mapping[str, str] | None = None,
    *,
    header_text: str = DEFAULT_HEADER,
    footer_text: str = DEFAULT_FOOTER,
    font_file: Path | None = DEFAULT_FONT_FILE,
    author: str = "ECOHESION",
) -> bytes:
    """PDF-Bytes; keine Datenzugriffe, Text wird stets als Text gesetzt."""
    rl = _reportlab()
    colors, pdfmetrics = rl["colors"], rl["pdfmetrics"]
    Paragraph, Spacer, ParagraphStyle = rl["Paragraph"], rl["Spacer"], rl["ParagraphStyle"]
    A4 = rl["A4"]
    params = dict(params or {})
    font = "Helvetica"
    if font_file is not None and font_file.is_file():
        font = "EcoResearchSans"
        if font not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(rl["TTFont"](font, str(font_file)))
    ink = colors.HexColor("#172e35")
    body = ParagraphStyle(
        "body",
        fontName=font,
        fontSize=9,
        leading=14,
        textColor=ink,
        spaceAfter=5,
        alignment=rl["TA_LEFT"],
        splitLongWords=True,
    )
    heading = ParagraphStyle(
        "heading",
        parent=body,
        fontSize=12,
        leading=17,
        spaceBefore=15,
        spaceAfter=8,
        keepWithNext=True,
    )
    title_style = ParagraphStyle("title", parent=body, fontSize=22, leading=29, spaceAfter=16)
    muted = ParagraphStyle("muted", parent=body, textColor=colors.HexColor("#526776"))

    def text(value: Any) -> str:
        if value is None:
            return "—"
        if isinstance(value, (dict, list, tuple)):
            value = json.dumps(value, ensure_ascii=False, default=str)
        return escape(str(value)).replace("\n", "<br/>")

    def label(key: str) -> str:
        return text(LABELS.get(key, key.replace("_", " ")))

    story: list[Any] = [Paragraph(text(title), title_style)]
    generated = report.generated_at
    if generated.tzinfo is None:
        generated = generated.replace(tzinfo=UTC)
    stamp = generated.astimezone(ZoneInfo("Europe/Berlin"))
    story.append(Paragraph(f"Recherche vom {stamp:%d.%m.%Y, %H:%M} (Europe/Berlin)", muted))
    story.append(
        Paragraph(f"{len(report.rows)} Datensätze im PDF · {report.total} Treffer insgesamt", body)
    )
    if report.truncated or report.total > len(report.rows):
        story.append(
            Paragraph("Dieser Export enthält einen begrenzten Ausschnitt der Treffer.", body)
        )
    if params:
        story.append(Paragraph("Suchkriterien", heading))
        for key, value in params.items():
            display = PARAM_DISPLAY.get(key, {}).get(str(value), value)
            story.append(Paragraph(f"{label(key)}: {text(display)}", body))
    for note in report.notes:
        story.append(Paragraph(text(note), body))
    story.append(Paragraph("Ergebnisse", heading))
    if not report.rows:
        story.append(Paragraph("Keine Datensätze für diese Suchkriterien gefunden.", body))
    columns = report.columns or (list(report.rows[0]) if report.rows else [])
    for index, row in enumerate(report.rows, 1):
        story.append(Paragraph(f"Treffer {index}", heading))
        for column in columns:
            if (
                report.tool == "double-funding-crosscheck"
                or report.extra.get("matching_mode") == "direct_registers"
            ) and column in {"beneficiary_records", "state_aid_records"}:
                for record_index, record in enumerate(row.get(column, []), 1):
                    story.append(Paragraph(f"{label(column)} · {record_index}", heading))
                    for key, value in record.items():
                        if value is not None and value != "":
                            story.append(Paragraph(f"{label(key)}: {text(value)}", body))
                continue
            story.append(Paragraph(f"{label(column)}: {text(row.get(column))}", body))
    if report.extra:
        story.append(Paragraph("Zusammenfassung und ergänzende Angaben", heading))

        def append_detail(key: str, value: Any) -> None:
            if isinstance(value, dict):
                story.append(Paragraph(label(key), heading))
                for child_key, child_value in value.items():
                    append_detail(child_key, child_value)
            elif isinstance(value, (list, tuple)) and any(isinstance(i, dict) for i in value):
                for item_index, item in enumerate(value, 1):
                    append_detail(f"{key} · {item_index}", item)
            else:
                story.append(Paragraph(f"{label(key)}: {text(value)}", body))

        for key, value in report.extra.items():
            append_detail(key, value)
    for section_title, value in (
        ("Methodik", report.methodology),
        ("Fachliche Grenzen", report.limitations),
    ):
        if value:
            story.append(Paragraph(section_title, heading))
            story.append(Paragraph(text(value), body))
    if report.data_sources or report.source_findings:
        story.append(Paragraph("Datenquellen und Quellenbefunde", heading))
        for source in [*report.data_sources, *report.source_findings]:
            for key, value in source.items():
                if value is not None and value != "":
                    story.append(Paragraph(f"{label(key)}: {text(value)}", muted))
            story.append(Spacer(1, 6))

    def page_frame(canvas: Any, doc: Any) -> None:
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#9bbb79"))
        canvas.line(42, A4[1] - 43, A4[0] - 42, A4[1] - 43)
        canvas.setFont(font, 8)
        canvas.setFillColor(ink)
        canvas.drawString(42, A4[1] - 33, header_text)
        canvas.drawString(42, 27, footer_text)
        canvas.drawRightString(A4[0] - 42, 27, f"Seite {doc.page}")
        canvas.restoreState()

    output = io.BytesIO()
    rl["SimpleDocTemplate"](
        output,
        pagesize=A4,
        leftMargin=42,
        rightMargin=42,
        topMargin=62,
        bottomMargin=45,
        title=title,
        author=author,
    ).build(story, onFirstPage=page_frame, onLaterPages=page_frame)
    return output.getvalue()
