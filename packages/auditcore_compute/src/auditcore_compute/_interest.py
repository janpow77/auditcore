"""Day-exact interest on repayment claims with piecewise annual rates.

The interest of one row is ``principal * Σ rate_k * yearfraction_k`` over the
periods of the rate table that overlap ``[start, end)``. Everything is exact
integer arithmetic: rates in basis points (0.01 percentage points), day
counts scaled to a common denominator per convention, one commercial
rounding (half away from zero) at the very end.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

import numpy as np
import numpy.typing as npt

from ._buffers import cents_input, to_days
from ._engine import accelerate, jitable, prange
from ._intmath import civil_from_days, days_from_civil, is_leap, month_end, mul_div_round

#: Day-count conventions and their codes inside the kernel.
#: ``30e/360`` is ISDA 2006 § 4.16(g) (Eurobond basis), ``30e/360-isda`` is
#: § 4.16(h) (often called the German method).
CONVENTIONS: dict[str, int] = {
    "act/360": 0,
    "act/365": 1,
    "act/act-isda": 2,
    "30e/360": 3,
    "30e/360-isda": 4,
}
#: Common denominator of the year fraction per convention (lcm(365, 366) for act/act).
_YEAR_SCALE = (360, 365, 133590, 360, 360)
_BASIS_POINTS = 10_000
_FIRST_DAY = dt.date(1900, 1, 1)
_LAST_DAY = dt.date(2199, 12, 31)


@dataclass(frozen=True)
class RatePeriod:
    """Annual interest rate in percent, valid from ``valid_from`` until the next period."""

    valid_from: dt.date
    rate_percent: Decimal


@dataclass(frozen=True)
class RateTable:
    """Piecewise constant annual rates, sorted by start date, without gaps."""

    periods: tuple[RatePeriod, ...]

    def __post_init__(self) -> None:
        if not self.periods:
            raise ValueError("Die Zinssatztabelle ist leer.")
        starts = [p.valid_from for p in self.periods]
        if starts != sorted(set(starts)):
            raise ValueError("Die Zeiträume müssen streng aufsteigend sortiert sein.")
        for period in self.periods:
            _basis_points(period.rate_percent)

    def plus_points(self, points: Decimal | str | int) -> RateTable:
        """Same table with every rate raised by ``points`` percentage points."""
        shift = _decimal(points)
        return RateTable(
            tuple(RatePeriod(p.valid_from, p.rate_percent + shift) for p in self.periods)
        )

    def buffers(self) -> tuple[npt.NDArray[np.int64], npt.NDArray[np.int64]]:
        """Start day numbers and rates in basis points as int64 buffers."""
        starts = to_days([p.valid_from for p in self.periods])
        points = np.array([_basis_points(p.rate_percent) for p in self.periods], dtype=np.int64)
        return starts, points


def _decimal(value: Decimal | str | int) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (Decimal, str, int)):
        raise TypeError("Zinssätze als Decimal, str oder int angeben.")
    try:
        number = Decimal(value) if not isinstance(value, Decimal) else value
    except InvalidOperation:
        raise ValueError(f"Kein gültiger Zinssatz: {value!r}") from None
    if not number.is_finite():
        raise ValueError(f"Kein endlicher Zinssatz: {value!r}")
    return number


def _basis_points(rate_percent: Decimal) -> int:
    scaled = _decimal(rate_percent) * 100
    if scaled != scaled.to_integral_value() or abs(scaled) > _BASIS_POINTS:
        raise ValueError(
            f"Zinssatz {rate_percent} %: nur ganze Basispunkte (zwei Nachkommastellen) "
            "bis höchstens 100 % werden unterstützt."
        )
    return int(scaled)


def rate_table(entries: Iterable[tuple[dt.date, Decimal | str | int]]) -> RateTable:
    """Build a rate table from ``(valid_from, rate_percent)`` pairs (input data, not built in)."""
    return RateTable(tuple(RatePeriod(start, _decimal(rate)) for start, rate in entries))


@jitable
def _thirty_days(start: int, end: int, convention: int, terminal: bool) -> int:
    y1, m1, d1 = civil_from_days(start)
    y2, m2, d2 = civil_from_days(end)
    if convention == 3:
        d1 = min(d1, 30)
        d2 = min(d2, 30)
    else:
        if d1 == month_end(y1, m1):
            d1 = 30
        if d2 == month_end(y2, m2) and not (terminal and m2 == 2):
            d2 = 30
    return 360 * (y2 - y1) + 30 * (m2 - m1) + d2 - d1


@jitable
def _actual_actual(start: int, end: int) -> int:
    total = 0
    year = civil_from_days(start)[0]
    last = civil_from_days(end - 1)[0]
    while year <= last:
        lower = max(start, days_from_civil(year, 1, 1))
        upper = min(end, days_from_civil(year + 1, 1, 1))
        total += (upper - lower) * (365 if is_leap(year) else 366)
        year += 1
    return total


@jitable
def scaled_days(start: int, end: int, convention: int, terminal: bool) -> int:
    """Year fraction of ``[start, end)`` times the convention's common denominator."""
    if end <= start:
        return 0
    if convention <= 1:
        return end - start
    if convention == 2:
        return _actual_actual(start, end)
    return _thirty_days(start, end, convention, terminal)


