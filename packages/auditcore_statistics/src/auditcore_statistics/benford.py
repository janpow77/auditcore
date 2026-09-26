"""Benford first-digit and first-two-digit distribution with a chi-square statistic.

The result is a descriptive statistic. It names the method profile, reports
every excluded value and never classifies records or data sets as suspicious;
a significance statement is only made for an explicitly supplied level.

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

from .numeric import chi2_survival, numpy_pairwise_sum, numpy_round

METHOD = "auditcore_statistics.benford/1"
LEGACY_METHOD = "flowstat.run_benford@d665ac221f50ba1f465b7337bdd4aa218d78ec8a"
ShortValues = Literal["exclude", "pad"]


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

    @property
    def deviates_at_level(self) -> bool | None:
        """True if p < explicitly given level; ``None`` without a level."""
        if self.significance_level is None:
            return None
        return self.p_value < self.significance_level

    def to_dict(self) -> dict[str, Any]:
        """JSON-compatible result including exclusion counts."""
        return {
            "library": "auditcore_statistics 0.3.2",
            "method": self.method,
            "digits": self.digits,
            "short_values": self.short_values,
            "analysed": self.analysed,
            "excluded": {
                "missing": self.missing,
                "zero": self.zero,
                "short": self.short_excluded,
            },
            "negative_absolute": self.negative_absolute,
            "chi2_statistic": self.chi2_statistic,
            "degrees_of_freedom": self.degrees_of_freedom,
            "p_value": self.p_value,
            "significance_level": self.significance_level,
            "deviates_at_level": self.deviates_at_level,
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
    """Significant digits of a positive finite number, from its exact decimal form."""
    text = repr(value) if isinstance(value, float) else str(value)
    digits = "".join(str(d) for d in Decimal(text).normalize().as_tuple().digits)
    return digits.lstrip("0")


def _check_options(
    digits: int, short_values: ShortValues | None, significance_level: float | None
) -> None:
    if isinstance(digits, bool) or digits not in (1, 2):
        raise StatisticsInputError("'digits' muss 1 oder 2 sein.")
    if digits == 2 and short_values not in ("exclude", "pad"):
        raise StatisticsInputError(
            "Für die Analyse der ersten zwei Ziffern ist 'short_values' ausdrücklich "
            "als 'exclude' oder 'pad' anzugeben."
        )
    if digits == 1 and short_values is not None:
        raise StatisticsInputError("'short_values' gilt nur für digits=2.")
    if significance_level is not None and not 0 < significance_level < 1:
        raise StatisticsInputError("'significance_level' muss zwischen 0 und 1 liegen.")


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
    """Digit group of the significant digits; ``None`` for an excluded short value."""
    if digits == 1:
        return int(significant[0])
    if len(significant) >= 2:
        return int(significant[:2])
    if short_values == "pad":
        return int(significant[0]) * 10
    return None


def benford_test(
    values: Sequence[int | float | Decimal | None],
    *,
    digits: int,
    short_values: ShortValues | None = None,
    significance_level: float | None = None,
) -> BenfordResult:
    """Compare leading digits with Benford's law.

    Args:
        values: Numbers; ``None`` and NaN count as missing, zero is excluded,
            negative numbers are analysed by absolute value and counted.
        digits: 1 (first digit 1..9) or 2 (first two digits 10..99).
        short_values: Required for ``digits=2``: ``"exclude"`` values with a
            single significant digit, or ``"pad"`` them (5 → 50).
        significance_level: Optional α for ``deviates_at_level``.

    Raises:
        StatisticsInputError: invalid digits/short_values/level, booleans,
            non-numeric or infinite values, or no analysable value.
    """
    _check_options(digits, short_values, significance_level)
    tally = _classify(values, digits, short_values)
    if not tally.groups:
        raise StatisticsInputError("Keine auswertbaren Werte vorhanden.")
    total = len(tally.groups)
    domain = range(1, 10) if digits == 1 else range(10, 100)
    counts = {d: 0 for d in domain}
    for group in tally.groups:
        counts[group] += 1
    rows = tuple(DigitRow(d, counts[d], counts[d] / total, expected_share(d)) for d in domain)
    statistic = _chi2_statistic(rows, total)
    dof = len(rows) - 1
    return BenfordResult(
        method=METHOD,
        digits=digits,
        short_values=short_values,
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
    )


@dataclass
class _Tally:
    """Leading digit groups plus the counts of every exclusion reason."""

    groups: list[int] = field(default_factory=list)
    missing: int = 0
    zero: int = 0
    negative: int = 0
    short: int = 0


def _classify(
    values: Sequence[int | float | Decimal | None],
    digits: int,
    short_values: ShortValues | None,
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


# ---------------------------------------------------------------------------
# Legacy adapter (flowstat run_benford)
# ---------------------------------------------------------------------------

LegacyDtype = Literal["int", "float", "bool"]
_TOLERANCE = 1e-8


def _legacy_text(value: int | float | bool, dtype: LegacyDtype) -> str:
    if dtype == "bool":
        return str(bool(value))
    if dtype == "int":
        return str(int(value))
    return repr(float(value))


def _legacy_positive(values: Sequence[int | float | bool | None]) -> list[int | float]:
    """Absolute values above zero; ``None`` and NaN are dropped like ``dropna``."""
    positive = []
    for value in values:
        if value is None or (isinstance(value, float) and math.isnan(value)):
            continue
        absolute = abs(value)
        if absolute > 0:
            positive.append(absolute)
    if not positive:
        raise ValueError("Keine positiven Werte in der Spalte gefunden.")
    return positive


def _legacy_leading(positive: list[int | float], dtype: LegacyDtype, digit: object) -> list[int]:
    """Leading digit (group) from the source's string form; 0 for a short value."""
    leading: list[int] = []
    for value in positive:
        text = _legacy_text(value, dtype).replace(".", "").lstrip("0")
        if digit == 1:
            leading.append(int(text[0]))
        else:
            leading.append(int(text[:2]) if len(text) >= 2 else 0)
    return leading


