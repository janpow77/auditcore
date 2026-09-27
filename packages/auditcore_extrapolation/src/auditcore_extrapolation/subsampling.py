"""Two-stage and three-stage sampling: the error of a unit from a sub-sample.

When a selected unit (operation, project partner, payment claim) contains
many expenditure items, only a random sub-sample of them may be audited
(guidance section 7.6; non-statistical sampling 6.4.10; ETC programmes
6.5.3.1–6.5.3.3). The error of the unit is projected from its sub-sample and
then treated as if it were the true error of the unit (7.6.3); the precision
of the main sample ignores the sub-sampling (7.6.4).

Inside the unit the sub-sample may be stratified, e.g. the lead partner of an
ETC operation audited in full (exhaustive stratum) and a sample of the other
project partners (6.5.3.3.1). A :class:`SubSample` therefore consists of
:class:`~auditcore_extrapolation.design.Stratum` objects whose book values add
up to the book value of the unit. Projection per sub-stratum (no precision):

* ratio estimation: EE_i = BV_i × ΣE_ij / ΣBV_ij (7.6.3, 6.5.3.3.1),
* mean-per-unit estimation: EE_i = N_i × ΣE_ij / n_i (7.6.3),
* probability proportional to size: EE_i = BV_is / n_is × Σ E_ij / BV_ij
  (7.6.1: any statistical design may be used at the second stage),

plus the errors of the exhaustive sub-units. A sub-unit may itself carry a
projected error from its own sub-sample (three-stage design, 6.5.3.2.2).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from types import MappingProxyType

from . import equal_probability, mus
from .design import Stratum, check_strata
from .errors import ExtrapolationInputError
from .projection import StratumResult
from .sources import Step, guidance
from .units import SampleUnit, check_unit

MEAN_PER_UNIT = "mean_per_unit"
RATIO = "ratio"
PPS = "pps"
#: Projection estimators for the sub-sample of a unit (section 7.6.3).
SUBSAMPLE_ESTIMATORS = MappingProxyType(
    {
        RATIO: "Verhältnisschätzung (gleiche Auswahlwahrscheinlichkeit)",
        MEAN_PER_UNIT: "Mittelwertschätzung (gleiche Auswahlwahrscheinlichkeit)",
        PPS: "Wertproportionale Auswahl (MUS-Formel)",
    }
)
#: Minimum sub-sample size of the guidance (sections 6.5.3.1, 7.6.1, 7.6.2).
MIN_SUBSAMPLE = 30
#: Recommended expenditure coverage of smaller non-statistical sub-samples (6.4.10).
MIN_SUBSAMPLE_COVERAGE = 0.10


@dataclass(frozen=True)
class SubSample:
    """Audited sub-sample of one unit: the unit id, estimator and sub-strata."""

    unit_id: str
    estimator: str
    strata: tuple[Stratum, ...]

    @property
    def book_value(self) -> float:
        """Book value of the unit = Σ book values of its sub-strata."""
        return math.fsum(s.book_value for s in self.strata)


@dataclass(frozen=True)
class SubSampleResult:
    """Projected error of one unit from its sub-sample (section 7.6.3)."""

    unit_id: str
    estimator: str
    book_value: float
    projected_error: float
    audited_book_value: float
    sampled_items: int
    exhaustive_items: int
    strata: tuple[StratumResult, ...]
    steps: tuple[Step, ...]
    warnings: tuple[str, ...]

    @property
    def coverage(self) -> float:
        """Share of the unit's book value that was audited."""
        return self.audited_book_value / self.book_value

    @property
    def error_rate(self) -> float:
        """Projected error rate of the unit."""
        return self.projected_error / self.book_value

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible result."""
        return {
            "unit_id": self.unit_id,
            "estimator": self.estimator,
            "book_value": self.book_value,
            "projected_error": self.projected_error,
            "error_rate": self.error_rate,
            "audited_book_value": self.audited_book_value,
            "coverage": self.coverage,
            "sampled_items": self.sampled_items,
            "exhaustive_items": self.exhaustive_items,
            "strata": [s.to_dict() for s in self.strata],
            "steps": [s.to_dict() for s in self.steps],
            "warnings": list(self.warnings),
        }


def _check_items(sub: SubSample) -> None:
    for stratum in sub.strata:
        for item in stratum.units + stratum.exhaustive_units:
            if item.systemic_error or item.anomalous_error:
                raise ExtrapolationInputError(
                    f"Einheit '{sub.unit_id}', Teileinheit '{item.id}': In der Teilstichprobe nur "
                    "zufällige Fehler erfassen; abgegrenzte systemische und anomale Fehler bei der "
                    "Einheit selbst (Leitfaden, Abschn. 7.6.1)."
                )
        if stratum.systemic_error:
            raise ExtrapolationInputError(
                f"Einheit '{sub.unit_id}': Systemische Fehler werden nicht auf Ebene der "
                "Teilstichprobe abgegrenzt (Leitfaden, Abschn. 7.6.1)."
            )


def _project(sub: SubSample) -> tuple[tuple[StratumResult, ...], float, list[Step]]:
    if sub.estimator == PPS:
        results, projected, _, steps = mus.project_standard(sub.strata, None)
        return results, projected, steps
    results, projected, _, steps, _ = equal_probability.project(sub.strata, sub.estimator, None)
    return results, projected, steps


def _warnings(sub: SubSample, sampled: int, coverage: float) -> list[str]:
    if not sampled or sampled >= MIN_SUBSAMPLE:
        return []
    return [
        f"Einheit '{sub.unit_id}': Teilstichprobe mit {sampled} Teileinheiten "
        f"(Deckung {coverage:.1%} des Buchwerts). Der Leitfaden verlangt mindestens "
        f"{MIN_SUBSAMPLE} Rechnungen oder Zahlungsanträge (Abschn. 6.5.3.1, 7.6.2); bei anderen "
        "Teilstichprobeneinheiten in nicht-statistischen Verfahren sollen weniger als 30 "
        "mindestens 10 % der Ausgaben der Einheit abdecken (Abschn. 6.4.10)."
    ]


def project_subsample(sub: SubSample) -> SubSampleResult:
    """Error of a unit projected from its sub-sample (guidance sections 7.6.3, 6.5.3.3.1).

    Raises:
        ExtrapolationInputError: unknown estimator, invalid sub-strata, missing
            N for mean-per-unit estimation, systemic or anomalous errors on
            sub-units, or a projected error above the unit's book value.
    """
    if not sub.unit_id.strip():
        raise ExtrapolationInputError("Die Teilstichprobe braucht die Kennung ihrer Einheit.")
    if sub.estimator not in SUBSAMPLE_ESTIMATORS:
        raise ExtrapolationInputError(
            f"Unbekannter Schätzer '{sub.estimator}' der Teilstichprobe. "
            f"Zulässig: {', '.join(SUBSAMPLE_ESTIMATORS)}."
        )
    try:
        check_strata(sub.strata, needs_population_size=sub.estimator == MEAN_PER_UNIT)
        _check_items(sub)
        results, projected, steps = _project(sub)
    except ExtrapolationInputError as exc:
        raise ExtrapolationInputError(f"Teilstichprobe der Einheit '{sub.unit_id}': {exc}") from exc
    book = sub.book_value
    if projected > book * (1 + 1e-12):
        raise ExtrapolationInputError(
            f"Einheit '{sub.unit_id}': Der hochgerechnete Fehler ({projected:.2f}) übersteigt den "
            f"Buchwert der Einheit ({book:.2f})."
        )
    items = [u for s in sub.strata for u in s.units]
    exhaustive = [u for s in sub.strata for u in s.exhaustive_units]
    audited = math.fsum(u.book_value for u in items + exhaustive)
    steps.append(
        Step(
            f"Fehler der Einheit {sub.unit_id} aus der Teilstichprobe",
            "EE_i = Σ Teilschichten (Hochrechnung + Vollerhebung)",
            projected,
            guidance("7.6.3, 6.5.3.3.1"),
        )
    )
    return SubSampleResult(
        sub.unit_id,
        sub.estimator,
        book,
        projected,
        audited,
        len(items),
        len(exhaustive),
        results,
        tuple(steps),
        tuple(_warnings(sub, len(items), audited / book)),
    )


def unit_from_subsample(
    sub: SubSample,
    *,
    systemic_error: float = 0.0,
    anomalous_error: float = 0.0,
    anomalous_reason: str = "",
    anomalous_corrected: bool = False,
) -> tuple[SampleUnit, SubSampleResult]:
    """Sampling unit whose random error is projected from ``sub`` (section 7.6.3).

    Delimited systemic and anomalous errors are recorded on the unit itself.
    """
    result = project_subsample(sub)
    unit = check_unit(
        SampleUnit(
            sub.unit_id,
            result.book_value,
            result.projected_error,
            systemic_error,
            anomalous_error,
            anomalous_reason,
            anomalous_corrected,
        )
    )
    return unit, result


def units_from_subsamples(
    subs: Sequence[SubSample],
) -> tuple[tuple[SampleUnit, ...], tuple[SubSampleResult, ...]]:
    """:func:`unit_from_subsample` for several units (random errors only)."""
    pairs = [unit_from_subsample(sub) for sub in subs]
    return tuple(u for u, _ in pairs), tuple(r for _, r in pairs)
