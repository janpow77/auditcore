"""Sample size for monetary unit sampling (MUS) along the Commission guidance.

* Standard approach, 6.3.1.2: n = (z × BV × σ_r / (TE − AE))², high-value
  (100 %) stratum by the cut-off BV/n and the iteration of 6.3.1.3.
* Stratified, 6.3.2.2: σ_rw² = Σ BV_h/BV × σ_rh², n_h = BV_h/BV × n.
* Conservative approach, 6.3.5.2: n = BV × RF / (TE − AE × EF), SI = BV/n
  (6.3.5.3), reliability factor RF from Table 4 and expansion factor EF from
  Table 5.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from ..sizes import SamplingInputError
from .equal_probability import MINIMUM_STATISTICAL
from .factors import expansion_factor, reliability_factor, z_value
from .plan import (
    GuidancePlan,
    StratumAllocation,
    StratumInput,
    finite,
    frozen,
    largest_remainder,
    round_up,
    tolerance,
    whole,
)
from .sources import Step, guidance

MUS_STANDARD = "guidance.mus_standard"
MUS_STRATIFIED = "guidance.mus_stratified"
MUS_CONSERVATIVE = "guidance.mus_conservative"


@dataclass(frozen=True)
class HighValueSplit:
    """High-value stratum of a MUS sample (guidance 6.3.1.3).

    ``exhaustive`` are the positions audited at 100 %, ``sampling_size`` the
    remaining n_s and ``interval`` the sampling interval SI = BV_s / n_s.
    """

    exhaustive: tuple[int, ...]
    cut_off: float
    sampling_book_value: float
    sampling_size: int
    interval: float
    rounds: int

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible split."""
        return {
            "exhaustive": list(self.exhaustive),
            "cut_off": self.cut_off,
            "sampling_book_value": self.sampling_book_value,
            "sampling_size": self.sampling_size,
            "interval": self.interval,
            "rounds": self.rounds,
        }


def high_value_split(book_values: Sequence[float], sample_size: int) -> HighValueSplit:
    """Units with BV_i > BV/n go to the 100 % stratum; repeat with BV_s/n_s (6.3.1.3).

    Raises:
        SamplingInputError: non-positive book values, n < 1, or all sample
            places taken by the high-value stratum.
    """
    size = whole(sample_size, "sample_size")
    values = [finite(v, "book_values", positive=True) for v in book_values]
    if not values:
        raise SamplingInputError("Die Buchwerte der Grundgesamtheit fehlen.")
    cut_off = math.fsum(values) / size
    limit = cut_off
    top: set[int] = set()
    rounds = 0
    while True:
        moved = {i for i, v in enumerate(values) if i not in top and v > limit}
        if not moved:
            break
        top |= moved
        rounds += 1
        if size - len(top) < 1:
            raise SamplingInputError(
                "Alle Stichprobenplätze entfallen auf die Hochwertschicht; Umfang erhöhen."
            )
        limit = math.fsum(v for i, v in enumerate(values) if i not in top) / (size - len(top))
    rest = math.fsum(v for i, v in enumerate(values) if i not in top)
    return HighValueSplit(tuple(sorted(top)), cut_off, rest, size - len(top), limit, rounds)


def _split_rows(split: HighValueSplit, total_value: float) -> tuple[StratumAllocation, ...]:
    exhaustive_value = total_value - split.sampling_book_value
    return (
        StratumAllocation(
            "Hochwertschicht",
            len(split.exhaustive),
            True,
            len(split.exhaustive),
            exhaustive_value,
            cut_off=split.cut_off,
        ),
        StratumAllocation(
            "Stichprobenschicht",
            split.sampling_size,
            False,
            None,
            split.sampling_book_value,
            cut_off=split.interval,
        ),
    )


