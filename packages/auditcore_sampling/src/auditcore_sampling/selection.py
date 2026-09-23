"""Deterministic selection mechanics with explicitly supplied randomness.

Random numbers never come from a global state: callers pass a
``random.Random`` (seeded for reproducibility) or an already drawn start
value. Positions refer to the order of the supplied values.
"""

from __future__ import annotations

import bisect
import math
import random
from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass

from ._numeric import is_missing, pandas_cumsum
from .sizes import SamplingInputError


@dataclass(frozen=True)
class MusSelection:
    """Selected positions of one systematic MUS draw."""

    variant: str
    start: float
    hits: tuple[int, ...]
    positions: tuple[int, ...]
    excluded_negative: tuple[int, ...]
    excluded_zero_or_missing: tuple[int, ...]


def first_reaching(cumulative: Sequence[float | None], targets: Sequence[float]) -> list[int]:
    """For each target the first position whose cumulative value is ≥ target.

    Missing cumulative values never match (pandas comparison semantics);
    targets that are never reached are skipped.
    """
    running_max: list[float] = []
    positions: list[int] = []
    best = -math.inf
    for position, value in enumerate(cumulative):
        if value is not None and value > best:
            best = value
            running_max.append(value)
            positions.append(position)
    result = []
    for target in targets:
        index = bisect.bisect_left(running_max, target)
        if index < len(running_max):
            result.append(positions[index])
    return result


def draw_start(rng: random.Random, interval: float) -> float:
    """Random start in [0, interval) from an explicit generator; 0 without interval."""
    if not isinstance(rng, random.Random):
        raise SamplingInputError("Ein ausdrücklicher random.Random-Generator ist erforderlich.")
    return rng.uniform(0, interval) if interval > 0 else 0.0


def systematic_mus(
    values: Sequence[float | int | None],
    *,
    sample_size: int,
    interval: float,
    start: float,
    variant: str,
) -> MusSelection:
    """Systematic monetary-unit selection.

    ``variant="flowstat"``: cumulative sum over all values (negative values
    included), a position hit by several monetary points appears repeatedly.
    ``variant="portal"``: only positive values form the population, zero,
    missing and negative positions are reported separately, and every position
    appears once ("certainty items" deduplicated).
    """
    if variant not in ("flowstat", "portal"):
        raise SamplingInputError("Variante muss 'flowstat' oder 'portal' sein.")
    if sample_size < 0 or interval < 0 or not math.isfinite(start):
        raise SamplingInputError("Stichprobenumfang, Intervall und Start müssen gültig sein.")
    targets = [start + i * interval for i in range(sample_size)]
    negative: list[int] = []
    zero_or_missing: list[int] = []
    if variant == "flowstat":
        hits = first_reaching(pandas_cumsum(values), targets)
        positions = hits
    else:
        positive_positions = []
        positive_values = []
        for position, value in enumerate(values):
            if is_missing(value) or value == 0:
                zero_or_missing.append(position)
            elif value < 0:  # type: ignore[operator]
                negative.append(position)
            else:
                positive_positions.append(position)
                positive_values.append(value)
        local = first_reaching(pandas_cumsum(positive_values), targets)
        hits = [positive_positions[i] for i in local]
        positions = list(dict.fromkeys(hits))
    return MusSelection(
        variant, start, tuple(hits), tuple(positions), tuple(negative), tuple(zero_or_missing)
    )


def simple_random(rng: random.Random, population: Sequence[Hashable], size: int) -> list[Hashable]:
    """Draw ``size`` distinct elements without replacement from an explicit generator."""
    if not isinstance(rng, random.Random):
        raise SamplingInputError("Ein ausdrücklicher random.Random-Generator ist erforderlich.")
    if not 0 <= size <= len(population):
        raise SamplingInputError("Der Stichprobenumfang liegt außerhalb der Grundgesamtheit.")
    return rng.sample(list(population), size)


def stratified_allocation(
    total_sample_size: int, strata_sizes: Mapping[Hashable, int], method: str
) -> dict[Hashable, int]:
    """flowstat allocation: proportional ceil(n·Nh/N) or equal ceil(n/H), capped at Nh."""
    if method not in ("proportional", "equal"):
        raise SamplingInputError("Aufteilung muss 'proportional' oder 'equal' sein.")
    population = sum(strata_sizes.values())
    if population <= 0:
        raise SamplingInputError("Die Schichten enthalten keine Elemente.")
    count = len(strata_sizes)
    result = {}
    for key, size in strata_sizes.items():
        if method == "proportional":
            wanted = math.ceil(total_sample_size * (size / population))
        else:
            wanted = math.ceil(total_sample_size / count)
        result[key] = min(wanted, size)
    return result
