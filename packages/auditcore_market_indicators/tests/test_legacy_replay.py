"""Every recorded krypto indicator call is reproduced or covered by a documented change."""

from __future__ import annotations

import math
from typing import Any

import pytest
from replay import (
    EXACT,
    GAP_CASES,
    column,
    expected_change,
    fixture,
    legacy_values,
    new_values,
    same_value,
)
from replay import call as run

import auditcore_market_indicators as mi

OBSERVATIONS = fixture()["observations"]
IDS = [f"{o['function']}-{o['case']}-{i}" for i, o in enumerate(OBSERVATIONS)]


def breakout_flag_alignment(old: list[Any], new: list[Any]) -> bool:
    """MI-C03: the flag is ``None`` exactly where the strength cannot be evaluated."""
    half = len(old) // 2
    old_flag, old_strength = old[:half], old[half:]
    new_flag, new_strength = new[:half], new[half:]
    for of, os, nf, ns in zip(old_flag, old_strength, new_flag, new_strength, strict=True):
        undefined = os is None or (isinstance(os, float) and not math.isfinite(os))
        if undefined:
            if not (of is False and nf is None and ns is None):
                return False
        elif of != nf or not same_value(os, ns, exact=False):
            return False
    return True


def assert_gap_poisoning_is_replaced(observation: dict[str, Any]) -> None:
    """MI-C06: NaN gaps poison every later value in the numpy originals."""
    function, case = observation["function"], observation["case"]
    close = column(case, "close")
    if function in {"confluence._ema_numpy", "hmm._ema"} and case != "gap-leading":
        with pytest.raises(mi.IndicatorInputError, match="keine Lücken"):
            run(observation)
        return
    old, new = legacy_values(observation), new_values(run(observation))
    if function != "ma_crossover._rolling_mean":
        # Leading missing values: original all NaN, contract starts after the warm-up.
        assert all(isinstance(o, float) and not math.isfinite(o) for o in old)
        span = observation["parameters"].get("n") or observation["parameters"]["span"]
        present = sum(v is not None for v in close)
        assert any(n is not None for n in new) == (present >= span or function == "hmm._ema")
        return
    window = observation["parameters"]["window"]
    for index, (o, n) in enumerate(zip(old, new, strict=True)):
        part = close[max(0, index + 1 - window) : index + 1]
        if index + 1 < window or any(v is None for v in part):
            assert n is None
        elif isinstance(o, float) and math.isfinite(o):
            assert same_value(o, n, exact=False)
        else:
            assert n is not None  # original poisoned by an earlier gap


def assert_gap_in_first_window(observation: dict[str, Any], old: list[Any], new: list[Any]) -> None:
    """MI-C05: a gap in the first EMA window — NaN start, then a single-value restart."""
    close = column(observation["case"], "close")
    parameters = observation["parameters"]
    period = parameters.get("period") or parameters.get("slow", 26)
    if all(v is not None for v in close[:period]):
        assert all(same_value(o, n, exact=True) for o, n in zip(old, new, strict=True))
        return
    if observation["function"] == "rsi_macd._ema":
        assert isinstance(old[period - 1], float) and math.isnan(old[period - 1])
        assert new[period - 1] is None
        restart = old[period]
        assert restart == close[period]  # original re-seeds with the current value
    else:
        assert old != new


@pytest.mark.parametrize("observation", OBSERVATIONS, ids=IDS)
def test_recorded_call_is_reproduced(observation: dict[str, Any]) -> None:
    change = expected_change(observation)
    if change == "MI-C07":
        # Empty series: the original raises IndexError, the contract returns [].
        assert observation["exception"]["type"] == "IndexError" and run(observation) == []
        return
    if observation["exception"] is not None:
        # Parameter errors keep the original ValueError text (checked before the data).
        with pytest.raises(ValueError) as caught:
            run(observation)
        assert str(caught.value) == observation["exception"]["message"]
        assert observation["exception"]["type"] == "ValueError"
        return
    if change == "MI-C01":
        # Non-finite inputs are rejected instead of propagating NaN/inf.
        with pytest.raises(mi.IndicatorInputError, match="nicht endlich"):
            run(observation)
        return
    if change == "MI-C06":
        assert_gap_poisoning_is_replaced(observation)
        return
    old, new = legacy_values(observation), new_values(run(observation))
    if change == "MI-C05":
        assert_gap_in_first_window(observation, old, new)
        return
    assert len(old) == len(new)
    if observation["function"] == "breakout":
        assert breakout_flag_alignment(old, new)
        return
    exact = observation["function"] in EXACT
    mismatches = [
        (i, o, n)
        for i, (o, n) in enumerate(zip(old, new, strict=True))
        if not same_value(o, n, exact=exact)
    ]
    assert not mismatches, mismatches[:5]


def test_fixture_is_the_pinned_source_and_environment() -> None:
    data = fixture()
    assert data["status"] == "OBSERVED"
    assert data["source"]["repository"] == "janpow77/krypto"
    assert data["source"]["commit"] == "34d601726227f913548a118e144de5519eee0f3f"
    base = data["source"]["files"]["backend/app/services/indicators/base.py"]
    assert base == {"git_blob": "1bad05faad43915662f87971ef0d8ae55a1b4fe0", "loaded": "module"}
    assert data["environment"]["polars"] == "1.44.2"
    assert len(data["observations"]) == 1922
    assert len(data["series"]) == 31


def test_fixture_documents_the_legacy_semantics_that_profiles_keep() -> None:
    by = {(o["function"], o["case"], str(o["parameters"])): o for o in fixture()["observations"]}
    # MI-L02: flat market — base RSI says 100, rsi_macd says 50.
    flat_base = by[("rsi", "flat", "{'n': 14}")]["output"]["values"]
    assert flat_base[14:] == [100.0] * (40 - 14)
    assert by[("rsi_macd.compute_rsi", "flat", "{'period': 14}")]["output"] == 50.0
    # MI-L01: the ATR is a simple mean of the true range (flat bars: TR = 2).
    assert by[("atr", "flat", "{'n': 14}")]["output"]["values"][13:] == [2.0] * 27
    # MI-C02/C03: division by zero gives NaN; the flag is False although not evaluable.
    zero = by[("volume_factor", "zero-volume", "{'n': 3}")]["output"]["values"]
    assert zero[12] == {"$float": "nan"}
    flags = by[("breakout", "zero-volume", "{'n': 3, 'vf_threshold': 1.5}")]["output"]
    assert flags[0]["values"][12] is False and flags[1]["values"][12] == {"$float": "nan"}
    # MI-C07: the hmm EMA fails on an empty series.
    assert by[("hmm._ema", "length-0", "{'span': 3}")]["exception"]["type"] == "IndexError"


def test_gap_cases_really_contain_gaps() -> None:
    for case in GAP_CASES:
        assert any(v is None for v in column(case, "close"))
