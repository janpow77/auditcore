"""Reduction, co-financing and own-contribution shares in exact integer cents.

A rate is an exact fraction ``numerator / denominator`` (e.g. ``Decimal("0.4")``
becomes 2/5); amounts are int64 cents. Each share is rounded commercially
(half away from zero) once per row, and the complementary amount is derived by
subtraction so that both parts always add up to the original cent amount.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction

import numpy as np
import numpy.typing as npt

from ._buffers import cents_input
from ._engine import accelerate, jitable, prange
from ._intmath import MAX_DENOMINATOR, div_round, mul_div_round

RateInput = Fraction | Decimal | str | int | float

#: Status codes of ``check_quota``.
QUOTA_OK = 0
QUOTA_BELOW_MINIMUM = 1
QUOTA_ABOVE_MAXIMUM = 2
QUOTA_UNDEFINED = 3


def rate(value: RateInput) -> Fraction:
    """Exact rate between 0 and 1 (``"0.4"``, ``Decimal("0.4")``, ``Fraction(2, 5)``).

    Floats go through ``Decimal(str(value))``. The reduced denominator may not
    exceed 10**6 (covers six decimal places and fractions such as 1/3).
    """
    if isinstance(value, bool) or not isinstance(value, (Fraction, Decimal, str, int, float)):
        raise TypeError(f"{type(value).__name__} ist keine Quote.")
    exact = Fraction(Decimal(str(value))) if isinstance(value, float) else Fraction(value)
    if not 0 <= exact <= 1:
        raise ValueError(f"Quote {value} liegt nicht zwischen 0 und 1.")
    if exact.denominator > MAX_DENOMINATOR:
        raise ValueError(f"Quote {value}: Nenner höchstens 10**6 (z. B. sechs Nachkommastellen).")
    return exact


def percent(value: Decimal | str | int) -> Fraction:
    """Rate from a percentage (``percent("40")`` is 2/5)."""
    return rate(Fraction(Decimal(str(value))) / 100)


def _rate_buffers(
    rates: RateInput | Sequence[RateInput], size: int
) -> tuple[npt.NDArray[np.int64], npt.NDArray[np.int64]]:
    if isinstance(rates, (Fraction, Decimal, str, int, float)):
        single = rate(rates)
        return (
            np.full(size, single.numerator, dtype=np.int64),
            np.full(size, single.denominator, dtype=np.int64),
        )
    exact = [rate(r) for r in rates]
    if len(exact) != size:
        raise ValueError("Je Betrag ist genau eine Quote anzugeben.")
    numerators = np.array([r.numerator for r in exact], dtype=np.int64)
    return numerators, np.array([r.denominator for r in exact], dtype=np.int64)


@accelerate(parallel=True)
def share_kernel(
    amounts: npt.NDArray[np.int64],
    numerators: npt.NDArray[np.int64],
    denominators: npt.NDArray[np.int64],
    out: npt.NDArray[np.int64],
) -> None:
    """Element-wise ``amount * numerator / denominator`` rounded half away from zero."""
    for i in prange(amounts.shape[0]):
        out[i] = mul_div_round(amounts[i], numerators[i], denominators[i])


def share_cents(
    amounts_cents: object, rates: RateInput | Sequence[RateInput]
) -> npt.NDArray[np.int64]:
    """Share of each amount (one rate for all rows or one per row), in cents."""
    amounts = cents_input(amounts_cents, "Betrag")
    numerators, denominators = _rate_buffers(rates, amounts.shape[0])
    out = np.zeros(amounts.shape, dtype=np.int64)
    share_kernel(amounts, numerators, denominators, out)
    return out


@dataclass(frozen=True)
class Split:
    """An amount split into a rounded share and the exact remainder (both in cents)."""

    share: npt.NDArray[np.int64]
    rest: npt.NDArray[np.int64]


def apply_reduction(
    amounts_cents: object, reduction_rate: RateInput | Sequence[RateInput]
) -> Split:
    """Reduction amount (``share``) and remaining eligible amount (``rest``) per row."""
    amounts = cents_input(amounts_cents, "Betrag")
    share = share_cents(amounts, reduction_rate)
    return Split(share, amounts - share)


def cofinancing(eligible_cents: object, funding_rate: RateInput | Sequence[RateInput]) -> Split:
    """Funding (``share``) and own contribution (``rest``) of the eligible costs."""
    return apply_reduction(eligible_cents, funding_rate)


@dataclass(frozen=True)
class QuotaCheck:
    """Actual quota in basis points (rounded) and an exact threshold status per row."""

    basis_points: npt.NDArray[np.int64]
    status: npt.NDArray[np.int8]


@accelerate(parallel=True)
def quota_kernel(
    parts: npt.NDArray[np.int64],
    totals: npt.NDArray[np.int64],
    bounds: npt.NDArray[np.int64],
    basis_points: npt.NDArray[np.int64],
    status: npt.NDArray[np.int8],
) -> None:
    """Element-wise quota ``part / total``; see ``_bounds`` for the bound layout."""
    for i in prange(parts.shape[0]):
        part = parts[i]
        total = totals[i]
        if total <= 0:
            basis_points[i] = 0
            status[i] = 3
        else:
            basis_points[i] = div_round(part * 10000, total)
            status[i] = _quota_status(part, total, bounds)


@jitable
def _quota_status(part: int, total: int, bounds: npt.NDArray[np.int64]) -> int:
    if bounds[0] == 1 and part * bounds[2] < total * bounds[1]:
        return 1
    if bounds[3] == 1 and part * bounds[5] > total * bounds[4]:
        return 2
    return 0


def _bounds(minimum: RateInput | None, maximum: RateInput | None) -> npt.NDArray[np.int64]:
    """``[has_min, min_num, min_den, has_max, max_num, max_den]`` as exact integers."""
    low = rate(minimum) if minimum is not None else Fraction(0)
    high = rate(maximum) if maximum is not None else Fraction(1)
    flags = (int(minimum is not None), int(maximum is not None))
    values = (flags[0], low.numerator, low.denominator, flags[1], high.numerator, high.denominator)
    return np.array(values, dtype=np.int64)


def check_quota(
    parts_cents: object,
    totals_cents: object,
    *,
    minimum: RateInput | None = None,
    maximum: RateInput | None = None,
) -> QuotaCheck:
    """Quota ``part / total`` per row with an exact comparison against the thresholds.

    Status: ``QUOTA_OK``, ``QUOTA_BELOW_MINIMUM``, ``QUOTA_ABOVE_MAXIMUM`` or
    ``QUOTA_UNDEFINED`` (total ≤ 0). The thresholds are inputs of the caller
    (e.g. the maximum funding rate of a funding guideline); none is built in.
    Basis points are only for display; the status never uses the rounded value.
    """
    parts = cents_input(parts_cents, "Anteil")
    totals = cents_input(totals_cents, "Gesamtbetrag")
    if parts.shape != totals.shape:
        raise ValueError("Anteile und Gesamtbeträge müssen gleich lang sein.")
    points = np.zeros(parts.shape, dtype=np.int64)
    status = np.zeros(parts.shape, dtype=np.int8)
    quota_kernel(parts, totals, _bounds(minimum, maximum), points, status)
    return QuotaCheck(points, status)
