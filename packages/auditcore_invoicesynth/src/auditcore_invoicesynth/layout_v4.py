"""Anordnungen der Generatorvariante ``v4``: Betrag hervorgehoben, Summenfolge, Fußzeile.

Teil von :mod:`auditcore_invoicesynth.layouts`. Bewusst kein Nachbau der
Diagnosevorlage ``holdout_b_tabelle`` (grauer Streifen, Betrag links groß,
Netto/Steuer rechts, direkt über der Tabelle): Der hervorgehobene Betrag steht
ohne Hinterlegung an wechselnden Orten, Netto und Steuer bleiben im regulären
Summenblock.
"""

from __future__ import annotations

from dataclasses import replace

from auditcore_invoicesynth.enrich import SynthInvoice
from auditcore_invoicesynth.identifiers import format_iban
from auditcore_invoicesynth.layout_body import vat_label
from auditcore_invoicesynth.layout_head import currency_field, ensure_space, label_value
from auditcore_invoicesynth.layout_model import GRAY, Canvas, LayoutSpec, Variant
from auditcore_invoicesynth.variety_v4 import FooterIds, TotalHighlight

#: Kopfanordnungen, die rechts neben dem Empfänger stehen (dort kein Betrag).
RIGHT_HEAD_METAS = frozenset({"right_column", "stacked_box", "label_table"})
#: Beschriftungs- und Wertspalte je Summenort für die umgestellte Summenfolge.
ORDER_COLUMNS: dict[str, tuple[float, float]] = {
    "right": (112, 190),
    "left_box": (22, 98),
    "boxed": (112, 188),
    "bottom_left": (20, 112),
    "top_box": (114, 188),
}
BOXED_PLACES = frozenset({"left_box", "boxed", "top_box"})
VALUE_SIZE = 1.6
Row = tuple[str, str, bool]


def highlight_stage(variant: Variant, spec: LayoutSpec) -> str | None:
    """Abschnitt, nach dem der hervorgehobene Betrag gezeichnet wird (``None`` = keiner)."""
    highlight = variant.variety.highlight if variant.variety is not None else None
    if highlight is None:
        return None
    if highlight.place == "beside_recipient":
        return "head" if spec.meta in RIGHT_HEAD_METAS else "recipient"
    return "head" if highlight.place == "head_right" else "end"


def draw_highlight(
    canvas: Canvas, inv: SynthInvoice, variant: Variant, spec: LayoutSpec, y: float, stage: str
) -> float:
    """Hervorgehobenen Betrag zeichnen, wenn ``stage`` passt; gibt das neue ``y`` zurück."""
    highlight = variant.variety.highlight if variant.variety is not None else None
    if highlight is None or highlight_stage(variant, spec) != stage:
        return y
    if stage == "recipient":
        _amount(canvas, inv, variant, highlight, 190, y + canvas.line_height(0.65) + 3, "right")
        return y
    height = canvas.line_height(0.8) + canvas.line_height(VALUE_SIZE) + 4
    y = ensure_space(canvas, inv, variant, y, height + 4)
    if stage == "head":
        return _amount(canvas, inv, variant, highlight, 190, y + 1, "right") + 4
    if highlight.place == "below_table_center":
        canvas.line(70, y, 140, y, width=0.3)
        return _amount(canvas, inv, variant, highlight, 105, y + 2, "center") + 4
    end = _amount(canvas, inv, variant, highlight, 24, y + 2, "left")
    width = _amount_width(canvas, variant, highlight, inv)
    canvas.rect(21, y, 27 + width, end + 1.5, fill=None)
    return end + 5


def _amount_width(
    canvas: Canvas, variant: Variant, highlight: TotalHighlight, inv: SynthInvoice
) -> float:
    value = variant.money(inv.printed_total)
    value_width = canvas.text_width(value, size=VALUE_SIZE, bold=True)
    label_width = canvas.text_width(highlight.label + ":", size=0.9)
    if highlight.inline:
        return value_width + 3 + label_width
    return max(value_width, canvas.text_width(highlight.label, size=0.8))


def _amount(
    canvas: Canvas,
    inv: SynthInvoice,
    variant: Variant,
    highlight: TotalHighlight,
    x: float,
    y: float,
    align: str,
) -> float:
    """Beschriftung über oder vor dem großen Betrag; gibt das Ende des Blocks zurück."""
    currency_field(canvas, variant)
    value = canvas.field("total", variant.money(inv.printed_total))
    value_height = canvas.line_height(VALUE_SIZE)
    if not highlight.inline:
        canvas.text(x, y, highlight.label, size=0.8, color=GRAY, align=align)
        y += canvas.line_height(0.8) + 0.5
        canvas.text(x, y, value, size=VALUE_SIZE, bold=True, align=align)
        return y + value_height
    width = _amount_width(canvas, variant, highlight, inv)
    left = {"right": x - width, "center": x - width / 2}.get(align, x)
    label_y = y + value_height - canvas.line_height(0.9)
    canvas.text(left, label_y, highlight.label + ":", size=0.9)
    canvas.text(left + width, y, value, size=VALUE_SIZE, bold=True, align="right")
    return y + value_height


