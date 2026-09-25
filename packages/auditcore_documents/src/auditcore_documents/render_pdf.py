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
from collections.abc import Callable, Mapping
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


def _text(value: object) -> str:
    """Als Text gesetzter, XML-maskierter Wert (``None`` → Gedankenstrich)."""
    if value is None:
        return "—"
    if isinstance(value, (dict, list, tuple)):
        value = json.dumps(value, ensure_ascii=False, default=str)
    return escape(str(value)).replace("\n", "<br/>")


def _label(key: str) -> str:
    return _text(LABELS.get(key, key.replace("_", " ")))


def _register_font(rl: dict[str, Any], font_file: Path | None) -> str:
    """DejaVuSans (als ``EcoResearchSans``), falls vorhanden, sonst Helvetica."""
    if font_file is None or not font_file.is_file():
        return "Helvetica"
    font = "EcoResearchSans"
    pdfmetrics = rl["pdfmetrics"]
    if font not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(rl["TTFont"](font, str(font_file)))
    return font


def _styles(rl: dict[str, Any], font: str) -> dict[str, Any]:
    colors, paragraph_style = rl["colors"], rl["ParagraphStyle"]
    body = paragraph_style(
        "body",
        fontName=font,
        fontSize=9,
        leading=14,
        textColor=colors.HexColor("#172e35"),
        spaceAfter=5,
        alignment=rl["TA_LEFT"],
        splitLongWords=True,
    )
    return {
        "body": body,
        "heading": paragraph_style(
            "heading",
            parent=body,
            fontSize=12,
            leading=17,
            spaceBefore=15,
            spaceAfter=8,
            keepWithNext=True,
        ),
        "title": paragraph_style("title", parent=body, fontSize=22, leading=29, spaceAfter=16),
        "muted": paragraph_style("muted", parent=body, textColor=colors.HexColor("#526776")),
    }


def _is_register_column(report: SynopsisReport, column: str) -> bool:
    direct = (
        report.tool == "double-funding-crosscheck"
        or report.extra.get("matching_mode") == "direct_registers"
    )
    return direct and column in {"beneficiary_records", "state_aid_records"}


class _Story:
    """Baut die Absatzfolge des Berichts in der Reihenfolge des Originals."""

    def __init__(self, rl: dict[str, Any], styles: dict[str, Any]) -> None:
        self.rl = rl
        self.styles = styles
        self.items: list[Any] = []

    def add(self, markup: str, style: str = "body") -> None:
        self.items.append(self.rl["Paragraph"](markup, self.styles[style]))

    def intro(self, title: str, report: SynopsisReport) -> None:
        self.add(_text(title), "title")
        generated = report.generated_at
        if generated.tzinfo is None:
            generated = generated.replace(tzinfo=UTC)
        stamp = generated.astimezone(ZoneInfo("Europe/Berlin"))
        self.add(f"Recherche vom {stamp:%d.%m.%Y, %H:%M} (Europe/Berlin)", "muted")
        self.add(f"{len(report.rows)} Datensätze im PDF · {report.total} Treffer insgesamt")
        if report.truncated or report.total > len(report.rows):
            self.add("Dieser Export enthält einen begrenzten Ausschnitt der Treffer.")

    def criteria(self, params: Mapping[str, str]) -> None:
        if not params:
            return
        self.add("Suchkriterien", "heading")
        for key, value in params.items():
            display = PARAM_DISPLAY.get(key, {}).get(str(value), value)
            self.add(f"{_label(key)}: {_text(display)}")

    def results(self, report: SynopsisReport) -> None:
        for note in report.notes:
            self.add(_text(note))
        self.add("Ergebnisse", "heading")
        if not report.rows:
            self.add("Keine Datensätze für diese Suchkriterien gefunden.")
        columns = report.columns or (list(report.rows[0]) if report.rows else [])
        for index, row in enumerate(report.rows, 1):
            self.add(f"Treffer {index}", "heading")
            for column in columns:
                if _is_register_column(report, column):
                    self.register_records(column, row.get(column, []))
                else:
                    self.add(f"{_label(column)}: {_text(row.get(column))}")

    def register_records(self, column: str, records: list[dict[str, Any]]) -> None:
        for record_index, record in enumerate(records, 1):
            self.add(f"{_label(column)} · {record_index}", "heading")
            self.filled_fields(record, "body")

    def filled_fields(self, record: Mapping[str, object], style: str) -> None:
        for key, value in record.items():
            if value is not None and value != "":
                self.add(f"{_label(key)}: {_text(value)}", style)

    def detail(self, key: str, value: object) -> None:
        if isinstance(value, dict):
            self.add(_label(key), "heading")
            for child_key, child_value in value.items():
                self.detail(child_key, child_value)
        elif isinstance(value, (list, tuple)) and any(isinstance(i, dict) for i in value):
            for item_index, item in enumerate(value, 1):
                self.detail(f"{key} · {item_index}", item)
        else:
            self.add(f"{_label(key)}: {_text(value)}")

    def appendix(self, report: SynopsisReport) -> None:
        if report.extra:
            self.add("Zusammenfassung und ergänzende Angaben", "heading")
            for key, value in report.extra.items():
                self.detail(key, value)
        for section_title, section_text in (
            ("Methodik", report.methodology),
            ("Fachliche Grenzen", report.limitations),
        ):
            if section_text:
                self.add(section_title, "heading")
                self.add(_text(section_text))
        if report.data_sources or report.source_findings:
            self.add("Datenquellen und Quellenbefunde", "heading")
            for source in [*report.data_sources, *report.source_findings]:
                self.filled_fields(source, "muted")
                self.items.append(self.rl["Spacer"](1, 6))


def _page_frame(
    rl: dict[str, Any], font: str, header_text: str, footer_text: str
) -> Callable[[Any, Any], None]:
    colors, page_size = rl["colors"], rl["A4"]

    def draw(canvas: Any, doc: Any) -> None:
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#9bbb79"))
        canvas.line(42, page_size[1] - 43, page_size[0] - 42, page_size[1] - 43)
        canvas.setFont(font, 8)
        canvas.setFillColor(colors.HexColor("#172e35"))
        canvas.drawString(42, page_size[1] - 33, header_text)
        canvas.drawString(42, 27, footer_text)
        canvas.drawRightString(page_size[0] - 42, 27, f"Seite {doc.page}")
        canvas.restoreState()

    return draw


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
    font = _register_font(rl, font_file)
    story = _Story(rl, _styles(rl, font))
    story.intro(title, report)
    story.criteria(dict(params or {}))
    story.results(report)
    story.appendix(report)
    frame = _page_frame(rl, font, header_text, footer_text)
    output = io.BytesIO()
    rl["SimpleDocTemplate"](
        output,
        pagesize=rl["A4"],
        leftMargin=42,
        rightMargin=42,
        topMargin=62,
        bottomMargin=45,
        title=title,
        author=author,
    ).build(story.items, onFirstPage=frame, onLaterPages=frame)
    return output.getvalue()
