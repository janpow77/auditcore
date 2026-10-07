"""Kopfbereich eines Belegs: Kennzeichnung, Absender, Empfänger, Titel, Kopfdaten.

Teil von :mod:`auditcore_invoicesynth.layouts`.
"""

from __future__ import annotations

from auditcore_invoicesynth.enrich import SynthInvoice
from auditcore_invoicesynth.identifiers import format_iban
from auditcore_invoicesynth.labels import SYNTHETIC_FOOTER, SYNTHETIC_MARKER
from auditcore_invoicesynth.layout_model import FOOTER_TOP, GRAY, Canvas, LayoutSpec, Variant


def currency_field(canvas: Canvas, variant: Variant) -> None:
    if variant.currency_style != "none":
        canvas.field("currency", "EUR")


def markers(canvas: Canvas) -> None:
    canvas.text(105, 5, SYNTHETIC_MARKER, size=0.75, align="center", color=GRAY)
    canvas.text(105, 289, SYNTHETIC_FOOTER, size=0.7, align="center", color=GRAY)


def page_footer(canvas: Canvas, variant: Variant) -> None:
    canvas.text(190, 284, f"{variant['page']} {canvas.page_number}", size=0.75, align="right")


def key_value(
    canvas: Canvas,
    x: float,
    y: float,
    label: str,
    key: str | None,
    value: str,
    *,
    value_x: float,
    align: str = "left",
    size: float = 1.0,
    bold: bool = False,
) -> float:
    """Beschriftung + Wert; mit ``key`` wird der Wert als Feld erfasst."""
    shown = canvas.field(key, value) if key else value
    label_value(
        canvas, x, y, label + ":", shown, value_x=value_x, align=align, size=size, bold=bold
    )
    return y + canvas.line_height(size)


def label_value(
    canvas: Canvas,
    x: float,
    y: float,
    label: str,
    value: str,
    *,
    value_x: float,
    align: str = "left",
    size: float = 1.0,
    bold: bool = False,
) -> None:
    """Beschriftung und Wert ohne Überlappung (Sichtprüfung des Piloten, 24.09.2026)."""
    gap = 2.0
    label_width = canvas.text_width(label, size=size, bold=bold)
    if align == "left":
        value_x = max(value_x, x + label_width + gap)
    else:
        value_width = canvas.text_width(value, size=size, bold=bold)
        x = min(x, value_x - value_width - gap - label_width)
    canvas.text(x, y, label, size=size, bold=bold)
    canvas.text(value_x, y, value, size=size, bold=bold, align=align)


def sender(
    canvas: Canvas, inv: SynthInvoice, variant: Variant, spec: LayoutSpec, x: float, y: float
) -> float:
    align = "right" if spec.header == "right" else "left"
    canvas.text(
        x, y, canvas.field("supplier.name", inv.supplier.name), size=1.4, bold=True, align=align
    )
    y += canvas.line_height(1.4) + 1
    vat_under_name = variant.variety is not None and variant.variety.vat_id_under_name
    if vat_under_name and spec.vat_id_place == "header":
        y = _sender_vat_id(canvas, inv, variant, x, y, align)
    for line in (inv.supplier.street, inv.supplier.postal_city):
        canvas.text(x, y, line, size=0.9, align=align)
        y += canvas.line_height(0.9)
    if spec.vat_id_place == "header" and not vat_under_name:
        y = _sender_vat_id(canvas, inv, variant, x, y, align)
    if spec.bank == "sender" and inv.bank is not None:
        iban = canvas.field("iban", format_iban(inv.bank.iban, grouped=variant.iban_grouped))
        canvas.text(x, y, f"{variant['iban']}: {iban}", size=0.8, align=align)
        y += canvas.line_height(0.8)
        canvas.text(
            x, y, f"{variant['bic']}: " + canvas.field("bic", inv.bank.bic), size=0.8, align=align
        )
        y += canvas.line_height(0.8)
    return y


