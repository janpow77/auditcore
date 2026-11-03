"""Concentration measures: Lorenz curve, Gini coefficient, HHI and concentration ratio.

Exact discrete formulas with compensated summation (``math.fsum``); no
numerical integration.
Negative values are rejected instead of being dropped, because a silently
shortened population changes the result without notice. An empty population
or a population with total zero has no concentration (``None``).

Scales: Gini, HHI and CR_k are shares between 0 and 1. The HHI is *not*
given on the competition-law scale 0..10.000; multiply by 10.000 for it.
A single unit (``n = 1``) gives Gini 0, HHI 1 and CR_k 1: one unit holds
everything, and its distribution is trivially equal.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from .benford import StatisticsInputError

Number = int | float | Decimal


@dataclass(frozen=True)
class LorenzCurve:
    """Points of the Lorenz curve, starting at (0, 0), and the Gini coefficient."""

    population_share: tuple[float, ...]
    value_share: tuple[float, ...]
    gini: float
    count: int


def _checked(values: Sequence[Number]) -> list[float]:
    checked: list[float] = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, int | float | Decimal):
            raise StatisticsInputError(f"Kein Zahlwert: {value!r}")
        number = float(value)
        if not math.isfinite(number):
            raise StatisticsInputError("Werte müssen endlich sein.")
        if number < 0:
            raise StatisticsInputError("Konzentrationsmaße verlangen nichtnegative Werte.")
        checked.append(number)
    return checked


def gini(values: Sequence[Number]) -> float | None:
    """Gini coefficient ``sum_i (2i - n - 1) x_(i) / (n * sum x)`` of sorted values.

    0 means equal distribution, ``(n - 1) / n`` the maximum for ``n`` units.
    ``None`` for an empty population or total zero.
    """
    ordered = sorted(_checked(values))
    count, total = len(ordered), math.fsum(ordered)
    if count == 0 or total == 0:
        return None
    weighted = math.fsum((2 * rank - count - 1) * x for rank, x in enumerate(ordered, 1))
    return weighted / (count * total)


def lorenz_curve(values: Sequence[Number]) -> LorenzCurve | None:
    """Lorenz curve with ``n + 1`` points and its Gini coefficient; ``None`` as :func:`gini`."""
    ordered = sorted(_checked(values))
    count, total = len(ordered), math.fsum(ordered)
    coefficient = gini(ordered)
    if coefficient is None:
        return None
    shares = [0.0]
    running, compensation = 0.0, 0.0
    for value in ordered:
        # Neumaier summation: each prefix share as exact as math.fsum, in O(n).
        step = running + value
        if abs(running) >= abs(value):
            compensation += (running - step) + value
        else:
            compensation += (value - step) + running
        running = step
        shares.append((running + compensation) / total)
    shares[-1] = 1.0
    population = tuple(rank / count for rank in range(count + 1))
    return LorenzCurve(population, tuple(shares), coefficient, count)


def herfindahl_hirschman(values: Sequence[Number]) -> float | None:
    """Sum of squared shares on the scale 0..1 (between ``1/n`` and 1, not 0..10.000).

    ``n = 1`` gives 1. ``None`` as :func:`gini`.
    """
    checked = _checked(values)
    total = math.fsum(checked)
    if not checked or total == 0:
        return None
    return math.fsum((value / total) ** 2 for value in checked)


def concentration_ratio(values: Sequence[Number], top: int) -> float | None:
    """Share of the ``top`` largest units in the total (CR_k); ``None`` as :func:`gini`."""
    if top < 1:
        raise StatisticsInputError("top muss mindestens 1 sein.")
    checked = sorted(_checked(values), reverse=True)
    total = math.fsum(checked)
    if not checked or total == 0:
        return None
    return math.fsum(checked[:top]) / total
