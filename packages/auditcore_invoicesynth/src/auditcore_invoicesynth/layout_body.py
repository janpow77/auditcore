"""Positionstabelle, Summenblock, Zahlungshinweis, Bankverbindung und Fußzeile.

Teil von :mod:`auditcore_invoicesynth.layouts`.
"""

from __future__ import annotations

from decimal import Decimal

from auditcore_invoicesynth.enrich import SynthInvoice, VatLine
from auditcore_invoicesynth.identifiers import format_iban
from auditcore_invoicesynth.labels import VAT_NOTES
from auditcore_invoicesynth.layout_head import (
    continuation_header,
    currency_field,
    ensure_space,
    key_value,
    label_value,
    page_footer,
)
from auditcore_invoicesynth.layout_model import GRAY, PAGE_BOTTOM, Canvas, LayoutSpec, Variant

COLUMNS = {"pos": 20.0, "desc": 31.0, "qty": 128.0, "unit": 158.0, "amount": 190.0}


def table_header(canvas: Canvas, variant: Variant, y: float, spec: LayoutSpec) -> float:
    size = 0.85
    canvas.text(COLUMNS["pos"], y, variant["position"], size=size, bold=True)
    canvas.text(COLUMNS["desc"], y, variant["description"], size=size, bold=True)
    canvas.text(COLUMNS["qty"], y, variant["quantity"], size=size, bold=True, align="right")
    canvas.text(COLUMNS["unit"], y, variant["unit_price"], size=size, bold=True, align="right")
    canvas.text(COLUMNS["amount"], y, variant["line_amount"], size=size, bold=True, align="right")
    y += canvas.line_height(size)
    canvas.line(20, y, 190, y, width=0.4)
    return y + 1


def fit_text(canvas: Canvas, text: str, width: float, size: float) -> str:
    while text and canvas.text_width(text, size=size) > width:
        text = text[:-2] + "…" if len(text) > 2 else ""
    return text


def table(canvas: Canvas, inv: SynthInvoice, variant: Variant, spec: LayoutSpec, y: float) -> float:
    y = table_header(canvas, variant, y, spec)
    running = Decimal(0)
    size = 0.9
    for number, position in enumerate(inv.positions, 1):
        if y > PAGE_BOTTOM:
            canvas.text(120, y + 1, variant["carry_over"] + ":", size=size, bold=True)
            canvas.text(190, y + 1, variant.money(running), size=size, bold=True, align="right")
            page_footer(canvas, variant)
            canvas.new_page()
            y = continuation_header(canvas, inv, variant)
            canvas.text(120, y, variant["carry_over"] + ":", size=size, bold=True)
            canvas.text(190, y, variant.money(running), size=size, bold=True, align="right")
            y = table_header(canvas, variant, y + canvas.line_height(size) + 1, spec)
        canvas.text(COLUMNS["pos"], y, str(number), size=size)
        canvas.text(COLUMNS["desc"], y, fit_text(canvas, position.description, 80, size), size=size)
        canvas.text(COLUMNS["qty"], y, str(position.quantity), size=size, align="right")
        unit = variant.money(position.unit_price)
        canvas.text(COLUMNS["unit"], y, unit, size=size, align="right")
        canvas.text(COLUMNS["amount"], y, variant.money(position.amount), size=size, align="right")
        currency_field(canvas, variant)
        running += position.amount
        y += canvas.line_height(size)
        if spec.table_lines:
            canvas.line(20, y - 0.6, 190, y - 0.6, width=0.15)
    canvas.line(20, y, 190, y, width=0.4)
    return y + 3


def vat_label(variant: Variant, spec: LayoutSpec, canvas: Canvas, index: int, line: VatLine) -> str:
    rate = canvas.field(f"vat_lines.{index}.rate", variant.rate(line.rate))
    label = f"{variant['vat']} {rate}"
    if spec.show_vat_base:
        base = canvas.field(f"vat_lines.{index}.base", variant.money(line.base))
        label += f" auf {base}" if variant.language == "de" else f" on {base}"
    return label


#: Beschriftungs- und Wertspalte der spaltenförmigen Summenblöcke.
_TOTAL_COLUMNS: dict[str, tuple[float, float]] = {
    "right": (112, 190),
    "left_box": (22, 98),
    "boxed": (112, 188),
}


def totals(
    canvas: Canvas, inv: SynthInvoice, variant: Variant, spec: LayoutSpec, y: float
) -> float:
    y = ensure_space(canvas, inv, variant, y, 12 + 7 * canvas.line_height(1.1))
    vat_rows = list(enumerate(inv.vat_lines)) if inv.vat_note_kind is None else []
    currency_field(canvas, variant)
    if spec.totals in _TOTAL_COLUMNS:
        return _totals_column(canvas, inv, variant, spec, y, vat_rows)
    if spec.totals == "bottom":
        return _totals_bottom(canvas, inv, variant, spec, y, vat_rows)
    raise ValueError(f"Unbekannte Summenanordnung: {spec.totals}")


