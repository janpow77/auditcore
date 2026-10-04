"""PDF rendering of a resolved document (extra ``pdf``: reportlab, BSD licence).

reportlab runs in invariant mode (fixed creation date and document id), so
identical input gives identical bytes for a given reportlab version. The
base-14 fonts cover German umlauts, ß, € and typographic quotes (WinAnsi);
texts are escaped before they reach reportlab's paragraph markup.
"""

from __future__ import annotations

import io
from xml.sax.saxutils import escape

from auditcore_common.optional import require_module

from .design import NEUTRAL_DESIGN, DesignProfile
from .errors import RenderDependencyError
from .options import DEFAULT_OPTIONS, RenderOptions
from .render_docx import provenance
from .resolve import (
    Node,
    ResolvedDocument,
    RFields,
    RHeading,
    RList,
    RPageBreak,
    RParagraph,
    RTable,
)

_MESSAGE = "PDF-Ausgabe nicht verfügbar: Extra auditcore_reporting[pdf] (reportlab) fehlt."
_BOLD = {"Helvetica": "Helvetica-Bold", "Times-Roman": "Times-Bold", "Courier": "Courier-Bold"}
_ALIGN = {"left": "LEFT", "right": "RIGHT", "center": "CENTER"}


def _markup(text: str) -> str:
    return escape(text).replace("\n", "<br/>")


def _color(value: str) -> object:
    colors = require_module("reportlab.lib.colors", RenderDependencyError, _MESSAGE)
    return colors.HexColor(f"#{value}")


class _Styles:
    def __init__(self, design: DesignProfile) -> None:
        styles = require_module("reportlab.lib.styles", RenderDependencyError, _MESSAGE)
        size, font = design.font_size_pt, design.pdf_font
        self.body = styles.ParagraphStyle(
            "body", fontName=font, fontSize=size, leading=size * 1.35, spaceAfter=size * 0.55
        )
        self.cell = styles.ParagraphStyle("cell", parent=self.body, spaceAfter=0)
        self.bold = styles.ParagraphStyle("bold", parent=self.cell, fontName=_BOLD[font])
        self.headings = [
            styles.ParagraphStyle(
                f"h{level}", parent=self.body, fontName=_BOLD[font], fontSize=h, leading=h * 1.25,
                spaceBefore=h * 0.9, spaceAfter=h * 0.4, textColor=_color(design.accent_color),
            )
            for level, h in enumerate(design.heading_sizes_pt, start=1)
        ]  # fmt: skip

    def aligned(self, align: str, bold: bool = False) -> object:
        enums = require_module("reportlab.lib.enums", RenderDependencyError, _MESSAGE)
        alignment = {"left": enums.TA_LEFT, "right": enums.TA_RIGHT, "center": enums.TA_CENTER}
        styles = require_module("reportlab.lib.styles", RenderDependencyError, _MESSAGE)
        parent = self.bold if bold else self.cell
        return styles.ParagraphStyle(
            f"{parent.name}-{align}", parent=parent, alignment=alignment[align]
        )


def _table(node: RTable, styles: _Styles, width: float, design: DesignProfile) -> object:
    platypus = require_module("reportlab.platypus", RenderDependencyError, _MESSAGE)
    head = [
        platypus.Paragraph(_markup(h), styles.aligned(a, True))
        for h, a in zip(node.headers, node.aligns, strict=True)
    ]
    body = [
        [
            platypus.Paragraph(_markup(c), styles.aligned(a))
            for c, a in zip(row, node.aligns, strict=True)
        ]
        for row in node.rows
    ]
    table = platypus.Table(
        [head, *body], colWidths=[width / len(node.headers)] * len(node.headers), repeatRows=1
    )
    grey = _color("808080")
    table.setStyle(
        [
            ("GRID", (0, 0), (-1, -1), 0.5, grey),
            ("BACKGROUND", (0, 0), (-1, 0), _color(design.table_header_fill)),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]
    )
    return table