def _sender_vat_id(
    canvas: Canvas, inv: SynthInvoice, variant: Variant, x: float, y: float, align: str
) -> float:
    if not inv.supplier.vat_id:
        return y
    text = f"{variant['vat_id']}: " + canvas.field("supplier.vat_id", inv.supplier.vat_id)
    canvas.text(x, y, text, size=0.9, align=align)
    return y + canvas.line_height(0.9)


def recipient(canvas: Canvas, inv: SynthInvoice, variant: Variant, x: float, y: float) -> float:
    s = inv.supplier
    canvas.text(x, y, f"{s.name} · {s.street} · {s.postal_city}", size=0.65, color=GRAY)
    y += canvas.line_height(0.65) + 2
    r = inv.recipient
    lines = [r.name, r.street, r.postal_city]
    if r.country != inv.country:
        lines.append({"AT": "Österreich", "DE": "Deutschland"}.get(r.country, r.country))
    for line in lines:
        canvas.text(x, y, line)
        y += canvas.line_height()
    if inv.vat_note_kind == "reverse_charge":
        canvas.text(x, y, f"{variant['recipient_vat_id']}: {r.vat_id}", size=0.85)
        y += canvas.line_height(0.85)
    return y


def title(canvas: Canvas, inv: SynthInvoice, variant: Variant, x: float, y: float) -> float:
    canvas.field("document_type", inv.kind)
    key = "title_credit_note" if inv.kind == "credit_note" else "title_invoice"
    canvas.text(x, y, variant[key], size=1.8, bold=True)
    return y + canvas.line_height(1.8) + 2


def due_in_text(spec: LayoutSpec, variant: Variant) -> bool:
    """Fälligkeit im Fließtext statt in den Kopfdaten (Vorlage oder Variante ``v2``)."""
    return spec.due_in_text or (variant.variety is not None and variant.variety.due_in_text)


def meta_rows(inv: SynthInvoice, variant: Variant, spec: LayoutSpec) -> list[tuple[str, str, str]]:
    number_label = "credit_note_number" if inv.kind == "credit_note" else "invoice_number"
    rows = [
        (variant[number_label], "invoice_number", inv.invoice_number),
        (variant["invoice_date"], "invoice_date", variant.date(inv.invoice_date)),
        (variant["supply_date"], "supply_date", variant.date(inv.supply_date)),
    ]
    if not due_in_text(spec, variant):
        rows.append((variant["due_date"], "due_date", variant.date(inv.due_date)))
    variety = variant.variety
    if variety is None:
        return rows
    if not variety.show_supply_date:
        rows = [row for row in rows if row[1] != "supply_date"]
    return sorted(rows, key=lambda row: variety.meta_order.index(row[1]))


MetaRow = tuple[str, str, str]


def _meta_right_column(
    canvas: Canvas, inv: SynthInvoice, variant: Variant, rows: list[MetaRow], y_top: float
) -> float:
    y = y_top
    for label, key, value in rows:
        y = key_value(canvas, 120, y, label, key, value, value_x=190, align="right", size=0.9)
    return max(y, title(canvas, inv, variant, 20, 100)) + 4


def _meta_below_title(
    canvas: Canvas, inv: SynthInvoice, variant: Variant, rows: list[MetaRow], y_top: float
) -> float:
    y = title(canvas, inv, variant, 20, 100)
    for label, key, value in rows:
        y = key_value(canvas, 20, y, label, key, value, value_x=68)
    return y + 4


def _meta_two_column(
    canvas: Canvas, inv: SynthInvoice, variant: Variant, rows: list[MetaRow], y_top: float
) -> float:
    y = title(canvas, inv, variant, 20, 100)
    half = (len(rows) + 1) // 2
    left_y = right_y = y
    for number, (label, key, value) in enumerate(rows):
        if number < half:
            left_y = key_value(canvas, 20, left_y, label, key, value, value_x=62, size=0.9)
        else:
            right_y = key_value(canvas, 110, right_y, label, key, value, value_x=152, size=0.9)
    return max(left_y, right_y) + 4


