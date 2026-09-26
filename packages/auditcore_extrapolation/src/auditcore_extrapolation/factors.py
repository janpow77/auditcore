"""Confidence coefficients: z values and Poisson reliability factors.

Two named profiles, never chosen silently:

* ``kom_2017_tables`` – the values exactly as printed in the guidance
  (Table 3 for z, Table 4 for the basic reliability factor of the MUS
  conservative approach, Appendix 3 for the reliability factor of the k-th
  error). Only the confidence levels of these tables are allowed.
* ``exact`` – the same quantities computed without rounding: z is the
  two-sided quantile of the standard normal distribution (the guidance's z
  for 80 % is 1.282 = Φ⁻¹(0.90)), the reliability factor is the upper Poisson
  limit λ with P(X ≤ k | λ) = 1 − confidence level. Any level in (0, 1).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist
from types import MappingProxyType

from . import _rf_table
from .errors import ExtrapolationInputError
from .sources import guidance

KOM_TABLES = "kom_2017_tables"
EXACT = "exact"

#: Table 3 of the guidance (section 5.3): z by confidence level.
Z_TABLE = MappingProxyType({0.60: 0.842, 0.70: 1.036, 0.80: 1.282, 0.90: 1.645, 0.95: 1.960})
#: Table 4 of the guidance (section 6.3.5.2): reliability factor for zero errors.
RF_ZERO_TABLE = MappingProxyType(
    {
        0.99: 4.61,
        0.95: 3.00,
        0.90: 2.31,
        0.85: 1.90,
        0.80: 1.61,
        0.75: 1.39,
        0.70: 1.21,
        0.60: 0.92,
        0.50: 0.70,
    }
)
MAX_ERRORS_EXACT = 5_000


@dataclass(frozen=True)
class FactorProfile:
    """A named source of z values and reliability factors."""

    id: str
    label: str
    source: str
    note: str

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible profile description."""
        return {"id": self.id, "label": self.label, "source": self.source, "note": self.note}


PROFILES = MappingProxyType(
    {
        KOM_TABLES: FactorProfile(
            KOM_TABLES,
            "Tabellenwerte des KOM-Leitfadens",
            f"{guidance('5.3')} (Tabelle 3), {guidance('6.3.5.2')} (Tabelle 4), Anhang 3",
            "Werte wie gedruckt; nur die dort genannten Konfidenzniveaus.",
        ),
        EXACT: FactorProfile(
            EXACT,
            "Exakt berechnete Werte",
            "Normalverteilung (zweiseitiges Quantil) und Poisson-Obergrenze",
            "Ungerundet; jedes Konfidenzniveau in (0, 1). Weicht in der 3. Nachkommastelle "
            "von den Tabellen ab.",
        ),
    }
)
RECOMMENDED_PROFILE = KOM_TABLES


def profile(profile_id: str) -> FactorProfile:
    """The explicitly named factor profile."""
    found = PROFILES.get(profile_id)
    if found is None:
        allowed = ", ".join(sorted(PROFILES))
        raise ExtrapolationInputError(
            f"Unbekanntes Faktorprofil '{profile_id}'. Zulässig: {allowed}."
        )
    return found


def _level(confidence_level: float) -> float:
    if isinstance(confidence_level, bool) or not isinstance(confidence_level, (int, float)):
        raise ExtrapolationInputError("Das Konfidenzniveau muss eine Zahl sein.")
    if not 0 < confidence_level < 1 or not math.isfinite(confidence_level):
        raise ExtrapolationInputError("Das Konfidenzniveau muss in (0, 1) liegen.")
    return round(float(confidence_level), 6)


def _lookup(table: MappingProxyType[float, float], level: float, name: str) -> float:
    try:
        return table[level]
    except KeyError as exc:
        allowed = ", ".join(f"{k:.0%}" for k in sorted(table))
        raise ExtrapolationInputError(
            f"Konfidenzniveau {level:.2%} ist in {name} nicht enthalten; zulässig: {allowed}. "
            "Für andere Niveaus das Profil 'exact' wählen."
        ) from exc


def z_value(confidence_level: float, profile_id: str) -> float:
    """z coefficient of the precision formulas.

    Source: guidance section 5.3, Table 3 (profile ``kom_2017_tables``);
    ``exact``: z = Φ⁻¹(1 − (1 − CL)/2).
    """
    level = _level(confidence_level)
    if profile(profile_id).id == KOM_TABLES:
        return _lookup(Z_TABLE, level, "Tabelle 3 des Leitfadens")
    return NormalDist().inv_cdf(1 - (1 - level) / 2)


def poisson_cdf(errors: int, mean: float) -> float:
    """P(X ≤ errors) for X ~ Poisson(mean), summed in log space."""
    if mean == 0:
        return 1.0
    log_mean = math.log(mean)
    return math.fsum(math.exp(-mean + j * log_mean - math.lgamma(j + 1)) for j in range(errors + 1))


def poisson_factor(errors: int, confidence_level: float) -> float:
    """Upper Poisson limit λ with P(X ≤ errors | λ) = 1 − CL (exact Appendix 3 factor)."""
    level = _level(confidence_level)
    if isinstance(errors, bool) or not isinstance(errors, int) or errors < 0:
        raise ExtrapolationInputError("Die Fehlerzahl muss eine ganze Zahl ≥ 0 sein.")
    if errors > MAX_ERRORS_EXACT:
        raise ExtrapolationInputError(f"Höchstens {MAX_ERRORS_EXACT} Fehler je Berechnung.")
    target = 1 - level
    low, high = 0.0, errors + 10 * math.sqrt(errors + 1) + 50
    for _ in range(200):
        middle = (low + high) / 2
        if poisson_cdf(errors, middle) > target:
            low = middle
        else:
            high = middle
        if high - low < 1e-12:
            break
    return (low + high) / 2


def basic_reliability_factor(confidence_level: float, profile_id: str) -> float:
    """Reliability factor for zero errors (basic precision, conservative MUS).

    Source: guidance section 6.3.5.2, Table 4 (``kom_2017_tables``).
    """
    level = _level(confidence_level)
    if profile(profile_id).id == KOM_TABLES:
        return _lookup(RF_ZERO_TABLE, level, "Tabelle 4 des Leitfadens")
    return poisson_factor(0, level)


def reliability_factor(errors: int, confidence_level: float, profile_id: str) -> float:
    """Reliability factor RF(k) for the k-th error (incremental allowance).

    Source: guidance Appendix 3 (``kom_2017_tables``, k ≤ 50) as used in the
    worked example of section 6.3.5.7.
    """
    level = _level(confidence_level)
    if profile(profile_id).id == EXACT:
        return poisson_factor(errors, level)
    if level not in _rf_table.LEVELS:
        allowed = ", ".join(f"{k:.0%}" for k in _rf_table.LEVELS)
        raise ExtrapolationInputError(
            f"Konfidenzniveau {level:.2%} fehlt in Anhang 3 des Leitfadens; zulässig: {allowed}."
        )
    if isinstance(errors, bool) or not isinstance(errors, int) or not 0 <= errors <= 50:
        raise ExtrapolationInputError(
            "Anhang 3 des Leitfadens enthält Faktoren für 0 bis 50 Fehler; bei mehr Fehlern "
            "das Profil 'exact' wählen."
        )
    return _rf_table.ROWS[errors][_rf_table.LEVELS.index(level)]
