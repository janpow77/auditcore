"""Vorlagen des Diagnosesatzes T2d (versiegelter Unbekannt-Test, nie Training).

Teil von :mod:`auditcore_invoicesynth.layouts`. Beide Vorlagen zeichnen den
Beleg vollständig selbst und teilen keine Geometrie mit Trainings-, T2-, T2b-
oder T2c-Vorlagen:

* ``holdout_d_zahlinfo`` – Kennungen in einer Tabelle neben dem Titel,
  Summen als Steuertabelle, Absender unten.
* ``holdout_d_ueberweisung`` – Fuß nach Art eines Überweisungsträgers mit
  QR-Platzhalter; Gesamtbetrag und Kennungen stehen dort.
"""

from __future__ import annotations

from auditcore_invoicesynth.enrich import SynthInvoice
from auditcore_invoicesynth.identifiers import format_iban
from auditcore_invoicesynth.labels import VAT_NOTES
from auditcore_invoicesynth.layout_head import currency_field, ensure_space, markers, page_footer
from auditcore_invoicesynth.layout_holdout_d_parts import (
    RULE,
    centered_head,
    numbered_positions,
    phrase_d,
    recipient_block,
    sender_foot,
    tax_table,
    title_text,
)
from auditcore_invoicesynth.layout_model import GRAY, Canvas, Color, Variant
from auditcore_invoicesynth.layout_prose import fit_size

INFO_FILL: Color = (238, 234, 222)
SLIP_FILL: Color = (250, 240, 214)


def render_holdout_d(canvas: Canvas, inv: SynthInvoice, variant: Variant, name: str) -> None:
    """Beleg in einer T2d-Vorlage zeichnen."""
    if name == "holdout_d_zahlinfo":
        _render_info_table(canvas, inv, variant)
    elif name == "holdout_d_ueberweisung":
        _render_transfer(canvas, inv, variant)
    else:
        raise ValueError(f"Keine T2d-Vorlage: {name}")
    page_footer(canvas, variant)


def _vat_note(canvas: Canvas, inv: SynthInvoice, x: float, y: float) -> float:
    note = inv.vat_note_kind
    if note is None:
        return y
    text = VAT_NOTES[note][len(inv.invoice_number) % len(VAT_NOTES[note])]
    canvas.text(x, y, text, size=fit_size(canvas, text, 170, 0.8), color=GRAY)
    return y + canvas.line_height(0.8) + 2


# --- Zahlungsinformationen neben dem Titel --------------------------------------------


def _info_rows(inv: SynthInvoice, variant: Variant) -> list[tuple[str, str | None, str]]:
    rows: list[tuple[str, str | None, str]] = []
    if inv.supplier.vat_id:
        rows.append((variant["vat_id"], "supplier.vat_id", inv.supplier.vat_id))
    if inv.bank is not None:
        iban = format_iban(inv.bank.iban, grouped=variant.iban_grouped)
        rows += [
            (variant["iban"], "iban", iban),
            (variant["bic"], "bic", inv.bank.bic),
            (variant["bank"], None, inv.bank.bank_name),
        ]
    return rows


def _info_table(canvas: Canvas, inv: SynthInvoice, variant: Variant) -> float:
    """Umrahmte Tabelle rechts oben: Überschrift, darunter Beschriftung | Wert."""
    rows = _info_rows(inv, variant)
    size = 0.78
    step = canvas.line_height(size) + 1.2
    top, left, split, right = 12.0, 104.0, 128.0, 190.0
    bottom = top + step * (len(rows) + 1) + 1.5
    canvas.rect(left, top, right, bottom, fill=None, outline=RULE)
    canvas.rect(left, top, right, top + step, fill=INFO_FILL, outline=RULE)
    heading = phrase_d(variant, "payment_info")
    canvas.text(left + 2, top + 0.8, heading, size=size, bold=True)
    y = top + step + 0.8
    for label, key, value in rows:
        canvas.text(left + 2, y, label, size=fit_size(canvas, label, split - left - 3, size))
        shown = canvas.field(key, value) if key else value
        canvas.text(split, y, shown, size=fit_size(canvas, shown, right - split - 2, size))
        y += step
    canvas.line(split - 1.5, top + step, split - 1.5, bottom, width=0.15)
    return bottom