def _totals_column(
    canvas: Canvas,
    inv: SynthInvoice,
    variant: Variant,
    spec: LayoutSpec,
    y: float,
    vat_rows: list[tuple[int, VatLine]],
) -> float:
    """Netto, Steuerzeilen und Gesamtbetrag untereinander, optional umrahmt."""
    x_label, x_value = _TOTAL_COLUMNS[spec.totals]
    y_start = y
    size = 0.95
    if inv.vat_note_kind != "kleinunternehmer":
        net = variant.money(inv.net_amount)
        y = key_value(
            canvas,
            x_label,
            y,
            variant["net_amount"],
            "net_amount",
            net,
            value_x=x_value,
            align="right",
            size=size,
            bold=False,
        )
    for index, line in vat_rows:
        label = vat_label(variant, spec, canvas, index, line)
        amount = canvas.field(f"vat_lines.{index}.amount", variant.money(line.amount))
        label_value(
            canvas, x_label, y, label + ":", amount, value_x=x_value, align="right", size=size
        )
        y += canvas.line_height(size)
    canvas.line(x_label, y, x_value, y, width=0.3)
    y += 1
    total = variant.money(inv.printed_total)
    y = key_value(
        canvas,
        x_label,
        y,
        variant["total"],
        "total",
        total,
        value_x=x_value,
        align="right",
        size=1.1,
        bold=True,
    )
    if spec.totals in {"left_box", "boxed"}:
        canvas.rect(x_label - 2, y_start - 2, x_value + 2, y + 1)
    return y + 4


def _totals_bottom(
    canvas: Canvas,
    inv: SynthInvoice,
    variant: Variant,
    spec: LayoutSpec,
    y: float,
    vat_rows: list[tuple[int, VatLine]],
) -> float:
    """Netto, Steuer und Gesamtbetrag nebeneinander am Tabellenende."""
    columns = [(20.0, variant["net_amount"]), (80.0, variant["vat"]), (140.0, variant["total"])]
    canvas.line(20, y, 190, y, width=0.3)
    y += 1
    for x, label in columns:
        canvas.text(x, y, label, size=0.8, color=GRAY)
    y += canvas.line_height(0.8)
    if inv.vat_note_kind != "kleinunternehmer":
        canvas.text(20, y, canvas.field("net_amount", variant.money(inv.net_amount)))
    vat_y = y
    for index, line in vat_rows:
        label = vat_label(variant, spec, canvas, index, line)
        amount = canvas.field(f"vat_lines.{index}.amount", variant.money(line.amount))
        canvas.text(80, vat_y, label, size=0.75, color=GRAY)
        canvas.text(80, vat_y + canvas.line_height(0.75), amount)
        vat_y += canvas.line_height(0.75) + canvas.line_height()
    canvas.text(
        140, y, canvas.field("total", variant.money(inv.printed_total)), size=1.2, bold=True
    )
    return max(vat_y, y + canvas.line_height(1.2)) + 4


def payment(
    canvas: Canvas, inv: SynthInvoice, variant: Variant, spec: LayoutSpec, y: float
) -> float:
    note = inv.vat_note_kind
    if note is not None:
        text = VAT_NOTES[note][len(inv.invoice_number) % len(VAT_NOTES[note])]
        canvas.text(20, y, text, size=0.85)
        y += canvas.line_height(0.85) + 1
    if spec.due_in_text:
        due = canvas.field("due_date", variant.date(inv.due_date))
        text = (
            f"Zahlbar bis {due} ohne Abzug."
            if variant.language == "de"
            else f"Payable by {due} without deduction."
        )
    elif inv.kind == "credit_note":
        text = (
            "Der Betrag wird Ihrem Konto gutgeschrieben."
            if variant.language == "de"
            else "The amount will be credited to your account."
        )
    else:
        text = (
            "Bitte überweisen Sie den Betrag unter Angabe der Rechnungsnummer."
            if variant.language == "de"
            else "Please transfer the amount quoting the invoice number."
        )
    canvas.text(20, y, text, size=0.9)
    return y + canvas.line_height(0.9) + 2


def bank_below(canvas: Canvas, inv: SynthInvoice, variant: Variant, y: float) -> float:
    if inv.bank is None:
        return y
    canvas.text(20, y, f"{variant['bank']}: {inv.bank.bank_name}", size=0.9, bold=True)
    y += canvas.line_height(0.9)
    iban = canvas.field("iban", format_iban(inv.bank.iban, grouped=variant.iban_grouped))
    y = key_value(canvas, 20, y, variant["iban"], None, iban, value_x=40, size=0.9)
    y = key_value(canvas, 20, y, variant["bic"], "bic", inv.bank.bic, value_x=40, size=0.9)
    return y


def footer(canvas: Canvas, inv: SynthInvoice, variant: Variant, spec: LayoutSpec) -> None:
    y = 266.0
    canvas.line(20, y - 2, 190, y - 2, width=0.2)
    size = 0.7
    s = inv.supplier
    for number, line in enumerate((s.name, s.street, s.postal_city)):
        canvas.text(20, y + number * canvas.line_height(size), line, size=size)
    if spec.bank == "footer" and inv.bank is not None:
        iban = canvas.field("iban", format_iban(inv.bank.iban, grouped=variant.iban_grouped))
        lines = [
            inv.bank.bank_name,
            f"{variant['iban']}: {iban}",
            f"{variant['bic']}: " + canvas.field("bic", inv.bank.bic),
        ]
        for number, line in enumerate(lines):
            canvas.text(78, y + number * canvas.line_height(size), line, size=size)
    tax_lines = [f"{variant['tax_number']}: {s.tax_number}"]
    if spec.vat_id_place == "footer" and s.vat_id:
        tax_lines.append(f"{variant['vat_id']}: " + canvas.field("supplier.vat_id", s.vat_id))
    for number, line in enumerate(tax_lines):
        canvas.text(190, y + number * canvas.line_height(size), line, size=size, align="right")
