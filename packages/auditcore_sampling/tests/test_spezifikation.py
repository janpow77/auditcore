"""Invariants of docs/spezifikation.md as Hypothesis properties (I1–I10)."""

from __future__ import annotations

import math
import random

from hypothesis import given, settings
from hypothesis import strategies as st

from auditcore_sampling import (
    MUS_POISSON,
    SRS_PORTAL,
    draw_start,
    mus_size,
    simple_random,
    srs_size,
    stratified_allocation,
    systematic_mus,
)
from auditcore_sampling.guidance import (
    KOM_TABLES,
    SRS,
    Z_TABLE,
    equal_probability_size,
    high_value_split,
    mus_conservative_size,
)
from auditcore_sampling.guidance.plan import largest_remainder
from auditcore_sampling.intermediate_body import (
    PROFILES,
    VALUE_SHARE_ESCALATION,
    draw_order,
    value_share_draw,
)

values = st.floats(min_value=1.0, max_value=1e7, allow_nan=False)
mus_levels = st.sampled_from(sorted(MUS_POISSON.factors))


@given(values, st.floats(100.0, 1e6), st.floats(0.0, 0.2), mus_levels, mus_levels)
def test_i1_mus_size_covers_the_population_and_grows_with_confidence(
    value: float, materiality: float, rate: float, a: float, b: float
) -> None:
    """I1: n ≥ 1, n × J = V, n wächst mit dem Konfidenzniveau."""
    low, high = sorted((a, b))
    plans = [
        mus_size(
            MUS_POISSON.id,
            population_value=value,
            materiality=materiality,
            expected_error_rate=rate,
            confidence_level=level,
        )
        for level in (low, high)
    ]
    assert plans[0].sample_size >= 1
    assert math.isclose(plans[0].interval * plans[0].sample_size, value, rel_tol=1e-9)
    assert plans[0].sample_size <= plans[1].sample_size


@given(st.integers(1, 100_000), st.floats(0.01, 0.5), st.floats(0.01, 0.5), st.floats(0.0, 1.0))
def test_i2_srs_size_stays_within_population_and_falls_with_tolerance(
    units: int, e1: float, e2: float, p: float
) -> None:
    """I2: 0 ≤ n ≤ N; größere Fehlertoleranz ergibt keinen größeren Umfang."""
    small, large = sorted((e1, e2))
    sizes = [
        srs_size(
            SRS_PORTAL.id,
            population_size=units,
            confidence_level=0.95,
            margin_of_error=e,
            expected_proportion=p,
        ).sample_size
        for e in (small, large)
    ]
    assert 0 <= sizes[1] <= sizes[0] <= units


@settings(max_examples=60)
@given(
    st.lists(st.one_of(st.none(), st.floats(-1e5, 1e6)), min_size=1, max_size=80),
    st.integers(1, 30),
    st.integers(0, 2**32),
)
def test_i3_portal_selection_takes_positive_units_once_and_all_certainty_items(
    amounts: list[float | None], n: int, seed: int
) -> None:
    """I3: Variante portal – Positionen eindeutig und positiv, Ausschlüsse vollständig,
    jede Einheit über dem Intervall ausgewählt."""
    positive = [v for v in amounts if v is not None and v > 0]
    total = math.fsum(positive)
    interval = total / n if total > 0 else 0.0
    start = draw_start(random.Random(seed), interval)
    chosen = systematic_mus(
        amounts, sample_size=n, interval=interval, start=start, variant="portal"
    )
    assert len(set(chosen.positions)) == len(chosen.positions)
    assert all((amounts[i] or 0) > 0 for i in chosen.positions)
    excluded = set(chosen.excluded_negative) | set(chosen.excluded_zero_or_missing)
    assert excluded == {i for i, v in enumerate(amounts) if v is None or v <= 0}
    if total > 0:
        assert {i for i, v in enumerate(amounts) if v and v > interval} <= set(chosen.positions)


@given(
    st.lists(st.integers(), min_size=0, max_size=50, unique=True), st.integers(0, 2**32), st.data()
)
def test_i4_random_selection_is_reproducible_and_without_replacement(
    population: list[int], seed: int, data: st.DataObject
) -> None:
    """I4: gleicher Seed → gleiche Auswahl; keine Wiederholung; Umfang wie verlangt."""
    size = data.draw(st.integers(0, len(population)))
    first = simple_random(random.Random(seed), population, size)
    assert first == simple_random(random.Random(seed), population, size)
    assert len(first) == len(set(first)) == size and set(first) <= set(population)


@given(
    st.integers(0, 500),
    st.dictionaries(st.text(min_size=1, max_size=3), st.integers(1, 200), min_size=1, max_size=6),
    st.sampled_from(["proportional", "equal"]),
)
def test_i5_allocation_respects_strata_and_reaches_the_total(
    total: int, strata: dict[str, int], method: str
) -> None:
    """I5: n_h ≤ N_h und Σ n_h ≥ min(n, N) bei proportionaler Aufteilung."""
    result = stratified_allocation(total, strata, method)
    assert all(result[k] <= strata[k] for k in strata)
    if method == "proportional":
        assert sum(result.values()) >= min(total, sum(strata.values()))


