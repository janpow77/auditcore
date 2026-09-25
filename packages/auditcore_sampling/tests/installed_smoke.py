"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

import random
from importlib.metadata import distribution
from importlib.util import find_spec

from auditcore_sampling import draw_start, mus_size, srs_size, systematic_mus
from auditcore_sampling.legacy import flowstat_mus_size


def main() -> None:
    """Sample sizes of both named methods, a seeded MUS draw and the legacy formula."""
    package = distribution("auditcore_sampling")
    assert package.version == "0.1.1"
    assert not [r for r in package.requires or [] if "extra ==" not in r]
    assert find_spec("auditcore") is None
    values = [random.Random(3).uniform(100, 10000) for _ in range(300)]
    total = sum(values)
    poisson = mus_size(
        "portal.mus_poisson",
        population_value=total,
        materiality=50_000.0,
        expected_error_rate=0.005,
        confidence_level=0.95,
    )
    z = mus_size(
        "flowstat.mus_z_attribute",
        population_value=total,
        materiality=50_000.0,
        expected_error_rate=0.005,
        confidence_level=0.95,
    )
    assert z.sample_size == 1 and poisson.sample_size > 30
    start = draw_start(random.Random(7), poisson.interval)
    first = systematic_mus(
        values,
        sample_size=poisson.sample_size,
        interval=poisson.interval,
        start=start,
        variant="portal",
    )
    again = systematic_mus(
        values,
        sample_size=poisson.sample_size,
        interval=poisson.interval,
        start=draw_start(random.Random(7), poisson.interval),
        variant="portal",
    )
    assert first == again and len(first.positions) == len(set(first.positions))
    assert (
        srs_size(
            "flowstat.srs_normal", population_size=1000, confidence_level=0.95, margin_of_error=0.05
        ).sample_size
        == 278
    )
    assert flowstat_mus_size(1_000_000.0, 50_000.0, 0.005, 0.95)[0] == 1
    print("PASS: installed auditcore_sampling sizes, seeded selection and legacy formula")


if __name__ == "__main__":
    main()
