"""Monetary unit sampling, conservative approach (guidance section 6.3.5).

Sampling interval SI = BV / n over the whole population; units with a book
value above SI form the exhaustive stratum. Precision is the basic precision
BP = SI × RF(0) plus the incremental allowance for every sampled unit with an
error, ordered by decreasing projected error:
IA_i = (RF(i) − RF(i − 1) − 1) × SI × E_i / BV_i. The approach cannot be
combined with stratification (section 6.3.5.1).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from types import MappingProxyType

from .design import Stratum
from .errors import ExtrapolationInputError
from .factors import basic_reliability_factor, reliability_factor
from .mus import tainting_projection
from .projection import StratumResult, exhaustive_random_error
from .sources import Step, guidance


@dataclass(frozen=True)
class Allowance:
    """Incremental allowance of the error in position ``order`` (1-based)."""

    unit_id: str
    order: int
    tainting: float
    projected_error: float
    factor: float
    allowance: float

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible row."""
        return {
            "unit_id": self.unit_id,
            "order": self.order,
            "tainting": self.tainting,
            "projected_error": self.projected_error,
            "factor": self.factor,
            "allowance": self.allowance,
        }


def incremental_allowances(
    taintings: Sequence[tuple[str, float]],
    interval: float,
    confidence_level: float,
    profile_id: str,
) -> tuple[Allowance, ...]:
    """IA_i for the positive taintings by decreasing projected error (guidance section 6.3.5.5)."""
    ordered = sorted((t for t in taintings if t[1] > 0), key=lambda t: (-t[1], t[0]))
    rows = []
    previous = reliability_factor(0, confidence_level, profile_id)
    for order, (unit_id, tainting) in enumerate(ordered, start=1):
        current = reliability_factor(order, confidence_level, profile_id)
        factor = current - previous - 1
        projected = interval * tainting
        rows.append(Allowance(unit_id, order, tainting, projected, factor, factor * projected))
        previous = current
    return tuple(rows)


def _interval(stratum: Stratum, sample_size: int) -> float:
    if isinstance(sample_size, bool) or not isinstance(sample_size, int) or sample_size < 1:
        raise ExtrapolationInputError(
            "Für den konservativen Ansatz ist der geplante Stichprobenumfang n (ganze Zahl ≥ 1) "
            "anzugeben (SI = BV / n)."
        )
    return stratum.book_value / sample_size


def _placement_warnings(stratum: Stratum, interval: float) -> list[str]:
    warnings = []
    if any(u.book_value > interval for u in stratum.units):
        warnings.append(
            "Einheiten der Stichprobe mit Buchwert über dem Intervall gehören zur Vollerhebung "
            "(Leitfaden, Abschn. 6.3.5.3)."
        )
    if any(u.book_value <= interval for u in stratum.exhaustive_units):
        warnings.append("Vollständig geprüfte Einheiten mit Buchwert ≤ Intervall.")
    return warnings


def project_conservative(
    strata: Sequence[Stratum], sample_size: int, confidence_level: float, profile_id: str
) -> tuple[tuple[StratumResult, ...], float, float, list[Step], list[str], tuple[Allowance, ...]]:
    """Projection and precision of the conservative approach."""
    if len(strata) != 1:
        raise ExtrapolationInputError(
            "Der konservative MUS-Ansatz lässt keine Schichtung zu (Leitfaden, Abschn. 6.3.5.1)."
        )
    stratum = strata[0]
    interval = _interval(stratum, sample_size)
    taintings = [(u.id, u.random_rate) for u in stratum.units]
    tainting_sum = math.fsum(t for _, t in taintings)
    exhaustive = exhaustive_random_error(stratum)
    projected = exhaustive + tainting_projection(interval, tainting_sum)
    basic_factor = basic_reliability_factor(confidence_level, profile_id)
    basic = interval * basic_factor
    rows = incremental_allowances(taintings, interval, confidence_level, profile_id)
    incremental = math.fsum(r.allowance for r in rows)
    figures = {
        "interval": interval,
        "tainting_sum": tainting_sum,
        "basic_precision": basic,
        "incremental_allowance": incremental,
    }
    result = StratumResult(
        stratum.name,
        projected,
        exhaustive,
        len(stratum.units),
        stratum.sampling_book_value,
        MappingProxyType(figures),
    )
    steps = [
        Step("Stichprobenintervall", "SI = BV / n", interval, guidance("6.3.5.3")),
        Step("Fehler der Vollerhebung", "EE_e = Σ E_i", exhaustive, guidance("6.3.5.4")),
        Step(
            "Hochgerechneter Fehler",
            "EE = EE_e + SI × Σ E_i / BV_i",
            projected,
            guidance("6.3.5.4"),
        ),
        Step("Zuverlässigkeitsfaktor (0 Fehler)", "RF", basic_factor, guidance("6.3.5.2")),
        Step("Basispräzision", "BP = SI × RF", basic, guidance("6.3.5.5")),
    ]
    steps += [
        Step(
            f"Zuschlag Fehler {r.order} ({r.unit_id})",
            "(RF(i) − RF(i−1) − 1) × SI × E_i/BV_i",
            r.allowance,
            guidance("6.3.5.5"),
        )
        for r in rows
    ]
    se = basic + incremental
    steps.append(Step("Präzision", "SE = BP + IA", se, guidance("6.3.5.5")))
    return (result,), projected, se, steps, _placement_warnings(stratum, interval), rows
