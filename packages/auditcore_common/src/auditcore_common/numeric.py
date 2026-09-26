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


def share_percent(
    part: float, total: float, *, digits: int = 2, multiply_first: bool = False
) -> float:
    """Share of ``part`` in ``total`` in percent, rounded; ``0.0`` if ``total <= 0``.

    ``multiply_first`` computes ``part * 100 / total`` instead of
    ``part / total * 100``; the two orders can differ in the last binary digit.
    """
    if total <= 0:
        return 0.0
    value = part * 100.0 / total if multiply_first else part / total * 100.0
    return round(value, digits)


def as_float(
    value: object,
    *,
    blank_as_none: bool = False,
    bool_as_none: bool = False,
    catch_type_error: bool = True,
) -> float | None:
    """``float(value)`` or ``None`` for ``None`` and unconvertible values.

    ``blank_as_none`` also maps ``""`` to ``None``; ``bool_as_none`` maps
    ``True``/``False`` to ``None``; ``catch_type_error=False`` lets a
    ``TypeError`` propagate (only ``ValueError`` becomes ``None``). NaN and
    infinities are returned unchanged.
    """
    if (
        value is None
        or (blank_as_none and value == "")
        or (bool_as_none and isinstance(value, bool))
    ):
        return None
    errors: tuple[type[Exception], ...] = (
        (TypeError, ValueError) if catch_type_error else (ValueError,)
    )
    try:
        return float(value)  # type: ignore[arg-type]
    except errors:
        return None


def as_float_comma(value: object) -> float | None:
    """Numbers as ``float`` (NaN → ``None``), other values via text with ``,`` → ``.``.

    Text is not checked for NaN (``"nan"`` stays ``nan``), as in the source.
    """
    if value is None:
        return None
    if isinstance(value, int | float):
        number = float(value)
        return None if math.isnan(number) else number
    try:
        return float(str(value).replace(",", ".").strip())
    except (TypeError, ValueError):
        return None