@given(
    st.integers(30, 50_000),
    st.floats(1e5, 1e10),
    st.floats(1.0, 1e5),
    st.sampled_from(sorted(Z_TABLE)),
    st.floats(0.0, 0.015),
)
def test_i6_guidance_size_reaches_the_planned_precision(
    units: int, value: float, sd: float, level: float, rate: float
) -> None:
    """I6: N z σ/√n ≤ TE − AE (außer bei Vollerhebung); Korrektur verkleinert nie."""
    plain = equal_probability_size(
        SRS,
        population_size=units,
        book_value=value,
        error_sd=sd,
        confidence_level=level,
        factor_profile=KOM_TABLES,
        anticipated_error_rate=rate,
    )
    corrected = equal_probability_size(
        SRS,
        population_size=units,
        book_value=value,
        error_sd=sd,
        confidence_level=level,
        factor_profile=KOM_TABLES,
        anticipated_error_rate=rate,
        finite_population_correction=True,
    )
    assert plain.sample_size >= min(units, math.floor(plain.raw_size))
    if plain.sample_size < units:
        margin = 0.02 * value - rate * value
        assert units * Z_TABLE[level] * sd / math.sqrt(plain.sample_size) <= margin * (1 + 1e-9)
    assert corrected.sample_size <= plain.sample_size


@given(st.integers(0, 1000), st.lists(st.floats(0.001, 1e9), min_size=1, max_size=20))
def test_i7_largest_remainder_is_exact_and_fair(total: int, weights: list[float]) -> None:
    """I7: Σ n_h = n und |n_h − n·w_h/Σw| < 1."""
    shares = largest_remainder(total, weights)
    whole = math.fsum(weights)
    assert sum(shares) == total
    assert all(abs(s - total * w / whole) < 1 for s, w in zip(shares, weights, strict=True))


@given(st.floats(1e5, 1e11), st.sampled_from([0.6, 0.7, 0.8, 0.9, 0.95]), st.floats(0.0, 0.009))
def test_i8_conservative_basic_precision_stays_within_the_margin(
    value: float, level: float, rate: float
) -> None:
    """I8: ohne Fehler ist BV × RF / n ≤ TE − AE × EF."""
    plan = mus_conservative_size(
        book_value=value,
        confidence_level=level,
        factor_profile=KOM_TABLES,
        anticipated_error_rate=rate,
    )
    rf = float(plan.inputs["reliability_factor"])  # type: ignore[arg-type]
    ef = float(plan.inputs["expansion_factor"])  # type: ignore[arg-type]
    assert value * rf / plan.sample_size <= (0.02 - rate * ef) * value * (1 + 1e-9)


@settings(max_examples=60)
@given(st.lists(st.floats(1.0, 1e7), min_size=1, max_size=200), st.integers(1, 100))
def test_i9_high_value_split_leaves_no_unit_above_the_interval(book: list[float], n: int) -> None:
    """I9: keine Einheit der Stichprobenschicht über SI; n_s = n − n_e ≥ 1."""
    split = high_value_split(book, n)
    rest = [v for i, v in enumerate(book) if i not in split.exhaustive]
    assert split.sampling_size == n - len(split.exhaustive) >= 1
    assert all(v <= split.interval * (1 + 1e-12) for v in rest)


@settings(max_examples=80)
@given(
    st.lists(st.floats(0.0, 1e5), min_size=0, max_size=60),
    st.lists(st.booleans(), min_size=60, max_size=60),
    st.integers(0, 2**32),
    st.sampled_from([0.1, 0.25, 0.4]),
)
def test_i10_value_share_draw_reaches_the_share_and_escalates_only_on_errors(
    amounts: list[float], faults: list[bool], seed: int, start: float
) -> None:
    """I10: eindeutige Positionen, Stufen aufsteigend, Anteil erreicht; ohne Fehler nur Stufe 1."""
    chosen = PROFILES[VALUE_SHARE_ESCALATION].with_parameters(start_share=start)
    order = draw_order(random.Random(seed), len(amounts))
    errors = [1.0 if faults[i] else 0.0 for i in range(len(amounts))]
    result = value_share_draw(amounts, errors, order, chosen)
    assert len(set(result.positions)) == len(result.positions)
    assert list(result.stages) == sorted(result.stages)
    total = result.population_value
    if total > 0 and len(result.positions) < len(amounts):
        assert result.drawn_value >= start * total * (1 - 1e-12)
    clean = value_share_draw(amounts, [0.0] * len(amounts), order, chosen)
    assert set(clean.stages) <= {1}
