"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

from decimal import Decimal
from importlib.metadata import distribution
from importlib.util import find_spec

from auditcore_extrapolation import (
    KOM_TABLES,
    ResidualInputs,
    SampleUnit,
    Stratum,
    assess,
    residual_error_rate,
    residual_from_total,
)


def main() -> None:
    """Guidance example 6.4.7 (non-statistical PPS), a MUS run and the RER template example B."""
    package = distribution("auditcore_extrapolation")
    assert package.version == "0.1.0"
    assert [r for r in package.requires or [] if "extra ==" not in r] == ["auditcore_common==0.1.1"]
    assert find_spec("auditcore") is None
    exhaustive = tuple(
        SampleUnit(f"h{i}", 12_411_965 / 4, e) for i, e in enumerate((50_000.0, 30_028.0, 0, 0))
    )
    sampled = tuple(
        SampleUnit(f"s{i}", 500_000.0, 500_000.0 * t) for i, t in enumerate((0.02, 0.0072, 0, 0))
    )
    stratum = Stratum("alle", 22_031_228.0, sampled, exhaustive, population_size=36)
    result = assess("nonstatistical.pps", [stratum])
    assert abs(result.total_error_rate.total_error - 145_439) < 1
    assert result.total_error_rate.conclusion == "not_material"
    mus = assess("mus.standard", [stratum], confidence_level=0.9, factor_profile=KOM_TABLES)
    assert mus.total_error_rate.upper_limit is not None
    rer = residual_error_rate(ResidualInputs(1000, Decimal("0.025"), financial_corrections=2.1))
    assert rer.exceeds_materiality and rer.rate_rounded == Decimal("0.0229")
    assert residual_from_total(mus.total_error_rate).rate is not None
    print("PASS: installed auditcore_extrapolation projection, TER and RER")


if __name__ == "__main__":
    main()
