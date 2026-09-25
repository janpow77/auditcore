"""Floating-point helpers with documented, NumPy-compatible results without NumPy."""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Sequence
from decimal import Decimal

_BLOCK = 128
_RATE = re.compile(r"(\d{1,2})(?:[.,](\d))?\s*%?")


def _unrolled_sum(values: Sequence[float]) -> float:
    count = len(values)
    acc = [float(v) for v in values[:8]]
    index = 8
    limit = count - (count % 8)
    while index < limit:
        for lane in range(8):
            acc[lane] += values[index + lane]
        index += 8
    result = ((acc[0] + acc[1]) + (acc[2] + acc[3])) + ((acc[4] + acc[5]) + (acc[6] + acc[7]))
    while index < count:
        result += values[index]
        index += 1
    return result


def numpy_pairwise_sum(values: Sequence[float]) -> float:
    """NumPy ``add.reduce`` order for contiguous float64 data (blocks of 128, 8 lanes)."""
    count = len(values)
    if count < 8:
        result = 0.0
        for value in values:
            result += value
        return result
    if count <= _BLOCK:
        return _unrolled_sum(values)
    half = count // 2
    half -= half % 8
    return numpy_pairwise_sum(values[:half]) + numpy_pairwise_sum(values[half:])


def numpy_round(value: float, decimals: int) -> float:
    """``numpy.round`` for float64: scale, round half to even, unscale."""
    factor = 10.0**decimals
    return round(value * factor) / factor


def require_finite(
    value: object,
    *,
    not_number: Callable[[], Exception],
    not_finite: Callable[[], Exception],
) -> float:
    """``float(value)`` for real ``int``/``float`` (not ``bool``) that is finite."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise not_number()
    number = float(value)
    if not math.isfinite(number):
        raise not_finite()
    return number


def parse_percent_rate(text: str) -> Decimal | None:
    """``"19 %"``/``"19%"``/``"19,0 %"``/``"7.5"`` → ``Decimal``; integral rates without exponent.

    One or two digits, optionally one decimal after ``.`` or ``,``; anything
    else is ``None``.
    """
    match = _RATE.fullmatch(text.strip())
    if not match:
        return None
    value = Decimal(match[1] + ("." + match[2] if match[2] else ""))
    return value.quantize(Decimal(1)) if value == value.to_integral() else value
