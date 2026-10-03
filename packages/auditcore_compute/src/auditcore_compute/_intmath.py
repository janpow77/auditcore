"""Exact integer helpers shared by the kernels (run as Python or inside Numba).

All helpers use only int64-safe operations within the documented input bounds,
so that the compiled and the Python path agree bit for bit.
"""

from __future__ import annotations

from ._engine import jitable

#: Largest absolute amount accepted by the money kernels: 10 billion euros in cents.
MAX_ABS_CENTS = 10**12
#: Largest denominator of a rate (exact rational ``numerator / denominator``).
MAX_DENOMINATOR = 10**6


@jitable
def mul_div_round(value: int, factor: int, divisor: int) -> int:
    """``value * factor / divisor`` rounded half away from zero, without overflow.

    Requires ``divisor > 0``, ``divisor**2`` below 2**63 and a quotient below
    2**61 (the callers bound amounts, rates and day counts). Small products
    are divided directly; otherwise ``value = a*divisor + b`` and
    ``factor = c*divisor + e`` keep every intermediate result within int64.
    Both branches are exact, so the choice between them never changes a result.
    """
    negative = (value < 0) != (factor < 0)
    value = abs(value)
    factor = abs(factor)
    if float(value) * float(factor) < 4.0e18:
        product = value * factor
        whole = (2 * product + divisor) // (2 * divisor)
        return -whole if negative else whole
    a = value // divisor
    b = value % divisor
    c = factor // divisor
    e = factor % divisor
    product = b * e
    whole = a * factor + b * c + product // divisor
    if 2 * (product % divisor) >= divisor:
        whole += 1
    return -whole if negative else whole


@jitable
def civil_from_days(days: int) -> tuple[int, int, int]:
    """Year, month, day of a day number counted from 1970-01-01 (proleptic Gregorian)."""
    z = days + 719468
    era = z // 146097
    doe = z - era * 146097
    yoe = (doe - doe // 1460 + doe // 36524 - doe // 146096) // 365
    doy = doe - (365 * yoe + yoe // 4 - yoe // 100)
    mp = (5 * doy + 2) // 153
    day = doy - (153 * mp + 2) // 5 + 1
    month = mp + 3 if mp < 10 else mp - 9
    year = yoe + era * 400 + (1 if month <= 2 else 0)
    return year, month, day


@jitable
def days_from_civil(year: int, month: int, day: int) -> int:
    """Day number counted from 1970-01-01 of a proleptic Gregorian date."""
    year -= 1 if month <= 2 else 0
    era = year // 400
    yoe = year - era * 400
    shifted = month - 3 if month > 2 else month + 9
    doy = (153 * shifted + 2) // 5 + day - 1
    doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
    return era * 146097 + doe - 719468


@jitable
def is_leap(year: int) -> bool:
    """Gregorian leap year."""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


@jitable
def month_end(year: int, month: int) -> int:
    """Last day of the month."""
    if month == 2:
        return 29 if is_leap(year) else 28
    if month == 4 or month == 6 or month == 9 or month == 11:
        return 30
    return 31


@jitable
def div_round(numerator: int, divisor: int) -> int:
    """``numerator / divisor`` rounded half away from zero (``divisor > 0``)."""
    magnitude = (2 * abs(numerator) + divisor) // (2 * divisor)
    return -magnitude if numerator < 0 else magnitude
