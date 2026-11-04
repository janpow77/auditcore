"""Bausteine der T2d-Vorlagen: zentrierte Kopfzeilen, Positionen, Steuertabelle, Absenderfuß.

Teil von :mod:`auditcore_invoicesynth.layouts` (nur Diagnosesatz T2d). Felder
werden über ``Canvas.field`` erfasst; das Ziel-JSON enthält nur Gedrucktes.
"""

from __future__ import annotations

from auditcore_invoicesynth.enrich import SynthInvoice
from auditcore_invoicesynth.layout_body import fit_text
from auditcore_invoicesynth.layout_head import continuation_header, currency_field, page_footer
from auditcore_invoicesynth.layout_model import GRAY, PAGE_BOTTOM, Canvas, Color, Variant
from auditcore_invoicesynth.layout_prose import fit_size

HEAD_FILL: Color = (228, 222, 238)
RULE: Color = (150, 150, 150)

PHRASES_D: dict[str, dict[str, str]] = {
    "de": {
        "payment_info": "Zahlungsinformationen",
        "transfer": "Überweisung",
        "payout": "Auszahlung",
        "payee": "Empfänger",
        "payer": "Auftraggeber",
        "amount": "Betrag",
        "reference": "Verwendungszweck",
        "sender": "Absender",
        "rate": "Steuersatz",
        "tax": "Steuer",
        "net": "Netto",
        "gross": "Brutto",
        "sum": "Summe",
        "tax_number": "St.-Nr.",
        "vat_id_payee": "USt-IdNr. Empfänger",
        "scan": "Zum Bezahlen scannen",
    },
    "en": {
        "payment_info": "Payment information",
        "transfer": "Bank transfer",
        "payout": "Payout",
        "payee": "Payee",
        "payer": "Originator",
        "amount": "Amount",
        "reference": "Reference",
        "sender": "Sender",
        "rate": "Tax rate",
        "tax": "Tax",
        "net": "Net",
        "gross": "Gross",
        "sum": "Sum",
        "tax_number": "Tax no.",
        "vat_id_payee": "Payee VAT ID",
        "scan": "Scan to pay",
    },
}


def phrase_d(variant: Variant, key: str) -> str:
    return PHRASES_D[variant.language][key]


def title_text(inv: SynthInvoice, variant: Variant) -> str:
    return variant["title_credit_note" if inv.kind == "credit_note" else "title_invoice"]


def centered_head(canvas: Canvas, inv: SynthInvoice, variant: Variant, y: float) -> float:
    """Kopfdaten als zwei zentrierte Zeilen: Nummer · Datum / Leistung · Fälligkeit."""
    number_label = "credit_note_number" if inv.kind == "credit_note" else "invoice_number"
    rows = (
        (
            (variant[number_label], "invoice_number", inv.invoice_number),
            (variant["invoice_date"], "invoice_date", variant.date(inv.invoice_date)),
        ),
        (
            (variant["supply_date"], "supply_date", variant.date(inv.supply_date)),
            (variant["due_date"], "due_date", variant.date(inv.due_date)),
        ),
    )
    for row in rows:
        parts = [f"{label} {canvas.field(key, value)}" for label, key, value in row]
        line = "   ·   ".join(parts)
        canvas.text(105, y, line, size=fit_size(canvas, line, 170, 1.0), align="center")
        y += canvas.line_height(1.0) + 1
    return y


def recipient_block(
    canvas: Canvas, inv: SynthInvoice, variant: Variant, x: float, y: float, width: float
) -> float:
    r = inv.recipient
    lines = [r.name, r.street, r.postal_city]
    if r.country != inv.country:
        lines.append({"AT": "Österreich", "DE": "Deutschland"}.get(r.country, r.country))
    if inv.vat_note_kind == "reverse_charge":
        lines.append(f"{variant['recipient_vat_id']}: {r.vat_id}")
    for line in lines:
        canvas.text(x, y, line, size=fit_size(canvas, line, width, 0.95))
        y += canvas.line_height(0.95)
    return y


