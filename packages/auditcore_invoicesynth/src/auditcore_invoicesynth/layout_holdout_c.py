"""Vorlagen des Diagnosesatzes T2c (versiegelter Unbekannt-Test, nie Training).

Teil von :mod:`auditcore_invoicesynth.layouts`. Beide Vorlagen zeichnen den
Beleg vollständig selbst und teilen keine Geometrie mit Trainings-, T2- oder
T2b-Vorlagen:

* ``holdout_c_brief`` – Geschäftsbrief mit Briefkopf, Kopfdaten im Fließtext und
  Summenliste, in der der Gesamtbetrag nicht am Ende steht.
* ``holdout_c_balken`` – farbiger Seitenbalken mit Kopfdaten, Gesamtbetrag und
  Bankverbindung; Netto und Steuer im Fließtext.
"""

from __future__ import annotations

from auditcore_invoicesynth.enrich import SynthInvoice
from auditcore_invoicesynth.identifiers import format_iban
from auditcore_invoicesynth.labels import VAT_NOTES
from auditcore_invoicesynth.layout_head import currency_field, ensure_space, markers, page_footer
from auditcore_invoicesynth.layout_model import GRAY, Canvas, Color, Variant
from auditcore_invoicesynth.layout_prose import (
    Part,
    fit_size,
    flow,
    number_parts,
    payment_parts,
    phrase,
    positions,
)

LOGO: Color = (176, 196, 214)
SIDEBAR: Color = (214, 230, 222)
STRIPES: Color = (241, 241, 241)
SIDEBAR_X, SIDEBAR_WIDTH = 6.0, 44.0


def render_holdout_c(canvas: Canvas, inv: SynthInvoice, variant: Variant, name: str) -> None:
    """Beleg in einer T2c-Vorlage zeichnen."""
    if name == "holdout_c_brief":
        _render_letter(canvas, inv, variant)
    elif name == "holdout_c_balken":
        _render_sidebar(canvas, inv, variant)
    else:
        raise ValueError(f"Keine T2c-Vorlage: {name}")
    page_footer(canvas, variant)


def _recipient(canvas: Canvas, inv: SynthInvoice, variant: Variant, x: float, y: float) -> float:
    r = inv.recipient
    lines = [r.name, r.street, r.postal_city]
    if r.country != inv.country:
        lines.append({"AT": "Österreich", "DE": "Deutschland"}.get(r.country, r.country))
    if inv.vat_note_kind == "reverse_charge":
        lines.append(f"{variant['recipient_vat_id']}: {r.vat_id}")
    for line in lines:
        canvas.text(x, y, line, size=fit_size(canvas, line, 190 - x, 1.0))
        y += canvas.line_height()
    return y


def _vat_note(canvas: Canvas, inv: SynthInvoice, x: float, y: float) -> float:
    note = inv.vat_note_kind
    if note is None:
        return y
    text = VAT_NOTES[note][len(inv.invoice_number) % len(VAT_NOTES[note])]
    return flow(canvas, [(text, None)], x, y, 190, size=0.85) + 1


def _closing(canvas: Canvas, inv: SynthInvoice, variant: Variant, x: float, y: float) -> None:
    y = ensure_space(canvas, inv, variant, y, 2 * canvas.line_height() + 4)
    canvas.text(x, y + 2, phrase(variant, "regards"), size=0.9)
    canvas.text(x, y + 2 + canvas.line_height(0.9), inv.supplier.name, size=0.9)


def _opening(canvas: Canvas, inv: SynthInvoice, variant: Variant, x: float, y: float) -> float:
    canvas.text(x, y, phrase(variant, "greeting"), size=0.9)
    y += canvas.line_height(0.9) + 1
    intro = "intro_credit" if inv.kind == "credit_note" else "intro"
    return flow(canvas, [(phrase(variant, intro), None)], x, y, 190) + 3


# --- Geschäftsbrief -------------------------------------------------------------------


