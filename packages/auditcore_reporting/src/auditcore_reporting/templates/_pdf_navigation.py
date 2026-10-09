"""PDF build for documents with jump targets: links, table of contents, outline.

The plain build defers every page to number them "Seite X von Y"; reportlab
binds link targets to the page that is current when they are created, which
a deferred page is not yet. Documents with anchors are therefore built with
``multiBuild`` (needed anyway for the page numbers of the table of contents)
and a canvas that decorates each page immediately; the total page count
comes from the previous pass, and the build repeats until it is stable.
Documents without anchors keep the plain build and its bytes.
"""

from __future__ import annotations

import io
from collections.abc import Callable
from typing import Protocol

from auditcore_common.optional import require_module

from ._pdf_fonts import MESSAGE
from .errors import RenderDependencyError, RenderLimitError

#: Rebuilds until the total page count used for "Seite X von Y" is stable.
MAX_PASSES = 4


class PdfCanvas(Protocol):
    """The part of reportlab's canvas used for page decoration."""

    _pagesize: tuple[float, float]

    def setFont(self, name: str, size: float) -> None: ...  # noqa: N802 - reportlab API

    def drawString(self, x: float, y: float, text: str) -> None: ...  # noqa: N802

    def drawRightString(self, x: float, y: float, text: str) -> None: ...  # noqa: N802

    def setDateFormatter(self, formatter: Callable[..., str]) -> None: ...  # noqa: N802


class DocTemplate(Protocol):
    """The part of reportlab's doc templates used here."""

    width: float

    def build(self, story: list[object], canvasmaker: object) -> None: ...

    def multiBuild(self, story: list[object], canvasmaker: object) -> None: ...  # noqa: N802


#: Header, footer and page number of one page: ``decorate(canvas, page, total)``.
Decorate = Callable[[PdfCanvas, int, int], None]


def heading_flowable(flowable: object, anchor: str, level: int) -> object:
    """Mark a heading paragraph as target for the table of contents and the outline."""
    flowable._ac_anchor = anchor  # type: ignore[attr-defined]
    flowable._ac_level = level  # type: ignore[attr-defined]
    return flowable


def contents_flowable(levels: int, styles: list[object]) -> object:
    """reportlab table of contents limited to ``levels`` (1–3), entries are links."""
    module = require_module("reportlab.platypus.tableofcontents", RenderDependencyError, MESSAGE)

    class Contents(module.TableOfContents):  # type: ignore[misc,name-defined]
        def notify(self, kind: str, stuff: tuple[object, ...]) -> None:
            level = stuff[0]
            if kind == "TOCEntry" and isinstance(level, int) and level < levels:
                super().notify(kind, stuff)

    contents = Contents(dotsMinLevel=0)
    contents.levelStyles = styles[:levels]
    return contents


def _template_class(outline: bool) -> type:
    platypus = require_module("reportlab.platypus", RenderDependencyError, MESSAGE)

    class NavigatedTemplate(platypus.SimpleDocTemplate):  # type: ignore[misc,name-defined]
        def beforeDocument(self) -> None:  # noqa: N802 - reportlab API
            self._ac_last = -1

        def afterFlowable(self, flowable: object) -> None:  # noqa: N802 - reportlab API
            anchor = getattr(flowable, "_ac_anchor", "")
            if not anchor:
                return
            level = min(getattr(flowable, "_ac_level", 1) - 1, self._ac_last + 1)
            text = flowable.getPlainText()  # type: ignore[attr-defined]
            self.notify("TOCEntry", (level, text, self.page, anchor))
            if outline:
                self.canv.addOutlineEntry(text, anchor, level)
                self._ac_last = level

    return NavigatedTemplate


def _canvas_class(decorate: Decorate, counts: dict[str, int]) -> type:
    canvas_module = require_module("reportlab.pdfgen.canvas", RenderDependencyError, MESSAGE)

    class PagedCanvas(canvas_module.Canvas):  # type: ignore[misc,name-defined]
        def __init__(self, *args: object, **kwargs: object) -> None:
            super().__init__(*args, **kwargs)
            self._ac_total = counts["total"]

        def showPage(self) -> None:  # noqa: N802 - reportlab API
            decorate(self, self._pageNumber, self._ac_total)
            super().showPage()

        def save(self) -> None:
            counts["used"], counts["total"] = self._ac_total, self._pageNumber - 1
            super().save()

    return PagedCanvas


def build_navigated(
    make: Callable[[type, io.BytesIO], DocTemplate],
    story: list[object],
    decorate: Decorate,
    prepare: Callable[[PdfCanvas], None],
    outline: bool,
) -> bytes:
    """PDF bytes of ``story`` built with ``multiBuild`` until the page count is stable.

    ``make(template_class, buffer)`` creates the doc template, ``prepare`` sets
    the date formatter (or similar) on each new canvas.
    """
    counts = {"total": 0, "used": -1}
    canvas_class = _canvas_class(decorate, counts)

    def canvasmaker(*args: object, **kwargs: object) -> PdfCanvas:
        canvas: PdfCanvas = canvas_class(*args, **kwargs)
        prepare(canvas)
        return canvas

    template_class = _template_class(outline)
    for _ in range(MAX_PASSES):
        buffer = io.BytesIO()
        template = make(template_class, buffer)
        template.multiBuild(list(story), canvasmaker=canvasmaker)
        if counts["used"] == counts["total"]:
            return buffer.getvalue()
    raise RenderLimitError("PDF: Seitenzahl wird nach mehreren Durchläufen nicht stabil.")
