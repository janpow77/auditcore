"""Reference cases of chapter 7 and section 6.5 of the guidance, recomputed.

7.6.5 (two-stage sampling), 6.5.3.3.2 (ETC: lead partner and a sample of
project partners), 7.7 (recalculation of the confidence level), 7.8.2
(group of programmes) and 7.9.5 (attribute sampling). Misprints are
documented in docs/referenzfaelle.md.
"""

from __future__ import annotations

import math

import pytest

from auditcore_extrapolation import (
    KOM_TABLES,
    MATERIAL,
    NOT_MATERIAL,
    SampleUnit,
    Stratum,
    SubSample,
    assess,
    evaluate_attributes,
    mean_per_unit_error,
    precision,
    project_subsample,
    recalculated_level,
    unit_from_subsample,
)

#: 7.6.5: operation id, book value, payment claims, audited expenditure, error, printed EE.
TOP_OPERATIONS = (
    ("243", 90_142_818, 629, 7_829, 845, 9_729_299),
    ("6324", 89_027_451, 1239, 1_409, 76, 4_802_048),
    ("734", 79_908_909, 729, 56_729, 1_991, 2_804_538),
    ("451", 79_271_094, 769, 48_392, 3_080, 5_045_358),
    ("95", 89_771_154, 2839, 3_078, 81, 2_362_399),
    ("9458", 100_525_834, 4818, 67_128, 419, 627_463),
    ("849", 165_336_715, 1972, 12_345, 1_220, 16_339_473),
    ("872", 92_853_106, 1256, 29_735, 1_544, 4_821_429),
)


def _subsample(unit: str, book: float, claims: int, audited: float, error: float) -> SubSample:
    items = tuple(SampleUnit(f"{unit}-{j}", audited / 40, error / 40) for j in range(40))
    return SubSample(
        unit, "ratio", (Stratum("Zahlungsanträge", book, items, population_size=claims),)
    )


def test_two_stage_sampling_7_6_5() -> None:
    """MUS for operations (90 %), ratio estimation within the 8 high-value operations."""
    top = []
    for unit, book, claims, audited, error, printed in TOP_OPERATIONS:
        operation, sub = unit_from_subsample(_subsample(unit, book, claims, audited, error))
        assert sub.projected_error == pytest.approx(printed, abs=1)
        assert not sub.warnings  # 40 claims ≥ 30
        top.append(operation)
    assert math.fsum(u.random_error for u in top) == pytest.approx(46_532_007, abs=1)
    # 69 sampled operations with Σ E_i/BV_i = 1.034 (errors partly from sub-samples, 7.6.3)
    sampled = tuple(SampleUnit(f"o{i}", 1_000_000, 1_000_000 * 1.034 / 69) for i in range(69))
    stratum = Stratum("Programm", 4_199_882_024, sampled, tuple(top))
    result = assess("mus.standard", [stratum], confidence_level=0.9, factor_profile=KOM_TABLES)
    assert stratum.sampling_book_value / 69 == pytest.approx(49_464_419, abs=1)
    assert result.projection.projected_random_error == pytest.approx(97_678_216, abs=2)
    assert result.total_error_rate.rate == pytest.approx(0.0233, abs=5e-5)
    assert result.total_error_rate.conclusion == MATERIAL


#: 6.5.3.3.2: operation, lead partner BV, its error, partners BV, audited partner BV, error.
ETC_OPERATIONS = (
    ("864", 890_563, 0, 234_567, 37_147, 0),
    ("12895", 1_278_327, 0, 834_459, 164_152, 0),
    ("6724", 658_748, 5_274, 766_567, 152_024, 23),
    ("763", 234_739, 20_327, 666_578, 83_384, 0),
    ("65a", 987_329, 0, 245_538, 56_318, 127),
    ("3", 1_045_698, 0, 344_765, 101_258, 0),
    ("65b", 895_398, 0, 678_927, 97_656, 0),
    ("567", 444_584, 0, 1_023_346, 213_216, 1_264),
    ("24", 678_927, 0, 789_491, 137_311, 0),
)
ETC_PRINTED = {"6724": 5_390, "763": 20_327, "65a": 554, "567": 6_067}


def _etc_operation(row: tuple[str, int, int, int, int, int]) -> SubSample:
    unit, lead, lead_error, partners, audited, error = row
    return SubSample(
        unit,
        "ratio",
        (
            Stratum(
                "Lead-Partner", lead, exhaustive_units=(SampleUnit(f"{unit}-LP", lead, lead_error),)
            ),
            Stratum("Projektpartner", partners, (SampleUnit(f"{unit}-PP", audited, error),)),
        ),
    )


