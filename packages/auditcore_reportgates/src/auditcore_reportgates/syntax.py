"""How prose numbers are tokenised: unit set, reading of a lone point, masks.

:data:`DEFAULT_SYNTAX` is the strict reading of :func:`~.prose.extract_claims`.
A caller that has to keep an established reading passes its own
:class:`ClaimSyntax`, for example only the units of :data:`BASIC_UNITS`, a
lone point as decimal point (``"2.5"``) or no masks because it masks itself.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache

DEFAULT_UNITS = (
    r"%-Punkte?n?|Prozentpunkten?|Pp\.|%|Prozent"
    r"|(?:Mio\.|Mrd\.|Tsd\.|Millionen|Milliarden)(?:\s?(?:Euro|EUR)\b|\s?€)?"
    r"|(?:Euro|EUR)\b|€"
)
"""Units read by default: percent, percentage points, scales and currency."""

BASIC_UNITS = r"%|Prozentpunkte|Prozentpunkt|Prozent|Mio\.|Mrd\.|Tsd\."
"""Narrow unit set: percent, percentage points and the three scale abbreviations.

No currency words, no ``Pp.``/``%-Punkte``, no ``Millionen``; ``"5 Euro"`` is a
number without unit, ``"3 %-Punkte"`` reads as percent.
"""


class PointReading(StrEnum):
    """Reading of a point that is not a thousands separator (``"2.5"``)."""

    AMBIGUOUS = "ambiguous"
    """Not read; :func:`~.prose.ambiguous_numbers` lists it, the gate reports it."""
    DECIMAL = "decimal"
    """Decimal point: ``"2.5"`` is 2,5 with one decimal; ``"1.234"`` stays 1234."""
    SPLIT = "split"
    """Point ends the number: ``"2.5"`` gives the numbers 2 and 5.

    No guards against adjacent digits, points or commas, and a dash after
    ``"5 "`` is a sign (``"5 - 3"`` gives 5 and -3). This is the tokeniser of
    the FlowStat prose gate before the extraction. Only the tokeniser is
    reproduced: year detection, unit inheritance and masks remain those of
    :func:`~.prose.extract_claims` and :class:`ClaimSyntax`.
    """


DEFAULT_MASKS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b"),
    re.compile(r"\*\s?\d+"),
    re.compile(
        r"\b(?:Tabelle|Abbildung|Kapitel|Abschnitt|Ziffer|Nummer|Anhang|Anlage)\s+\d+(?:\.\d+)*"
    ),
    re.compile(r"\bArt\.\s?\d+|\bNr\.\s?\d+|§\s?\d+|\bAbs\.\s?\d+"),
    re.compile(r"\b(?:je|pro)\s+\d[\d.]*(?:,\d+)?"),
    re.compile(r"(?<=[A-Za-zÄÖÜäöüß])\d{1,3}(?=[A-Za-zÄÖÜäöüß])"),
)
"""Dates, footnote markers, cross references, legal citations, ``je 100.000``."""


@dataclass(frozen=True)
class ClaimSyntax:
    """Tokeniser settings; the defaults are the strict reading.

    ``units`` is a regular expression alternation matched case-sensitively
    directly (or after one space) behind the number; its match is the unit
    token given to :func:`~.units.unit_of`. ``masks`` are blanked out before
    reading, positions stay valid.
    """

    units: str = DEFAULT_UNITS
    point: PointReading = PointReading.AMBIGUOUS
    masks: tuple[re.Pattern[str], ...] = DEFAULT_MASKS


DEFAULT_SYNTAX = ClaimSyntax()

_GUARDED_SIGN = r"(?:(?<![\w\d])(?<!\d\s)(?P<sign>[-–−])\s?)?(?<![\d.,])"
_PLAIN_SIGN = r"(?:(?<![\w\d])(?P<sign>[-–−])\s?)?"
_GUARDED = (
    r"\d{1,3}(?:\.\d{3})+(?:,\d+)?(?![.,]?\d)|\d+(?:,\d+)?(?![.,]?\d)",
    r"|(?P<ambiguous>\d+(?:[.,]\d+)+)",
)
_NUMBERS = {
    PointReading.AMBIGUOUS: _GUARDED_SIGN + f"(?P<number>{''.join(_GUARDED)})",
    PointReading.DECIMAL: _GUARDED_SIGN
    + f"(?P<number>{_GUARDED[0]}|(?P<point>\\d+\\.\\d+)(?![.,]?\\d){_GUARDED[1]})",
    PointReading.SPLIT: _PLAIN_SIGN + r"(?P<number>\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?)",
}


@lru_cache(maxsize=32)
def number_pattern(syntax: ClaimSyntax) -> re.Pattern[str]:
    """Compiled pattern with the groups ``sign``, ``number``, ``unit``.

    Depending on :attr:`ClaimSyntax.point` also ``ambiguous`` and ``point``.
    An invalid ``units`` expression raises :class:`re.error`; it must not
    contain named groups.
    """
    return re.compile(_NUMBERS[syntax.point] + f"(?:\\s?(?P<unit>{syntax.units}))?")


def masked(text: str, syntax: ClaimSyntax) -> str:
    """Blank out the masks of ``syntax`` (same length, positions stay valid)."""
    for pattern in syntax.masks:
        text = pattern.sub(lambda m: " " * len(m.group()), text)
    return text
