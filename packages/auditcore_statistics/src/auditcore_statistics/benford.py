"""Benford first-digit and first-two-digit distribution with a chi-square statistic.

The result is a descriptive statistic. It names the method profile, reports
every excluded value and never classifies records or data sets as suspicious;
a significance statement is only made for an explicitly supplied level.

Leading digits follow the mathematical definition of Benford's law: the
significand of x > 0 is x / 10^floor(log10 x), and its first two digits are
the first-two-digit group (Hill 1995, *A statistical derivation of the
significant-digit law*; Berger/Hill 2015, *An Introduction to Benford's
Law*, ch. 2). Trailing zeros of the integer part are digits: 500 belongs to
group 50, 1 000 and 10,00 to group 10. Round amounts therefore stay in the
first-two digits test, where their clustering at 10, 20, 50 … is exactly the
pattern the test is meant to show (Nigrini 2012, ch. 5).

``legacy_run_benford`` reproduces ``flowstat@d665ac2``
``analysis_core_service.run_benford`` exactly, including its behavior that
this contract corrects (see ``docs/behavior-changes.md``).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Literal

from ._legacy_flowstat import LEGACY_METHOD, legacy_run_benford
from ._legacy_flowstat import LegacyDtype as LegacyDtype  # import path before 0.5.0
from .numeric import chi2_survival, numpy_pairwise_sum
from .numeric import numpy_round as numpy_round  # import path before 0.5.0

__all__ = [
    "LEGACY_METHOD",
    "METHOD",
    "SHORT_SHARE_WARNING",
    "BenfordResult",
    "DigitRow",
    "ShortValues",
    "StatisticsInputError",
    "benford_test",
    "expected_share",
    "legacy_run_benford",
]

#: Version 2: trailing zeros count as digits (version 1 dropped them, see CHANGELOG 0.5.0).
METHOD = "auditcore_statistics.benford/2"
ShortValues = Literal["exclude", "pad"]
#: Share of explicitly excluded single-digit values above which the result warns.
#: Application default, not a statistical norm.
SHORT_SHARE_WARNING = 0.05
_VERSION = "0.5.0"  # keep equal to __version__ (tests/test_version.py)


class StatisticsInputError(ValueError):
    """Input does not satisfy the documented contract."""


@dataclass(frozen=True)
class DigitRow:
    """Observed and expected frequency of one leading digit (group)."""

    digit: int
    observed_count: int
    observed_share: float
    expected_share: float

    @property
    def deviation(self) -> float:
        """Observed minus expected share."""
        return self.observed_share - self.expected_share


@dataclass(frozen=True)
class BenfordResult:
    """Distribution, exclusions and chi-square statistic of one analysis."""

    method: str
    digits: int
    short_values: str | None
    rows: tuple[DigitRow, ...]
    analysed: int
    missing: int
    zero: int
    negative_absolute: int
    short_excluded: int
    chi2_statistic: float
    degrees_of_freedom: int
    p_value: float
    significance_level: float | None
    #: Explicit lower bound on the absolute value; ``None`` without a bound.
    lower_bound: float | None = None
    below_lower_bound: int = 0
    warnings: tuple[str, ...] = ()

    @property
    def deviates_at_level(self) -> bool | None:
        """True if p < explicitly given level; ``None`` without a level."""
        if self.significance_level is None:
            return None
        return self.p_value < self.significance_level

    @property
    def short_share(self) -> float:
        """Excluded single-digit values relative to all values that reached the digit step."""
        considered = self.analysed + self.short_excluded
        return self.short_excluded / considered if considered else 0.0

    def to_dict(self) -> dict[str, Any]:
        """JSON-compatible result including exclusion counts and warnings."""
        return {
            "library": f"auditcore_statistics {_VERSION}",
            "method": self.method,
            "digits": self.digits,
            "short_values": self.short_values,
            "lower_bound": self.lower_bound,
            "analysed": self.analysed,
            "excluded": {
                "missing": self.missing,
                "zero": self.zero,
                "short": self.short_excluded,
                "below_lower_bound": self.below_lower_bound,
            },
            "short_share": self.short_share,
            "negative_absolute": self.negative_absolute,
            "chi2_statistic": self.chi2_statistic,
            "degrees_of_freedom": self.degrees_of_freedom,
            "p_value": self.p_value,
            "significance_level": self.significance_level,
            "deviates_at_level": self.deviates_at_level,
            "warnings": list(self.warnings),
            "rows": [
                {
                    "digit": r.digit,
                    "observed_count": r.observed_count,
                    "observed_share": r.observed_share,
                    "expected_share": r.expected_share,
                    "deviation": r.deviation,
                }
                for r in self.rows
            ],
        }


def expected_share(digit: int) -> float:
    """Benford probability log10(1 + 1/d) of a leading digit group d."""
    return math.log10(1 + 1 / digit)


def _significant_digits(value: int | float | Decimal) -> str:
    """Digits of a positive finite number from its first non-zero digit on.

    The value is read exactly (floats via their shortest repr), without
    rounding to a context precision, so 5, 5.0 and Decimal("5.00") give the
    same digits and 10**29 − 1 stays "999…". Zeros of the integer part are
    kept: 500 → "500", 1E+3 → "100…", 10.00 → "10"; only zeros after the
    decimal point are dropped, they do not change the significand.
    """
    text = repr(value) if isinstance(value, float) else str(value)
    _, raw, exponent = Decimal(text).as_tuple()
    digits = list(raw)
    places = exponent if isinstance(exponent, int) else 0
    while places < 0 and len(digits) > 1 and digits[-1] == 0:
        digits.pop()
        places += 1
    # Two digits suffice for every test; capping the zeros keeps 1e300 cheap.
    written = "".join(str(d) for d in digits) + "0" * min(max(places, 0), 2)
    return written.lstrip("0")


def _check_options(
    digits: int,
    short_values: ShortValues | None,
    significance_level: float | None,
    lower_bound: float | None,
) -> None:
    if isinstance(digits, bool) or digits not in (1, 2):
        raise StatisticsInputError("'digits' muss 1 oder 2 sein.")
    if digits == 2 and short_values not in (None, "exclude", "pad"):
        raise StatisticsInputError("'short_values' ist 'pad' (Standard) oder 'exclude'.")
    if digits == 1 and short_values is not None:
        raise StatisticsInputError("'short_values' gilt nur für digits=2.")
    if significance_level is not None and not 0 < significance_level < 1:
        raise StatisticsInputError("'significance_level' muss zwischen 0 und 1 liegen.")
    if lower_bound is not None and not (
        not isinstance(lower_bound, bool)
        and isinstance(lower_bound, (int, float, Decimal))
        and math.isfinite(lower_bound)
        and lower_bound > 0
    ):
        raise StatisticsInputError("'lower_bound' muss eine endliche Zahl größer als 0 sein.")


def _checked_number(value: object) -> int | float | Decimal | None:
    """Validated finite number, or ``None`` for a missing value."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise StatisticsInputError(f"Kein numerischer Wert: {value!r}.")
    if isinstance(value, float) and math.isinf(value):
        raise StatisticsInputError("Unendliche Werte sind nicht zulässig.")
    if isinstance(value, Decimal) and not value.is_finite():
        raise StatisticsInputError("Nicht endliche Dezimalwerte sind nicht zulässig.")
    return value


