"""Indicator contract: original krypto hand calculations, warm-up, variants, errors."""

from __future__ import annotations

import dataclasses
import math
import random

import pytest

import auditcore_market_indicators as mi

approx = pytest.approx


def walk(length: int, seed: int = 3) -> tuple[list[float], list[float], list[float]]:
    rng = random.Random(seed)
    close, high, low, price = [], [], [], 50.0
    for _ in range(length):
        opening = price
        price *= math.exp(rng.gauss(0, 0.02))
        close.append(price)
        high.append(max(opening, price) * 1.01)
        low.append(min(opening, price) * 0.99)
    return high, low, close


# --------------------------------------------------------------------------- #
# The hand calculations of krypto tests/backend/indicators/test_indicators_math.py
# and test_adx.py, run against the library (profile krypto.indicators_base).
# --------------------------------------------------------------------------- #
def test_returns_three_periods_matches_hand_calculation() -> None:
    result = mi.returns([100.0, 105.0, 110.0, 108.0, 115.0], 3)
    assert result[:3] == [None, None, None]
    assert result[3] == approx(0.08) and result[4] == approx(10 / 105)


def test_returns_one_period_and_zero_periods() -> None:
    assert mi.returns([10.0, 11.0, 12.1], 1)[1:] == [approx(0.1), approx(0.1)]
    with pytest.raises(ValueError, match="periods muss > 0 sein"):
        mi.returns([1.0, 2.0], 0)


def test_log_returns_matches_natural_log() -> None:
    result = mi.log_returns([100.0, 110.0, 121.0])
    assert result == [None, approx(math.log(1.1)), approx(math.log(121 / 110))]


def test_sma_window_three() -> None:
    assert mi.sma([1.0, 2.0, 3.0, 4.0, 5.0], 3) == [None, None, 2.0, 3.0, 4.0]


def test_ema_starts_with_sma_then_applies_alpha(base: mi.IndicatorProfile) -> None:
    assert mi.ema([10.0] * 6, 3, profile=base) == [None, None, 10.0, 10.0, 10.0, 10.0]
    assert mi.ema([10.0, 10.0, 10.0, 20.0], 3, profile=base)[2:] == [10.0, 15.0]


def test_rsi_rising_falling_alternating(base: mi.IndicatorProfile) -> None:
    assert mi.rsi([100.0 + i for i in range(6)], 3, profile=base)[3] == 100.0
    assert mi.rsi([100.0 - i for i in range(6)], 3, profile=base)[3] == 0.0
    last = mi.rsi([100.0, 101.0] * 3 + [100.0], 3, profile=base)[-1]
    assert last is not None and 40 <= last <= 60


def test_atr_basic_triangle(base: mi.IndicatorProfile) -> None:
    high = [105.0, 106.0, 107.0, 108.0, 109.0]
    low = [100.0, 101.0, 102.0, 103.0, 104.0]
    close = [103.0, 104.0, 105.0, 106.0, 107.0]
    result = mi.atr(high, low, close, 3, profile=base)
    assert result[:2] == [None, None] and result[2] == approx(5.0)


def test_historical_volatility_positive() -> None:
    result = mi.historical_volatility([100.0, 102.0, 99.0, 103.0, 98.0, 105.0, 97.0], 3, 1.0)
    assert result[:3] == [None, None, None]
    assert all(v is not None and v > 0 for v in result[3:])


def test_volume_factor_and_zscore() -> None:
    assert mi.volume_factor([100.0] * 6, 3)[2:] == [1.0] * 4
    assert mi.zscore([10.0] * 6, 3)[2:] == [None] * 4  # σ = 0: undefined, not NaN
    assert mi.zscore([0.0, 0.0, 3.0], 3)[2] == approx((3 - 1) / math.sqrt(3))


def test_normalized_range() -> None:
    assert mi.normalized_range([5.0] * 6, 3)[2:] == [0.0] * 4
    assert mi.normalized_range([10.0, 10.0, 12.0], 3)[2] == approx(2.0 / (32 / 3))