def mus_standard_size(
    *,
    book_value: float,
    error_rate_sd: float,
    confidence_level: float,
    factor_profile: str,
    anticipated_error_rate: float,
    materiality_rate: float = 0.02,
    book_values: Sequence[float] | None = None,
) -> GuidancePlan:
    """MUS standard approach (6.3.1.2); with ``book_values`` also the 100 % stratum (6.3.1.3).

    ``error_rate_sd`` is σ_r of the error rates of a MUS sample
    (:func:`auditcore_sampling.guidance.error_rate_sd`). With ``book_values``
    their sum must equal ``book_value``.
    """
    sd = finite(error_rate_sd, "error_rate_sd", positive=True)
    limits = tolerance(book_value, materiality_rate, anticipated_error_rate)
    z = z_value(confidence_level, factor_profile)
    raw = (z * limits.book_value * sd / (limits.tolerable_error - limits.anticipated_error)) ** 2
    size = round_up(raw)
    source = guidance("6.3.1.2")
    steps = [
        Step("z-Wert", "z", z, guidance("5.3")),
        *limits.steps(),
        Step("Stichprobenumfang", "n = (z × BV × σ_r / (TE − AE))²", raw, source),
        Step(
            "Schwellenwert der Hochwertschicht",
            "BV / n",
            limits.book_value / size,
            guidance("6.3.1.3"),
        ),
    ]
    rows: tuple[StratumAllocation, ...] = ()
    interval = limits.book_value / size
    if book_values is not None:
        _check_total(book_values, limits.book_value)
        split = high_value_split(book_values, size)
        rows, interval = _split_rows(split, limits.book_value), split.interval
        steps.append(Step("Stichprobenintervall", "SI = BV_s / n_s", interval, guidance("6.3.1.3")))
    inputs = {
        **limits.inputs(),
        "error_rate_sd": sd,
        "confidence_level": confidence_level,
        "factor_profile": factor_profile,
        "z": z,
    }
    return GuidancePlan(
        MUS_STANDARD,
        size,
        raw,
        frozen(inputs),
        tuple(steps),
        rows,
        interval,
        tuple(_minimum_warning(size)),
    )


def _check_total(book_values: Sequence[float], book_value: float) -> None:
    total = math.fsum(finite(v, "book_values", positive=True) for v in book_values)
    if abs(total - book_value) > 1e-6 * max(1.0, book_value):
        raise SamplingInputError(
            f"Die Buchwerte ergeben {total:.2f}, der Buchwert der Grundgesamtheit ist "
            f"{book_value:.2f}."
        )


def _minimum_warning(size: int) -> list[str]:
    if size >= MINIMUM_STATISTICAL:
        return []
    return [f"Umfang unter {MINIMUM_STATISTICAL} Einheiten (Leitfaden, Fußnote 37)."]


def _mus_strata(strata: Sequence[StratumInput]) -> list[tuple[str, float, float]]:
    if not strata or len({s.name for s in strata}) != len(strata):
        raise SamplingInputError("Mindestens eine Schicht mit eindeutigem Namen ist erforderlich.")
    rows = []
    for stratum in strata:
        label = f"Schicht '{stratum.name}'"
        if stratum.exhaustive or not stratum.name.strip():
            raise SamplingInputError(
                f"{label}: Beim geschichteten MUS bildet jede Schicht ihre Hochwertgruppe selbst "
                "(Leitfaden, Abschn. 6.3.2.3); eigene Vollerhebungsschichten und leere Namen "
                "sind nicht vorgesehen."
            )
        rows.append(
            (
                stratum.name,
                finite(stratum.book_value, f"{label}: book_value", positive=True),
                finite(stratum.sd, f"{label}: sd", positive=True),
            )
        )
    return rows