def _leading_group(significant: str, digits: int, short_values: ShortValues | None) -> int | None:
    """Digit group of the significant digits; ``None`` for an excluded single-digit value."""
    if digits == 1:
        return int(significant[0])
    if len(significant) >= 2:
        return int(significant[:2])
    if short_values == "exclude":
        return None
    return int(significant[0]) * 10


def _digit_rows(groups: Sequence[int], digits: int) -> tuple[DigitRow, ...]:
    domain = range(1, 10) if digits == 1 else range(10, 100)
    counts = {d: 0 for d in domain}
    for group in groups:
        counts[group] += 1
    total = len(groups)
    return tuple(DigitRow(d, counts[d], counts[d] / total, expected_share(d)) for d in domain)


def benford_test(
    values: Sequence[int | float | Decimal | None],
    *,
    digits: int,
    short_values: ShortValues | None = None,
    significance_level: float | None = None,
    lower_bound: float | None = None,
) -> BenfordResult:
    """Compare leading digits with Benford's law.

    Args:
        values: Numbers; ``None`` and NaN count as missing, zero is excluded,
            negative numbers are analysed by absolute value and counted.
        digits: 1 (first digit 1..9) or 2 (first two digits 10..99).
        short_values: Only for ``digits=2``. Default ``"pad"``: a value with
            one significant digit gets its second digit 0 (5 → 50, 0.07 → 70),
            as the significand of Benford's law defines it. ``"exclude"``
            drops such values (only d × 10^k with k ≤ 0, such as 5 or 0.3;
            never round amounts like 500, 1 000 or 10,00) and the result
            states their number, their share and, above
            :data:`SHORT_SHARE_WARNING`, a warning.
        significance_level: Optional α for ``deviates_at_level``.
        lower_bound: Optional bound on the absolute value; smaller values are
            excluded and counted as ``below_lower_bound``. Small amounts
            often follow other processes than the bulk of the data, which is
            why applications commonly analyse amounts from 10 on.

    Raises:
        StatisticsInputError: invalid digits/short_values/level/bound,
            booleans, non-numeric or infinite values, or no analysable value.
    """
    _check_options(digits, short_values, significance_level, lower_bound)
    mode: ShortValues | None = (short_values or "pad") if digits == 2 else None
    tally = _classify(values, digits, mode, lower_bound)
    if not tally.groups:
        raise StatisticsInputError("Keine auswertbaren Werte vorhanden.")
    total = len(tally.groups)
    rows = _digit_rows(tally.groups, digits)
    statistic = _chi2_statistic(rows, total)
    dof = len(rows) - 1
    return BenfordResult(
        method=METHOD,
        digits=digits,
        short_values=mode,
        rows=rows,
        analysed=total,
        missing=tally.missing,
        zero=tally.zero,
        negative_absolute=tally.negative,
        short_excluded=tally.short,
        chi2_statistic=statistic,
        degrees_of_freedom=dof,
        p_value=chi2_survival(statistic, dof),
        significance_level=significance_level,
        lower_bound=None if lower_bound is None else float(lower_bound),
        below_lower_bound=tally.below,
        warnings=_warnings(tally, total),
    )


