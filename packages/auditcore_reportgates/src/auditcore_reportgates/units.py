"""Units of printed numbers: percent is not percentage points, scale from the column.

Three dimensions are kept apart and never converted into each other:

``absolute``  amounts and counts, optionally scaled (``Tsd.``, ``Mio.``, ``Mrd.``)
``share``     percent (``%``, ``Prozent``, column ``Anteil``/``Quote``)
``points``    percentage points (``Prozentpunkte``, ``Pp.``)

The scale of a table value is read from its column header (``Mio. Euro``),
never guessed from the size of the number.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class Dimension(StrEnum):
    """Kind of quantity."""

    ABSOLUTE = "absolute"
    SHARE = "share"
    POINTS = "points"


@dataclass(frozen=True)
class Unit:
    """Dimension and decimal exponent of the scale; ``exponent`` ``None`` = not stated."""

    dimension: Dimension
    exponent: int | None = None


PLAIN = Unit(Dimension.ABSOLUTE, None)
PERCENT = Unit(Dimension.SHARE, 0)
PERCENTAGE_POINTS = Unit(Dimension.POINTS, 0)

_SCALES = (
    (re.compile(r"\bmrd\b\.?|milliarde"), 9),
    (re.compile(r"\bmio\b\.?|million"), 6),
    (re.compile(r"\btsd\b\.?|tausend"), 3),
)
_POINTS = re.compile(r"prozentpunkt|\bpp\b\.?|%-punkt")
_SHARE = re.compile(r"%|prozent|\banteil|\bquote")
_EURO = re.compile(r"euro|\beur\b|€")


def _scale(text: str) -> int | None:
    for pattern, exponent in _SCALES:
        if pattern.search(text):
            return exponent
    return None


def unit_of(text: str) -> Unit:
    """Unit named in a prose token (``"%"``, ``"Mio."``) or a column header.

    Percentage points are checked before percent, so ``"Prozentpunkte"`` is
    never read as percent. A header without unit is ``PLAIN``.
    """
    lowered = text.lower()
    if _POINTS.search(lowered):
        return PERCENTAGE_POINTS
    if _SHARE.search(lowered):
        return PERCENT
    exponent = _scale(lowered)
    if exponent is None and _EURO.search(lowered):
        exponent = 0
    return Unit(Dimension.ABSOLUTE, exponent)


def conversion_exponent(source: Unit, target: Unit) -> int | None:
    """Exponent ``e`` with ``value_in_target = value_in_source * 10**e``.

    ``None`` when the dimensions differ (percent against percentage points,
    share against amount). An unstated scale on either side is taken to be the
    scale of the other side: a number printed without scale next to a column
    ``Mio. Euro`` is read in millions.
    """
    if source.dimension is not target.dimension:
        return None
    if source.exponent is None or target.exponent is None:
        return 0
    return source.exponent - target.exponent