def _legacy_row(d: int, count: int, total: int) -> tuple[dict[str, object], float]:
    """Table row of one digit and its expected count (pandas/NumPy rounding paths)."""
    expected_percent = math.log10(1 + 1 / d) * 100
    if count:
        observed_percent = count / total * 100
        observed_rounded = numpy_round(observed_percent, 2)
        deviation = numpy_round(observed_percent - expected_percent, 2)
    else:
        observed_percent = 0 / total * 100
        observed_rounded = round(observed_percent, 2)
        deviation = round(observed_percent - expected_percent, 2)
    row = {
        "digit": str(d),
        "observed_count": count,
        "observed_percent": observed_rounded,
        "expected_percent": round(expected_percent, 2),
        "deviation": deviation,
    }
    return row, (expected_percent / 100) * total


def _legacy_check_sums(observed: list[float], expected: list[float]) -> None:
    """SciPy 1.11 ``chisquare`` frequency-sum check with its original message."""
    observed_sum = numpy_pairwise_sum(observed)
    expected_sum = numpy_pairwise_sum(expected)
    relative = abs(observed_sum - expected_sum) / min(observed_sum, expected_sum)
    if relative > _TOLERANCE:
        raise ValueError(
            "For each axis slice, the sum of the observed frequencies must agree with the "
            f"sum of the expected frequencies to a relative tolerance of {_TOLERANCE}, but the "
            "percent differences are:"
            f"\n{relative!r}"
        )


def legacy_run_benford(
    values: Sequence[int | float | bool | None],
    *,
    dtype: LegacyDtype,
    digit: object,
    column: str,
) -> dict[str, Any]:
    """Exact ``run_benford`` result for values already coerced by ``pd.to_numeric``.

    ``dtype`` is the pandas dtype family of the coerced column (``int64``,
    ``float64`` or ``bool``); it determines the string form the source uses
    for digit extraction. Column/parameter checks stay with the caller.

    Raises:
        ValueError: with the source application's messages, including the
            chi-square frequency-sum error of SciPy 1.11.
    """
    if digit not in [1, 2]:
        raise ValueError("Parameter 'digit' muss 1 oder 2 sein.")
    leading = _legacy_leading(_legacy_positive(values), dtype, digit)
    domain = range(1, 10) if digit == 1 else range(10, 100)
    total = len(leading)
    counts: dict[int, int] = {}
    for d in leading:
        counts[d] = counts.get(d, 0) + 1
    rows: list[dict[str, object]] = []
    observed: list[float] = []
    expected: list[float] = []
    for d in domain:
        count = counts.get(d, 0)
        row, expected_count = _legacy_row(d, count, total)
        rows.append(row)
        observed.append(float(count))
        expected.append(expected_count)
    _legacy_check_sums(observed, expected)
    statistic = numpy_pairwise_sum(
        [(o - e) ** 2 / e for o, e in zip(observed, expected, strict=True)]
    )
    p_value = chi2_survival(statistic, len(observed) - 1)
    return {
        "type": "table",
        "columns": ["digit", "observed_count", "observed_percent", "expected_percent", "deviation"],
        "rows": rows,
        "meta": {
            "analysis": "core_benford",
            "column": column,
            "digit": digit,
            "chi2_statistic": numpy_round(statistic, 4),
            "p_value": numpy_round(p_value, 4),
            "significant": p_value < 0.05,
            "sample_size": total,
        },
    }
