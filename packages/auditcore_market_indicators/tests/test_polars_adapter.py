"""The optional polars adapter is a drop-in for krypto ``indicators/base.py``."""

from __future__ import annotations

from typing import Any

import pytest
from replay import column, fixture, legacy_values, same_value

import auditcore_market_indicators as mi

pl = pytest.importorskip("polars")
from auditcore_market_indicators import polars_adapter as pa  # noqa: E402


def frame(case: str) -> dict[str, Any]:
    names = ("high", "low", "close", "volume")
    return {k: pl.Series(k, column(case, k), dtype=pl.Float64) for k in names}


def adapter_call(observation: dict[str, Any], base: mi.IndicatorProfile) -> Any:
    f, p = frame(observation["case"]), observation["parameters"]
    name = observation["function"]
    if name in {"ema", "rsi"}:
        return getattr(pa, name)(f["close"], p["n"], profile=base)
    if name in {"atr", "adx"}:
        return getattr(pa, name)(f["high"], f["low"], f["close"], p["n"], profile=base)
    if name == "breakout":
        return pa.breakout(f["close"], f["volume"], **p)
    if name == "volume_factor":
        return pa.volume_factor(f["volume"], **p)
    if name == "zscore":
        return pa.zscore(f[observation["inputs"]], **p)
    return getattr(pa, name)(f["close"], **p)


WALK = [
    o
    for o in fixture()["observations"]
    if o["case"] in {"walk-300", "gap-close-inside", "zero-volume"}
    and o["exception"] is None
    and "." not in o["function"]
]


IDS = [f"{o['function']}-{o['case']}-{i}" for i, o in enumerate(WALK)]


@pytest.mark.parametrize("observation", WALK, ids=IDS)
def test_names_dtypes_and_values_match_the_original(
    observation: dict[str, Any], base: mi.IndicatorProfile
) -> None:
    result = adapter_call(observation, base)
    parts = list(result) if isinstance(result, tuple) else [result]
    output = observation["output"]
    recorded = output if isinstance(output, list) else [output]
    assert [(s.name, str(s.dtype)) for s in parts] == [(r["name"], r["dtype"]) for r in recorded]
    new = [v for s in parts for v in s.to_list()]
    old = legacy_values(observation)
    exact = observation["function"] in {"returns", "log_returns", "ema", "rsi", "adx"}
    if observation["function"] == "breakout":
        half = len(old) // 2
        for of, nf, os, ns in zip(old[:half], new[:half], old[half:], new[half:], strict=True):
            assert nf is None if ns is None else of == nf
            assert same_value(os, ns, exact=False)
        return
    assert all(same_value(o, n, exact=exact) for o, n in zip(old, new, strict=True))


def test_nan_is_rejected_and_nulls_are_gaps(base: mi.IndicatorProfile) -> None:
    with pytest.raises(mi.IndicatorInputError, match="nicht endlich"):
        pa.sma(pl.Series("c", [1.0, float("nan")]), 1)
    result = pa.ema(pl.Series("c", [None, 1.0, 2.0, 3.0]), 2, profile=base)
    assert result.to_list() == [None, None, 1.5, 2.5]
    with pytest.raises(mi.IndicatorInputError, match="polars.Series"):
        pa.sma([1.0, 2.0], 1)  # type: ignore[arg-type]


def test_macd_and_true_range_series(base: mi.IndicatorProfile) -> None:
    scoring = mi.load_profile("krypto.scoring_rsi_macd", "2026.09.1")
    close = pl.Series("close", column("walk-300", "close"))
    macd, signal, histogram = pa.macd(close, profile=scoring)
    assert (macd.name, signal.name, histogram.name) == ("macd", "signal", "histogram")
    assert macd.to_list() == mi.macd(close.to_list(), profile=scoring).macd
    tr = pa.true_range(close, close, close)
    assert tr.name == "tr" and tr.to_list()[0] == 0.0
    assert pa.rolling_std(close, 5).to_list() == mi.rolling_std(close.to_list(), 5)
