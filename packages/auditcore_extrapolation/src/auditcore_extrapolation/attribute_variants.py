"""Discovery and stop-or-go sampling for tests of controls (guidance section 7.9.6).

The guidance describes both variants only by purpose and refers to the
specialised audit sampling literature (footnote 63: AICPA Audit Guide on
Sampling). The library evaluates them with the exact one-sided binomial upper
limit of the deviation rate (Clopper–Pearson): p_u with
P(X ≤ k | n, p_u) = 1 − confidence level; for k = 0, p_u = 1 − (1 − CL)^(1/n).

* Discovery sampling: aims at detecting a single critical deviation. With no
  deviation the population deviation rate is below p_u at the confidence
  level; any deviation found is a critical case to be investigated – the
  method is not suited to project it (7.9.6).
* Stop-or-go sampling: stop as soon as the upper limit is at or below the
  tolerable rate; otherwise extend the sample (the size of the extension is
  planning, ``auditcore_sampling``).

Methodological choice of the library (the guidance gives no formula); to be
confirmed by the audit authority in its audit strategy.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .errors import ExtrapolationInputError
from .sources import Step, guidance

CRITERION_MET = "criterion_met"
DEVIATION_FOUND = "deviation_found"
STOP = "stop"
GO = "go"
SOURCE = f"{guidance('7.9.6')}; exakte Binomial-Obergrenze (Clopper-Pearson)"


def _log_pmf(k: int, n: int, p: float) -> float:
    return (
        math.lgamma(n + 1)
        - math.lgamma(k + 1)
        - math.lgamma(n - k + 1)
        + k * math.log(p)
        + (n - k) * math.log1p(-p)
    )


def binomial_cdf(k: int, n: int, p: float) -> float:
    """P(X ≤ k) for X ~ Bin(n, p)."""
    if p <= 0:
        return 1.0
    if p >= 1:
        return 1.0 if k >= n else 0.0
    return min(1.0, math.fsum(math.exp(_log_pmf(i, n, p)) for i in range(k + 1)))


def upper_deviation_limit(deviations: int, sample_size: int, confidence_level: float) -> float:
    """Exact one-sided upper limit p_u with P(X ≤ k | n, p_u) = 1 − CL (section 7.9.6)."""
    if isinstance(sample_size, bool) or not isinstance(sample_size, int) or sample_size < 1:
        raise ExtrapolationInputError("Der Stichprobenumfang muss eine ganze Zahl ≥ 1 sein.")
    if (
        isinstance(deviations, bool)
        or not isinstance(deviations, int)
        or not 0 <= deviations <= sample_size
    ):
        raise ExtrapolationInputError("Die Zahl der Abweichungen liegt zwischen 0 und n.")
    if not 0 < confidence_level < 1:
        raise ExtrapolationInputError("Das Konfidenzniveau liegt zwischen 0 und 1.")
    if deviations == sample_size:
        return 1.0
    if deviations == 0:
        return float(1 - (1 - confidence_level) ** (1 / sample_size))
    target, low, high = 1 - confidence_level, deviations / sample_size, 1.0
    for _ in range(200):
        middle = (low + high) / 2
        if binomial_cdf(deviations, sample_size, middle) > target:
            low = middle
        else:
            high = middle
    return (low + high) / 2


@dataclass(frozen=True)
class SequentialEvaluation:
    """Result of discovery or stop-or-go sampling."""

    approach: str
    deviations: int
    sample_size: int
    confidence_level: float
    rate: float
    upper_limit: float
    threshold: float
    conclusion: str
    steps: tuple[Step, ...]

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible result."""
        return {
            "approach": self.approach,
            "deviations": self.deviations,
            "sample_size": self.sample_size,
            "confidence_level": self.confidence_level,
            "rate": self.rate,
            "upper_limit": self.upper_limit,
            "threshold": self.threshold,
            "conclusion": self.conclusion,
            "steps": [s.to_dict() for s in self.steps],
        }


def _threshold(value: float) -> float:
    if not math.isfinite(value) or not 0 < value < 1:
        raise ExtrapolationInputError("Die Schwelle der Abweichungsquote liegt zwischen 0 und 1.")
    return value


def _evaluate(
    approach: str, k: int, n: int, level: float, threshold: float, conclusion: str
) -> SequentialEvaluation:
    upper = upper_deviation_limit(k, n, level)
    steps = (
        Step("Abweichungsquote", "k / n", k / n, guidance("7.9.3")),
        Step("Obere Abweichungsgrenze (exakt)", "P(X ≤ k | n, p_u) = 1 − KN", upper, SOURCE),
    )
    return SequentialEvaluation(approach, k, n, level, k / n, upper, threshold, conclusion, steps)


def evaluate_discovery(
    deviations: int, sample_size: int, *, confidence_level: float, critical_rate: float
) -> SequentialEvaluation:
    """Discovery sampling (guidance section 7.9.6): no deviation and p_u ≤ critical rate → met."""
    rate = _threshold(critical_rate)
    upper = upper_deviation_limit(deviations, sample_size, confidence_level)
    met = CRITERION_MET if upper <= rate else GO
    conclusion = DEVIATION_FOUND if deviations > 0 else met
    return _evaluate("discovery", deviations, sample_size, confidence_level, rate, conclusion)


def evaluate_stop_or_go(
    deviations: int, sample_size: int, *, confidence_level: float, tolerable_rate: float
) -> SequentialEvaluation:
    """Stop-or-go sampling (guidance section 7.9.6): stop when p_u ≤ tolerable rate, else extend."""
    rate = _threshold(tolerable_rate)
    upper = upper_deviation_limit(deviations, sample_size, confidence_level)
    return _evaluate(
        "stop_or_go", deviations, sample_size, confidence_level, rate, STOP if upper <= rate else GO
    )