def _render_info_table(canvas: Canvas, inv: SynthInvoice, variant: Variant) -> None:
    markers(canvas)
    canvas.field("document_type", inv.kind)
    title = title_text(inv, variant)
    canvas.text(20, 14, title, size=fit_size(canvas, title, 80, 1.9, bold=True), bold=True)
    table_end = _info_table(canvas, inv, variant)
    y = centered_head(canvas, inv, variant, max(46.0, table_end + 6))
    canvas.line(60, y + 1, 150, y + 1, width=0.15)
    y = recipient_block(canvas, inv, variant, 20, y + 8, 90)
    y = numbered_positions(canvas, inv, variant, max(y, 96.0) + 8)
    y = ensure_space(canvas, inv, variant, y, 6 * canvas.line_height() + 8)
    y = tax_table(canvas, inv, variant, y)
    y = _vat_note(canvas, inv, 20, y)
    y = ensure_space(canvas, inv, variant, y, 3 * canvas.line_height() + 6)
    sender_foot(canvas, inv, variant, max(y + 4, 248.0))


# --- Überweisungsträger im Fuß --------------------------------------------------------


QR_LEFT, QR_SIZE = 20.0, 34.0
SLIP_LEFT, SLIP_RIGHT = 62.0, 190.0
SLIP_HEIGHT = 66.0


