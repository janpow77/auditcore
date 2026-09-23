"""Selection mechanics, explicit randomness and allocation (SA-C ids)."""

from __future__ import annotations

import random

import pytest

from auditcore_sampling import (
    SamplingInputError,
    draw_start,
    first_reaching,
    legacy,
    mus_size,
    simple_random,
    stratified_allocation,
    systematic_mus,
)
from auditcore_sampling._numeric import pandas_cumsum, pandas_sum


def brute_force(cumulative: list[float | None], targets: list[float]) -> list[int]:
    result = []
    for target in targets:
        for position, value in enumerate(cumulative):
            if value is not None and value >= target:
                result.append(position)
                break
    return result


def test_first_reaching_equals_linear_scan_including_negative_values() -> None:
    rng = random.Random(11)
    for _ in range(300):
        values = [rng.choice([None, rng.uniform(-500, 2000)]) for _ in range(rng.randint(0, 60))]
        cumulative = pandas_cumsum(values)
        targets = sorted(rng.uniform(-100, 5000) for _ in range(rng.randint(0, 40)))
        assert first_reaching(cumulative, targets) == brute_force(cumulative, targets)


def test_flowstat_keeps_repeated_hits_portal_deduplicates_and_excludes() -> None:
    values = [100.0, 5000.0, -50.0, None, 0.0, 100.0]
    flow = systematic_mus(values, sample_size=6, interval=900.0, start=10.0, variant="flowstat")
    portal = systematic_mus(values, sample_size=6, interval=900.0, start=10.0, variant="portal")
    assert flow.positions == (0, 1, 1, 1, 1, 1)
    assert portal.hits == (0, 1, 1, 1, 1, 1) and portal.positions == (0, 1)
    assert portal.excluded_negative == (2,) and portal.excluded_zero_or_missing == (3, 4)
    with pytest.raises(SamplingInputError):
        systematic_mus(values, sample_size=1, interval=1.0, start=0.0, variant="other")


def test_sa_c04_randomness_requires_an_explicit_generator_and_is_reproducible() -> None:
    with pytest.raises(SamplingInputError):
        draw_start(None, 10.0)  # type: ignore[arg-type]
    with pytest.raises(SamplingInputError):
        simple_random(None, [1, 2], 1)  # type: ignore[arg-type]
    values = [random.Random(1).uniform(100, 10000) for _ in range(200)]
    plan = mus_size(
        "portal.mus_poisson",
        population_value=pandas_sum(values),
        materiality=50_000.0,
        expected_error_rate=0.005,
        confidence_level=0.95,
    )

    def run(seed: int) -> tuple[int, ...]:
        start = draw_start(random.Random(seed), plan.interval)
        return systematic_mus(
            values,
            sample_size=plan.sample_size,
            interval=plan.interval,
            start=start,
            variant="portal",
        ).positions

    assert run(42) == run(42) and run(42) != run(43)
    assert draw_start(random.Random(1), 0.0) == 0.0
    first = simple_random(random.Random(5), list(range(50)), 10)
    assert first == simple_random(random.Random(5), list(range(50)), 10)
    assert len(set(first)) == 10
    with pytest.raises(SamplingInputError):
        simple_random(random.Random(5), [1, 2], 3)


def test_library_selection_matches_legacy_given_the_same_start() -> None:
    values = [random.Random(2).uniform(1, 9000) for _ in range(120)]
    summary, positions = legacy.flowstat_mus(
        values,
        template="run_mus_standard",
        materiality=30.0,
        confidence_level=0.95,
        expected_error_rate=0.005,
        start=3.5,
    )
    size, interval = legacy.flowstat_mus_size(
        pandas_sum(values), 30.0, 0.005, 0.95, numpy_scalars=True
    )
    direct = systematic_mus(
        values, sample_size=size, interval=interval, start=3.5, variant="flowstat"
    )
    assert list(direct.positions) == positions and summary["Stichprobenumfang"] == size


def test_stratified_allocation() -> None:
    sizes = {"A": 50, "B": 30, "C": 5}
    assert stratified_allocation(40, sizes, "proportional") == {"A": 24, "B": 15, "C": 3}
    assert stratified_allocation(40, sizes, "equal") == {"A": 14, "B": 14, "C": 5}
    for bad in (("other", sizes), ("equal", {"A": 0})):
        with pytest.raises(SamplingInputError):
            stratified_allocation(10, bad[1], bad[0])
