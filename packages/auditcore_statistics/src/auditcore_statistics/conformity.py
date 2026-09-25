"""Benford conformity measures (MAD, z per digit, second digit) with named profiles.

The measures are derived from a :class:`~auditcore_statistics.BenfordResult`
and never re-parse the values. Assessment levels and critical values come
only from an explicitly chosen :class:`ConformityProfile`; there is no
implicit default. The labels describe how closely the distribution follows
Benford's law — they are statistics, not audit findings about records.

The second-digit test aggregates the first-two-digit groups 10..99 by their
last digit (0..9); observed counts and expected shares add up exactly.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from .benford import BenfordResult, StatisticsInputError
from .numeric import chi2_survival, numpy_pairwise_sum

Test = Literal["first", "first_two", "second"]
TESTS: tuple[Test, ...] = ("first", "first_two", "second")
AUDIT_DESIGNER_COMMIT = "2c726f3c1481775cd34aeaa83f87137d6ab12ffe"


@dataclass(frozen=True)
class ConformityProfile:
    """Named, source-bound thresholds for MAD bands, z and chi-square."""

    id: str
    label: str
    source: str
    mad_bounds: Mapping[str, tuple[float, float, float]]
    level_labels: tuple[str, str, str, str]
    z_critical: float
    continuity_correction: bool
    significance_level: float
    note: str

    def to_dict(self) -> dict[str, Any]:
        """JSON-compatible profile description."""
        return {
            "id": self.id,
            "label": self.label,
            "source": self.source,
            "mad_bounds": {k: list(v) for k, v in self.mad_bounds.items()},
            "level_labels": list(self.level_labels),
            "z_critical": self.z_critical,
            "continuity_correction": self.continuity_correction,
            "significance_level": self.significance_level,
            "note": self.note,
        }


NIGRINI_2012 = ConformityProfile(
    id="nigrini.2012",
    label="Nigrini (2012) – MAD-Bänder, z-Test je Ziffer",
    source=(
        "M. J. Nigrini: Benford's Law, Wiley 2012, Tab. 7.1 (MAD) und Gl. 4.1 (z mit "
        f"Stetigkeitskorrektur); MAD-Grenzen identisch mit janpow77/audit_designer@"
        f"{AUDIT_DESIGNER_COMMIT}:backend/app/modules/flowstat/services/"
        "audit_tests_service.py:_interpret_benford_mad"
    ),
    mad_bounds={
        "first": (0.006, 0.012, 0.015),
        "first_two": (0.0012, 0.0018, 0.0022),
        "second": (0.008, 0.010, 0.012),
    },
    level_labels=(
        "Enge Übereinstimmung",
        "Akzeptable Übereinstimmung",
        "Grenzwertig akzeptable Übereinstimmung",
        "Keine Übereinstimmung",
    ),
    z_critical=1.96,
    continuity_correction=True,
    significance_level=0.05,
    note=(
        "Grenzen je Band mit '<' (wie FlowStat). Der z-Test je Ziffer ist gegenüber "
        "FlowStat ergänzt. Eine Einstufung ist keine Feststellung."
    ),
)
PROFILES: Mapping[str, ConformityProfile] = {NIGRINI_2012.id: NIGRINI_2012}


@dataclass(frozen=True)
class DigitAssessment:
    """One digit (group) with its z statistic."""

    digit: int
    observed_count: int
    observed_share: float
    expected_share: float
    z: float
    exceeds: bool

    @property
    def deviation(self) -> float:
        """Observed minus expected share."""
        return self.observed_share - self.expected_share


@dataclass(frozen=True)
class Conformity:
    """Conformity measures of one digit test under one profile."""

    profile: str
    test: Test
    analysed: int
    rows: tuple[DigitAssessment, ...]
    mad: float
    mad_level: int
    mad_label: str
    chi2_statistic: float
    degrees_of_freedom: int
    p_value: float
    significance_level: float
    z_critical: float

    @property
    def chi2_exceeds(self) -> bool:
        """p below the profile's significance level."""
        return self.p_value < self.significance_level

    @property
    def exceeding_digits(self) -> tuple[int, ...]:
        """Digits whose |z| is above the profile's critical value."""
        return tuple(r.digit for r in self.rows if r.exceeds)

    def to_dict(self) -> dict[str, Any]:
        """JSON-compatible result."""
        return {
            "profile": self.profile,
            "test": self.test,
            "analysed": self.analysed,
            "mad": self.mad,
            "mad_level": self.mad_level,
            "mad_label": self.mad_label,
            "chi2_statistic": self.chi2_statistic,
            "degrees_of_freedom": self.degrees_of_freedom,
            "p_value": self.p_value,
            "significance_level": self.significance_level,
            "chi2_exceeds": self.chi2_exceeds,
            "z_critical": self.z_critical,
            "exceeding_digits": list(self.exceeding_digits),
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


def profile(profile_id: str) -> ConformityProfile:
    """An explicitly named profile."""
    found = PROFILES.get(profile_id)
    if found is None:
        allowed = ", ".join(sorted(PROFILES))
        raise StatisticsInputError(
            f"Unbekanntes Bewertungsprofil '{profile_id}'. Zulässig: {allowed}."
        )
    return found


def z_statistic(observed: float, expected: float, n: int, *, correction: bool) -> float:
    """z = (|p − p₀| − 1/(2n)) / √(p₀(1 − p₀)/n); correction only if smaller than |p − p₀|."""
    difference = abs(observed - expected)
    if correction and 1 / (2 * n) < difference:
        difference -= 1 / (2 * n)
    return difference / math.sqrt(expected * (1 - expected) / n)


def _counts(result: BenfordResult, test: Test) -> list[tuple[int, int, float]]:
    """(digit, observed count, expected share) for the requested test."""
    expected_digits = 1 if test == "first" else 2
    if result.digits != expected_digits:
        raise StatisticsInputError(
            f"Test '{test}' erfordert ein Ergebnis mit digits={expected_digits}."
        )
    if test != "second":
        return [(r.digit, r.observed_count, r.expected_share) for r in result.rows]
    counts = [0] * 10
    shares = [0.0] * 10
    for row in result.rows:
        counts[row.digit % 10] += row.observed_count
        shares[row.digit % 10] += row.expected_share
    return [(d, counts[d], shares[d]) for d in range(10)]


def _level(mad: float, bounds: tuple[float, float, float]) -> int:
    return next((i for i, bound in enumerate(bounds) if mad < bound), len(bounds))


def assess(result: BenfordResult, test: Test, profile_id: str) -> Conformity:
    """MAD band, z per digit and chi-square of ``result`` under the named profile.

    Raises:
        StatisticsInputError: unknown profile/test or digits not matching the test.
    """
    chosen = profile(profile_id)
    if test not in TESTS:
        raise StatisticsInputError(f"Unbekannter Test '{test}'. Zulässig: {', '.join(TESTS)}.")
    n = result.analysed
    rows = []
    for digit, count, expected in _counts(result, test):
        share = count / n
        z = z_statistic(share, expected, n, correction=chosen.continuity_correction)
        rows.append(DigitAssessment(digit, count, share, expected, z, z > chosen.z_critical))
    mad = numpy_pairwise_sum([abs(r.deviation) for r in rows]) / len(rows)
    level = _level(mad, chosen.mad_bounds[test])
    chi2 = numpy_pairwise_sum(
        [(r.observed_count - r.expected_share * n) ** 2 / (r.expected_share * n) for r in rows]
    )
    return Conformity(
        profile=chosen.id,
        test=test,
        analysed=n,
        rows=tuple(rows),
        mad=mad,
        mad_level=level,
        mad_label=chosen.level_labels[level],
        chi2_statistic=chi2,
        degrees_of_freedom=len(rows) - 1,
        p_value=chi2_survival(chi2, len(rows) - 1),
        significance_level=chosen.significance_level,
        z_critical=chosen.z_critical,
    )