def test_breakout_flag_and_strength() -> None:
    close = [10.0, 10.0, 10.0, 10.0, 15.0]
    flag, strength = mi.breakout(close, [100.0, 100.0, 100.0, 100.0, 300.0], 3, 1.5)
    assert flag[3] is False and flag[4] is True
    assert strength[4] == approx(0.9, abs=1e-6)
    flag, _ = mi.breakout(close, [100.0, 100.0, 100.0, 100.0, 120.0], 3, 1.5)
    assert flag[4] is False


def test_adx_rising_falling_flat_and_short(base: mi.IndicatorProfile) -> None:
    n = 14
    up = [100.0 + 2 * i for i in range(60)]
    plus, minus, adx = mi.adx([c + 1 for c in up], [c - 1 for c in up], up, n, profile=base)
    assert adx[-1] is not None and adx[-1] > 40 and plus[-1] > minus[-1]  # type: ignore[operator]
    assert adx[2 * n - 1] is None and adx[2 * n] is not None
    down = [200.0 - 2 * i for i in range(60)]
    plus, minus, adx = mi.adx([c + 1 for c in down], [c - 1 for c in down], down, n, profile=base)
    assert adx[-1] > 40 and minus[-1] > plus[-1]  # type: ignore[operator]
    plus, minus, adx = mi.adx([101.0] * 60, [99.0] * 60, [100.0] * 60, n, profile=base)
    assert adx[-1] is not None and adx[-1] < 20 and plus[-1] == minus[-1] == 0.0
    short = [100.0 + i for i in range(10)]
    result = mi.adx([c + 1 for c in short], [c - 1 for c in short], short, n, profile=base)
    assert all(v is None for series in result for v in series)


# --------------------------------------------------------------------------- #
# Warm-up positions and undefined values
# --------------------------------------------------------------------------- #
def test_first_values_sit_at_the_documented_warm_up_positions(
    base: mi.IndicatorProfile, rsi_macd: mi.IndicatorProfile
) -> None:
    high, low, close = walk(80)

    def first(values: list[float | None]) -> int:
        return next(i for i, v in enumerate(values) if v is not None)

    assert first(mi.sma(close, 20)) == 19
    assert first(mi.ema(close, 20, profile=base)) == 19
    assert first(mi.rsi(close, 14, profile=base)) == 14
    assert first(mi.atr(high, low, close, 14, profile=base)) == 13
    assert first(mi.historical_volatility(close, 20)) == 20
    assert first(mi.zscore(close, 20)) == 19
    plus, _, adx = mi.adx(high, low, close, 14, profile=base)
    assert (first(plus), first(adx)) == (14, 28)
    macd = mi.macd(close, profile=rsi_macd)
    assert (first(macd.macd), first(macd.signal)) == (25, 33)


def test_outputs_never_contain_nan_or_infinity(base: mi.IndicatorProfile) -> None:
    close = [0.0, 0.0, 1.0, 0.0, 2.0, 2.0, 2.0, -1.0, 3.0, 3.0]
    volume = [0.0] * 10
    results = [
        mi.returns(close, 1),
        mi.log_returns(close),
        mi.zscore(close, 3),
        mi.normalized_range(close, 3),
        mi.volume_factor(volume, 3),
        *mi.breakout(close, volume, 2, 1.5),
        mi.rsi(close, 3, profile=base),
        *mi.adx(close, close, close, 2, profile=base),
    ]
    for series in results:
        for value in series:
            assert value is None or isinstance(value, bool) or math.isfinite(value)
    assert mi.returns(close, 1)[1] is None and mi.log_returns(close)[2] is None


def test_ema_value_depends_on_the_warm_up_window(base: mi.IndicatorProfile) -> None:
    """MI-K03: krypto recomputes EMA(50) on 60 bars; the start window changes the value."""
    _, _, close = walk(300)
    full = mi.ema(close, 50, profile=base)
    window = mi.ema(close[-60:], 50, profile=base)
    assert window[-1] != full[-1]
    assert abs(window[-1] - full[-1]) / full[-1] > 1e-6  # type: ignore[operator]


