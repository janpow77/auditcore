"""Werteumwandlung des Watchdogs (unverändert aus den Hilfsmethoden des Originals)."""

from __future__ import annotations

import math
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

#: Platzhalter, die als „kein Wert“ gelten (Pflichtfeldprüfung).
EMPTY_MARKERS = frozenset({"nan", "null", "undefined", "none", "n/a", "invalid date", "-"})
#: Platzhalter, die bei der Betragsumwandlung als „kein Betrag“ gelten.
AMOUNT_MARKERS = frozenset({"nan", "null", "undefined", "none", "n/a", ""})
#: Bekannte Fehlerwerte eines Datumsfelds (C-02).
INVALID_DATE_MARKERS = frozenset({"invalid date", "nan", "null", "undefined", "n/a", "none"})
#: Ungültige Werte numerischer Felder (A-07).
NAN_MARKERS = frozenset({"nan", "null", "undefined", "none", "inf", "-inf", "n/a"})
#: Datumsformate, die ``try_parse_date`` nacheinander versucht.
DATE_FORMATS = ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y")
#: Rechtsformzusätze, die für Lieferantenvergleiche entfernt werden.
LEGAL_FORM_SUFFIXES = (" gmbh", " ag", " ohg", " kg", " e.k.", " gbr", " mbh")


def float_is_nan_or_inf(value: object) -> bool:
    """True, wenn ``float(value)`` gelingt und NaN oder unendlich ergibt."""
    try:
        number = float(value)  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return False
    return math.isnan(number) or math.isinf(number)


def is_empty_or_invalid(value: object) -> bool:
    """Prüft, ob ein Wert leer, None, NaN oder ein Platzhalter ist."""
    if value is None:
        return True
    text = str(value).strip().lower()
    if not text or text in EMPTY_MARKERS:
        return True
    try:
        return math.isnan(float(value))  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return False


def to_decimal(value: object) -> Decimal | None:
    """Konvertiert einen Wert sicher in Decimal."""
    if value is None:
        return None
    try:
        text = str(value).replace(",", ".").strip()
        if text.lower() in AMOUNT_MARKERS:
            return None
        number = Decimal(text)
    except (InvalidOperation, ValueError, TypeError):
        return None
    if number.is_nan() or number.is_infinite():
        return None
    return number


def to_float(value: object) -> float | None:
    """Konvertiert einen Wert sicher in float (``%`` am Ende wird ignoriert)."""
    if value is None:
        return None
    try:
        number = float(str(value).replace(",", ".").strip().rstrip("%"))
    except (ValueError, TypeError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def try_parse_date(date_str: str) -> date | None:
    """Versucht ein Datum aus verschiedenen Formaten zu parsen."""
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


def normalize_supplier_name(name: object) -> str:
    """Normalisiert Lieferantennamen für Vergleiche."""
    if not name:
        return ""
    text = str(name).strip().lower()
    for suffix in LEGAL_FORM_SUFFIXES:
        text = text.replace(suffix, "")
    return text.strip()
