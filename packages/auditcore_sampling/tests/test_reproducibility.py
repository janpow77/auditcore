"""Framework T-31 (F-17): same data, method, version and seed give the same sample."""

from __future__ import annotations

import random

from auditcore_sampling import __version__, draw_start, mus_size, simple_random, systematic_mus


def test_seeded_draw_repeats_and_plan_records_method_inputs_and_version() -> None:
    values = [random.Random(21).uniform(10, 50_000) for _ in range(500)]

    def run(seed: int) -> tuple[dict[str, object], tuple[int, ...], list[object]]:
        plan = mus_size(
            "portal.mus_poisson",
            population_value=sum(values),
            materiality=250_000.0,
            expected_error_rate=0.01,
            confidence_level=0.9,
        )
        rng = random.Random(seed)
        start = draw_start(rng, plan.interval)
        selection = systematic_mus(
            values,
            sample_size=plan.sample_size,
            interval=plan.interval,
            start=start,
            variant="portal",
        )
        return plan.to_dict(), selection.positions, simple_random(rng, range(500), 25)

    assert run(2026) == run(2026)
    assert run(2026)[1] != run(2027)[1]
    plan = run(2026)[0]
    assert plan["library"] == f"auditcore_sampling {__version__}"
    assert plan["method"] == "portal.mus_poisson"
    assert plan["inputs"]["confidence_level"] == 0.9 and plan["inputs"]["factor"] == 2.31