# --------------------------------------------------------------------------- #
# Profile variants
# --------------------------------------------------------------------------- #
def reference_rsi(close: list[float], n: int, smoothing: str) -> list[float | None]:
    deltas = [b - a for a, b in zip(close, close[1:], strict=False)]
    gains = [max(d, 0.0) for d in deltas]
    losses = [max(-d, 0.0) for d in deltas]
    out: list[float | None] = [None] * len(close)
    ag, al = sum(gains[:n]) / n, sum(losses[:n]) / n
    for index in range(n, len(close)):
        if index > n:
            g, lo = gains[index - 1], losses[index - 1]
            if smoothing == "wilder":
                ag, al = (ag * (n - 1) + g) / n, (al * (n - 1) + lo) / n
            elif smoothing == "ema":
                a = 2 / (n + 1)
                ag, al = a * g + (1 - a) * ag, a * lo + (1 - a) * al
            else:
                ag, al = sum(gains[index - n : index]) / n, sum(losses[index - n : index]) / n
        out[index] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    return out


@pytest.mark.parametrize("smoothing", ["wilder", "ema", "sma"])
def test_rsi_smoothing_variants_follow_their_definition(
    base: mi.IndicatorProfile, smoothing: str
) -> None:
    _, _, close = walk(120)
    rule = dataclasses.replace(base.rsi, smoothing=smoothing)  # type: ignore[type-var]
    profile = dataclasses.replace(base, rsi=rule)
    got = mi.rsi(close, 14, profile=profile)
    for g, e in zip(got, reference_rsi(close, 14, smoothing), strict=True):
        assert (g is None and e is None) or g == approx(e, rel=1e-12)
    if smoothing != "wilder":
        assert got[-1] != mi.rsi(close, 14, profile=base)[-1]


def test_rsi_flat_market_value_is_a_profile_choice(
    base: mi.IndicatorProfile, rsi_macd: mi.IndicatorProfile
) -> None:
    """MI-L02: no movement at all → 100 (indicators/base) versus 50 (scoring/rsi_macd)."""
    flat = [7.0] * 20
    assert mi.rsi(flat, 14, profile=base)[-1] == 100.0
    assert mi.rsi(flat, 14, profile=rsi_macd)[-1] == 50.0
    rising = [7.0 + i for i in range(20)]
    assert mi.rsi(rising, 14, profile=base)[-1] == mi.rsi(rising, 14, profile=rsi_macd)[-1]


@pytest.mark.parametrize("smoothing", ["sma", "wilder", "ema"])
def test_atr_smoothing_variants(base: mi.IndicatorProfile, smoothing: str) -> None:
    high, low, close = walk(60)
    tr = mi.true_range(high, low, close)
    profile = dataclasses.replace(base, atr=mi.profiles.AtrRule(smoothing))  # type: ignore[arg-type]
    got = mi.atr(high, low, close, 14, profile=profile)
    seed = sum(tr[:14]) / 14  # type: ignore[arg-type]
    assert got[:13] == [None] * 13 and got[13] == approx(seed, rel=1e-14)
    state, alpha = seed, 2 / 15
    for index in range(14, 60):
        value = tr[index]
        assert value is not None
        if smoothing == "sma":
            expected = sum(tr[index - 13 : index + 1]) / 14  # type: ignore[arg-type]
        elif smoothing == "wilder":
            state = expected = (state * 13 + value) / 14
        else:
            state = expected = alpha * value + (1 - alpha) * state
        assert got[index] == approx(expected, rel=1e-12)


