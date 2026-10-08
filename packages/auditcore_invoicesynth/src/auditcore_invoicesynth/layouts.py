"""Sechzehn Belegvorlagen (dreizehn fürs Training, zwei für den Layout-Holdout T2,
eine nur für den Diagnosesatz T2b).

Die Vorlagen ``kopf_zeile`` und ``kopf_kasten`` nutzen erst die Generatorvarianten
``v2``/``v3``; ``v3`` legt zusätzlich je Beleg Summenort und waagerechte Kopfdaten
über jede Trainingsvorlage (:func:`effective_spec`).

Die Vorlagen beschreiben nur Geometrie und Reihenfolge; gezeichnet wird über
die Schnittstelle ``Canvas`` (Pillow-Umsetzung in ``render``). Jeder als Feld
gedruckte Wert wird über ``Canvas.field`` erfasst – daraus entsteht das
Ziel-JSON je Seite (nur, was auf der Seite tatsächlich steht). Jede Seite trägt
oben und unten die Kennzeichnung ``SYNTHETISCH`` (Entscheidung E5).
"""

from __future__ import annotations

from dataclasses import replace

from auditcore_invoicesynth.enrich import SynthInvoice
from auditcore_invoicesynth.layout_body import COLUMNS as COLUMNS
from auditcore_invoicesynth.layout_body import bank_below, footer, payment, table, totals
from auditcore_invoicesynth.layout_extra import meta_header_row, totals_strip_columns
from auditcore_invoicesynth.layout_head import (
    ensure_space,
    markers,
    meta,
    page_footer,
    recipient,
    sender,
)
from auditcore_invoicesynth.layout_model import BLACK as BLACK
from auditcore_invoicesynth.layout_model import DIAGNOSTIC_LAYOUTS as DIAGNOSTIC_LAYOUTS
from auditcore_invoicesynth.layout_model import FOOTER_TOP as FOOTER_TOP
from auditcore_invoicesynth.layout_model import GRAY as GRAY
from auditcore_invoicesynth.layout_model import HOLDOUT_LAYOUTS as HOLDOUT_LAYOUTS
from auditcore_invoicesynth.layout_model import LAYOUTS as LAYOUTS
from auditcore_invoicesynth.layout_model import PAGE_BOTTOM as PAGE_BOTTOM
from auditcore_invoicesynth.layout_model import TRAINING_LAYOUTS as TRAINING_LAYOUTS
from auditcore_invoicesynth.layout_model import V2_LAYOUTS as V2_LAYOUTS
from auditcore_invoicesynth.layout_model import Canvas as Canvas
from auditcore_invoicesynth.layout_model import Color as Color
from auditcore_invoicesynth.layout_model import LayoutSpec as LayoutSpec
from auditcore_invoicesynth.layout_model import Variant as Variant
from auditcore_invoicesynth.layout_model import available_layouts as available_layouts
from auditcore_invoicesynth.layout_model import expansion as expansion

#: Summenanordnungen, die zwischen Kopfdaten und Positionstabelle stehen.
TOTALS_BEFORE_TABLE = frozenset({"above_table", "top_box", "strip_columns"})


def effective_spec(name: str, variant: Variant) -> LayoutSpec:
    """Vorlage mit den Zusätzen der Variante ``v3`` (Summenort, waagerechte Kopfdaten)."""
    spec = LAYOUTS[name]
    variety = variant.variety
    if variety is None:
        return spec
    if variety.totals_place is not None:
        spec = replace(spec, totals=variety.totals_place)
    if variety.header_row is not None:
        spec = replace(spec, meta="header_row")
    return spec


def _head_data(
    canvas: Canvas, inv: SynthInvoice, variant: Variant, spec: LayoutSpec, y: float
) -> float:
    if spec.meta == "header_row":
        return meta_header_row(canvas, inv, variant, spec, y)
    return meta(canvas, inv, variant, spec, y)


def _totals(
    canvas: Canvas, inv: SynthInvoice, variant: Variant, spec: LayoutSpec, y: float
) -> float:
    if spec.totals == "strip_columns":
        return totals_strip_columns(canvas, inv, variant, spec, y)
    return totals(canvas, inv, variant, spec, y)


def render_layout(canvas: Canvas, inv: SynthInvoice, variant: Variant, name: str) -> None:
    """Beleg vollständig auf die Zeichenfläche bringen (Seitenwechsel inklusive)."""
    spec = effective_spec(name, variant)
    markers(canvas)
    if spec.band:
        canvas.rect(0, 9, 210, 40, fill=(222, 229, 238), outline=None)
    sender_x = {"right": 190.0, "center": 105.0}.get(spec.header, 20.0)
    sender_end = sender(canvas, inv, variant, spec, sender_x, 14)
    recipient_y = max(50.0, sender_end + 4)
    recipient(canvas, inv, variant, 20, recipient_y)
    y = _head_data(canvas, inv, variant, spec, recipient_y + 2)
    if spec.totals in TOTALS_BEFORE_TABLE:
        y = _totals(canvas, inv, variant, spec, max(y, 110))
        y = table(canvas, inv, variant, spec, y)
    else:
        y = table(canvas, inv, variant, spec, max(y, 120))
        y = _totals(canvas, inv, variant, spec, y)
    y = ensure_space(canvas, inv, variant, y, 3 * canvas.line_height() + 4)
    y = payment(canvas, inv, variant, spec, y)
    if spec.bank == "below_totals":
        y = ensure_space(canvas, inv, variant, y, 3 * canvas.line_height())
        bank_below(canvas, inv, variant, y)
    footer(canvas, inv, variant, spec)
    page_footer(canvas, variant)
