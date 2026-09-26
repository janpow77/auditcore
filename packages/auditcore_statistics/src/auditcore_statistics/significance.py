"""Optional significance measures of a Benford result: chi-square test and z per digit.

Both measures are derived from a :class:`~auditcore_statistics.BenfordResult`
for one digit test (``first``, ``first_two``, ``second``) and never re-parse
the values. Nothing is decided without an explicitly supplied parameter:

* :func:`chi_square_test` reports statistic, degrees of freedom, p-value and
  the critical values of the chi-square distribution at the conventional
  levels 0.10, 0.05 and 0.01 (plus the requested level). A decision
  (``rejects``) exists only for an explicitly given ``significance_level``.
* :func:`digit_z_test` reports ``z = |p − p₀| / √(p₀(1 − p₀)/n)`` per digit,
  optionally with Nigrini's continuity correction. Digits are marked only
  against an explicitly given ``z_critical``.

The values equal those of flowinvoice's fraud check (see
``tools/capture_flowinvoice_significance.py`` and
``tests/test_significance_parity.py``). Marked digits are statistics, not
audit findings about records.
"""

from __future__ import annotations

from dataclasses import dataclass

from .benford import BenfordResult, StatisticsInputError
from .conformity import Test, digit_counts, z_statistic
from .numeric import chi2_survival, numpy_pairwise_sum

#: Conventional levels whose critical values are always reported.
STANDARD_LEVELS: tuple[float, ...] = (0.10, 0.05, 0.01)
_BISECTION_STEPS = 200


def _check_level(level: float, name: str) -> None:
    if isinstance(level, bool) or not isinstance(level, (int, float)) or not 0 < level < 1:
        raise StatisticsInputError(f"'{name}' muss zwischen 0 und 1 liegen.")


def chi2_critical_value(degrees_of_freedom: int, level: float) -> float:
    """Quantile x with P(X ≥ x) = level for a chi-square distribution (bisection).

    The interval is halved until it no longer shrinks, so the result is the
    float at which :func:`chi2_survival` crosses ``level``.
    """
    if isinstance(degrees_of_freedom, bool) or degrees_of_freedom < 1:
        raise StatisticsInputError("Die Freiheitsgrade müssen mindestens 1 betragen.")
    _check_level(level, "level")
    low, high = 0.0, float(degrees_of_freedom)
    while chi2_survival(high, degrees_of_freedom) > level:
        low, high = high, high * 2
    for _ in range(_BISECTION_STEPS):
        middle = (low + high) / 2
        if middle in (low, high):
            break
        if chi2_survival(middle, degrees_of_freedom) > level:
            low = middle
        else:
            high = middle
    return high


@dataclass(frozen=True)
class CriticalValue:
    """Critical value of the chi-square distribution at one level."""

    level: float
    value: float