def _meta_grid(
    canvas: Canvas, inv: SynthInvoice, variant: Variant, rows: list[MetaRow], y_top: float
) -> float:
    y = title(canvas, inv, variant, 20, 96)
    width = 170 / len(rows)
    for number, (label, key, value) in enumerate(rows):
        x = 20 + number * width
        canvas.rect(x, y, x + width, y + 11)
        canvas.text(x + 1.5, y + 1, label, size=0.7, color=GRAY)
        canvas.text(x + 1.5, y + 5.5, canvas.field(key, value), size=0.9, bold=True)
    return y + 15


def _meta_inline(
    canvas: Canvas, inv: SynthInvoice, variant: Variant, rows: list[MetaRow], y_top: float
) -> float:
    """Kopfdaten fortlaufend in einer Zeile („Nr. … · Datum … · Fällig …“), bei Bedarf umbrochen."""
    y = title(canvas, inv, variant, 20, 100)
    size, x = 0.9, 20.0
    separator = "  ·  "
    for number, (label, key, value) in enumerate(rows):
        text = f"{label}: {value}"
        width = canvas.text_width(text, size=size)
        if number and x + canvas.text_width(separator, size=size) + width > 190:
            x, y = 20.0, y + canvas.line_height(size)
        elif number:
            canvas.text(x, y, separator, size=size, color=GRAY)
            x += canvas.text_width(separator, size=size)
        canvas.text(x, y, f"{label}: ", size=size)
        x += canvas.text_width(f"{label}: ", size=size)
        canvas.text(x, y, canvas.field(key, value), size=size, bold=True)
        x += canvas.text_width(value, size=size, bold=True)
    return y + canvas.line_height(size) + 5


def _meta_stacked_box(
    canvas: Canvas, inv: SynthInvoice, variant: Variant, rows: list[MetaRow], y_top: float
) -> float:
    """Senkrechter Kasten rechts: je Feld die Beschriftung klein über dem Wert."""
    x1, x2 = 132.0, 190.0
    y = y_top
    for label, key, value in rows:
        canvas.text(x1 + 2, y + 1, label, size=0.7, color=GRAY)
        y += canvas.line_height(0.7) + 1
        canvas.text(x1 + 2, y, canvas.field(key, value), size=1.0, bold=True)
        y += canvas.line_height(1.0) + 1
    canvas.rect(x1, y_top, x2, y + 1, fill=None)
    return max(y + 4, title(canvas, inv, variant, 20, 100) + 4)


META_ARRANGEMENTS = {
    "right_column": _meta_right_column,
    "below_title": _meta_below_title,
    "two_column": _meta_two_column,
    "grid": _meta_grid,
    "inline": _meta_inline,
    "stacked_box": _meta_stacked_box,
}


def meta(
    canvas: Canvas, inv: SynthInvoice, variant: Variant, spec: LayoutSpec, y_top: float
) -> float:
    """Kopfdaten; liefert die y-Position, an der die Tabelle beginnen kann."""
    arrange = META_ARRANGEMENTS.get(spec.meta)
    if arrange is None:
        raise ValueError(f"Unbekannte Kopfdaten-Anordnung: {spec.meta}")
    return arrange(canvas, inv, variant, meta_rows(inv, variant, spec), y_top)


def continuation_header(canvas: Canvas, inv: SynthInvoice, variant: Variant) -> float:
    markers(canvas)
    label = variant["credit_note_number" if inv.kind == "credit_note" else "invoice_number"]
    canvas.text(20, 14, canvas.field("supplier.name", inv.supplier.name), size=1.1, bold=True)
    key_value(canvas, 20, 22, label, "invoice_number", inv.invoice_number, value_x=70, size=0.9)
    return 34


def ensure_space(
    canvas: Canvas, inv: SynthInvoice, variant: Variant, y: float, needed: float
) -> float:
    """Seitenwechsel, wenn der Block nicht mehr über die Fußzeile passt."""
    if y + needed <= FOOTER_TOP:
        return y
    page_footer(canvas, variant)
    canvas.new_page()
    return continuation_header(canvas, inv, variant)
