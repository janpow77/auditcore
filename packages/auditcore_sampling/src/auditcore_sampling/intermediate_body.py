"""Value-share draw with an escalation ladder – procedure of an intermediate body.

An intermediate body (Art. 71(3) Regulation (EU) 2021/1060) that carries out
management verifications on behalf of the managing authority may check the
invoices of a payment claim partially: invoices are drawn at random until
their amount reaches a share of the expenditure (not of the number of
invoices). If a newly drawn invoice carries a financial error, the draw is
extended by fixed steps up to a maximum share; invoices already drawn stay
in the sample. Additionally every k-th payment claim that the risk scoring
exempts from verification is verified as a quality sample.

The procedure is a versioned, parameterised profile; nothing is tied to one
institution. Adopted from flowinvoice (``backend/app/verwk/pipeline/pruefplan.py``
at commit ``fb2d18568d2e``), parity with recorded runs of that implementation
is tested with fixed seeds (``tests/test_intermediate_body_parity.py``).

Randomness only enters through the draw order: either a permutation from an
explicit ``random.Random`` (:func:`draw_order`) or one supplied by the caller
(e.g. from a NumPy generator seeded with :func:`derived_seed`, as flowinvoice
does).
"""

from __future__ import annotations

import dataclasses
import hashlib
import math
import random
from collections.abc import Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import TypeVar

from auditcore_common.numeric import numpy_pairwise_sum

from .sizes import SamplingInputError

T = TypeVar("T")

VALUE_SHARE_ESCALATION = "zs.value_share_escalation"
SOURCE_COMMIT = "fb2d18568d2eaf64574d131ceae51a936b9aac02"


@dataclass(frozen=True)
class ValueShareProfile:
    """Parameters of the value-share draw (version ``version`` of the procedure)."""

    id: str
    version: int
    label: str
    source: str
    start_share: float = 0.25
    step: float = 0.15
    max_share: float = 0.85
    escalate: bool = True
    quality_every: int = 20
    note: str = ""

    def with_parameters(self, **changes: object) -> ValueShareProfile:
        """Copy with changed parameters (e.g. ``start_share=0.3``), validated."""
        allowed = {"start_share", "step", "max_share", "escalate", "quality_every"}
        unknown = set(changes) - allowed
        if unknown:
            raise SamplingInputError(f"Unbekannte Parameter: {', '.join(sorted(unknown))}.")
        return check_profile(dataclasses.replace(self, **changes))  # type: ignore[arg-type]

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible profile."""
        return dataclasses.asdict(self)


def _share(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise SamplingInputError(f"'{name}' muss eine endliche Zahl sein.")
    if not 0 <= value <= 1:
        raise SamplingInputError(f"'{name}' muss in [0, 1] liegen.")
    return float(value)


def check_profile(profile: ValueShareProfile) -> ValueShareProfile:
    """Validate the parameters: shares in [0, 1], step > 0, quality sample every k ≥ 1."""
    _share(profile.start_share, "start_share")
    _share(profile.max_share, "max_share")
    if _share(profile.step, "step") <= 0:
        raise SamplingInputError("'step' muss größer als 0 sein.")
    if not isinstance(profile.escalate, bool):
        raise SamplingInputError("'escalate' muss wahr oder falsch sein.")
    every = profile.quality_every
    if isinstance(every, bool) or not isinstance(every, int) or every < 1:
        raise SamplingInputError("'quality_every' muss eine ganze Zahl ≥ 1 sein.")
    return profile


PROFILES = MappingProxyType(
    {
        VALUE_SHARE_ESCALATION: ValueShareProfile(
            VALUE_SHARE_ESCALATION,
            1,
            "Zwischengeschaltete Stelle: Belegziehung nach Ausgabenanteil mit Erweiterung",
            f"übernommen aus flowinvoice@{SOURCE_COMMIT[:12]}",
            note=(
                "Start 25 % der Ausgaben, Erweiterung in Schritten von 15 Prozentpunkten bis "
                "85 %, solange neu gezogene Belege einen finanziellen Fehler tragen (Auslegung "
                "der Quelle: maßgeblich sind die neu hinzugekommenen Belege; fachlich zu "
                "bestätigen). Qualitätsstichprobe: jeder 20. nicht zu prüfende Mittelabruf."
            ),
        ),
    }
)


def profile(profile_id: object) -> ValueShareProfile:
    """The explicitly named procedure profile."""
    found = PROFILES.get(profile_id) if isinstance(profile_id, str) else None
    if found is None:
        raise SamplingInputError(
            f"Unbekanntes Verfahren '{profile_id}'. Zulässig: {', '.join(sorted(PROFILES))}."
        )
    return found


def escalation_ladder(chosen: ValueShareProfile) -> tuple[float, ...]:
    """Shares of the ladder: start (clamped to [0, 1]), then + step while ≤ maximum."""
    stages = [max(0.0, min(1.0, float(chosen.start_share)))]
    while stages[-1] + chosen.step <= chosen.max_share + 1e-9:
        stages.append(round(stages[-1] + chosen.step, 4))
    return tuple(stages)


@dataclass(frozen=True)
class ValueShareDraw:
    """Drawn positions in draw order with the ladder stage (1-based) of each."""

    procedure: str
    version: int
    ladder: tuple[float, ...]
    positions: tuple[int, ...]
    stages: tuple[int, ...]
    population_value: float
    drawn_value: float

    @property
    def final_stage(self) -> int | None:
        """Highest stage reached, ``None`` if nothing was drawn."""
        return max(self.stages) if self.stages else None

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible draw."""
        return {
            "procedure": self.procedure,
            "version": self.version,
            "ladder": list(self.ladder),
            "positions": list(self.positions),
            "stages": list(self.stages),
            "final_stage": self.final_stage,
            "population_value": self.population_value,
            "drawn_value": self.drawn_value,
        }