def _warnings(tally: _Tally, total: int) -> tuple[str, ...]:
    share = tally.short / (total + tally.short)
    if share <= SHORT_SHARE_WARNING:
        return ()
    return (
        f"{tally.short} Werte mit nur einer signifikanten Ziffer ausgeschlossen "
        f"({_percent(share)} der Werte, mehr als {_percent(SHORT_SHARE_WARNING, 0)}). "
        "Der Ausschluss kann die Verteilung der ersten zwei Ziffern verzerren; mit der "
        "Standardregel 'pad' zählen diese Werte mit der zweiten Ziffer 0.",
    )


def _percent(share: float, places: int = 1) -> str:
    """German percent notation (decimal comma)."""
    return f"{share * 100:.{places}f} %".replace(".", ",")


@dataclass
class _Tally:
    """Leading digit groups plus the counts of every exclusion reason."""

    groups: list[int] = field(default_factory=list)
    missing: int = 0
    zero: int = 0
    negative: int = 0
    short: int = 0
    below: int = 0


def _classify(
    values: Sequence[int | float | Decimal | None],
    digits: int,
    short_values: ShortValues | None,
    lower_bound: float | None,
) -> _Tally:
    """Validate every value in input order and sort it into a group or an exclusion."""
    tally = _Tally()
    for value in values:
        number = _checked_number(value)
        if number is None:
            tally.missing += 1
            continue
        if number == 0:
            tally.zero += 1
            continue
        if number < 0:
            tally.negative += 1
            number = -number
        if lower_bound is not None and number < lower_bound:
            tally.below += 1
            continue
        group = _leading_group(_significant_digits(number), digits, short_values)
        if group is None:
            tally.short += 1
        else:
            tally.groups.append(group)
    return tally


def _chi2_statistic(rows: tuple[DigitRow, ...], total: int) -> float:
    """Pearson chi-square over all digit rows, summed in NumPy's pairwise order."""
    terms = [
        (row.observed_count - row.expected_share * total) ** 2 / (row.expected_share * total)
        for row in rows
    ]
    return numpy_pairwise_sum(terms)