def mus_stratified_size(
    *,
    strata: Sequence[StratumInput],
    confidence_level: float,
    factor_profile: str,
    anticipated_error_rate: float,
    materiality_rate: float = 0.02,
) -> GuidancePlan:
    """Stratified MUS (6.3.2.2): BV = Σ BV_h, allocation n_h = BV_h / BV × n, cut-off BV_h / n_h."""
    rows = _mus_strata(strata)
    total_value = math.fsum(value for _, value, _ in rows)
    limits = tolerance(total_value, materiality_rate, anticipated_error_rate)
    z = z_value(confidence_level, factor_profile)
    variance = math.fsum(value / total_value * sd**2 for _, value, sd in rows)
    margin = limits.tolerable_error - limits.anticipated_error
    raw = (z * total_value * math.sqrt(variance) / margin) ** 2
    size = round_up(raw)
    shares = largest_remainder(size, [value for _, value, _ in rows])
    allocation = tuple(
        StratumAllocation(
            name, n, False, None, value, value / total_value, value / n if n else None
        )
        for (name, value, _), n in zip(rows, shares, strict=True)
    )
    source = guidance("6.3.2.2")
    steps = [
        Step("z-Wert", "z", z, guidance("5.3")),
        *limits.steps(),
        Step(
            "Gewichtete Varianz der Fehlerquoten", "σ_rw² = Σ BV_h / BV × σ_rh²", variance, source
        ),
        Step("Stichprobenumfang", "n = (z × BV × σ_rw / (TE − AE))²", raw, source),
        Step("Aufteilung", "n_h = BV_h / BV × n (größter Rest)", float(size), source),
    ]
    warnings = _minimum_warning(size)
    if any(n == 0 for n in shares):
        warnings.append("Eine Schicht erhält keinen Stichprobenplatz; Schichtung prüfen.")
    inputs = {
        **limits.inputs(),
        "confidence_level": confidence_level,
        "factor_profile": factor_profile,
        "z": z,
        "weighted_variance": variance,
    }
    return GuidancePlan(
        MUS_STRATIFIED,
        size,
        raw,
        frozen(inputs),
        tuple(steps),
        allocation,
        warnings=tuple(warnings),
    )


def mus_conservative_size(
    *,
    book_value: float,
    confidence_level: float,
    factor_profile: str,
    anticipated_error_rate: float,
    materiality_rate: float = 0.02,
) -> GuidancePlan:
    """MUS conservative approach (6.3.5.2): n = BV × RF / (TE − AE × EF), SI = BV / n (6.3.5.3).

    EF is used only when errors are expected (AE > 0).
    """
    limits = tolerance(book_value, materiality_rate, anticipated_error_rate)
    rf = reliability_factor(confidence_level, factor_profile)
    ef = expansion_factor(confidence_level) if limits.anticipated_error > 0 else 1.0
    margin = limits.tolerable_error - limits.anticipated_error * ef
    if margin <= 0:
        raise SamplingInputError(
            "TE − AE × EF ist nicht positiv: Die erwartete Fehlerquote ist zu nahe an der "
            "Wesentlichkeit (Leitfaden, Abschn. 6.3.5.2, Fußnote 36)."
        )
    raw = limits.book_value * rf / margin
    size = round_up(raw)
    source = guidance("6.3.5.2")
    steps = [
        Step("Zuverlässigkeitsfaktor", "RF", rf, guidance("Tabelle 4")),
        Step("Expansionsfaktor", "EF (nur bei AE > 0)", ef, guidance("Tabelle 5")),
        *limits.steps(),
        Step("Stichprobenumfang", "n = BV × RF / (TE − AE × EF)", raw, source),
        Step("Stichprobenintervall", "SI = BV / n", limits.book_value / size, guidance("6.3.5.3")),
    ]
    inputs = {
        **limits.inputs(),
        "confidence_level": confidence_level,
        "factor_profile": factor_profile,
        "reliability_factor": rf,
        "expansion_factor": ef,
    }
    warnings = (
        "Einheiten mit Buchwert über dem Intervall bilden eine Hochwertschicht "
        "(Leitfaden, Abschn. 6.3.5.3).",
    )
    return GuidancePlan(
        MUS_CONSERVATIVE,
        size,
        raw,
        frozen(inputs),
        tuple(steps),
        (),
        limits.book_value / size,
        warnings,
    )
