"""Result of a projection: projected random error, precision and derivation."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType

from .design import Stratum
from .sources import Step
from .units import ErrorClasses


@dataclass(frozen=True)
class StratumResult:
    """Projection of one stratum (sampling part plus exhaustive units)."""

    name: str
    projected_error: float
    exhaustive_error: float
    sample_size: int
    sampling_book_value: float
    figures: Mapping[str, float] = field(default_factory=lambda: MappingProxyType({}))

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible stratum result."""
        return {
            "name": self.name,
            "projected_error": self.projected_error,
            "exhaustive_error": self.exhaustive_error,
            "sample_size": self.sample_size,
            "sampling_book_value": self.sampling_book_value,
            "figures": dict(self.figures),
        }


@dataclass(frozen=True)
class Projection:
    """Projected random error (EE) and precision (SE) of one method.

    ``precision`` is ``None`` for non-statistical sampling (guidance section
    6.4.5: no precision and no upper limit). ``error_classes`` are the sample
    totals; ``systemic_population`` is the delimited systemic error of the
    population and ``anomalous_uncorrected`` the anomalous errors that stay
    in the TER.
    """

    method: str
    projected_random_error: float
    precision: float | None
    confidence_level: float | None
    factor_profile: str | None
    coefficient: float | None
    strata: tuple[StratumResult, ...]
    error_classes: ErrorClasses
    systemic_population: float
    steps: tuple[Step, ...]
    warnings: tuple[str, ...] = ()
    #: Method-specific, JSON-ready details (estimator check, allowances, coverage).
    extra: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    @property
    def anomalous_uncorrected(self) -> float:
        """Anomalous errors that are not corrected (part of the TER)."""
        return self.error_classes.anomalous_uncorrected

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible projection."""
        classes = self.error_classes
        return {
            "method": self.method,
            "projected_random_error": self.projected_random_error,
            "precision": self.precision,
            "confidence_level": self.confidence_level,
            "factor_profile": self.factor_profile,
            "coefficient": self.coefficient,
            "strata": [s.to_dict() for s in self.strata],
            "sample_errors": {
                "random": classes.random,
                "systemic": classes.systemic,
                "anomalous_uncorrected": classes.anomalous_uncorrected,
                "anomalous_corrected": classes.anomalous_corrected,
            },
            "systemic_population": self.systemic_population,
            "steps": [s.to_dict() for s in self.steps],
            "warnings": list(self.warnings),
            "extra": dict(self.extra),
        }


def error_classes(strata: Sequence[Stratum]) -> ErrorClasses:
    """Sample totals of the error classes over all strata."""
    return ErrorClasses.of([u for s in strata for u in s.units + s.exhaustive_units])


def systemic_population(strata: Sequence[Stratum]) -> float:
    """Delimited systemic errors: sampling parts plus exhaustive units."""
    return math.fsum(
        s.systemic_error + math.fsum(u.systemic_error for u in s.exhaustive_units) for s in strata
    )


def exhaustive_random_error(stratum: Stratum) -> float:
    """EE_e: random errors of the units audited at 100 % (no sampling error)."""
    return math.fsum(u.random_error for u in stratum.exhaustive_units)


def anomaly_warnings(strata: Sequence[Stratum]) -> tuple[str, ...]:
    """Reminder that anomalous errors are exceptional (guidance, Appendix 6)."""
    count = sum(1 for s in strata for u in s.units + s.exhaustive_units if u.anomalous_error > 0)
    if not count:
        return ()
    return (
        f"{count} Einheit(en) mit anomalem Fehler aus der Hochrechnung ausgenommen. Anomale "
        "Fehler sind nur in sehr außergewöhnlichen, gut begründeten Fällen anzunehmen "
        "(Leitfaden, Anhang 6); nicht korrigierte anomale Fehler gehen in die TER ein.",
    )
