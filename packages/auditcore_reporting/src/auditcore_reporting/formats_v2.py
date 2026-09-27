"""Excel number formats of profile ``flowlib-v2`` (successor of ``flowlib-legacy-v1``).

The legacy profile searches substrings anywhere in the column name and ignores
the value, so ``Postleitzahl`` and ``Kontonummer`` get thousands separators,
``Stundensatz`` becomes a percentage and a date in a ``Betrag`` column is shown
as an amount. ``flowlib-v2`` keeps the legacy formats but decides differently:

* the column name is split into words; a word matches a term if it *is* the
  term or – for compound terms – *ends with* it (the head of a German compound
  carries its meaning: ``Förderbetrag`` → ``betrag``, ``Förderquote`` →
  ``quote``); the longest matching term wins within a word;
* identifiers (postcode, account number, IBAN, tax number, phone, file number,
  ``Nr.``/``ID`` …) are never formatted as numbers;
* across words the kind with the highest priority wins (identifier, date,
  percentage, amount, count, duration);
* a supplied value decides where its type contradicts the name: dates always
  get the date format, text and booleans never a number format, numbers never
  the date format.

``flowlib-legacy-v1`` (:mod:`auditcore_reporting.formats`) stays unchanged.
"""

from __future__ import annotations

import re
from datetime import date

GENERAL = "General"
TEXT = "@"
PLAIN_INTEGER = "0"
FORMATS = {
    "date": "DD.MM.YYYY",
    "percent": "0.00%",
    "amount": '#,##0.00 "EUR"',
    "count": "#,##0",
    "duration": "#,##0.00",
}
PRIORITY = ("identifier", "date", "percent", "amount", "count", "duration")

# Terms that match as a whole word or as the head (end) of a compound word.
_COMPOUND: dict[str, tuple[str, ...]] = {
    "identifier": (
        "plz",
        "postleitzahl",
        "iban",
        "bic",
        "kontonummer",
        "kontonr",
        "steuernummer",
        "steuernr",
        "steuerid",
        "ustid",
        "idnr",
        "telefon",
        "telefonnummer",
        "fax",
        "handelsregister",
        "registernummer",
        "aktenzeichen",
        "kennung",
        "kennziffer",
        "nummer",
        "hausnummer",
    ),
    "date": ("datum", "stichtag", "zeitpunkt"),
    "percent": (
        "quote",
        "anteil",
        "prozent",
        "satz",
        "rate",
        "foerdersatz",
        "zinssatz",
        "steuersatz",
        "beihilfesatz",
        "erstattungssatz",
    ),
    "amount": (
        "betrag",
        "summe",
        "kosten",
        "ausgabe",
        "ausgaben",
        "einnahme",
        "einnahmen",
        "saldo",
        "preis",
        "entgelt",
        "honorar",
        "zuwendung",
        "zuschuss",
        "foerdermittel",
        "eigenmittel",
        "drittmittel",
        "auszahlung",
        "bewilligung",
        "umsatz",
        "stundensatz",
        "tagessatz",
        "stundenlohn",
    ),
    "count": ("anzahl", "menge", "stueckzahl"),
    "duration": ("stunden", "tage", "arbeitstage", "personentage"),
    # Compounds whose head looks like a term above but means something else.
    "neutral": ("datensatz", "grundsatz", "einsatz", "zusatz", "ersatz", "montage", "etage"),
}
# Terms that match only as a whole word (too short or ambiguous as a compound head).
_WORDS: dict[str, tuple[str, ...]] = {
    "identifier": ("nr", "id", "hrb", "hra", "tel"),
    "date": ("date", "von", "bis", "beginn", "ende"),
    "percent": ("percent", "%"),
    "amount": ("netto", "brutto", "gesamt", "eur", "euro"),
    "count": ("count", "stueck", "pos", "lfd"),
    "duration": ("hours", "days"),
}
_FOLD = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})
_TOKEN = re.compile(r"%|[^\W\d_]+")


def words(column: str) -> list[str]:
    """Lower-case letter runs of a column name, umlauts folded; digits separate, ``%`` is a word."""
    return _TOKEN.findall(column.casefold().translate(_FOLD))


def _word_kind(word: str) -> str | None:
    """Kind of one word: whole-word terms first, else the longest matching compound head."""
    whole = next((kind for kind in PRIORITY if word in _WORDS[kind]), None)
    if whole:
        return whole
    heads = [(len(t), kind) for kind, terms in _COMPOUND.items() for t in terms if word.endswith(t)]
    kind = max(heads)[1] if heads else None
    return None if kind == "neutral" else kind


def column_kind(column: str) -> str | None:
    """Kind of a column name (identifier, date, percent, amount, count, duration) or None."""
    found = {kind for kind in map(_word_kind, words(column)) if kind}
    return next((kind for kind in PRIORITY if kind in found), None)


def get_number_format_v2(column: str, value: object = None) -> str:
    """Excel number format of profile ``flowlib-v2`` for ``column`` and optional ``value``.

    Raises:
        TypeError: ``column`` is not a string.
    """
    if not isinstance(column, str):
        raise TypeError("column must be a string")
    kind = column_kind(column)
    if isinstance(value, bool):
        return GENERAL
    if isinstance(value, date):
        return FORMATS["date"]
    if isinstance(value, str):
        return TEXT if kind == "identifier" else GENERAL
    numeric = isinstance(value, (int, float))
    if kind == "identifier":
        return PLAIN_INTEGER if numeric else TEXT
    if kind is None or (kind == "date" and numeric):
        return GENERAL
    return FORMATS[kind]
