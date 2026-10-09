"""Font selection for the PDF output: base-14 fonts or registered TrueType files.

TrueType fonts come as bytes from the design profile (:class:`PdfFont`); they
are registered with reportlab under a name derived from their digest, so the
same file is registered once per process and two profiles cannot overwrite
each other's fonts. Without a TrueType font the base-14 fonts are used.
"""

from __future__ import annotations

import io
import threading

from auditcore_common.optional import require_module

from .design import DesignProfile, PdfFont
from .errors import RenderDependencyError, TemplateError

MESSAGE = "PDF-Ausgabe nicht verfügbar: Extra auditcore_reporting[pdf] (reportlab) fehlt."
_BOLD = {"Helvetica": "Helvetica-Bold", "Times-Roman": "Times-Bold", "Courier": "Courier-Bold"}
_LOCK = threading.Lock()


def _register(name: str, data: bytes, label: str) -> str:
    pdfmetrics = require_module("reportlab.pdfbase.pdfmetrics", RenderDependencyError, MESSAGE)
    ttfonts = require_module("reportlab.pdfbase.ttfonts", RenderDependencyError, MESSAGE)
    with _LOCK:
        if name not in pdfmetrics.getRegisteredFontNames():
            try:
                font = ttfonts.TTFont(name, io.BytesIO(data))
            except Exception as exc:  # reportlab raises TTFError, struct.error, …
                raise TemplateError(f"Schrift {label}: Datei nicht lesbar ({exc}).") from exc
            pdfmetrics.registerFont(font)
    return name


def _true_type(font: PdfFont) -> tuple[str, str]:
    key = font.sha256[:16]
    regular = _register(f"ac-{font.name}-{key}", font.regular, font.name)
    if font.bold is None:
        return regular, regular
    return regular, _register(f"ac-{font.name}-{key}-bold", font.bold, f"{font.name} (fett)")


def pdf_fonts(design: DesignProfile) -> tuple[str, str]:
    """reportlab names of the regular and bold font of ``design``."""
    font = design.pdf_font_file()
    if font is None:
        return design.pdf_font, _BOLD[design.pdf_font]
    return _true_type(font)
