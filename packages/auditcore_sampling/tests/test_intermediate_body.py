"""Value-share draw of an intermediate body: ladder, value basis, escalation, randomness."""

from __future__ import annotations

import random

import pytest

from auditcore_sampling import SamplingInputError
from auditcore_sampling.intermediate_body import (
    PROFILES,
    VALUE_SHARE_ESCALATION,
    draw_order,
    escalation_ladder,
    profile,
    quality_sample,
    value_share_draw,
)

BASE = PROFILES[VALUE_SHARE_ESCALATION]


def draw(
    amounts: list[float], errors: list[float] | None = None, seed: int = 1, **changes: object
) -> tuple[list[int], list[int]]:
    chosen = BASE.with_parameters(**changes) if changes else BASE
    order = draw_order(random.Random(seed), len(amounts))
    result = value_share_draw(amounts, errors or [0.0] * len(amounts), order, chosen)
    return list(result.positions), list(result.stages)


def test_profile_is_versioned_and_neutral() -> None:
    assert (BASE.version, BASE.start_share, BASE.step, BASE.max_share) == (1, 0.25, 0.15, 0.85)
    assert BASE.id.startswith("zs.")
    assert escalation_ladder(BASE) == (0.25, 0.40, 0.55, 0.70, 0.85)
    assert escalation_ladder(BASE.with_parameters(start_share=0.1))[:3] == (0.1, 0.25, 0.4)
    assert escalation_ladder(BASE.with_parameters(start_share=0.9)) == (0.9,)
    with pytest.raises(SamplingInputError, match="Unbekanntes Verfahren"):
        profile("zs.andere")
    with pytest.raises(SamplingInputError, match="Unbekannte Parameter"):
        BASE.with_parameters(anteil=0.3)
    with pytest.raises(SamplingInputError, match="größer als 0"):
        BASE.with_parameters(step=0.0)


def test_value_basis_stops_at_the_target_share() -> None:
    amounts = [1000.0] + [10.0] * 99
    drawn, _ = draw(amounts)
    value = sum(amounts[i] for i in drawn)
    assert value >= 0.25 * sum(amounts)
    assert value - amounts[drawn[-1]] < 0.25 * sum(amounts)
    counts = {len(draw(amounts, seed=s)[0]) for s in range(1, 7)}
    assert len(counts) > 1


def test_escalation_runs_while_new_invoices_carry_errors() -> None:
    _, stages = draw([100.0] * 40, [50.0] * 40, seed=5)
    assert max(stages) == 5
    drawn, stages = draw([100.0] * 40, seed=5)
    assert set(stages) == {1}
    _, stages = draw([100.0] * 40, [50.0] * 40, seed=5, escalate=False)
    assert set(stages) == {1}


def test_empty_and_zero_volume_draw_nothing() -> None:
    assert draw([]) == ([], [])
    assert draw([0.0, 0.0]) == ([], [])


def test_inputs_are_checked() -> None:
    with pytest.raises(SamplingInputError, match="genau einmal"):
        value_share_draw([1.0, 2.0], [0.0, 0.0], [0, 0], BASE)
    with pytest.raises(SamplingInputError, match="gleich lang"):
        value_share_draw([1.0, 2.0], [0.0], [0, 1], BASE)
    with pytest.raises(SamplingInputError, match="endliche Zahl"):
        value_share_draw([float("inf")], [0.0], [0], BASE)
    with pytest.raises(SamplingInputError, match="random.Random"):
        draw_order(None, 3)  # type: ignore[arg-type]


def test_quality_sample_takes_every_kth() -> None:
    assert quality_sample(list(range(1, 45)), 20) == [20, 40]
    assert quality_sample([], 20) == []
    with pytest.raises(SamplingInputError):
        quality_sample([1], 0)
