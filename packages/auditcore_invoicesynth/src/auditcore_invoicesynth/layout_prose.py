"""Bausteine der T2c-Vorlagen: Fließtext mit Feldern, linienlose Positionsliste, Wendungen.

Teil von :mod:`auditcore_invoicesynth.layouts` (nur Diagnosesatz T2c). Felder in
Fließtext werden als Ganzes gesetzt und über ``Canvas.field`` erfasst; das
Ziel-JSON enthält damit nur Gedrucktes.
"""

from __future__ import annotations

from decimal import Decimal

from auditcore_invoicesynth.enrich import SynthInvoice
from auditcore_invoicesynth.identifiers import format_iban
from auditcore_invoicesynth.layout_body import fit_text
from auditcore_invoicesynth.layout_head import continuation_header, currency_field, page_footer
from auditcore_invoicesynth.layout_model import BLACK, GRAY, PAGE_BOTTOM, Canvas, Color, Variant

#: Fließtextstück: Text und optional Feldschlüssel (dann als Feld erfasst, fett gesetzt).
Part = tuple[str, str | None]

PHRASES: dict[str, dict[str, str]] = {
    "de": {
        "no": "Nr.",
        "of": "vom",
        "supplied": "Leistungsdatum:",
        "greeting": "Sehr geehrte Damen und Herren,",
        "intro": "für unsere Leistungen erlauben wir uns zu berechnen:",
        "intro_credit": "wir schreiben Ihnen folgende Beträge gut:",
        "subtotal": "Zwischensumme",
        "thereof": "davon",
        "plus": "zzgl.",
        "pay": "Bitte überweisen Sie den Betrag bis zum",
        "pay_credit": "Der Betrag wird bis zum",
        "pay_credit_end": "auf Ihr Konto überwiesen.",
        "account": "auf unser Konto",
        "at": "bei der",
        "regards": "Mit freundlichen Grüßen",
        "tax_number": "St.-Nr.",
        "pay_to": "Zahlbar bis",
    },
    "en": {
        "no": "No.",
        "of": "dated",
        "supplied": "Date of supply:",
        "greeting": "Dear Sir or Madam,",
        "intro": "we hereby invoice the following services:",
        "intro_credit": "we credit you with the following amounts:",
        "subtotal": "Subtotal",
        "thereof": "thereof",
        "plus": "plus",
        "pay": "Please transfer the amount by",
        "pay_credit": "The amount will be transferred to your account by",
        "pay_credit_end": "",
        "account": "to our account",
        "at": "at",
        "regards": "Kind regards",
        "tax_number": "Tax no.",
        "pay_to": "Payable by",
    },
}


#: Satzzeichen, die ohne Leerzeichen an das vorige Wort anschließen.
GLUED = frozenset(".,;:)")


def phrase(variant: Variant, key: str) -> str:
    return PHRASES[variant.language][key]


def fit_size(canvas: Canvas, text: str, width: float, size: float, *, bold: bool = False) -> float:
    """Größte Schriftgröße bis ``size``, mit der ``text`` in ``width`` passt."""
    measured = canvas.text_width(text, size=size, bold=bold)
    return size if measured <= width else max(0.5, size * width / measured)


def flow(
    canvas: Canvas,
    parts: list[Part],
    x: float,
    y: float,
    right: float,
    *,
    size: float = 0.9,
    color: Color = BLACK,
) -> float:
    """Fließtext ab ``(x, y)`` bis ``right`` umbrechen; liefert die y-Position darunter."""
    cursor = x
    space = canvas.text_width(" ", size=size)
    for text, key in parts:
        words = [canvas.field(key, text)] if key else text.split()
        for word in words:
            width = canvas.text_width(word, size=size, bold=key is not None)
            if word[:1] in GLUED and cursor > x:
                cursor -= space
            if cursor > x and cursor + width > right:
                cursor, y = x, y + canvas.line_height(size)
            canvas.text(cursor, y, word, size=size, bold=key is not None, color=color)
            cursor += width + space
    return y + canvas.line_height(size)