@dataclass(frozen=True)
class ChiSquareTest:
    """Pearson chi-square test of one digit test against Benford's law."""

    test: Test
    analysed: int
    chi2_statistic: float
    degrees_of_freedom: int
    p_value: float
    significance_level: float | None
    critical_values: tuple[CriticalValue, ...]

    @property
    def critical_value(self) -> float | None:
        """Critical value at the chosen level; ``None`` without a level."""
        chosen = self.significance_level
        return next((c.value for c in self.critical_values if c.level == chosen), None)

    @property
    def rejects(self) -> bool | None:
        """True if p < chosen level (null hypothesis rejected); ``None`` without a level."""
        if self.significance_level is None:
            return None
        return self.p_value < self.significance_level

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible result."""
        return {
            "test": self.test,
            "analysed": self.analysed,
            "chi2_statistic": self.chi2_statistic,
            "degrees_of_freedom": self.degrees_of_freedom,
            "p_value": self.p_value,
            "significance_level": self.significance_level,
            "critical_value": self.critical_value,
            "rejects": self.rejects,
            "critical_values": [{"level": c.level, "value": c.value} for c in self.critical_values],
        }


def _levels(significance_level: float | None) -> tuple[float, ...]:
    if significance_level is None or significance_level in STANDARD_LEVELS:
        return STANDARD_LEVELS
    return tuple(sorted((*STANDARD_LEVELS, significance_level), reverse=True))


def chi_square_test(
    result: BenfordResult, test: Test, *, significance_level: float | None = None
) -> ChiSquareTest:
    """Chi-square statistic, p-value and critical values of ``test`` (see module docstring).

    Raises:
        StatisticsInputError: invalid level or digits not matching the test.
    """
    if significance_level is not None:
        _check_level(significance_level, "significance_level")
    counts = digit_counts(result, test)
    n = result.analysed
    statistic = numpy_pairwise_sum(
        [(count - share * n) ** 2 / (share * n) for _, count, share in counts]
    )
    dof = len(counts) - 1
    return ChiSquareTest(
        test=test,
        analysed=n,
        chi2_statistic=statistic,
        degrees_of_freedom=dof,
        p_value=chi2_survival(statistic, dof),
        significance_level=significance_level,
        critical_values=tuple(
            CriticalValue(level, chi2_critical_value(dof, level))
            for level in _levels(significance_level)
        ),
    )


@dataclass(frozen=True)
class DigitZ:
    """z statistic of one digit (group)."""

    digit: int
    observed_count: int
    observed_share: float
    expected_share: float
    z: float
    exceeds: bool | None

    @property
    def deviation(self) -> float:
        """Observed minus expected share (sign gives the direction)."""
        return self.observed_share - self.expected_share


@dataclass(frozen=True)
class DigitZTest:
    """z per digit and the digits above an explicitly chosen critical value."""

    test: Test
    analysed: int
    continuity_correction: bool
    z_critical: float | None
    rows: tuple[DigitZ, ...]

    @property
    def exceeding_digits(self) -> tuple[int, ...] | None:
        """Digits with z > ``z_critical`` in digit order; ``None`` without a critical value."""
        if self.z_critical is None:
            return None
        return tuple(r.digit for r in self.rows if r.exceeds)

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible result."""
        exceeding = self.exceeding_digits
        return {
            "test": self.test,
            "analysed": self.analysed,
            "continuity_correction": self.continuity_correction,
            "z_critical": self.z_critical,
            "exceeding_digits": None if exceeding is None else list(exceeding),
            "rows": [
                {
                    "digit": r.digit,
                    "observed_count": r.observed_count,
                    "observed_share": r.observed_share,
                    "expected_share": r.expected_share,
                    "deviation": r.deviation,
                    "z": r.z,
                    "exceeds": r.exceeds,
                }
                for r in self.rows
            ],
        }


def digit_z_test(
    result: BenfordResult,
    test: Test,
    *,
    continuity_correction: bool,
    z_critical: float | None = None,
) -> DigitZTest:
    """z per digit of ``test``; digits are marked only against an explicit ``z_critical``.

    Raises:
        StatisticsInputError: non-boolean correction, non-positive critical value
            or digits not matching the test.
    """
    if not isinstance(continuity_correction, bool):
        raise StatisticsInputError("'continuity_correction' muss true oder false sein.")
    if z_critical is not None and (
        isinstance(z_critical, bool) or not isinstance(z_critical, (int, float)) or z_critical <= 0
    ):
        raise StatisticsInputError("'z_critical' muss eine positive Zahl sein.")
    n = result.analysed
    rows = []
    for digit, count, expected in digit_counts(result, test):
        share = count / n
        z = z_statistic(share, expected, n, correction=continuity_correction)
        rows.append(
            DigitZ(digit, count, share, expected, z, None if z_critical is None else z > z_critical)
        )
    return DigitZTest(
        test=test,
        analysed=n,
        continuity_correction=continuity_correction,
        z_critical=None if z_critical is None else float(z_critical),
        rows=tuple(rows),
    )