def numbered_positions(canvas: Canvas, inv: SynthInvoice, variant: Variant, y: float) -> float:
    """Positionen mit hinterlegter Kopfzeile und laufender Nummer; Seitenwechsel inklusive."""
    y = _positions_header(canvas, variant, y)
    size = 0.88
    for number, position in enumerate(inv.positions, 1):
        if y > PAGE_BOTTOM:
            page_footer(canvas, variant)
            canvas.new_page()
            y = _positions_header(canvas, variant, continuation_header(canvas, inv, variant))
        canvas.text(22, y, f"{number:02d}", size=size, color=GRAY)
        canvas.text(32, y, fit_text(canvas, position.description, 92, size), size=size)
        canvas.text(138, y, str(position.quantity), size=size, align="right")
        canvas.text(164, y, variant.money(position.unit_price), size=size, align="right")
        canvas.text(190, y, variant.money(position.amount), size=size, align="right")
        currency_field(canvas, variant)
        y += canvas.line_height(size) + 0.6
    canvas.line(20, y, 190, y, width=0.2)
    return y + 4


def _positions_header(canvas: Canvas, variant: Variant, y: float) -> float:
    size = 0.78
    canvas.rect(20, y - 1, 190, y + canvas.line_height(size) + 0.5, fill=HEAD_FILL, outline=None)
    canvas.text(22, y, variant["position"], size=size, bold=True)
    canvas.text(32, y, variant["description"], size=size, bold=True)
    for x, key in ((138, "quantity"), (164, "unit_price"), (190, "line_amount")):
        canvas.text(x - 1, y, variant[key], size=size, bold=True, align="right")
    return y + canvas.line_height(size) + 2.5


#: Spalten der Steuertabelle (rechte Kanten): Netto, Steuersatz, Steuer, Brutto.
TAX_COLUMNS: tuple[float, float, float, float] = (98.0, 126.0, 156.0, 190.0)


def tax_table(canvas: Canvas, inv: SynthInvoice, variant: Variant, y: float) -> float:
    """Summen als Tabelle Netto | Steuersatz | Steuer | Brutto je Satz plus Gesamtzeile."""
    size = 0.85
    labels = [phrase_d(variant, k) for k in ("net", "rate", "tax", "gross")]
    for x, label in zip(TAX_COLUMNS, labels, strict=True):
        canvas.text(x, y, label, size=0.75, color=GRAY, align="right")
    y += canvas.line_height(0.75) + 0.5
    canvas.line(60, y, 190, y, width=0.2)
    y += 1.5
    if inv.vat_note_kind is None:
        for index, line in enumerate(inv.vat_lines):
            cells = (
                canvas.field(f"vat_lines.{index}.base", variant.money(line.base)),
                canvas.field(f"vat_lines.{index}.rate", variant.rate(line.rate)),
                canvas.field(f"vat_lines.{index}.amount", variant.money(line.amount)),
                variant.money(line.base + line.amount),
            )
            for x, cell in zip(TAX_COLUMNS, cells, strict=True):
                canvas.text(x, y, cell, size=size, align="right")
            y += canvas.line_height(size)
    return _tax_total_row(canvas, inv, variant, y + 0.5)


def _tax_total_row(canvas: Canvas, inv: SynthInvoice, variant: Variant, y: float) -> float:
    canvas.line(20, y, 190, y, width=0.35)
    y += 1.5
    currency_field(canvas, variant)
    label = variant["total"]
    canvas.text(20, y, label, size=fit_size(canvas, label, 36, 0.95, bold=True), bold=True)
    if inv.vat_note_kind != "kleinunternehmer":
        net = canvas.field("net_amount", variant.money(inv.net_amount))
        canvas.text(TAX_COLUMNS[0], y, net, size=0.95, align="right")
    if inv.vat_note_kind is None:
        canvas.text(TAX_COLUMNS[2], y, variant.money(inv.vat_amount), size=0.95, align="right")
    total = canvas.field("total", variant.money(inv.printed_total))
    canvas.text(TAX_COLUMNS[3], y, total, size=0.95, bold=True, align="right")
    y += canvas.line_height(0.95)
    canvas.line(150, y, 190, y, width=0.35)
    return y + 5


def sender_foot(canvas: Canvas, inv: SynthInvoice, variant: Variant, y: float) -> None:
    """Absenderblock unten: Beschriftung, Name fett, Anschrift und Steuernummer in einer Zeile."""
    s = inv.supplier
    canvas.line(20, y, 190, y, width=0.2)
    canvas.text(20, y + 2, phrase_d(variant, "sender").upper(), size=0.7, color=GRAY)
    name = canvas.field("supplier.name", s.name)
    canvas.text(20, y + 6, name, size=fit_size(canvas, name, 120, 1.1, bold=True), bold=True)
    tail = f"{s.street} · {s.postal_city} · {phrase_d(variant, 'tax_number')} {s.tax_number}"
    canvas.text(20, y + 6 + canvas.line_height(1.1), tail, size=fit_size(canvas, tail, 170, 0.8))
