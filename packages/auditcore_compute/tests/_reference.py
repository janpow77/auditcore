"""Pure-Python reference implementations (lists, Fraction, datetime) of every kernel.

Deliberately independent of the package: dates via ``datetime``/``calendar``
instead of day-number arithmetic, money via ``Fraction`` instead of int64
splitting, quantiles via sorted lists.
"""

from __future__ import annotations

import calendar
import datetime as dt
import math
from collections.abc import Hashable, Sequence
from decimal import Decimal
from fractions import Fraction


def round_half_up(value: Fraction) -> int:
    """Commercial rounding: half away from zero."""
    magnitude = math.floor(abs(value) + Fraction(1, 2))
    return -magnitude if value < 0 else magnitude


def share(amount: int, rate: Fraction) -> int:
    return round_half_up(Fraction(amount) * rate)


def _last_day(day: dt.date) -> bool:
    return day.day == calendar.monthrange(day.year, day.month)[1]


def year_fraction(start: dt.date, end: dt.date, convention: str, terminal: bool) -> Fraction:
    if end <= start:
        return Fraction(0)
    if convention in ("act/360", "act/365"):
        return Fraction((end - start).days, 360 if convention == "act/360" else 365)
    if convention == "act/act-isda":
        total = Fraction(0)
        for year in range(start.year, end.year + 1):
            lower = max(start, dt.date(year, 1, 1))
            upper = min(end, dt.date(year + 1, 1, 1))
            if upper > lower:
                total += Fraction((upper - lower).days, 366 if calendar.isleap(year) else 365)
        return total
    d1, d2 = start.day, end.day
    if convention == "30e/360":
        d1, d2 = min(d1, 30), min(d2, 30)
    else:
        if _last_day(start):
            d1 = 30
        if _last_day(end) and not (terminal and end.month == 2):
            d2 = 30
    days = 360 * (end.year - start.year) + 30 * (end.month - start.month) + d2 - d1
    return Fraction(days, 360)


def interest(
    principal: int,
    begin: dt.date,
    end: dt.date,
    table: Sequence[tuple[dt.date, Decimal]],
    convention: str,
) -> int:
    total = Fraction(0)
    for index, (valid_from, rate) in enumerate(table):
        upper = table[index + 1][0] if index + 1 < len(table) else end
        lower = max(begin, valid_from)
        upper = min(end, upper)
        if upper > lower:
            fraction = year_fraction(lower, upper, convention, upper == end)
            total += Fraction(rate) / 100 * fraction
    return round_half_up(Fraction(principal) * total)


def quota_status(
    part: int, total: int, minimum: Fraction | None, maximum: Fraction | None
) -> tuple[int, int]:
    if total <= 0:
        return 0, 3
    quota = Fraction(part, total)
    points = round_half_up(quota * 10_000)
    if minimum is not None and quota < minimum:
        return points, 1
    if maximum is not None and quota > maximum:
        return points, 2
    return points, 0


def reconcile(expected: int | None, actual: int | None, tolerance: int) -> tuple[int, int]:
    if expected is None or actual is None:
        return 0, 3
    delta = actual - expected
    if delta == 0:
        return 0, 0
    return delta, 1 if abs(delta) <= tolerance else 2


def quantile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (position - lower) * (ordered[upper] - ordered[lower])


def mad_bounds(values: Sequence[float], factor: float) -> tuple[float, float, float, float]:
    center = quantile(values, 0.5)
    spread = quantile([abs(v - center) for v in values], 0.5)
    reach = factor * spread / 0.6745
    return center, spread, center - reach, center + reach


def iqr_bounds(values: Sequence[float], factor: float) -> tuple[float, float, float, float]:
    first, third = quantile(values, 0.25), quantile(values, 0.75)
    spread = third - first
    return (first + third) / 2.0, spread, first - factor * spread, third + factor * spread


def double_funding(
    keys: Sequence[Hashable],
    amounts: Sequence[int],
    projects: Sequence[Hashable],
    match_amount: bool,
) -> list[bool]:
    seen: dict[tuple[Hashable, int], set[Hashable]] = {}
    for key, amount, project in zip(keys, amounts, projects, strict=True):
        seen.setdefault((key, amount if match_amount else 0), set()).add(project)
    return [
        len(seen[(key, amount if match_amount else 0)]) >= 2
        for key, amount in zip(keys, amounts, strict=True)
    ]


def neumaier(values: Sequence[float]) -> float:
    total = 0.0
    compensation = 0.0
    for value in values:
        candidate = total + value
        if abs(total) >= abs(value):
            compensation += (total - candidate) + value
        else:
            compensation += (value - candidate) + total
        total = candidate
    return total + compensation


def weighted_moments(values: Sequence[float], weights: Sequence[float]) -> tuple[Fraction, ...]:
    """Exact rational weight sum, mean, Σ w·(x−m)² and Σ w² (for tolerance checks)."""
    exact_w = [Fraction(w) for w in weights]
    exact_x = [Fraction(x) for x in values]
    weight_sum = sum(exact_w, Fraction(0))
    if weight_sum == 0:
        return weight_sum, Fraction(0), Fraction(0), Fraction(0)
    mean = sum((w * x for w, x in zip(exact_w, exact_x, strict=True)), Fraction(0)) / weight_sum
    squared = sum((w * (x - mean) ** 2 for w, x in zip(exact_w, exact_x, strict=True)), Fraction(0))
    return weight_sum, mean, squared, sum((w * w for w in exact_w), Fraction(0))
