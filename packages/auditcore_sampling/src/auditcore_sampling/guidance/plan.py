"""Result types and shared inputs of the guidance-based sample-size planning.

Tolerable error, anticipated error, rounding and allocation are the same for
all statistical methods of EGESIF_16-0014-01 and therefore live here.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType

from ..sizes import SamplingInputError
from .sources import GUIDANCE_STATUS, Step, guidance

#: Maximum materiality: 2 % of the declared expenditure (guidance 5.3, 4.10).
MATERIALITY_RATE = 0.02


@dataclass(frozen=True)
class StratumInput:
    """One stratum of the planning population.

    ``population_size`` (N_h) is needed for equal-probability methods,
    ``book_value`` (BV_h) for MUS. ``sd`` is the anticipated standard
    deviation of the errors (equal probability) or of the error rates (MUS);
    an ``exhaustive`` stratum is audited at 100 % and needs no ``sd``.
    """

    name: str
    population_size: int | None = None
    book_value: float | None = None
    sd: float | None = None
    exhaustive: bool = False


@dataclass(frozen=True)
class StratumAllocation:
    """Planned sample of one stratum (``cut_off`` only for MUS)."""

    name: str
    sample_size: int
    exhaustive: bool
    population_size: int | None = None
    book_value: float | None = None
    share: float | None = None
    cut_off: float | None = None

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible allocation row."""
        return {
            "name": self.name,
            "sample_size": self.sample_size,
            "exhaustive": self.exhaustive,
            "population_size": self.population_size,
            "book_value": self.book_value,
            "share": self.share,
            "cut_off": self.cut_off,
        }


@dataclass(frozen=True)
class GuidancePlan:
    """Planned sample size of one method of the guidance with its derivation.

    ``raw_size`` is the unrounded value of the formula; ``sample_size`` is the
    planned total including exhaustive (100 %) units.
    """

    method: str
    sample_size: int
    raw_size: float
    inputs: Mapping[str, object]
    steps: tuple[Step, ...]
    strata: tuple[StratumAllocation, ...] = ()
    interval: float | None = None
    warnings: tuple[str, ...] = ()
    status: str = field(default=GUIDANCE_STATUS)

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible plan."""
        return {
            "method": self.method,
            "status": self.status,
            "sample_size": self.sample_size,
            "raw_size": self.raw_size,
            "interval": self.interval,
            "inputs": dict(self.inputs),
            "strata": [s.to_dict() for s in self.strata],
            "derivation": [s.to_dict() for s in self.steps],
            "warnings": list(self.warnings),
        }


def finite(value: object, name: str, *, positive: bool = False) -> float:
    """A finite number, ≥ 0 (or > 0 with ``positive``); booleans are rejected."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise SamplingInputError(f"'{name}' muss eine endliche Zahl sein.")
    number = float(value)
    if number < 0 or (positive and number == 0):
        bound = "größer als 0" if positive else "nicht negativ"
        raise SamplingInputError(f"'{name}' muss {bound} sein.")
    return number


def whole(value: object, name: str, *, minimum: int = 1) -> int:
    """An integer ≥ ``minimum``."""
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise SamplingInputError(f"'{name}' muss eine ganze Zahl ≥ {minimum} sein.")
    return value


@dataclass(frozen=True)
class Tolerance:
    """TE = materiality × BV and AE = anticipated error rate × BV (guidance 5.3)."""

    book_value: float
    materiality_rate: float
    anticipated_rate: float

    @property
    def tolerable_error(self) -> float:
        """Maximum tolerable error TE."""
        return self.materiality_rate * self.book_value

    @property
    def anticipated_error(self) -> float:
        """Anticipated error AE."""
        return self.anticipated_rate * self.book_value

    def inputs(self) -> dict[str, object]:
        """BV, rates, TE and AE for the plan inputs."""
        return {
            "book_value": self.book_value,
            "materiality_rate": self.materiality_rate,
            "anticipated_error_rate": self.anticipated_rate,
            "tolerable_error": self.tolerable_error,
            "anticipated_error": self.anticipated_error,
        }

    def steps(self) -> list[Step]:
        """Derivation lines of TE and AE."""
        return [
            Step(
                "Tolerierbarer Fehler",
                "TE = Wesentlichkeit × BV",
                self.tolerable_error,
                guidance("5.3"),
            ),
            Step(
                "Erwarteter Fehler",
                "AE = erwartete Fehlerquote × BV",
                self.anticipated_error,
                guidance("5.3"),
            ),
        ]


def tolerance(book_value: object, materiality_rate: object, anticipated_rate: object) -> Tolerance:
    """Validated TE/AE inputs: 0 < materiality ≤ 2 %, 0 ≤ anticipated rate < materiality."""
    value = finite(book_value, "book_value", positive=True)
    rate = finite(materiality_rate, "materiality_rate", positive=True)
    if rate > MATERIALITY_RATE + 1e-12:
        raise SamplingInputError(
            "Die Wesentlichkeit darf höchstens 2 % der Ausgaben betragen (Leitfaden, Abschn. 5.3)."
        )
    expected = finite(anticipated_rate, "anticipated_error_rate")
    if expected >= rate:
        raise SamplingInputError(
            "Die erwartete Fehlerquote muss kleiner als die Wesentlichkeit sein; sonst ist kein "
            "Stichprobenumfang bestimmbar (Leitfaden, Abschn. 6.3.5.2, Fußnote 36)."
        )
    return Tolerance(value, rate, expected)


def round_up(raw: float) -> int:
    """Sample sizes are rounded up; float noise below 1e-9 does not add a unit."""
    return max(1, math.ceil(round(raw, 9)))


def largest_remainder(total: int, weights: Sequence[float]) -> list[int]:
    """Proportional allocation n_h = n × w_h / Σw rounded by the largest remainder.

    The shares sum to ``total``; ties go to the earlier stratum. Guidance
    6.1.2.2, 6.2.2.2 and 6.3.2.2 prescribe the proportion, not the rounding.
    """
    whole_sum = math.fsum(weights)
    if whole_sum <= 0:
        raise SamplingInputError("Die Gewichte der Schichten müssen größer als 0 sein.")
    exact = [total * w / whole_sum for w in weights]
    shares = [math.floor(x) for x in exact]
    order = sorted(range(len(exact)), key=lambda i: (-(exact[i] - shares[i]), i))
    for index in order[: total - sum(shares)]:
        shares[index] += 1
    return shares


def frozen(mapping: Mapping[str, object]) -> Mapping[str, object]:
    """Read-only copy of the plan inputs."""
    return MappingProxyType(dict(mapping))
