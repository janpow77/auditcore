"""Decimal amounts: rounding, shares and allocation with remainder balancing.

This is the one implementation of "split a total into parts that add up to the
cent". All arithmetic is :class:`~decimal.Decimal`; binary floats never touch
an amount. The remainder of a rounded allocation always goes to the last part.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from random import Random

#: One cent, the default quantum of every amount.
CENT = Decimal("0.01")
ZERO = Decimal("0.00")


def quantize(value: Decimal, quantum: Decimal = CENT) -> Decimal:
    """Round ``value`` commercially (half up) to a multiple of ``quantum``."""
    return (value / quantum).quantize(Decimal(1), rounding=ROUND_HALF_UP) * quantum


def share(amount: Decimal, rate: Decimal, quantum: Decimal = CENT) -> Decimal:
    """``amount`` times ``rate``, rounded commercially to ``quantum``."""
    return quantize(amount * rate, quantum)


def _units(total: Decimal, quantum: Decimal) -> int:
    if quantum <= 0:
        raise ValueError("quantum must be positive")
    units = total / quantum
    if total < 0 or units != units.to_integral_value():
        raise ValueError("total must be a non-negative multiple of quantum")
    return int(units)


def allocate(
    total: Decimal, weights: Sequence[Decimal | int], quantum: Decimal = CENT
) -> list[Decimal]:
    """Split ``total`` proportionally to ``weights``; the parts add up exactly.

    Every part but the last is rounded down to ``quantum``; the last part takes
    the remainder and is therefore never negative. ``weights`` must be
    non-negative with a positive sum.
    """
    units = _units(total, quantum)
    decimal_weights = [Decimal(weight) for weight in weights]
    weight_sum = sum(decimal_weights, Decimal(0))
    if not decimal_weights or weight_sum <= 0 or min(decimal_weights) < 0:
        raise ValueError("weights must be non-negative with a positive sum")
    parts = [
        int((units * weight / weight_sum).to_integral_value(rounding=ROUND_DOWN))
        for weight in decimal_weights[:-1]
    ]
    parts.append(units - sum(parts))
    return [Decimal(part) * quantum for part in parts]


def split_random(
    total: Decimal,
    parts: int,
    rng: Random,
    *,
    spread: Decimal = Decimal("0.25"),
    minimum: Decimal = CENT,
    quantum: Decimal = CENT,
) -> list[Decimal]:
    """Split ``total`` into ``parts`` scattered amounts of at least ``minimum`` each.

    Weights are drawn uniformly from ``1 ± spread``; the remainder goes to the
    last part. Raises :class:`ValueError` if ``total`` cannot cover the minimums.
    """
    if parts < 1:
        raise ValueError("parts must be at least 1")
    if not Decimal(0) <= spread < Decimal(1):
        raise ValueError("spread must be in [0, 1)")
    floor = minimum * parts
    if total < floor:
        raise ValueError("total is smaller than the sum of the minimum parts")
    weights = [
        Decimal(1) + spread * (Decimal(rng.randrange(0, 20_001)) / 10_000 - 1) for _ in range(parts)
    ]
    return [minimum + part for part in allocate(total - floor, weights, quantum)]
