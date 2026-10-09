"""Zusätze der Generatorvariante ``v4`` (Stufe 7): Betrag, Summenfolge, Fußzeilenkennungen.

Befund auf dem Diagnosesatz T2b: Das Modell verwechselte einen groß gedruckten,
alleinstehenden Gesamtbetrag mit Positions-, Netto- oder Steuerbeträgen und las
kleine Kennungen in der Fußzeile fehlerhaft. ``v4`` legt deshalb – als Konzept,
nicht als Nachbau der Diagnosevorlage – je Beleg aus einer eigenen Zufallsfolge fest,

- ob der Rechnungsbetrag zusätzlich hervorgehoben steht (Ort, Beschriftung über
  oder vor dem Wert),
- in welcher Reihenfolge die Summenzeilen stehen (auch Gesamtbetrag zuerst bzw.
  nicht als letzte Zeile) und ob die Beschriftung über dem Wert steht,
- ob Steuernummer, USt-IdNr. und Bankverbindung klein in Fußzeilenspalten stehen.

Die Ziehungen von ``v1`` bis ``v3`` bleiben unberührt.
"""

from __future__ import annotations

from dataclasses import dataclass
from random import Random

from auditcore_invoicesynth.labels import Language

V4_SALT = 0x5EED_0B04
HIGHLIGHT_SHARE = 0.20
TOTALS_ORDER_SHARE = 0.25
FOOTER_IDS_SHARE = 0.20
#: Orte des hervorgehobenen Betrags; ``beside_recipient`` weicht bei belegter rechter
#: Kopfspalte auf ``head_right`` aus.
HIGHLIGHT_PLACES: tuple[str, ...] = (
    "head_right",
    "below_table_center",
    "bottom_left_box",
    "beside_recipient",
)
HIGHLIGHT_LABELS: dict[Language, tuple[str, ...]] = {
    "de": ("Rechnungsbetrag", "Zu zahlen", "Zahlbetrag", "Gesamtbetrag"),
    "en": ("Amount due", "Total due"),
}
CREDIT_HIGHLIGHT_LABELS: dict[Language, tuple[str, ...]] = {
    "de": ("Gutschriftsbetrag", "Gesamtbetrag"),
    "en": ("Total credit", "Credit amount"),
}
#: Reihenfolgen der Summenzeilen (``net``, ``vat`` = alle Steuerzeilen, ``total``).
TOTALS_ORDERS: tuple[tuple[str, ...], ...] = (
    ("total", "net", "vat"),
    ("total", "vat", "net"),
    ("vat", "net", "total"),
    ("net", "total", "vat"),
)
IBAN_LABELS: tuple[str, ...] = ("IBAN", "Konto (IBAN)", "IBAN-Nr.")


@dataclass(frozen=True)
class TotalHighlight:
    """Groß gedruckter Rechnungsbetrag; ``inline`` = Beschriftung vor statt über dem Wert."""

    place: str
    label: str
    inline: bool


@dataclass(frozen=True)
class TotalsOrder:
    """Reihenfolge der Summenzeilen; ``label_above`` = Beschriftung klein über dem Wert."""

    order: tuple[str, ...]
    label_above: bool


@dataclass(frozen=True)
class FooterIds:
    """Kennungen klein in 2–3 Fußzeilenspalten, IBAN-Beschriftung und -Gruppierung frei."""

    columns: int
    iban_label: str
    iban_grouped: bool


@dataclass(frozen=True)
class V4Choice:
    highlight: TotalHighlight | None
    totals_order: TotalsOrder | None
    footer_ids: FooterIds | None


def choose_v4(seed: int, *, language: Language, credit_note: bool) -> V4Choice:
    """Zusätze der Variante ``v4`` aus eigener Zufallsfolge je Beleg."""
    rng = Random(seed ^ V4_SALT)
    highlight = None
    if rng.random() < HIGHLIGHT_SHARE:
        labels = (CREDIT_HIGHLIGHT_LABELS if credit_note else HIGHLIGHT_LABELS)[language]
        highlight = TotalHighlight(
            place=rng.choice(HIGHLIGHT_PLACES),
            label=rng.choice(labels),
            inline=rng.random() < 0.4,
        )
    order = None
    if rng.random() < TOTALS_ORDER_SHARE:
        order = TotalsOrder(order=rng.choice(TOTALS_ORDERS), label_above=rng.random() < 0.4)
    footer = None
    if rng.random() < FOOTER_IDS_SHARE:
        footer = FooterIds(
            columns=rng.choice((2, 3)),
            iban_label=rng.choice(IBAN_LABELS) if language == "de" else "IBAN",
            iban_grouped=rng.random() < 0.5,
        )
    return V4Choice(highlight, order, footer)


def v4_meta(
    highlight: TotalHighlight | None, order: TotalsOrder | None, footer: FooterIds | None
) -> dict[str, object]:
    """Metadaten der ``v4``-Zusätze je Beleg (nur für ``v4``-Datensätze geschrieben)."""
    return {
        "total_highlight": highlight.place if highlight is not None else None,
        "totals_order": "-".join(order.order) if order is not None else None,
        "footer_ids": footer is not None,
    }