def _letterhead(canvas: Canvas, inv: SynthInvoice, variant: Variant) -> float:
    """Logo-Platzhalter und Absender rechts oben, Steuernummern links daneben."""
    canvas.rect(166, 10, 190, 22, fill=LOGO, outline=None)
    s = inv.supplier
    name = canvas.field("supplier.name", s.name)
    canvas.text(
        190, 25, name, size=fit_size(canvas, name, 95, 1.2, bold=True), bold=True, align="right"
    )
    y = 25 + canvas.line_height(1.2)
    for line in (s.street, s.postal_city):
        canvas.text(190, y, line, size=0.85, align="right")
        y += canvas.line_height(0.85)
    left_y = 14.0
    if s.vat_id:
        vat_id = canvas.field("supplier.vat_id", s.vat_id)
        canvas.text(20, left_y, f"{variant['vat_id']}: {vat_id}", size=0.75, color=GRAY)
        left_y += canvas.line_height(0.75)
    canvas.text(
        20, left_y, f"{phrase(variant, 'tax_number')} {s.tax_number}", size=0.75, color=GRAY
    )
    return y


def _totals_list(canvas: Canvas, inv: SynthInvoice, variant: Variant, y: float) -> float:
    """Zweispaltige Liste links: Netto, unterstrichener Gesamtbetrag, danach „davon“-Zeilen."""
    y = ensure_space(canvas, inv, variant, y, 6 * canvas.line_height() + 6)
    currency_field(canvas, variant)
    x_label, x_value = 20.0, 98.0
    if inv.vat_note_kind != "kleinunternehmer":
        canvas.text(x_label, y, variant["net_amount"], size=0.9)
        net = canvas.field("net_amount", variant.money(inv.net_amount))
        canvas.text(x_value, y, net, size=0.9, align="right")
        y += canvas.line_height(0.9) + 1
    total = canvas.field("total", variant.money(inv.printed_total))
    canvas.text(x_label, y, variant["total"], size=1.05, bold=True)
    canvas.text(x_value, y, total, size=1.05, bold=True, align="right")
    y += canvas.line_height(1.05)
    canvas.line(x_label, y, x_value, y, width=0.35)
    canvas.line(x_label, y + 0.7, x_value, y + 0.7, width=0.35)
    y += 2
    if inv.vat_note_kind is None:
        for index, line in enumerate(inv.vat_lines):
            rate = canvas.field(f"vat_lines.{index}.rate", variant.rate(line.rate))
            label = f"{phrase(variant, 'thereof')} {variant['vat']} {rate}"
            canvas.text(x_label, y, label, size=0.85, color=GRAY)
            amount = canvas.field(f"vat_lines.{index}.amount", variant.money(line.amount))
            canvas.text(x_value, y, amount, size=0.85, color=GRAY, align="right")
            y += canvas.line_height(0.85)
    return y + 4


def _render_letter(canvas: Canvas, inv: SynthInvoice, variant: Variant) -> None:
    markers(canvas)
    head_end = _letterhead(canvas, inv, variant)
    y = _recipient(canvas, inv, variant, 118, max(48.0, head_end + 8))
    y = max(y, 82.0) + 6
    canvas.field("document_type", inv.kind)
    y = flow(canvas, number_parts(inv, variant), 20, y, 190, size=1.25) + 1
    supplied: list[Part] = [
        (phrase(variant, "supplied"), None),
        (variant.date(inv.supply_date), "supply_date"),
    ]
    y = flow(canvas, supplied, 20, y, 190) + 5
    y = _opening(canvas, inv, variant, 20, y)
    y = positions(canvas, inv, variant, (20.0, 122.0, 154.0, 190.0), y)
    y = _totals_list(canvas, inv, variant, y)
    y = _vat_note(canvas, inv, 20, y)
    y = ensure_space(canvas, inv, variant, y, 3 * canvas.line_height() + 2)
    y = flow(canvas, payment_parts(inv, variant, with_bank=True), 20, y, 190)
    _closing(canvas, inv, variant, 20, y + 2)
    s = inv.supplier
    canvas.line(70, 268, 140, 268, width=0.15)
    canvas.text(
        105, 270, f"{s.name} · {s.street} · {s.postal_city}", size=0.65, color=GRAY, align="center"
    )


# --- Seitenbalken ---------------------------------------------------------------------


def _side_entry(
    canvas: Canvas, label: str, key: str | None, value: str, y: float, *, size: float = 0.95
) -> float:
    """Beschriftung klein, darunter der Wert fett; Wert passt sich der Balkenbreite an."""
    canvas.text(SIDEBAR_X, y, label, size=fit_size(canvas, label, SIDEBAR_WIDTH, 0.7), color=GRAY)
    y += canvas.line_height(0.7) + 0.5
    shown = canvas.field(key, value) if key else value
    value_size = fit_size(canvas, shown, SIDEBAR_WIDTH, size, bold=True)
    canvas.text(SIDEBAR_X, y, shown, size=value_size, bold=True)
    return y + canvas.line_height(size) + 2.5


