"""Generatorvariante ``v2`` (Trainingsrunde Stufe 5): Vielfalt der Kopfdaten.

Befund auf dem Layout-Holdout T2: Das Modell lernte die *Position* der
Kopfdaten (Nummer, Rechnungsdatum, Lieferdatum, Fälligkeit) statt ihrer
Beschriftung. ``v2`` variiert deshalb je Beleg seed-bestimmt

- die Reihenfolge der Kopfdatenzeilen,
- ob das Lieferdatum gedruckt wird (Ziel-JSON enthält nur Gedrucktes),
- ob die Fälligkeit im Fließtext steht und mit welcher Formulierung,
- zusätzliche Beschriftungssynonyme und
- ob die USt-IdNr. direkt unter dem Absendernamen steht.

Alle Ziehungen kommen aus einem eigenen ``Random`` je Beleg; die Ziehungen
der Variante ``v1`` bleiben unberührt, ältere Datensätze damit reproduzierbar.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from random import Random
from typing import TYPE_CHECKING

from auditcore_invoicesynth.labels import LABELS, Language

if TYPE_CHECKING:  # pragma: no cover
    from auditcore_invoicesynth.layout_model import Variant

VARIETIES: tuple[str, ...] = ("v1", "v2")
META_KEYS: tuple[str, ...] = ("invoice_number", "invoice_date", "supply_date", "due_date")
VARIETY_SALT = 0x5EED_0B02

EXTRA_LABELS: dict[str, dict[Language, tuple[str, ...]]] = {
    "invoice_date": {
        "de": ("Rechnungsdatum/Invoice date", "Datum der Rechnung", "Rechnungsdatum"),
        "en": ("Invoice date", "Date of issue"),
    },
    "supply_date": {
        "de": ("Leistungserbringung", "Liefertag", "Leistungsdatum", "Lieferdatum"),
        "en": ("Date of supply", "Delivery date"),
    },
    "due_date": {
        "de": ("Fälligkeitsdatum", "zahlbar bis spätestens", "Fällig am", "Zahlbar bis"),
        "en": ("Due date", "Payment due", "Pay by"),
    },
}

DUE_PHRASES: dict[Language, tuple[str, ...]] = {
    "de": (
        "Zahlbar bis {due} ohne Abzug.",
        "Bitte überweisen Sie den Betrag bis zum {due}.",
        "Zahlungsziel: {days} Tage, fällig am {due}.",
        "Zahlbar ohne Abzug bis spätestens {due}.",
        "Fälligkeitsdatum: {due}",
    ),
    "en": (
        "Payable by {due} without deduction.",
        "Please transfer the amount by {due}.",
        "Payment terms: {days} days, due on {due}.",
    ),
}


@dataclass(frozen=True)
class Variety:
    """Seed-bestimmte Wahl der Variante ``v2`` für einen Beleg."""

    meta_order: tuple[str, ...]
    show_supply_date: bool
    due_in_text: bool
    due_phrase: int
    vat_id_under_name: bool


def variety_rng(seed: int) -> Random:
    """Eigene Zufallsfolge je Beleg, getrennt von den Ziehungen der Variante ``v1``."""
    return Random(seed ^ VARIETY_SALT)


def choose_variety(rng: Random, *, language: Language, credit_note: bool) -> Variety:
    order = list(META_KEYS)
    rng.shuffle(order)
    if rng.random() < 0.5:
        # Rechnungsnummer steht in der Praxis meist zuerst; die Hälfte der Belege so lassen.
        order.remove("invoice_number")
        order.insert(0, "invoice_number")
    return Variety(
        meta_order=tuple(order),
        show_supply_date=rng.random() >= 0.25,
        due_in_text=not credit_note and rng.random() < 0.35,
        due_phrase=rng.randrange(len(DUE_PHRASES[language])),
        vat_id_under_name=rng.random() < 0.3,
    )


def apply_variety(variant: Variant, seed: int, *, credit_note: bool) -> Variant:
    """Variante ``v2`` auf eine fertige ``v1``-Wahl legen (eigene Zufallsfolge)."""
    rng = variety_rng(seed)
    labels = dict(variant.labels)
    for key in sorted(EXTRA_LABELS):
        options = (*LABELS[key][variant.language], *EXTRA_LABELS[key][variant.language])
        labels[key] = rng.choice(options)
    variety = choose_variety(rng, language=variant.language, credit_note=credit_note)
    return replace(variant, labels=labels, variety=variety)


def due_text(variant: Variant, due: str, invoice_date: date, due_date: date) -> str:
    """Fälligkeit als Fließtext; ohne ``v2`` die bisherige Formulierung."""
    phrases = DUE_PHRASES[variant.language]
    index = variant.variety.due_phrase if variant.variety is not None else 0
    return phrases[index % len(phrases)].format(due=due, days=(due_date - invoice_date).days)
