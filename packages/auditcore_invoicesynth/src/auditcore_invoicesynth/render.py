"""Pillow-Zeichenfläche für die Vorlagen (Extra ``render``).

Rendert direkt in ein Seitenbild der gewünschten Auflösung (kein PDF-Umweg,
keine Rasterungsbibliothek nötig). Schriften kommen aus ``FontSet``; es wird
nichts eingebettet oder mitverteilt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any

from auditcore_invoicesynth.enrich import SynthInvoice
from auditcore_invoicesynth.fonts import FontSet
from auditcore_invoicesynth.layouts import BLACK, LAYOUTS, Color, Variant

if TYPE_CHECKING:  # pragma: no cover
    from PIL.Image import Image

A4_MM = (210.0, 297.0)


class RenderDependencyError(ImportError):
    """Das Extra ``render`` (Pillow) ist nicht installiert."""


def _pil() -> tuple[ModuleType, ModuleType, ModuleType]:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:  # pragma: no cover - abhängig von der Installation
        raise RenderDependencyError(
            "Bitte auditcore_invoicesynth[render] installieren (Pillow)"
        ) from exc
    return Image, ImageDraw, ImageFont


@dataclass
class PageRecord:
    image: Image
    fields: dict[str, str] = field(default_factory=dict)
    texts: list[str] = field(default_factory=list)


class PillowCanvas:
    """``layouts.Canvas`` auf Pillow-Bildern in Millimeter-Koordinaten."""

    def __init__(self, fonts: FontSet, family: str, *, dpi: int, base_size_pt: float) -> None:
        self._image_mod, self._draw_mod, self._font_mod = _pil()
        self.fonts = fonts
        self.family = family
        self.dpi = dpi
        self.base_size_pt = base_size_pt
        self.pages: list[PageRecord] = []
        self._font_cache: dict[tuple[str, int], Any] = {}
        self.page_number = 0
        self.new_page()

    # Geometrie -------------------------------------------------------------
    def px(self, mm: float) -> int:
        return round(mm / 25.4 * self.dpi)

    def _font(self, size: float, bold: bool) -> Any:
        pixels = max(4, round(self.base_size_pt * size / 72 * self.dpi))
        path = self.fonts.path(self.family, "bold" if bold else "regular")
        key = (str(path), pixels)
        if key not in self._font_cache:
            self._font_cache[key] = self._font_mod.truetype(str(Path(path)), pixels)
        return self._font_cache[key]

    # Canvas-Vertrag --------------------------------------------------------
    def new_page(self) -> None:
        width, height = (self.px(v) for v in A4_MM)
        image = self._image_mod.new("RGB", (width, height), (255, 255, 255))
        self.pages.append(PageRecord(image))
        self._draw = self._draw_mod.Draw(image)
        self.page_number = len(self.pages)

    def text_width(self, value: str, *, size: float = 1.0, bold: bool = False) -> float:
        return float(self._draw.textlength(value, font=self._font(size, bold))) / self.dpi * 25.4

    def line_height(self, size: float = 1.0) -> float:
        return self.base_size_pt * size * 1.35 / 72 * 25.4

    def text(
        self,
        x: float,
        y: float,
        value: str,
        *,
        size: float = 1.0,
        bold: bool = False,
        align: str = "left",
        color: Color = BLACK,
    ) -> None:
        if not value:
            return
        anchor = {"left": "la", "right": "ra", "center": "ma"}[align]
        self._draw.text(
            (self.px(x), self.px(y)), value, font=self._font(size, bold), fill=color, anchor=anchor
        )
        self.pages[-1].texts.append(value)

    def line(self, x1: float, y1: float, x2: float, y2: float, *, width: float = 0.25) -> None:
        self._draw.line(
            [(self.px(x1), self.px(y1)), (self.px(x2), self.px(y2))],
            fill=BLACK,
            width=max(1, self.px(width)),
        )

    def rect(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        *,
        fill: Color | None = None,
        outline: Color | None = BLACK,
    ) -> None:
        self._draw.rectangle(
            [self.px(x1), self.px(y1), self.px(x2), self.px(y2)],
            fill=fill,
            outline=outline,
            width=max(1, self.px(0.25)),
        )

    def field(self, key: str, value: str) -> str:
        """Gedruckten Feldwert der aktuellen Seite erfassen (erste Fundstelle zählt)."""
        self.pages[-1].fields.setdefault(key, value)
        return value


def render_pages(
    invoice: SynthInvoice,
    variant: Variant,
    layout: str,
    fonts: FontSet,
    *,
    family: str,
    dpi: int,
    base_size_pt: float,
) -> list[PageRecord]:
    """Beleg mit Vorlage ``layout`` rendern; eine ``PageRecord`` je Seite."""
    from auditcore_invoicesynth.layouts import render_layout

    canvas = PillowCanvas(fonts, family, dpi=dpi, base_size_pt=base_size_pt * LAYOUTS[layout].scale)
    render_layout(canvas, invoice, variant, layout)
    return canvas.pages