def _flowables(node: Node, styles: _Styles, width: float, design: DesignProfile) -> list[object]:
    platypus = require_module("reportlab.platypus", RenderDependencyError, _MESSAGE)
    if isinstance(node, RHeading):
        return [platypus.Paragraph(_markup(node.text), styles.headings[node.level - 1])]
    if isinstance(node, RParagraph):
        return [platypus.Paragraph(_markup(node.text), styles.body)]
    if isinstance(node, RList):
        items = [platypus.ListItem(platypus.Paragraph(_markup(i), styles.body)) for i in node.items]
        return [platypus.ListFlowable(items, bulletType="bullet", start="•", leftIndent=14)]
    if isinstance(node, RTable):
        return [_table(node, styles, width, design), platypus.Spacer(1, 6)]
    if isinstance(node, RFields):
        rows = [
            [
                platypus.Paragraph(_markup(k), styles.bold),
                platypus.Paragraph(_markup(v), styles.cell),
            ]
            for k, v in node.rows
        ]
        return [
            platypus.Table(rows, colWidths=[width * 0.3, width * 0.7], hAlign="LEFT"),
            platypus.Spacer(1, 6),
        ]
    assert isinstance(node, RPageBreak)
    return [platypus.PageBreak()]


def _canvas_class(design: DesignProfile, options: RenderOptions) -> type:
    """Canvas that writes header, footer and "Seite X von Y" after the last page."""
    canvas_module = require_module("reportlab.pdfgen.canvas", RenderDependencyError, _MESSAGE)
    created = options.created_utc
    stamp = created.strftime("D:%Y%m%d%H%M%S+00'00'") if created is not None else ""

    class NumberedCanvas(canvas_module.Canvas):  # type: ignore[misc,name-defined]
        def __init__(self, *args: object, **kwargs: object) -> None:
            super().__init__(*args, **kwargs)
            self._pages: list[dict[str, object]] = []
            if stamp:
                self.setDateFormatter(lambda *_parts: stamp)

        def showPage(self) -> None:  # noqa: N802 - reportlab API
            self._pages.append(dict(self.__dict__))
            self._startPage()

        def save(self) -> None:
            total = len(self._pages)
            for state in self._pages:
                self.__dict__.update(state)
                self._decorate(total)
                super().showPage()
            super().save()

        def _decorate(self, total: int) -> None:
            width, height = self._pagesize
            margin = design.margin_cm * 28.3465
            self.setFont(design.pdf_font, 8)
            if design.header_text:
                self.drawString(
                    margin, height - margin * 0.6, design.header_text.replace("\n", " ")
                )
            if design.footer_text:
                self.drawString(margin, margin * 0.5, design.footer_text.replace("\n", " "))
            if design.page_numbers:
                self.drawRightString(
                    width - margin, margin * 0.5, f"Seite {self._pageNumber} von {total}"
                )

    return NumberedCanvas


def render_pdf(
    document: ResolvedDocument,
    design: DesignProfile = NEUTRAL_DESIGN,
    options: RenderOptions = DEFAULT_OPTIONS,
) -> bytes:
    """PDF bytes (A4); raises :class:`RenderDependencyError` without the ``pdf`` extra."""
    platypus = require_module("reportlab.platypus", RenderDependencyError, _MESSAGE)
    pagesizes = require_module("reportlab.lib.pagesizes", RenderDependencyError, _MESSAGE)
    margin = design.margin_cm * 28.3465
    buffer = io.BytesIO()
    template = platypus.SimpleDocTemplate(
        buffer, pagesize=pagesizes.A4, leftMargin=margin, rightMargin=margin, topMargin=margin,
        bottomMargin=margin, title=options.document_title(document.title),
        subject=provenance(document), creator="auditcore_reporting", author=options.author,
        invariant=1,
    )  # fmt: skip
    styles = _Styles(design)
    story: list[object] = []
    for node in document.nodes:
        story.extend(_flowables(node, styles, template.width, design))
    template.build(story, canvasmaker=_canvas_class(design, options))
    return buffer.getvalue()