def _numbers(values: Sequence[float], name: str) -> list[float]:
    result = []
    for value in values:
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise SamplingInputError(f"'{name}' enthält einen Wert, der keine endliche Zahl ist.")
        result.append(float(value))
    return result


def _checked_order(order: Sequence[int], size: int) -> list[int]:
    positions = list(order)
    if sorted(positions) != list(range(size)):
        raise SamplingInputError("Die Ziehreihenfolge muss jede Position genau einmal enthalten.")
    return positions


def value_share_draw(
    amounts: Sequence[float],
    errors: Sequence[float],
    order: Sequence[int],
    chosen: ValueShareProfile,
) -> ValueShareDraw:
    """Draw in ``order`` until the drawn amount reaches share × total; escalate on new errors.

    ``errors[i] > 0`` marks a financial error of invoice ``i``. The draw stops
    at a stage when escalation is off, the order is exhausted, the stage drew
    nothing new or none of the newly drawn invoices carries an error.
    """
    values = _numbers(amounts, "amounts")
    faults = _numbers(errors, "errors")
    if len(faults) != len(values) or any(v < 0 for v in values):
        raise SamplingInputError("Beträge (nicht negativ) und Fehler müssen gleich lang sein.")
    sequence = _checked_order(order, len(values))
    check_profile(chosen)
    ladder = escalation_ladder(chosen)
    total = float(numpy_pairwise_sum(values)) if values else 0.0
    drawn: list[int] = []
    stages: list[int] = []
    drawn_value = 0.0
    if total > 0:
        drawn_value = _escalate(
            values, faults, sequence, ladder, total, chosen.escalate, drawn, stages
        )
    return ValueShareDraw(
        chosen.id, chosen.version, ladder, tuple(drawn), tuple(stages), total, drawn_value
    )


def _escalate(
    values: list[float],
    faults: list[float],
    sequence: list[int],
    ladder: tuple[float, ...],
    total: float,
    escalate: bool,
    drawn: list[int],
    stages: list[int],
) -> float:
    """Run the ladder; appends to ``drawn``/``stages`` and returns the drawn amount."""
    drawn_value = 0.0
    following = 0
    for stage, share in enumerate(ladder, start=1):
        target = total * share
        new: list[int] = []
        while drawn_value < target and following < len(sequence):
            new.append(sequence[following])
            drawn_value += values[sequence[following]]
            following += 1
        drawn.extend(new)
        stages.extend([stage] * len(new))
        if not escalate or following >= len(sequence):
            break
        if not new or not any(faults[i] > 0 for i in new):
            break
    return drawn_value


def draw_order(rng: random.Random, size: int) -> list[int]:
    """A random permutation of ``range(size)`` from an explicit generator."""
    if not isinstance(rng, random.Random):
        raise SamplingInputError("Ein ausdrücklicher random.Random-Generator ist erforderlich.")
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        raise SamplingInputError("'size' muss eine ganze Zahl ≥ 0 sein.")
    return rng.sample(range(size), size)


def derived_seed(base_seed: int, key: object) -> int:
    """Per-claim seed: base + (first 32 bits of SHA-256 of ``str(key)``) mod 1 000 003.

    Gives every payment claim its own reproducible order; identical to the
    seed derivation of the source, so a consumer with a NumPy generator
    (``default_rng(derived_seed(...)).permutation(n)``) reproduces its draws.
    """
    if isinstance(base_seed, bool) or not isinstance(base_seed, int) or base_seed < 0:
        raise SamplingInputError("'base_seed' muss eine ganze Zahl ≥ 0 sein.")
    digest = hashlib.sha256(str(key).encode("utf-8")).hexdigest()
    return base_seed + int(digest[:8], 16) % 1_000_003


def quality_sample(candidates: Sequence[T], every: int) -> list[T]:
    """Every ``every``-th candidate (the k-th, 2k-th, …) in the given order."""
    if isinstance(every, bool) or not isinstance(every, int) or every < 1:
        raise SamplingInputError("'every' muss eine ganze Zahl ≥ 1 sein.")
    return list(candidates[every - 1 :: every])
