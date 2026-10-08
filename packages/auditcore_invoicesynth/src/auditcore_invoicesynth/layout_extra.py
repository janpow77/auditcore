"""Anordnungen der Generatorvariante ``v3``: waagerechte Kopfdaten und Summenstreifen.

Teil von :mod:`auditcore_invoicesynth.layouts`. Beide Anordnungen drucken die
Beschriftung klein über dem Wert. Sie sind bewusst anders gestaltet als die
Diagnosevorlage ``holdout_b_tabelle`` (dort: grau hinterlegter Streifen mit
Gesamtbetrag links und Beschriftung links vom Wert).
"""

from __future__ import annotations

import hashlib
from dataclasses import replace

from auditcore_invoicesynth.enrich import SynthInvoice
from auditcore_invoicesynth.layout_body import vat_label
from auditcore_invoicesynth.layout_head import currency_field, ensure_space, meta_rows, title
from auditcore_invoicesynth.layout_model import GRAY, Canvas, LayoutSpec, Variant
from auditcore_invoicesynth.variety import HeaderRow

Cell = tuple[str, str | None, str]
LEFT, RIGHT = 20.0, 190.0
CUSTOMER_LABELS = {"de": "Kundennummer", "en": "Customer no."}


def customer_number(inv: SynthInvoice) -> str:
    """Kundennummer als Zierwert (kein Zielfeld), stabil aus der Rechnungsnummer."""
    digest = hashlib.sha256(inv.invoice_number.encode()).hexdigest()
    return f"KD-{int(digest[:8], 16) % 900000 + 100000}"


def header_cells(
    inv: SynthInvoice, variant: Variant, spec: LayoutSpec, row: HeaderRow
) -> list[Cell]:
    """3–5 Zellen: Kopfdaten (Zielfelder) plus Kundennummer bzw. Seite (keine Zielfelder)."""
    cells: list[Cell] = [(label, key, value) for label, key, value in meta_rows(inv, variant, spec)]
    if row.customer_number or len(cells) < 3:
        cells.insert(1, (CUSTOMER_LABELS[variant.language], None, customer_number(inv)))
    if row.page_cell and len(cells) < 5:
        cells.append((variant["page"], None, "1"))
    return cells


def _fit(canvas: Canvas, texts: list[str], width: float, size: float, *, bold: bool) -> float:
    """Schriftgröße, mit der alle Texte in die Zellbreite passen (höchstens ``size``)."""
    widest = max(canvas.text_width(text, size=1.0, bold=bold) for text in texts)
    return max(0.55, min(size, size if widest <= 0 else width / widest))


def meta_header_row(
    canvas: Canvas, inv: SynthInvoice, variant: Variant, spec: LayoutSpec, y_top: float
) -> float:
    """Kopfdaten waagerecht unter dem Titel, ein- oder zweizeilig, optional umrahmt."""
    row = variant.variety.header_row if variant.variety is not None else None
    if row is None:
        raise ValueError("Kopfdatenzeile nur mit Variante v3")
    cells = header_cells(inv, variant, spec, row)
    per_row = (len(cells) + 1) // 2 if row.two_rows else len(cells)
    width = (RIGHT - LEFT) / per_row
    label_size = _fit(canvas, [c[0] for c in cells], width - 3, 0.7, bold=False)
    value_size = _fit(canvas, [c[2] for c in cells], width - 3, 1.0, bold=True)
    height = canvas.line_height(label_size) + canvas.line_height(value_size) + 3
    y = title(canvas, inv, variant, LEFT, 98)
    for start in range(0, len(cells), per_row):
        _cell_row(canvas, cells[start : start + per_row], y, width, height, framed=row.framed)
        for number, (label, key, value) in enumerate(cells[start : start + per_row]):
            x = LEFT + number * width + 1.5
            canvas.text(x, y + 1, label, size=label_size, color=GRAY)
            shown = canvas.field(key, value) if key else value
            y_value = y + 1.5 + canvas.line_height(label_size)
            canvas.text(x, y_value, shown, size=value_size, bold=True)
        y += height
    return y + 5


def _cell_row(
    canvas: Canvas, cells: list[Cell], y: float, width: float, height: float, *, framed: bool
) -> None:
    """Rahmen mit Trennstrichen oder nur Linien oberhalb und unterhalb der Zeile."""
    right = LEFT + len(cells) * width
    if framed:
        canvas.rect(LEFT, y, right, y + height, fill=None)
        for number in range(1, len(cells)):
            x = LEFT + number * width
            canvas.line(x, y, x, y + height, width=0.2)
    else:
        canvas.line(LEFT, y, right, y, width=0.3)
        canvas.line(LEFT, y + height, right, y + height, width=0.3)


def totals_strip_columns(
    canvas: Canvas,
    inv: SynthInvoice,
    variant: Variant,
    spec: LayoutSpec,
    y: float,
) -> float:
    """Netto | Steuerzeilen | Gesamtbetrag nebeneinander zwischen Kopf und Tabelle."""
    y = ensure_space(canvas, inv, variant, y, 20)
    vat_rows = list(enumerate(inv.vat_lines)) if inv.vat_note_kind is None else []
    currency_field(canvas, variant)
    columns: list[tuple[str, str, bool]] = []
    if inv.vat_note_kind != "kleinunternehmer":
        net = canvas.field("net_amount", variant.money(inv.net_amount))
        columns.append((variant["net_amount"], net, False))
    # Bei mehreren Steuersätzen wäre „auf <Basis>“ in der schmalen Spalte zu lang.
    label_spec = replace(spec, show_vat_base=False) if len(vat_rows) > 1 else spec
    for index, line in vat_rows:
        label = vat_label(variant, label_spec, canvas, index, line)
        amount = canvas.field(f"vat_lines.{index}.amount", variant.money(line.amount))
        columns.append((label, amount, False))
    total = canvas.field("total", variant.money(inv.printed_total))
    columns.append((variant["total"], total, True))
    width = (RIGHT - LEFT) / max(3, len(columns))
    label_size = _fit(canvas, [c[0] for c in columns], width - 3, 0.75, bold=False)
    height = canvas.line_height(label_size) + canvas.line_height(1.1) + 3
    canvas.line(LEFT, y, RIGHT, y, width=0.5)
    for number, (label, value, is_total) in enumerate(columns):
        # Gesamtbetrag immer ganz rechts, auch wenn weniger als drei Spalten belegt sind.
        slot = number if not is_total else max(3, len(columns)) - 1
        x = RIGHT - 1 - (max(3, len(columns)) - 1 - slot) * width
        canvas.text(x, y + 1, label, size=label_size, bold=is_total, color=GRAY, align="right")
        y_value = y + 1.5 + canvas.line_height(label_size)
        canvas.text(x, y_value, value, size=1.1 if is_total else 0.95, bold=is_total, align="right")
    canvas.line(LEFT, y + height, RIGHT, y + height, width=0.5)
    return y + height + 5