def number_parts(inv: SynthInvoice, variant: Variant) -> list[Part]:
    """„Rechnung Nr. <Nummer> vom <Datum>“ als Fließtextstücke (Titel und Kopfdaten)."""
    title = variant["title_credit_note" if inv.kind == "credit_note" else "title_invoice"]
    if not title.endswith(phrase(variant, "no")):
        title = f"{title} {phrase(variant, 'no')}"
    return [
        (title, None),
        (inv.invoice_number, "invoice_number"),
        (phrase(variant, "of"), None),
        (variant.date(inv.invoice_date), "invoice_date"),
    ]


def payment_parts(inv: SynthInvoice, variant: Variant, *, with_bank: bool) -> list[Part]:
    """Zahlungssatz mit Fälligkeit und – bei ``with_bank`` – IBAN, BIC und Bank."""
    due = (variant.date(inv.due_date), "due_date")
    if inv.kind == "credit_note":
        end = phrase(variant, "pay_credit_end")
        return [(phrase(variant, "pay_credit"), None), due, *([(end, None)] if end else [])]
    parts: list[Part] = [(phrase(variant, "pay"), None), due]
    if with_bank and inv.bank is not None:
        iban = format_iban(inv.bank.iban, grouped=variant.iban_grouped)
        parts += [
            (f"{phrase(variant, 'account')} {variant['iban']}", None),
            (iban, "iban"),
            (f"({variant['bic']}", None),
            (inv.bank.bic, "bic"),
            (f") {phrase(variant, 'at')} {inv.bank.bank_name}.", None),
        ]
    else:
        parts.append((".", None))
    return parts


def positions(
    canvas: Canvas,
    inv: SynthInvoice,
    variant: Variant,
    columns: tuple[float, float, float, float],
    y: float,
    *,
    stripes: Color | None = None,
) -> float:
    """Positionsliste ohne Linien: Beschreibung, Menge, Einzelpreis, Betrag; dann Zwischensumme.

    ``columns`` = linker Rand und rechte Kanten von Menge, Einzelpreis und Betrag.
    """
    left, qty_x, unit_x, amount_x = columns
    size = 0.9
    y = _positions_header(canvas, variant, columns, y)
    running = Decimal(0)
    for number, position in enumerate(inv.positions):
        if y > PAGE_BOTTOM:
            page_footer(canvas, variant)
            canvas.new_page()
            y = _positions_header(
                canvas, variant, columns, continuation_header(canvas, inv, variant)
            )
        if stripes is not None and number % 2 == 0:
            canvas.rect(
                left - 1,
                y - 0.6,
                amount_x + 1,
                y + canvas.line_height(size) - 0.6,
                fill=stripes,
                outline=None,
            )
        description = fit_text(canvas, position.description, qty_x - left - 22, size)
        canvas.text(left, y, description, size=size)
        canvas.text(qty_x, y, str(position.quantity), size=size, align="right")
        canvas.text(unit_x, y, variant.money(position.unit_price), size=size, align="right")
        canvas.text(amount_x, y, variant.money(position.amount), size=size, align="right")
        currency_field(canvas, variant)
        running += position.amount
        y += canvas.line_height(size)
    y += 1.5
    canvas.text(unit_x, y, phrase(variant, "subtotal"), size=size, color=GRAY, align="right")
    canvas.text(amount_x, y, variant.money(running), size=size, color=GRAY, align="right")
    return y + canvas.line_height(size) + 4


def _positions_header(
    canvas: Canvas, variant: Variant, columns: tuple[float, float, float, float], y: float
) -> float:
    left, qty_x, unit_x, amount_x = columns
    size = 0.75
    canvas.text(left, y, variant["description"].upper(), size=size, color=GRAY)
    for x, key in ((qty_x, "quantity"), (unit_x, "unit_price"), (amount_x, "line_amount")):
        canvas.text(x, y, variant[key].upper(), size=size, color=GRAY, align="right")
    return y + canvas.line_height(size) + 1.5
