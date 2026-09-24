"""Zehn Belegvorlagen (acht fürs Training, zwei nur für den Layout-Holdout).

Die Vorlagen beschreiben nur Geometrie und Reihenfolge; gezeichnet wird über
die Schnittstelle ``Canvas`` (Pillow-Umsetzung in ``render``). Jeder als Feld
gedruckte Wert wird über ``Canvas.field`` erfasst – daraus entsteht das
Ziel-JSON je Seite (nur, was auf der Seite tatsächlich steht). Jede Seite trägt
oben und unten die Kennzeichnung ``SYNTHETISCH`` (Entscheidung E5).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from random import Random
from typing import Protocol

from auditcore_invoicesynth.enrich import SynthInvoice, VatLine
from auditcore_invoicesynth.formats import (
    AmountStyle,
    CurrencyStyle,
    DateStyle,
    format_date,
    format_money,
    format_rate,
)
from auditcore_invoicesynth.identifiers import format_iban
from auditcore_invoicesynth.labels import (
    LABELS,
    SYNTHETIC_FOOTER,
    SYNTHETIC_MARKER,
    VAT_NOTES,
    Language,
    pick,
)

Color = tuple[int, int, int]
BLACK: Color = (0, 0, 0)
GRAY: Color = (90, 90, 90)
PAGE_BOTTOM = 250.0
FOOTER_TOP = 262.0


class Canvas(Protocol):
    """Zeichenfläche in Millimetern (A4 hoch, Ursprung oben links)."""

    page_number: int

    def text(
        self,
        x: float,
        y: float,
        value: str,
        *,
        size: float = 1.0,
        bold: bool = False,
        align: str = "left",
        color: Color = BLACK,
    ) -> None: ...

    def text_width(self, value: str, *, size: float = 1.0, bold: bool = False) -> float: ...

    def line_height(self, size: float = 1.0) -> float: ...

    def line(self, x1: float, y1: float, x2: float, y2: float, *, width: float = 0.25) -> None: ...

    def rect(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        *,
        fill: Color | None = None,
        outline: Color | None = BLACK,
    ) -> None: ...

    def field(self, key: str, value: str) -> str: ...

    def new_page(self) -> None: ...


@dataclass(frozen=True)
class LayoutSpec:
    header: str = "left"
    meta: str = "right_column"
    table_lines: bool = True
    totals: str = "right"
    bank: str = "footer"
    vat_id_place: str = "header"
    due_in_text: bool = False
    band: bool = False
    scale: float = 1.0
    min_positions: int = 0
    show_vat_base: bool = False


LAYOUTS: dict[str, LayoutSpec] = {
    "kopf_links": LayoutSpec(),
    "kopf_rechts": LayoutSpec(header="right", table_lines=False, bank="below_totals"),
    "summen_unten": LayoutSpec(meta="below_title", totals="bottom", show_vat_base=True),
    "fusszeile_bank": LayoutSpec(table_lines=False, vat_id_place="footer", due_in_text=True),
    "zweispaltig": LayoutSpec(meta="two_column", bank="below_totals", show_vat_base=True),
    "kleinunternehmer": LayoutSpec(header="right", meta="below_title", due_in_text=True),
    "gutschrift": LayoutSpec(meta="below_title", table_lines=False, bank="below_totals"),
    "mehrseitig": LayoutSpec(min_positions=40, vat_id_place="footer"),
    "holdout_kompakt": LayoutSpec(
        meta="grid", totals="left_box", bank="sender", scale=0.9, table_lines=False
    ),
    "holdout_briefkopf": LayoutSpec(
        header="right", band=True, totals="boxed", vat_id_place="footer", show_vat_base=True
    ),
}
HOLDOUT_LAYOUTS: tuple[str, ...] = ("holdout_kompakt", "holdout_briefkopf")
TRAINING_LAYOUTS: tuple[str, ...] = tuple(n for n in LAYOUTS if n not in HOLDOUT_LAYOUTS)


def expansion(layout: str, items: int) -> int:
    """Teilpositionen je Position, damit die Vorlage ihre Mindestzahl erreicht."""
    minimum = LAYOUTS[layout].min_positions
    return max(1, -(-minimum // max(1, items)))


@dataclass(frozen=True)
class Variant:
    """Formatierungs- und Beschriftungswahl eines Belegs."""

    language: Language
    country: str
    amount_style: AmountStyle
    currency_style: CurrencyStyle
    date_style: DateStyle
    rate_variant: int
    iban_grouped: bool
    labels: dict[str, str]

    @classmethod
    def choose(
        cls,
        rng: Random,
        *,
        language: Language,
        country: str,
        amount_style: AmountStyle,
        currency_style: CurrencyStyle,
        date_style: DateStyle,
        rate_variant: int,
        iban_grouped: bool,
    ) -> Variant:
        labels = {key: pick(rng, key, language) for key in sorted(LABELS)}
        if country == "AT":
            labels["vat_id"] = pick(rng, "vat_id_at", language)
        return cls(
            language,
            country,
            amount_style,
            currency_style,
            date_style,
            rate_variant,
            iban_grouped,
            labels,
        )

    def money(self, value: Decimal) -> str:
        return format_money(value, self.amount_style, self.currency_style)

    def date(self, value: date) -> str:
        return format_date(value, self.date_style, country=self.country)

    def rate(self, value: Decimal) -> str:
        return format_rate(value, variant=self.rate_variant)

    def __getitem__(self, key: str) -> str:
        return self.labels[key]


def _currency(canvas: Canvas, variant: Variant) -> None:
    if variant.currency_style != "none":
        canvas.field("currency", "EUR")


def _markers(canvas: Canvas) -> None:
    canvas.text(105, 5, SYNTHETIC_MARKER, size=0.75, align="center", color=GRAY)
    canvas.text(105, 289, SYNTHETIC_FOOTER, size=0.7, align="center", color=GRAY)


def _page_footer(canvas: Canvas, variant: Variant) -> None:
    canvas.text(190, 284, f"{variant['page']} {canvas.page_number}", size=0.75, align="right")


def _kv(
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
    _pair(canvas, x, y, label + ":", shown, value_x=value_x, align=align, size=size, bold=bold)
    return y + canvas.line_height(size)


def _pair(
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


def _sender(
    canvas: Canvas, inv: SynthInvoice, variant: Variant, spec: LayoutSpec, x: float, y: float
) -> float:
    align = "right" if spec.header == "right" else "left"
    canvas.text(
        x, y, canvas.field("supplier.name", inv.supplier.name), size=1.4, bold=True, align=align
    )
    y += canvas.line_height(1.4) + 1
    for line in (inv.supplier.street, inv.supplier.postal_city):
        canvas.text(x, y, line, size=0.9, align=align)
        y += canvas.line_height(0.9)
    if spec.vat_id_place == "header" and inv.supplier.vat_id:
        text = f"{variant['vat_id']}: " + canvas.field("supplier.vat_id", inv.supplier.vat_id)
        canvas.text(x, y, text, size=0.9, align=align)
        y += canvas.line_height(0.9)
    if spec.bank == "sender" and inv.bank is not None:
        iban = canvas.field("iban", format_iban(inv.bank.iban, grouped=variant.iban_grouped))
        canvas.text(x, y, f"{variant['iban']}: {iban}", size=0.8, align=align)
        y += canvas.line_height(0.8)
        canvas.text(
            x, y, f"{variant['bic']}: " + canvas.field("bic", inv.bank.bic), size=0.8, align=align
        )
        y += canvas.line_height(0.8)
    return y


def _recipient(canvas: Canvas, inv: SynthInvoice, variant: Variant, x: float, y: float) -> float:
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


def _title(canvas: Canvas, inv: SynthInvoice, variant: Variant, x: float, y: float) -> float:
    canvas.field("document_type", inv.kind)
    key = "title_credit_note" if inv.kind == "credit_note" else "title_invoice"
    canvas.text(x, y, variant[key], size=1.8, bold=True)
    return y + canvas.line_height(1.8) + 2


def _meta_rows(inv: SynthInvoice, variant: Variant, spec: LayoutSpec) -> list[tuple[str, str, str]]:
    number_label = "credit_note_number" if inv.kind == "credit_note" else "invoice_number"
    rows = [
        (variant[number_label], "invoice_number", inv.invoice_number),
        (variant["invoice_date"], "invoice_date", variant.date(inv.invoice_date)),
        (variant["supply_date"], "supply_date", variant.date(inv.supply_date)),
    ]
    if not spec.due_in_text:
        rows.append((variant["due_date"], "due_date", variant.date(inv.due_date)))
    return rows


def _meta(
    canvas: Canvas, inv: SynthInvoice, variant: Variant, spec: LayoutSpec, y_top: float
) -> float:
    """Kopfdaten; liefert die y-Position, an der die Tabelle beginnen kann."""
    rows = _meta_rows(inv, variant, spec)
    if spec.meta == "right_column":
        y = y_top
        for label, key, value in rows:
            y = _kv(canvas, 120, y, label, key, value, value_x=190, align="right", size=0.9)
        return max(y, _title(canvas, inv, variant, 20, 100)) + 4
    if spec.meta == "below_title":
        y = _title(canvas, inv, variant, 20, 100)
        for label, key, value in rows:
            y = _kv(canvas, 20, y, label, key, value, value_x=68)
        return y + 4
    if spec.meta == "two_column":
        y = _title(canvas, inv, variant, 20, 100)
        half = (len(rows) + 1) // 2
        left_y = right_y = y
        for number, (label, key, value) in enumerate(rows):
            if number < half:
                left_y = _kv(canvas, 20, left_y, label, key, value, value_x=62, size=0.9)
            else:
                right_y = _kv(canvas, 110, right_y, label, key, value, value_x=152, size=0.9)
        return max(left_y, right_y) + 4
    if spec.meta == "grid":
        y = _title(canvas, inv, variant, 20, 96)
        width = 170 / len(rows)
        for number, (label, key, value) in enumerate(rows):
            x = 20 + number * width
            canvas.rect(x, y, x + width, y + 11)
            canvas.text(x + 1.5, y + 1, label, size=0.7, color=GRAY)
            canvas.text(x + 1.5, y + 5.5, canvas.field(key, value), size=0.9, bold=True)
        return y + 15
    raise ValueError(f"Unbekannte Kopfdaten-Anordnung: {spec.meta}")


COLUMNS = {"pos": 20.0, "desc": 31.0, "qty": 128.0, "unit": 158.0, "amount": 190.0}


def _table_header(canvas: Canvas, variant: Variant, y: float, spec: LayoutSpec) -> float:
    size = 0.85
    canvas.text(COLUMNS["pos"], y, variant["position"], size=size, bold=True)
    canvas.text(COLUMNS["desc"], y, variant["description"], size=size, bold=True)
    canvas.text(COLUMNS["qty"], y, variant["quantity"], size=size, bold=True, align="right")
    canvas.text(COLUMNS["unit"], y, variant["unit_price"], size=size, bold=True, align="right")
    canvas.text(COLUMNS["amount"], y, variant["line_amount"], size=size, bold=True, align="right")
    y += canvas.line_height(size)
    canvas.line(20, y, 190, y, width=0.4)
    return y + 1


def _fit(canvas: Canvas, text: str, width: float, size: float) -> str:
    while text and canvas.text_width(text, size=size) > width:
        text = text[:-2] + "…" if len(text) > 2 else ""
    return text


def _continuation_header(canvas: Canvas, inv: SynthInvoice, variant: Variant) -> float:
    _markers(canvas)
    label = variant["credit_note_number" if inv.kind == "credit_note" else "invoice_number"]
    canvas.text(20, 14, canvas.field("supplier.name", inv.supplier.name), size=1.1, bold=True)
    _kv(canvas, 20, 22, label, "invoice_number", inv.invoice_number, value_x=70, size=0.9)
    return 34


def _table(
    canvas: Canvas, inv: SynthInvoice, variant: Variant, spec: LayoutSpec, y: float
) -> float:
    y = _table_header(canvas, variant, y, spec)
    running = Decimal(0)
    size = 0.9
    for number, position in enumerate(inv.positions, 1):
        if y > PAGE_BOTTOM:
            canvas.text(120, y + 1, variant["carry_over"] + ":", size=size, bold=True)
            canvas.text(190, y + 1, variant.money(running), size=size, bold=True, align="right")
            _page_footer(canvas, variant)
            canvas.new_page()
            y = _continuation_header(canvas, inv, variant)
            canvas.text(120, y, variant["carry_over"] + ":", size=size, bold=True)
            canvas.text(190, y, variant.money(running), size=size, bold=True, align="right")
            y = _table_header(canvas, variant, y + canvas.line_height(size) + 1, spec)
        canvas.text(COLUMNS["pos"], y, str(number), size=size)
        canvas.text(COLUMNS["desc"], y, _fit(canvas, position.description, 80, size), size=size)
        canvas.text(COLUMNS["qty"], y, str(position.quantity), size=size, align="right")
        unit = variant.money(position.unit_price)
        canvas.text(COLUMNS["unit"], y, unit, size=size, align="right")
        canvas.text(COLUMNS["amount"], y, variant.money(position.amount), size=size, align="right")
        _currency(canvas, variant)
        running += position.amount
        y += canvas.line_height(size)
        if spec.table_lines:
            canvas.line(20, y - 0.6, 190, y - 0.6, width=0.15)
    canvas.line(20, y, 190, y, width=0.4)
    return y + 3


def _vat_label(
    variant: Variant, spec: LayoutSpec, canvas: Canvas, index: int, line: VatLine
) -> str:
    rate = canvas.field(f"vat_lines.{index}.rate", variant.rate(line.rate))
    label = f"{variant['vat']} {rate}"
    if spec.show_vat_base:
        base = canvas.field(f"vat_lines.{index}.base", variant.money(line.base))
        label += f" auf {base}" if variant.language == "de" else f" on {base}"
    return label


def _ensure(canvas: Canvas, inv: SynthInvoice, variant: Variant, y: float, needed: float) -> float:
    """Seitenwechsel, wenn der Block nicht mehr über die Fußzeile passt."""
    if y + needed <= FOOTER_TOP:
        return y
    _page_footer(canvas, variant)
    canvas.new_page()
    return _continuation_header(canvas, inv, variant)


def _totals(
    canvas: Canvas, inv: SynthInvoice, variant: Variant, spec: LayoutSpec, y: float
) -> float:
    y = _ensure(canvas, inv, variant, y, 12 + 7 * canvas.line_height(1.1))
    note = inv.vat_note_kind
    total_label = variant["total"]
    rows: list[tuple[str, str | None, str, bool]] = []
    if note != "kleinunternehmer":
        rows.append((variant["net_amount"], "net_amount", variant.money(inv.net_amount), False))
    vat_rows: list[tuple[int, VatLine]] = []
    if note is None:
        vat_rows = list(enumerate(inv.vat_lines))
    _currency(canvas, variant)
    if spec.totals in {"right", "left_box", "boxed"}:
        x_label, x_value = {"right": (112, 190), "left_box": (22, 98), "boxed": (112, 188)}[
            spec.totals
        ]
        y_start = y
        size = 0.95
        for label, key, value, bold in rows:
            y = _kv(
                canvas,
                x_label,
                y,
                label,
                key,
                value,
                value_x=x_value,
                align="right",
                size=size,
                bold=bold,
            )
        for index, line in vat_rows:
            label = _vat_label(variant, spec, canvas, index, line)
            amount = canvas.field(f"vat_lines.{index}.amount", variant.money(line.amount))
            _pair(canvas, x_label, y, label + ":", amount, value_x=x_value, align="right",
                  size=size)
            y += canvas.line_height(size)
        canvas.line(x_label, y, x_value, y, width=0.3)
        y += 1
        y = _kv(
            canvas,
            x_label,
            y,
            total_label,
            "total",
            variant.money(inv.printed_total),
            value_x=x_value,
            align="right",
            size=1.1,
            bold=True,
        )
        if spec.totals in {"left_box", "boxed"}:
            canvas.rect(x_label - 2, y_start - 2, x_value + 2, y + 1)
        return y + 4
    if spec.totals == "bottom":
        columns = [(20.0, variant["net_amount"]), (80.0, variant["vat"]), (140.0, total_label)]
        canvas.line(20, y, 190, y, width=0.3)
        y += 1
        for x, label in columns:
            canvas.text(x, y, label, size=0.8, color=GRAY)
        y += canvas.line_height(0.8)
        if note != "kleinunternehmer":
            canvas.text(20, y, canvas.field("net_amount", variant.money(inv.net_amount)))
        vat_y = y
        for index, line in vat_rows:
            label = _vat_label(variant, spec, canvas, index, line)
            amount = canvas.field(f"vat_lines.{index}.amount", variant.money(line.amount))
            canvas.text(80, vat_y, label, size=0.75, color=GRAY)
            canvas.text(80, vat_y + canvas.line_height(0.75), amount)
            vat_y += canvas.line_height(0.75) + canvas.line_height()
        canvas.text(
            140, y, canvas.field("total", variant.money(inv.printed_total)), size=1.2, bold=True
        )
        return max(vat_y, y + canvas.line_height(1.2)) + 4
    raise ValueError(f"Unbekannte Summenanordnung: {spec.totals}")


def _payment(
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


def _bank_below(canvas: Canvas, inv: SynthInvoice, variant: Variant, y: float) -> float:
    if inv.bank is None:
        return y
    canvas.text(20, y, f"{variant['bank']}: {inv.bank.bank_name}", size=0.9, bold=True)
    y += canvas.line_height(0.9)
    iban = canvas.field("iban", format_iban(inv.bank.iban, grouped=variant.iban_grouped))
    y = _kv(canvas, 20, y, variant["iban"], None, iban, value_x=40, size=0.9)
    y = _kv(canvas, 20, y, variant["bic"], "bic", inv.bank.bic, value_x=40, size=0.9)
    return y


def _footer(canvas: Canvas, inv: SynthInvoice, variant: Variant, spec: LayoutSpec) -> None:
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


def render_layout(canvas: Canvas, inv: SynthInvoice, variant: Variant, name: str) -> None:
    """Beleg vollständig auf die Zeichenfläche bringen (Seitenwechsel inklusive)."""
    spec = LAYOUTS[name]
    _markers(canvas)
    if spec.band:
        canvas.rect(0, 9, 210, 40, fill=(222, 229, 238), outline=None)
    sender_x = 190.0 if spec.header == "right" else 20.0
    sender_end = _sender(canvas, inv, variant, spec, sender_x, 14)
    recipient_y = max(50.0, sender_end + 4)
    _recipient(canvas, inv, variant, 20, recipient_y)
    y = _meta(canvas, inv, variant, spec, recipient_y + 2)
    y = _table(canvas, inv, variant, spec, max(y, 120))
    y = _totals(canvas, inv, variant, spec, y)
    y = _ensure(canvas, inv, variant, y, 3 * canvas.line_height() + 4)
    y = _payment(canvas, inv, variant, spec, y)
    if spec.bank == "below_totals":
        y = _ensure(canvas, inv, variant, y, 3 * canvas.line_height())
        _bank_below(canvas, inv, variant, y)
    _footer(canvas, inv, variant, spec)
    _page_footer(canvas, variant)