def test_recursive_atr_rejects_gaps_after_the_start(base: mi.IndicatorProfile) -> None:
    high, low, close = walk(60)
    high[30] = None  # type: ignore[call-overload]
    wilder = dataclasses.replace(base, atr=mi.profiles.AtrRule("wilder"))
    with pytest.raises(mi.IndicatorInputError, match="lückenlose"):
        mi.atr(high, low, close, 14, profile=wilder)
    sma_result = mi.atr(high, low, close, 14, profile=base)
    assert sma_result[30:44] == [None] * 14 and sma_result[44] is not None


def test_ema_seed_and_gap_variants(
    base: mi.IndicatorProfile,
    rsi_macd: mi.IndicatorProfile,
    confluence: mi.IndicatorProfile,
    hmm: mi.IndicatorProfile,
) -> None:
    values: list[float | None] = [None, 2.0, 4.0, 6.0, None, 8.0, 10.0, 12.0]
    assert mi.ema(values, 3, profile=base) == [None, None, None, 4.0, None, 6.0, 8.0, 10.0]
    assert mi.ema(values, 3, profile=rsi_macd) == [None, None, None, 4.0, 4.0, 6.0, 8.0, 10.0]
    with pytest.raises(mi.IndicatorInputError, match="index|fehlt"):
        mi.ema(values, 3, profile=confluence)
    assert mi.ema([None, 2.0, 4.0, 6.0], 3, profile=confluence) == [None, None, None, 4.0]
    assert mi.ema([2.0, 4.0, 6.0], 3, profile=hmm) == [2.0, 3.0, 4.5]
    assert mi.ema([], 3, profile=hmm) == [] and mi.ema([None, None], 3, profile=hmm) == [
        None,
        None,
    ]


def test_zero_move_versus_error_gap_handling(base: mi.IndicatorProfile) -> None:
    _, _, close = walk(40)
    gapped: list[float | None] = list(close)
    gapped[20] = None
    assert mi.rsi(gapped, 14, profile=base)[25] is not None
    strict = dataclasses.replace(base, rsi=dataclasses.replace(base.rsi, gaps="error"))  # type: ignore[type-var]
    with pytest.raises(mi.IndicatorInputError, match="close\\[20\\] fehlt"):
        mi.rsi(gapped, 14, profile=strict)
    strict_adx = dataclasses.replace(base, adx=mi.profiles.AdxRule("error"))
    with pytest.raises(mi.IndicatorInputError, match="close\\[20\\] fehlt"):
        mi.adx(close, close, gapped, 5, profile=strict_adx)


def test_macd_is_the_difference_of_both_emas(rsi_macd: mi.IndicatorProfile) -> None:
    _, _, close = walk(60)
    result = mi.macd(close, 12, 26, 9, profile=rsi_macd)
    fast = mi.ema(close, 12, profile=rsi_macd)
    slow = mi.ema(close, 26, profile=rsi_macd)
    assert result.macd[40] == fast[40] - slow[40]  # type: ignore[operator]
    assert result.histogram[40] == result.macd[40] - result.signal[40]  # type: ignore[operator]


def test_profiles_without_an_indicator_refuse_it(
    base: mi.IndicatorProfile, confluence: mi.IndicatorProfile
) -> None:
    with pytest.raises(mi.ProfileError, match="keinen RSI"):
        mi.rsi([1.0] * 20, 14, profile=confluence)
    with pytest.raises(mi.ProfileError, match="keinen MACD"):
        mi.macd([1.0] * 40, profile=base)
    with pytest.raises(mi.ProfileError, match="keine ATR"):
        mi.atr([1.0], [1.0], [1.0], 1, profile=confluence)
    with pytest.raises(TypeError):
        mi.ema([1.0, 2.0], 2)  # type: ignore[call-arg]


# --------------------------------------------------------------------------- #
# Input contract
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("values", "message"),
    [
        ([1.0, float("nan")], "nicht endlich"),
        ([1.0, float("inf")], "nicht endlich"),
        ([1.0, True], "keine Zahl"),
        ([1.0, "2"], "keine Zahl"),
        ("123", "Folge"),
    ],
)
def test_invalid_values_are_rejected(values: object, message: str) -> None:
    with pytest.raises(mi.IndicatorInputError, match=message):
        mi.sma(values, 1)  # type: ignore[arg-type]


