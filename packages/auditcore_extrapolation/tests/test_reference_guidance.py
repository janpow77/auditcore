"""Reference cases: worked examples of the guidance EGESIF_16-0014-01, recomputed.

The examples print rounded intermediate values (sample sums and standard
deviations from spreadsheets that are not reproduced in the guidance). The
tests feed those printed aggregates into the library formulas and compare
with the printed results. Tolerances are stated per case; deviations above
0.01 % come from printed, rounded standard deviations or from misprints in
the guidance, each documented in docs/referenzfaelle.md.
"""

from __future__ import annotations

import math

import pytest

from auditcore_extrapolation import (
    INCONCLUSIVE,
    KOM_TABLES,
    NOT_MATERIAL,
    basic_reliability_factor,
    conclude,
    incremental_allowances,
    mean_per_unit_error,
    mus_precision,
    precision,
    ratio_error,
    reliability_factor,
    stratified_precision,
    tainting_projection,
    z_value,
)


def test_srs_standard_6_1_1_6() -> None:
    """80 %, N = 3,852, BV = 46,501,186, n = 53, ΣE = 7,797, ΣBV_i = 661,580."""
    z = z_value(0.80, KOM_TABLES)
    assert z == 1.282
    ee1 = mean_per_unit_error(3852, 7797, 53)
    ee2 = ratio_error(46_501_186, 7797, 661_580)
    # printed 566,703 and 548,058: the guidance used the unrounded error sum
    assert ee1 == pytest.approx(566_703, rel=1e-4)
    assert ee2 == pytest.approx(548_058, rel=1e-4)
    se1 = precision(3852, z, 758, 53)
    se2 = precision(3852, z, 755, 53)
    assert se1 == pytest.approx(514_169, abs=1)
    assert se2 == pytest.approx(512_134, abs=1)
    tolerable = 0.02 * 46_501_186
    assert tolerable == pytest.approx(930_024, abs=1)
    assert conclude(ee2, ee2 + se2, tolerable) == INCONCLUSIVE


def test_srs_stratified_6_1_2_6() -> None:
    """Two sampling strata and a 100 % stratum (error 889), 80 %."""
    ee1 = mean_per_unit_error(3582, 11_378, 90) + mean_per_unit_error(1225, 102_899, 31) + 889
    assert ee1 == pytest.approx(4_519_900, abs=10)  # printed with rounded averages 126 / 3,319
    ee2 = ratio_error(43_226_801, 11_378, 1_055_043) + ratio_error(
        1_348_417_361, 102_899, 35_377_240
    )
    assert ee2 + 889 == pytest.approx(4_389_095, abs=10)
    z = z_value(0.80, KOM_TABLES)
    se1 = stratified_precision(z, [(3582, 698, 90), (1225, 13_012, 31)])
    assert se1 == pytest.approx(3_695_304, rel=1e-3)  # printed sd rounded to whole euros
    se2 = stratified_precision(z, [(3582, 695, 90), (1225, 13_148, 31)])
    # the guidance prints √59 in the denominator but its result 3,733,563 belongs to √121
    assert se2 == pytest.approx(3_733_563, rel=1e-3)
    tolerable = 0.02 * 1_396_535_319
    assert conclude(ee2 + 889, ee2 + 889 + se2, tolerable) == NOT_MATERIAL


def test_difference_estimation_6_2_1_6() -> None:
    """60 %, N = 3,852, BV = 4,199,882,024, n = 101, ΣE = 1,339,765, s = 162,976."""
    z = z_value(0.60, KOM_TABLES)
    ee = mean_per_unit_error(3852, 1_339_765, 101)
    se = precision(3852, z, 162_976, 101)
    assert ee == pytest.approx(51_096_780, abs=1)
    assert se == pytest.approx(52_597_044, abs=1)
    book = 4_199_882_024
    corrected = book - ee
    assert corrected == pytest.approx(4_148_785_244, abs=1)
    assert corrected - se == pytest.approx(4_096_188_200, abs=1)
    assert (ee + se) / book == pytest.approx(0.0247, abs=5e-5)
    assert conclude(ee, ee + se, 0.02 * book) == INCONCLUSIVE


