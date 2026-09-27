"""Recalculation of the confidence level for inconclusive results (guidance section 7.7).

If the total error is below and the upper limit above the materiality
threshold, the audit authority may compute the confidence level at which the
result would be conclusive:

    z* = z × (TE − EE) / SE,   confidence level* = 1 − 2 × (1 − Φ(z*))

With delimited systemic or uncorrected anomalous errors the upper limit is
TER + SE (Appendix 1), so the total error takes the place of EE; without
them both coincide. If the recalculated level is still compatible with the
assessment of the management and control system (Table 1 of section 3.2.1),
the population is not materially misstated without further audit work;
otherwise the additional work of section 4.12 is needed.

The recalculation presupposes a precision of the form z × (…); the MUS
conservative approach (reliability factors, section 6.3.5) and
non-statistical samples are therefore excluded.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist
from types import MappingProxyType

from .errors import ExtrapolationInputError
from .evaluation import INCONCLUSIVE, TotalErrorRate
from .projection import Projection
from .sources import Step, guidance

#: Table 1 of section 3.2.1: category of the system assessment → confidence level.
SYSTEM_ASSESSMENT_LEVELS = MappingProxyType({1: 0.60, 2: 0.70, 3: 0.80, 4: 0.90})
SYSTEM_ASSESSMENT_LABELS = MappingProxyType(
    {
        1: "Funktioniert gut, allenfalls geringfügige Verbesserungen nötig",
        2: "Funktioniert, einige Verbesserungen nötig",
        3: "Funktioniert teilweise, erhebliche Verbesserungen nötig",
        4: "Funktioniert im Wesentlichen nicht",
    }
)


def system_confidence_level(category: int) -> float:
    """Confidence level for a system assessment category 1–4 (section 3.2.1, Table 1).

    For a group of programmes the most demanding category applies (section 3.2.2).
    """
    if isinstance(category, bool) or category not in SYSTEM_ASSESSMENT_LEVELS:
        raise ExtrapolationInputError(
            "Die Bewertung des Verwaltungs- und Kontrollsystems ist eine Kategorie 1 bis 4 "
            "(Leitfaden, Abschn. 3.2.1, Tabelle 1)."
        )
    return SYSTEM_ASSESSMENT_LEVELS[category]


@dataclass(frozen=True)
class ConfidenceRecalculation:
    """Result of section 7.7; ``applicable`` False names the ``reason``."""

    applicable: bool
    reason: str | None
    coefficient: float | None = None
    recalculated_coefficient: float | None = None
    confidence_level: float | None = None
    required_level: float | None = None
    supports_not_material: bool | None = None
    steps: tuple[Step, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible result."""
        return {
            "applicable": self.applicable,
            "reason": self.reason,
            "coefficient": self.coefficient,
            "recalculated_coefficient": self.recalculated_coefficient,
            "confidence_level": self.confidence_level,
            "required_level": self.required_level,
            "supports_not_material": self.supports_not_material,
            "steps": [s.to_dict() for s in self.steps],
        }


def recalculated_level(
    coefficient: float, tolerable: float, total: float, precision: float
) -> tuple[float, float]:
    """(z*, level*) with z* = z × (TE − EE) / SE and level* = 2Φ(z*) − 1 (section 7.7)."""
    values = (coefficient, tolerable, total, precision)
    if any(not math.isfinite(v) for v in values) or precision <= 0 or coefficient <= 0:
        raise ExtrapolationInputError("z und Präzision müssen endlich und größer als 0 sein.")
    z_star = coefficient * (tolerable - total) / precision
    return z_star, 2 * NormalDist().cdf(z_star) - 1


def _not_applicable(projection: Projection, ter: TotalErrorRate) -> str | None:
    if projection.precision is None or projection.coefficient is None:
        return "Nicht-statistische Stichprobe: keine Präzision, keine Neuberechnung."
    if projection.method == "mus.conservative":
        return (
            "Konservativer MUS-Ansatz: Die Präzision beruht auf Zuverlässigkeitsfaktoren, nicht "
            "auf z; Abschn. 7.7 ist nicht anwendbar."
        )
    if ter.conclusion != INCONCLUSIVE:
        return "Das Ergebnis ist bereits schlüssig; eine Neuberechnung ist nicht nötig."
    return None


def recalculate_confidence(
    projection: Projection, ter: TotalErrorRate, *, required_level: float | None = None
) -> ConfidenceRecalculation:
    """Confidence level at which an inconclusive result becomes conclusive (section 7.7).

    ``required_level`` is the confidence level compatible with the system
    assessment (e.g. :func:`system_confidence_level`); with it the result
    states whether the recalculated level supports "not material".
    """
    if required_level is not None and not 0 < required_level < 1:
        raise ExtrapolationInputError("Das verlangte Konfidenzniveau muss zwischen 0 und 1 liegen.")
    reason = _not_applicable(projection, ter)
    if reason is not None or projection.precision is None or projection.coefficient is None:
        return ConfidenceRecalculation(False, reason, required_level=required_level)
    z = projection.coefficient
    z_star, level = recalculated_level(
        z, ter.tolerable_error, ter.total_error, projection.precision
    )
    source = guidance("7.7")
    steps = (
        Step("Neuer z-Wert", "z* = z × (TE − Gesamtfehler) / SE", z_star, source),
        Step("Neu berechnetes Konfidenzniveau", "1 − 2 × (1 − Φ(z*))", level, source),
    )
    supports = None if required_level is None else level >= required_level - 1e-12
    return ConfidenceRecalculation(True, None, z, z_star, level, required_level, supports, steps)