def test_parameter_validation(base: mi.IndicatorProfile) -> None:
    with pytest.raises(mi.IndicatorInputError, match="ganze Zahl"):
        mi.sma([1.0], 1.0)  # type: ignore[arg-type]
    with pytest.raises(mi.IndicatorInputError, match="ganze Zahl"):
        mi.sma([1.0], True)
    with pytest.raises(ValueError, match="n muss > 0 sein"):
        mi.volume_factor([1.0], 0)
    with pytest.raises(ValueError, match="n muss > 1 sein"):
        mi.rolling_std([1.0, 2.0], 1)
    with pytest.raises(mi.IndicatorInputError, match="annualization_factor muss > 0"):
        mi.historical_volatility([1.0, 2.0, 3.0], 2, 0.0)
    with pytest.raises(mi.IndicatorInputError, match="vf_threshold muss endlich"):
        mi.breakout([1.0], [1.0], 1, float("nan"))
    with pytest.raises(mi.IndicatorInputError, match="unterschiedlich lang"):
        mi.true_range([1.0, 2.0], [1.0], [1.0, 2.0])
    assert mi.sma([1, 2, 3], 3) == [None, None, 2.0]  # integers are accepted


def test_method_reference_names_library_method_parameters_and_profile(
    base: mi.IndicatorProfile,
) -> None:
    ref = mi.method_reference("ema", profile=base, n=20)
    assert ref["library"] == f"auditcore_market_indicators {mi.__version__}"
    assert ref["method"] == mi.METHOD and ref["parameters"] == {"n": 20}
    assert ref["profile"] == base.reference
    assert mi.method_reference("sma", n=20)["profile"] is None
    with pytest.raises(mi.IndicatorInputError, match="ausdrücklich"):
        mi.method_reference("rsi", n=14)
    with pytest.raises(mi.IndicatorInputError, match="Unbekannter"):
        mi.method_reference("stochastic")


def test_decided_profile_uses_wilder_atr_and_flat_rsi_of_fifty() -> None:
    decided = mi.load_profile(*mi.RECOMMENDED_PROFILE)
    base = mi.load_profile("krypto.indicators_base", "2026.09.1")
    high, low, close = walk(300)
    tr = mi.true_range(high, low, close)
    atr = mi.atr(high, low, close, 14, profile=decided)
    state = sum(tr[:14]) / 14  # type: ignore[arg-type]
    for index in range(14, 300):
        state = (state * 13 + tr[index]) / 14  # type: ignore[operator]
    assert atr[-1] == approx(state, rel=1e-12)
    assert atr[-1] != mi.atr(high, low, close, 14, profile=base)[-1]
    assert mi.rsi([7.0] * 20, 14, profile=decided)[-1] == 50.0
    assert mi.rsi(close, 14, profile=decided) == mi.rsi(close, 14, profile=base)
    assert mi.ema(close, 50, profile=decided) == mi.ema(close, 50, profile=base)


def test_recommended_lookback_removes_the_start_dependence_of_ema50() -> None:
    """MI-K03 entschieden: 250 Kerzen statt 60; EMA(50) ist dann praktisch startunabhängig."""
    decided = mi.load_profile(*mi.RECOMMENDED_PROFILE)
    assert decided.min_lookback == 250
    _, _, close = walk(600)
    full = mi.ema(close, 50, profile=decided)[-1]
    short = mi.ema(close[-60:], 50, profile=decided)[-1]
    long = mi.ema(close[-decided.min_lookback :], 50, profile=decided)[-1]
    assert full is not None and short is not None and long is not None
    # gemessen: 60 Kerzen 1,5 % Abweichung, 250 Kerzen 1,4e-6
    assert abs(long - full) / full < 1e-5 and abs(short - full) / full > 1e-3