def test_mus_standard_6_3_1_7() -> None:
    """90 %, 8 high-value units (error 7,616,805), n_s = 69, Σ taintings 1.096, s_r 0.09."""
    book_s = 4_199_882_024 - 786_837_081
    interval = book_s / 69
    assert interval == pytest.approx(49_464_419, abs=1)
    ee_s = tainting_projection(interval, 1.096)
    assert ee_s == pytest.approx(54_213_004, abs=1)
    assert 7_616_805 + ee_s == pytest.approx(61_829_809, abs=1)
    se = mus_precision(z_value(0.90, KOM_TABLES), [(book_s, 69, 0.09)])
    assert se == pytest.approx(60_831_129, abs=1)
    assert 7_616_805 + ee_s + se == pytest.approx(122_660_937, abs=2)


def test_mus_stratified_6_3_2_7() -> None:
    """Two strata, exhaustive error 15,460,340, 90 %."""
    ee = (
        15_460_340
        + tainting_projection(22_520_054, 1.0234)
        + tainting_projection(22_541_865, 1.176)
    )
    assert ee == pytest.approx(65_016_597, abs=1)
    se = mus_precision(
        z_value(0.90, KOM_TABLES),
        [(1_643_963_923, 73, math.sqrt(0.000036)), (1_059_467_668, 47, math.sqrt(0.0081))],
    )
    assert se == pytest.approx(22_958_216, abs=1)
    assert ee + se == pytest.approx(87_974_813, abs=1)


def test_mus_conservative_6_3_5_7() -> None:
    """90 %, n = 136, SI = BV/n, 24 high-value units (error 7,843,574), Σ taintings 1.077."""
    book = 4_199_882_024
    assert math.ceil(book * 2.31 / (0.02 * book - 0.002 * book * 1.5)) == 136
    interval = book / 136
    assert interval == pytest.approx(30_881_485, abs=1)
    ee = 7_843_574 + tainting_projection(interval, 1.077)
    assert ee == pytest.approx(41_102_934, abs=1)
    basic = interval * basic_reliability_factor(0.90, KOM_TABLES)
    assert basic == pytest.approx(71_336_231, abs=1)
    # printed rows 12 to 16 of the allowance table (RF from Appendix 3)
    for order, rf, factor in ((12, 17.78, 0.18), (13, 18.96, 0.18), (16, 22.45, 0.16)):
        assert reliability_factor(order, 0.90, KOM_TABLES) == rf
        step = rf - reliability_factor(order - 1, 0.90, KOM_TABLES) - 1
        assert step == pytest.approx(factor, abs=0.005)
    printed_row_12 = 0.18 * 741_156
    assert printed_row_12 == pytest.approx(133_408, abs=1)
    se = basic + 14_430_761
    assert se == pytest.approx(85_766_992, abs=1)
    assert ee + se == pytest.approx(126_869_926, abs=2)


def test_mus_conservative_first_allowance_example_6_3_5_5() -> None:
    """Section 6.3.5.5: 10,000 of 40,000 (25 %), SI 200,000, factor from Appendix 3.

    The text computes 0.58 × 0.25 × 200,000 = 29,000 with RF(0) = 2.31 of
    Table 4; the worked example 6.3.5.7 uses RF(0) = 2.30 of Appendix 3
    (0.59), which is what the library applies for the allowances.
    """
    rows = incremental_allowances([("a", 0.25)], 200_000, 0.90, KOM_TABLES)
    assert rows[0].factor == pytest.approx(0.59)
    assert rows[0].allowance == pytest.approx(29_500)
    text_value = (3.89 - 2.31 - 1) * 0.25 * 200_000
    assert text_value == pytest.approx(29_000)


def test_nonstatistical_pps_6_4_7() -> None:
    """36 units, 4 high-value (error 80,028), 4 sampled with Σ taintings 0.0272."""
    ee = 80_028 + tainting_projection(9_619_263 / 4, 0.0272)
    assert ee == pytest.approx(145_439, abs=1)
    tolerable = 0.02 * 22_031_228
    assert tolerable == pytest.approx(440_625, abs=1)
    assert conclude(ee, None, tolerable) == NOT_MATERIAL