def _sidebar(canvas: Canvas, inv: SynthInvoice, variant: Variant) -> None:
    """Balken links: Titel, Kopfdaten, Gesamtbetrag, USt-IdNr. und Bankverbindung."""
    canvas.rect(0, 0, 56, 297, fill=SIDEBAR, outline=None)
    canvas.field("document_type", inv.kind)
    key = "title_credit_note" if inv.kind == "credit_note" else "title_invoice"
    title = variant[key]
    canvas.text(
        SIDEBAR_X, 16, title, size=fit_size(canvas, title, SIDEBAR_WIDTH, 1.4, bold=True), bold=True
    )
    y = 26.0
    number_label = "credit_note_number" if inv.kind == "credit_note" else "invoice_number"
    entries = (
        (variant[number_label], "invoice_number", inv.invoice_number),
        (variant["invoice_date"], "invoice_date", variant.date(inv.invoice_date)),
        (variant["supply_date"], "supply_date", variant.date(inv.supply_date)),
        (variant["due_date"], "due_date", variant.date(inv.due_date)),
    )
    for label, field_key, value in entries:
        y = _side_entry(canvas, label, field_key, value, y)
    currency_field(canvas, variant)
    y = _side_entry(
        canvas, variant["total"], "total", variant.money(inv.printed_total), y + 6, size=1.4
    )
    if inv.supplier.vat_id:
        y = _side_entry(canvas, variant["vat_id"], "supplier.vat_id", inv.supplier.vat_id, y + 6)
    if inv.bank is not None:
        y = _side_entry(canvas, variant["bank"], None, inv.bank.bank_name, y + 6, size=0.8)
        iban = format_iban(inv.bank.iban, grouped=variant.iban_grouped)
        y = _side_entry(canvas, variant["iban"], "iban", iban, y, size=0.8)
        _side_entry(canvas, variant["bic"], "bic", inv.bank.bic, y, size=0.8)


def _amount_sentence(inv: SynthInvoice, variant: Variant) -> list[Part]:
    """„Nettobetrag 100,00 € zzgl. 19 % USt 19,00 €“ ohne Gesamtbetrag (der steht im Balken)."""
    parts: list[Part] = []
    if inv.vat_note_kind != "kleinunternehmer":
        parts += [(f"{variant['net_amount']}", None), (variant.money(inv.net_amount), "net_amount")]
    if inv.vat_note_kind is None:
        for index, line in enumerate(inv.vat_lines):
            parts += [
                (phrase(variant, "plus"), None),
                (variant.rate(line.rate), f"vat_lines.{index}.rate"),
                (variant["vat"], None),
                (variant.money(line.amount), f"vat_lines.{index}.amount"),
            ]
    return parts


def _render_sidebar(canvas: Canvas, inv: SynthInvoice, variant: Variant) -> None:
    _sidebar(canvas, inv, variant)
    markers(canvas)
    left = 62.0
    canvas.rect(172, 10, 190, 24, fill=LOGO, outline=None)
    s = inv.supplier
    name = canvas.field("supplier.name", s.name)
    canvas.text(left, 14, name, size=fit_size(canvas, name, 105, 1.3, bold=True), bold=True)
    address = f"{s.street} · {s.postal_city}"
    canvas.text(left, 14 + canvas.line_height(1.3), address, size=0.8, color=GRAY)
    tax = f"{phrase(variant, 'tax_number')} {s.tax_number}"
    canvas.text(
        left, 14 + canvas.line_height(1.3) + canvas.line_height(0.8), tax, size=0.8, color=GRAY
    )
    y = _recipient(canvas, inv, variant, left, 42)
    y = _opening(canvas, inv, variant, left, max(y, 66.0) + 8)
    y = positions(canvas, inv, variant, (left, 136.0, 162.0, 190.0), y, stripes=STRIPES)
    y = ensure_space(canvas, inv, variant, y, 4 * canvas.line_height() + 4)
    sentence = _amount_sentence(inv, variant)
    if sentence:
        y = flow(canvas, sentence, left, y, 190) + 2
    y = _vat_note(canvas, inv, left, y)
    y = flow(canvas, payment_parts(inv, variant, with_bank=False), left, y, 190)
    _closing(canvas, inv, variant, left, y + 2)