def _qr_placeholder(canvas: Canvas, inv: SynthInvoice, variant: Variant, y: float) -> None:
    """Quadrat mit drei Suchmustern und einem Muster aus der Belegnummer (kein echter Code)."""
    canvas.rect(QR_LEFT, y, QR_LEFT + QR_SIZE, y + QR_SIZE, fill=None, outline=(0, 0, 0))
    for dx, dy in ((2.0, 2.0), (QR_SIZE - 10.0, 2.0), (2.0, QR_SIZE - 10.0)):
        canvas.rect(QR_LEFT + dx, y + dy, QR_LEFT + dx + 8, y + dy + 8, fill=(0, 0, 0))
        canvas.rect(
            QR_LEFT + dx + 2, y + dy + 2, QR_LEFT + dx + 6, y + dy + 6, fill=(255, 255, 255)
        )
    seed = sum(ord(char) for char in inv.invoice_number)
    for cell in range(36):
        if ((seed >> (cell % 7)) + cell * 5) % 3 == 0:
            cx = QR_LEFT + 12 + (cell % 6) * 2.4
            cy = y + 12 + (cell // 6) * 2.4
            canvas.rect(cx, cy, cx + 2.0, cy + 2.0, fill=(0, 0, 0), outline=None)
    note = phrase_d(variant, "scan")
    canvas.text(QR_LEFT, y + QR_SIZE + 1.5, note, size=fit_size(canvas, note, QR_SIZE, 0.65))


def _slip_rows(inv: SynthInvoice, variant: Variant) -> list[tuple[str, str | None, str]]:
    credit = inv.kind == "credit_note"
    rows: list[tuple[str, str | None, str]] = [
        (phrase_d(variant, "payer" if credit else "payee"), "supplier.name", inv.supplier.name)
    ]
    if inv.bank is not None and not credit:
        iban = format_iban(inv.bank.iban, grouped=variant.iban_grouped)
        rows += [(variant["iban"], "iban", iban), (variant["bic"], "bic", inv.bank.bic)]
    if inv.supplier.vat_id:
        rows.append((phrase_d(variant, "vat_id_payee"), "supplier.vat_id", inv.supplier.vat_id))
    rows.append((phrase_d(variant, "reference"), None, inv.invoice_number))
    return rows


def _slip(canvas: Canvas, inv: SynthInvoice, variant: Variant, y: float) -> None:
    """Formularfelder untereinander, Beschriftung klein über dem Wert; Betrag hervorgehoben."""
    canvas.rect(SLIP_LEFT, y, SLIP_RIGHT, y + SLIP_HEIGHT, fill=SLIP_FILL, outline=RULE)
    heading = phrase_d(variant, "payout" if inv.kind == "credit_note" else "transfer")
    canvas.text(SLIP_LEFT + 2, y + 1.2, heading.upper(), size=0.75, bold=True, color=GRAY)
    row_y = y + 6.0
    width = SLIP_RIGHT - SLIP_LEFT - 4
    for label, key, value in _slip_rows(inv, variant):
        canvas.text(SLIP_LEFT + 2, row_y, label, size=0.62, color=GRAY)
        shown = canvas.field(key, value) if key else value
        canvas.rect(SLIP_LEFT + 2, row_y + 2.6, SLIP_RIGHT - 2, row_y + 7.4, fill=(255, 255, 255))
        canvas.text(SLIP_LEFT + 3, row_y + 3, shown, size=fit_size(canvas, shown, width - 2, 0.85))
        row_y += 8.6
    _slip_amount(canvas, inv, variant, y + SLIP_HEIGHT - 2)


def _slip_amount(canvas: Canvas, inv: SynthInvoice, variant: Variant, bottom: float) -> None:
    currency_field(canvas, variant)
    label = f"{phrase_d(variant, 'amount')} ({variant['total']})"
    canvas.text(SLIP_RIGHT - 52, bottom - 11, label, size=fit_size(canvas, label, 50, 0.62))
    total = canvas.field("total", variant.money(inv.printed_total))
    canvas.rect(SLIP_RIGHT - 52, bottom - 8, SLIP_RIGHT - 2, bottom, fill=(255, 255, 255))
    size = fit_size(canvas, total, 46, 1.3, bold=True)
    canvas.text(SLIP_RIGHT - 4, bottom - 7, total, size=size, bold=True, align="right")


def _net_lines(canvas: Canvas, inv: SynthInvoice, variant: Variant, y: float) -> float:
    """Netto und Steuer rechtsbündig unter der Tabelle, ohne Gesamtbetrag."""
    rows: list[tuple[str, str, str]] = []
    if inv.vat_note_kind != "kleinunternehmer":
        rows.append((variant["net_amount"], "net_amount", variant.money(inv.net_amount)))
    if inv.vat_note_kind is None:
        for index, line in enumerate(inv.vat_lines):
            rate = canvas.field(f"vat_lines.{index}.rate", variant.rate(line.rate))
            label = f"{variant['vat']} {rate}"
            rows.append((label, f"vat_lines.{index}.amount", variant.money(line.amount)))
    for label, key, value in rows:
        canvas.text(150, y, label, size=0.85, align="right")
        canvas.text(190, y, canvas.field(key, value), size=0.85, align="right")
        y += canvas.line_height(0.85)
    return y + 3


def _render_transfer(canvas: Canvas, inv: SynthInvoice, variant: Variant) -> None:
    markers(canvas)
    canvas.field("document_type", inv.kind)
    title = title_text(inv, variant)
    canvas.text(
        105, 14, title, size=fit_size(canvas, title, 120, 1.6, bold=True), bold=True, align="center"
    )
    y = centered_head(canvas, inv, variant, 14 + canvas.line_height(1.6) + 2)
    y = recipient_block(canvas, inv, variant, 118, y + 8, 72)
    y = numbered_positions(canvas, inv, variant, max(y, 78.0) + 8)
    y = ensure_space(canvas, inv, variant, y, 4 * canvas.line_height() + 4)
    y = _net_lines(canvas, inv, variant, y)
    y = _vat_note(canvas, inv, 20, y)
    y = ensure_space(canvas, inv, variant, y, SLIP_HEIGHT + 10)
    top = max(y + 4, 270.0 - SLIP_HEIGHT - 8)
    canvas.line(14, top - 3, 196, top - 3, width=0.15)
    _qr_placeholder(canvas, inv, variant, top + 4)
    _slip(canvas, inv, variant, top)
