"""Belegvorlagen als Daten: Zeichenfläche, Vorlagenparameter und Formatwahl.

Teil von :mod:`auditcore_invoicesynth.layouts`, das alle Namen re-exportiert.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from random import Random
from typing import Protocol

from auditcore_invoicesynth.formats import (
    AmountStyle,
    CurrencyStyle,
    DateStyle,
    format_date,
    format_money,
    format_rate,
)
from auditcore_invoicesynth.labels import LABELS, Language, pick

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