@jitable
def _rate_sum(
    start: int,
    end: int,
    starts: npt.NDArray[np.int64],
    points: npt.NDArray[np.int64],
    convention: int,
) -> int:
    index = 0
    while index + 1 < starts.shape[0] and starts[index + 1] <= start:
        index += 1
    total = 0
    current = start
    while current < end:
        stop = end
        if index + 1 < starts.shape[0] and starts[index + 1] < end:
            stop = starts[index + 1]
        total += points[index] * scaled_days(current, stop, convention, stop == end)
        current = stop
        index += 1
    return total


@accelerate(parallel=True)
def interest_kernel(
    principals: npt.NDArray[np.int64],
    begins: npt.NDArray[np.int64],
    ends: npt.NDArray[np.int64],
    starts: npt.NDArray[np.int64],
    points: npt.NDArray[np.int64],
    convention: int,
    divisor: int,
    out: npt.NDArray[np.int64],
) -> None:
    """Element-wise interest in cents (independent rows, parallel-safe)."""
    for i in prange(principals.shape[0]):
        weighted = _rate_sum(begins[i], ends[i], starts, points, convention)
        out[i] = mul_div_round(principals[i], weighted, divisor)


def _check_dates(begins: npt.NDArray[np.int64], ends: npt.NDArray[np.int64], first: int) -> None:
    lowest, highest = (int(day) for day in to_days([_FIRST_DAY, _LAST_DAY]))
    if begins.size and (int(np.min(begins)) < max(first, lowest) or int(np.max(ends)) > highest):
        raise ValueError(
            "Zinsbeginn liegt vor dem ersten Tabelleneintrag oder Daten außerhalb 1900–2199."
        )
    if bool((ends < begins).any()):
        raise ValueError("Das Zinsende liegt vor dem Zinsbeginn.")


def interest_cents_batch(
    principals: object,
    begins: object,
    ends: object,
    table: RateTable,
    convention: str,
) -> npt.NDArray[np.int64]:
    """Day-exact interest in cents for many claims (``[begin, end)``, end not counted).

    ``principals`` are cents (int64, see ``to_cents_buffer``); the rate table is
    input data, e.g. base rate plus 5 percentage points under § 49a (3) VwVfG via
    ``RateTable.plus_points``. One commercial rounding per row.
    """
    if convention not in CONVENTIONS:
        raise ValueError(f"Unbekannte Zinsmethode {convention!r}; erlaubt: {sorted(CONVENTIONS)}")
    amounts = cents_input(principals, "Hauptforderung")
    first, last = to_days(begins), to_days(ends)
    if not amounts.shape == first.shape == last.shape:
        raise ValueError("Beträge, Zinsbeginn und Zinsende müssen gleich lang sein.")
    starts, points = table.buffers()
    _check_dates(first, last, int(starts[0]))
    code = CONVENTIONS[convention]
    out = np.zeros(amounts.shape, dtype=np.int64)
    interest_kernel(
        amounts, first, last, starts, points, code, _BASIS_POINTS * _YEAR_SCALE[code], out
    )
    return out


def interest_cents(
    principal_cents: int, begin: dt.date, end: dt.date, table: RateTable, convention: str
) -> int:
    """Day-exact interest in cents for one claim; see ``interest_cents_batch``."""
    result = interest_cents_batch([principal_cents], [begin], [end], table, convention)
    return int(result[0])
