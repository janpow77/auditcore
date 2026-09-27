"""Confidence coefficients of the sample-size formulas of the Commission guidance.

Two named profiles, never chosen silently (the same identifiers as in
``auditcore_extrapolation``, so that planning and evaluation use one source):

* ``kom_2017_tables`` – values exactly as printed in EGESIF_16-0014-01:
  Table 3 (section 5.3) for z, Table 4 (section 6.3.5.2) for the reliability
  factor RF and Table 5 (section 6.3.5.2) for the expansion factor EF. Only the
  confidence levels of these tables are allowed.
* ``exact`` – z = Φ⁻¹(1 − (1 − CL)/2) and RF = −ln(1 − CL) (upper Poisson limit
  for zero errors), unrounded, any level in (0, 1). The expansion factor has
  no closed form in the guidance; it always comes from Table 5.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist
from types import MappingProxyType

from ..sizes import SamplingInputError
from .sources import guidance

KOM_TABLES = "kom_2017_tables"
EXACT = "exact"

#: Table 3 of the guidance (section 5.3): z by confidence level.
Z_TABLE = MappingProxyType({0.60: 0.842, 0.70: 1.036, 0.80: 1.282, 0.90: 1.645, 0.95: 1.960})
#: Table 4 of the guidance (section 6.3.5.2): reliability factor for zero errors.
RF_TABLE = MappingProxyType(
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
#: Table 5 of the guidance (section 6.3.5.2): expansion factor for expected errors.
EF_TABLE = MappingProxyType(
    {
        0.99: 1.9,
        0.95: 1.6,
        0.90: 1.5,
        0.85: 1.4,
        0.80: 1.3,
        0.75: 1.25,
        0.70: 1.2,
        0.60: 1.1,
        0.50: 1.0,
    }
)


@dataclass(frozen=True)
class FactorProfile:
    """A named source of z values, reliability and expansion factors."""

    id: str
    label: str
    source: str
    note: str

    def to_dict(self) -> dict[str, str]:
        """JSON-compatible description."""
        return {"id": self.id, "label": self.label, "source": self.source, "note": self.note}


FACTOR_PROFILES = MappingProxyType(
    {
        KOM_TABLES: FactorProfile(
            KOM_TABLES,
            "Tabellenwerte des KOM-Leitfadens",
            f"{guidance('5.3')} (Tabelle 3), {guidance('6.3.5.2')} (Tabellen 4 und 5)",
            "Werte wie gedruckt; nur die dort genannten Konfidenzniveaus.",
        ),
        EXACT: FactorProfile(
            EXACT,
            "Exakt berechnete Werte",
            "Normalverteilung (zweiseitiges Quantil), Poisson-Obergrenze bei null Fehlern",
            "Ungerundet, jedes Konfidenzniveau in (0, 1); der Expansionsfaktor bleibt "
            "Tabelle 5 des Leitfadens.",
        ),
    }
)


def factor_profile(profile_id: object) -> FactorProfile:
    """The explicitly named factor profile."""
    found = FACTOR_PROFILES.get(profile_id) if isinstance(profile_id, str) else None
    if found is None:
        allowed = ", ".join(sorted(FACTOR_PROFILES))
        raise SamplingInputError(f"Unbekanntes Faktorprofil '{profile_id}'. Zulässig: {allowed}.")
    return found


def level(confidence_level: object) -> float:
    """A confidence level in (0, 1), rounded to six places for the table lookup."""
    if (
        isinstance(confidence_level, bool)
        or not isinstance(confidence_level, (int, float))
        or not math.isfinite(confidence_level)
        or not 0 < confidence_level < 1
    ):
        raise SamplingInputError("Das Konfidenzniveau muss eine Zahl in (0, 1) sein.")
    return round(float(confidence_level), 6)


def _lookup(table: MappingProxyType[float, float], chosen: float, name: str) -> float:
    try:
        return table[chosen]
    except KeyError as exc:
        allowed = ", ".join(f"{k:.0%}" for k in sorted(table))
        raise SamplingInputError(
            f"Konfidenzniveau {chosen:.2%} ist in {name} nicht enthalten; zulässig: {allowed}. "
            "Es wird kein Ersatzwert angenommen."
        ) from exc


def z_value(confidence_level: object, profile_id: object) -> float:
    """z of the precision-based size formulas (guidance 5.3, Table 3; ``exact``: Φ⁻¹)."""
    chosen = level(confidence_level)
    if factor_profile(profile_id).id == KOM_TABLES:
        return _lookup(Z_TABLE, chosen, "Tabelle 3 des Leitfadens")
    return NormalDist().inv_cdf(1 - (1 - chosen) / 2)


def reliability_factor(confidence_level: object, profile_id: object) -> float:
    """RF for zero errors (guidance 6.3.5.2, Table 4; ``exact``: −ln(1 − CL))."""
    chosen = level(confidence_level)
    if factor_profile(profile_id).id == KOM_TABLES:
        return _lookup(RF_TABLE, chosen, "Tabelle 4 des Leitfadens")
    return -math.log(1 - chosen)


def expansion_factor(confidence_level: object) -> float:
    """EF for expected errors (guidance 6.3.5.2, Table 5) in both profiles."""
    return _lookup(EF_TABLE, level(confidence_level), "Tabelle 5 des Leitfadens")
