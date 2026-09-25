"""Zehn Belegvorlagen (acht fürs Training, zwei nur für den Layout-Holdout).

Die Vorlagen beschreiben nur Geometrie und Reihenfolge; gezeichnet wird über
die Schnittstelle ``Canvas`` (Pillow-Umsetzung in ``render``). Jeder als Feld
gedruckte Wert wird über ``Canvas.field`` erfasst – daraus entsteht das
Ziel-JSON je Seite (nur, was auf der Seite tatsächlich steht). Jede Seite trägt
oben und unten die Kennzeichnung ``SYNTHETISCH`` (Entscheidung E5).
"""

from __future__ import annotations

from auditcore_invoicesynth.enrich import SynthInvoice
from auditcore_invoicesynth.layout_body import COLUMNS as COLUMNS
from auditcore_invoicesynth.layout_body import bank_below, footer, payment, table, totals
from auditcore_invoicesynth.layout_head import (
    ensure_space,
    markers,
    meta,
    page_footer,
    recipient,
    sender,
)
from auditcore_invoicesynth.layout_model import BLACK as BLACK
from auditcore_invoicesynth.layout_model import FOOTER_TOP as FOOTER_TOP
from auditcore_invoicesynth.layout_model import GRAY as GRAY
from auditcore_invoicesynth.layout_model import HOLDOUT_LAYOUTS as HOLDOUT_LAYOUTS
from auditcore_invoicesynth.layout_model import LAYOUTS as LAYOUTS
from auditcore_invoicesynth.layout_model import PAGE_BOTTOM as PAGE_BOTTOM
from auditcore_invoicesynth.layout_model import TRAINING_LAYOUTS as TRAINING_LAYOUTS
from auditcore_invoicesynth.layout_model import Canvas as Canvas
from auditcore_invoicesynth.layout_model import Color as Color
from auditcore_invoicesynth.layout_model import LayoutSpec as LayoutSpec
from auditcore_invoicesynth.layout_model import Variant as Variant
from auditcore_invoicesynth.layout_model import expansion as expansion


def render_layout(canvas: Canvas, inv: SynthInvoice, variant: Variant, name: str) -> None:
    """Beleg vollständig auf die Zeichenfläche bringen (Seitenwechsel inklusive)."""
    spec = LAYOUTS[name]
    markers(canvas)
    if spec.band:
        canvas.rect(0, 9, 210, 40, fill=(222, 229, 238), outline=None)
    sender_x = 190.0 if spec.header == "right" else 20.0
    sender_end = sender(canvas, inv, variant, spec, sender_x, 14)
    recipient_y = max(50.0, sender_end + 4)
    recipient(canvas, inv, variant, 20, recipient_y)
    y = meta(canvas, inv, variant, spec, recipient_y + 2)
    y = table(canvas, inv, variant, spec, max(y, 120))
    y = totals(canvas, inv, variant, spec, y)
    y = ensure_space(canvas, inv, variant, y, 3 * canvas.line_height() + 4)
    y = payment(canvas, inv, variant, spec, y)
    if spec.bank == "below_totals":
        y = ensure_space(canvas, inv, variant, y, 3 * canvas.line_height())
        bank_below(canvas, inv, variant, y)
    footer(canvas, inv, variant, spec)
    page_footer(canvas, variant)