def test_etc_lead_partner_and_partner_sample_6_5_3_3_2() -> None:
    """Non-statistical, equal probabilities, ratio estimation at both stages."""
    operations = []
    for row in ETC_OPERATIONS:
        unit, sub = unit_from_subsample(_etc_operation(row))
        assert sub.projected_error == pytest.approx(ETC_PRINTED.get(row[0], 0), abs=0.5)
        assert sub.warnings  # one partner per operation: below 30 sub-units
        operations.append(unit)
    assert math.fsum(u.book_value for u in operations) == pytest.approx(12_698_551, abs=1)
    assert math.fsum(u.random_error for u in operations) == pytest.approx(32_338, abs=1)
    stratum = Stratum(
        "Programme",
        113_300_285,
        tuple(operations),
        (SampleUnit("HV", 4_411_965, 80_328),),
        population_size=47,
    )
    result = assess("nonstatistical.ratio", [stratum])
    # printed 357,622 from operation errors rounded to whole euros (Σ 32,338 instead of 32,337.4)
    assert result.projection.projected_random_error == pytest.approx(357_622, abs=6)
    assert result.total_error_rate.tolerable_error == pytest.approx(2_266_006, abs=1)
    assert result.total_error_rate.conclusion == NOT_MATERIAL


def test_subsample_projection_lists_its_derivation() -> None:
    result = project_subsample(_etc_operation(ETC_OPERATIONS[2]))
    assert result.book_value == 658_748 + 766_567
    assert result.exhaustive_items == 1 and result.sampled_items == 1
    assert result.steps[-1].source.endswith("7.6.3, 6.5.3.3.1")


def test_recalculated_confidence_level_7_7() -> None:
    """BV 1,858,233,036, 90 %: EE 14,568,765, SE 26,195,819 → z* 1.419, 84.4 %."""
    z_star, level = recalculated_level(1.645, 37_164_661, 14_568_765, 26_195_819)
    assert z_star == pytest.approx(1.419, abs=5e-4)
    assert level == pytest.approx(0.844, abs=5e-4)


def test_group_of_programmes_7_8_2() -> None:
    """80 %, mean-per-unit per programme; exhaustive errors 1,983 and 992."""
    z = 1.282
    overall = mean_per_unit_error(4987, 47_728, 95) + mean_per_unit_error(1728, 3298, 33) + 2975
    assert overall == pytest.approx(2_681_139, abs=1)
    rows = (
        (4987, 674, 95, 47_728, 1983, 85_672_981 + 12_286_448, (442_105, 2_507_452, 0.0256)),
        (1728, 1183, 33, 3298, 992, 19_885_000 + 6_143_224, (456_204, 173_687, 0.0067)),
    )
    for size, sd, n, errors, exhaustive, book, (se_printed, ee_printed, rate) in rows:
        se = precision(size, z, sd, n)
        ee = mean_per_unit_error(size, errors, n) + exhaustive
        assert se == pytest.approx(se_printed, abs=1)
        assert ee == pytest.approx(ee_printed, abs=1)
        assert ee / book == pytest.approx(rate, abs=5e-5)
    # row P of programme 1 is printed as 2.90 %; (M) + (L) over (A) + (B) is 3.01 %
    upper_rate = (2_507_452 + 442_105) / (85_672_981 + 12_286_448)
    assert upper_rate == pytest.approx(0.0301, abs=5e-5)
    assert precision(1728, z, 1122, 89) == pytest.approx(263_469, abs=1)
    assert mean_per_unit_error(1728, 8278, 89) + 992 == pytest.approx(161_715, abs=1)


def test_attribute_sampling_7_9_5() -> None:
    """3 deviations in 150 at 95 %: EDR 2 %; ULD 4.24 % (the guidance prints 2.3 %)."""
    result = evaluate_attributes(
        3, 150, confidence_level=0.95, factor_profile=KOM_TABLES, tolerable_rate=0.05
    )
    assert result.rate == pytest.approx(0.02)
    assert result.upper_limit == pytest.approx(0.0424, abs=5e-5)
    assert result.conclusion == "supported"
    printed = 0.02 + 1.96 * 0.02 * 0.98 / math.sqrt(150)  # formula without square root
    assert printed == pytest.approx(0.023, abs=5e-4)
