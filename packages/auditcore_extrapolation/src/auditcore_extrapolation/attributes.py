"""Attribute sampling for tests of controls in system audits (guidance section 7.9).

Evaluation only (the sample size of section 7.9.2 is planning and belongs to
``auditcore_sampling``):

* extrapolated deviation rate EDR = deviations / n (7.9.3),
* precision SE = z × √(p_s × (1 − p_s) / n) (7.9.4),
* upper deviation limit ULD = EDR + SE, compared with the tolerable
  deviation rate T set by the audit authority (7.9.5).

The guidance prints SE = z × p_s × (1 − p_s) / √n without the square root and
its example follows the misprint (ULD 0.023 for 3 deviations in 150 at 95 %);
the normal approximation of the binomial distribution that the section refers
to has the square root (ULD 0.042). The library uses the square root; see
docs/referenzfaelle.md. The guidance itself calls this chapter general
information – statistical attribute sampling is not mandatory for system
audits.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .errors import ExtrapolationInputError
from .factors import profile, z_value
from .sources import Step, guidance

SUPPORTED = "supported"
NOT_SUPPORTED = "not_supported"


@dataclass(frozen=True)
class AttributeEvaluation:
    """Deviation rate, precision and upper deviation limit of an attribute sample."""

    deviations: int
    sample_size: int
    confidence_level: float
    factor_profile: str
    coefficient: float
    rate: float
    precision: float
    upper_limit: float
    tolerable_rate: float
    conclusion: str
    steps: tuple[Step, ...]

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible result."""
        return {
            "deviations": self.deviations,
            "sample_size": self.sample_size,
            "confidence_level": self.confidence_level,
            "factor_profile": self.factor_profile,
            "coefficient": self.coefficient,
            "rate": self.rate,
            "precision": self.precision,
            "upper_limit": self.upper_limit,
            "tolerable_rate": self.tolerable_rate,
            "conclusion": self.conclusion,
            "steps": [s.to_dict() for s in self.steps],
        }


def _whole(value: object, name: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ExtrapolationInputError(f"{name} muss eine ganze Zahl ≥ {minimum} sein.")
    return value


def evaluate_attributes(
    deviations: int,
    sample_size: int,
    *,
    confidence_level: float,
    factor_profile: str,
    tolerable_rate: float,
) -> AttributeEvaluation:
    """Evaluate a test of controls by attribute sampling (guidance sections 7.9.3–7.9.5).

    ``conclusion`` is ``supported`` if ULD ≤ T (the sample supports the
    assurance criterion), else ``not_supported``.
    """
    n = _whole(sample_size, "Der Stichprobenumfang", 1)
    k = _whole(deviations, "Die Zahl der Abweichungen", 0)
    if k > n:
        raise ExtrapolationInputError("Mehr Abweichungen als geprüfte Elemente.")
    if not math.isfinite(tolerable_rate) or not 0 < tolerable_rate < 1:
        raise ExtrapolationInputError(
            "Die tolerierbare Abweichungsquote muss zwischen 0 und 1 liegen."
        )
    profile(factor_profile)
    z = z_value(confidence_level, factor_profile)
    rate = k / n
    se = z * math.sqrt(rate * (1 - rate) / n)
    upper = rate + se
    steps = (
        Step("Abweichungsquote (EDR)", "Abweichungen / n", rate, guidance("7.9.3")),
        Step("Präzision", "SE = z × √(p_s × (1 − p_s) / n)", se, guidance("7.9.4")),
        Step("Obere Abweichungsgrenze (ULD)", "ULD = EDR + SE", upper, guidance("7.9.5")),
    )
    conclusion = SUPPORTED if upper <= tolerable_rate else NOT_SUPPORTED
    return AttributeEvaluation(
        k,
        n,
        confidence_level,
        factor_profile,
        z,
        rate,
        se,
        upper,
        tolerable_rate,
        conclusion,
        steps,
    )