def _total_rows(inv: SynthInvoice, variant: Variant, spec: LayoutSpec, canvas: Canvas) -> list[Row]:
    """Summenzeilen in der gezogenen Reihenfolge (Beschriftung, Wert, Gesamtbetrag?)."""
    order = variant.variety.totals_order if variant.variety is not None else None
    if order is None:
        raise ValueError("Summenfolge nur mit Variante v4")
    prefix = "davon " if order.order[0] == "total" and variant.language == "de" else ""
    groups: dict[str, list[Row]] = {"net": [], "vat": [], "total": []}
    if inv.vat_note_kind != "kleinunternehmer":
        net = canvas.field("net_amount", variant.money(inv.net_amount))
        groups["net"].append((prefix + variant["net_amount"], net, False))
    if inv.vat_note_kind is None:
        for index, line in enumerate(inv.vat_lines):
            label = vat_label(variant, spec, canvas, index, line)
            amount = canvas.field(f"vat_lines.{index}.amount", variant.money(line.amount))
            groups["vat"].append((prefix + label, amount, False))
    total = canvas.field("total", variant.money(inv.printed_total))
    groups["total"].append((variant["total"], total, True))
    return [row for key in order.order for row in groups[key]]


def totals_ordered(
    canvas: Canvas, inv: SynthInvoice, variant: Variant, spec: LayoutSpec, y: float
) -> float:
    """Summenblock in gezogener Reihenfolge, Beschriftung links vom bzw. über dem Wert."""
    y = ensure_space(canvas, inv, variant, y, 12 + 9 * canvas.line_height(1.1))
    currency_field(canvas, variant)
    order = variant.variety.totals_order if variant.variety is not None else None
    label_above = order is not None and order.label_above
    x_label, x_value = ORDER_COLUMNS.get(spec.totals, ORDER_COLUMNS["right"])
    y_start = y
    # Im Kasten wäre „auf <Basis>“ zu lang und ragte über den Rahmen hinaus.
    row_spec = replace(spec, show_vat_base=False) if spec.totals in BOXED_PLACES else spec
    for label, value, is_total in _total_rows(inv, variant, row_spec, canvas):
        size = 1.1 if is_total else 0.95
        if is_total:
            canvas.line(x_label, y, x_value, y, width=0.3)
            y += 1
        if label_above:
            canvas.text(x_value, y, label, size=0.7, color=GRAY, align="right")
            y += canvas.line_height(0.7)
            canvas.text(x_value, y, value, size=size, bold=is_total, align="right")
        else:
            label_value(
                canvas, x_label, y, label + ":", value, value_x=x_value, align="right", size=size,
                bold=is_total,
            )  # fmt: skip
        y += canvas.line_height(size) + (0.8 if label_above else 0)
    if spec.totals in BOXED_PLACES:
        canvas.rect(x_label - 2, y_start - 2, x_value + 2, y + 1)
    return y + 4


def footer_lines(
    inv: SynthInvoice, variant: Variant, ids: FooterIds, canvas: Canvas
) -> list[list[str]]:
    """Spalten der Fußzeile: Anschrift (nur bei drei Spalten), Steuerkennungen, Bank."""
    s = inv.supplier
    tax = [f"{variant['tax_number']}: {s.tax_number}"]
    if s.vat_id:
        tax.append(f"{variant['vat_id']}: " + canvas.field("supplier.vat_id", s.vat_id))
    bank: list[str] = []
    if inv.bank is not None:
        iban = canvas.field("iban", format_iban(inv.bank.iban, grouped=ids.iban_grouped))
        bank = [
            inv.bank.bank_name,
            f"{ids.iban_label}: {iban}",
            f"{variant['bic']}: " + canvas.field("bic", inv.bank.bic),
        ]
    if ids.columns == 3:
        return [[s.name, s.street, s.postal_city], tax, bank]
    return [[s.name, *tax], bank]


def footer_ids(canvas: Canvas, inv: SynthInvoice, variant: Variant) -> None:
    """Kennungen klein in Fußzeilenspalten nebeneinander (ersetzt die Fußzeile der Vorlage)."""
    ids = variant.variety.footer_ids if variant.variety is not None else None
    if ids is None:
        raise ValueError("Fußzeilenkennungen nur mit Variante v4")
    y = 266.0
    canvas.line(20, y - 2, 190, y - 2, width=0.2)
    columns = footer_lines(inv, variant, ids, canvas)
    width = 170 / len(columns)
    texts = [line for column in columns for line in column]
    widest = max(canvas.text_width(text, size=1.0) for text in texts)
    size = max(0.45, min(0.62, (width - 3) / widest if widest > 0 else 0.62))
    for number, column in enumerate(columns):
        for row, line in enumerate(column):
            canvas.text(20 + number * width, y + row * canvas.line_height(size), line, size=size)
