"""Replay support: map every recorded krypto call onto the library contract.

The fixture ``krypto_indicators_observed.json.gz`` holds the actually
executed original functions (``tools/capture_krypto_indicators.py``). Each
observation is classified:

* ``exact`` — loop-based originals (returns, log returns, EMA, RSI, ADX and
  the numpy EMA/RSI/MACD variants) are reproduced bit for bit;
* ``window`` — polars/numpy window statistics are reproduced within
  ``REL_TOL``/``ABS_TOL`` (MI-C04);
* a documented behavior change ``MI-Cxx`` whose new behavior is asserted
  explicitly (see ``docs/behavior-changes.md``).
"""

from __future__ import annotations

import gzip
import json
import math
from functools import cache
from pathlib import Path
from typing import Any

import auditcore_market_indicators as mi

FIXTURE = Path(__file__).parent / "fixtures" / "krypto_indicators_observed.json.gz"
VERSION = "2026.09.1"
#: MI-C04: window statistics (math.fsum) versus polars Kahan/Welford and numpy sums.
REL_TOL = 1e-10
ABS_TOL = 1e-12

EXACT = {
    "returns",
    "log_returns",
    "ema",
    "rsi",
    "adx",
    "rsi_macd.compute_rsi",
    "rsi_macd._ema",
    "rsi_macd.compute_macd",
    "confluence._ema_numpy",
    "hmm._ema",
}
NON_FINITE_CASES = {"nan-close", "inf-close"}
GAP_CASES = {"gap-close-inside", "gap-bar-inside", "gap-leading"}


@cache
def fixture() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(gzip.decompress(FIXTURE.read_bytes()))
    return data


@cache
def profile(name: str) -> mi.IndicatorProfile:
    return mi.load_profile(f"krypto.{name}", VERSION)


def revive(value: Any) -> Any:
    if isinstance(value, dict) and set(value) == {"$float"}:
        return float(value["$float"])
    return value


def column(case: str, name: str) -> list[Any]:
    return [revive(v) for v in fixture()["series"][case][name]]


def uses_close(observation: dict[str, Any]) -> bool:
    return observation["inputs"] not in {"volume", "hmm_log_returns"}


def hmm_log_returns(close: list[Any]) -> list[float | None]:
    """The inline log-return expression of ``hmm.build_features`` (first value 0)."""
    out: list[float | None] = [0.0] * len(close)
    for index in range(1, len(close)):
        current, previous = close[index], close[index - 1]
        if current is None or previous is None or not math.isfinite(current + previous):
            out[index] = None
            continue
        ratio = current / max(previous, 1e-12)
        # Non-finite logarithms make the original window NaN; here they are gaps.
        out[index] = math.log(ratio) if 0 < ratio < math.inf else None
    return out


def call(observation: dict[str, Any]) -> Any:
    """Run the library equivalent of one recorded call."""
    function, case, p = observation["function"], observation["case"], observation["parameters"]
    close, high, low = column(case, "close"), column(case, "high"), column(case, "low")
    volume = column(case, "volume")
    base = profile("indicators_base")
    if function == "returns":
        return mi.returns(close, p["periods"])
    if function == "log_returns":
        return mi.log_returns(close)
    if function == "sma":
        return mi.sma(close, p["n"])
    if function == "ema":
        return mi.ema(close, p["n"], profile=base)
    if function == "rsi":
        return mi.rsi(close, p["n"], profile=base)
    if function == "atr":
        return mi.atr(high, low, close, p["n"], profile=base)
    if function == "adx":
        return list(mi.adx(high, low, close, p["n"], profile=base))
    if function == "historical_volatility":
        return mi.historical_volatility(close, p["n"], p["annualization_factor"])
    if function == "volume_factor":
        return mi.volume_factor(volume, p["n"])
    if function == "zscore":
        return mi.zscore(close if observation["inputs"] == "close" else volume, p["n"])
    if function == "normalized_range":
        return mi.normalized_range(close, p["n"])
    if function == "breakout":
        return list(mi.breakout(close, volume, p["n"], p["vf_threshold"]))
    if function == "rsi_macd.compute_rsi":
        values = mi.rsi(close, p["period"], profile=profile("scoring_rsi_macd"))
        return values[-1] if values else None
    if function == "rsi_macd._ema":
        return mi.ema(close, p["period"], profile=profile("scoring_rsi_macd"))
    if function == "rsi_macd.compute_macd":
        periods = (p["fast"], p["slow"], p["signal"]) if p else (12, 26, 9)
        result = mi.macd(close, *periods, profile=profile("scoring_rsi_macd"))
        if len(close) < periods[1] or result.macd[-1] is None or result.signal[-1] is None:
            return None
        return {
            "histogram": result.histogram[-1],
            "macd": result.macd[-1],
            "macd_prev": result.macd[-2],
            "signal": result.signal[-1],
            "signal_prev": result.signal[-2],
        }
    if function == "confluence._ema_numpy":
        return mi.ema(close, p["n"], profile=profile("scoring_confluence"))
    if function == "hmm._ema":
        return mi.ema(close, p["span"], profile=profile("regime_hmm"))
    if function == "hmm._annualized_vol":
        std = mi.rolling_std(hmm_log_returns(close), p["window"])
        return [None if v is None else v * math.sqrt(365.0) for v in std]
    if function == "ma_crossover._rolling_mean":
        return mi.sma(close, p["window"])
    raise AssertionError(f"unmapped function {function}")


def legacy_values(observation: dict[str, Any]) -> list[Any]:
    """Recorded output flattened to one list (series, tuples of series, dicts)."""
    output = observation["output"]
    if output is None:
        return [None]
    if isinstance(output, dict) and "values" in output:
        return [revive(v) for v in output["values"]]
    if (
        isinstance(output, list)
        and output
        and isinstance(output[0], dict)
        and ("values" in output[0])
    ):
        return [revive(v) for part in output for v in part["values"]]
    if isinstance(output, dict):
        return [revive(output[k]) for k in sorted(output)]
    if isinstance(output, list):
        return [revive(v) for v in output]
    return [revive(output)]


def new_values(result: Any) -> list[Any]:
    if result is None:
        return [None]
    if isinstance(result, dict):
        return [result[k] for k in sorted(result)]
    if isinstance(result, list) and result and isinstance(result[0], list):
        return [v for part in result for v in part]
    if isinstance(result, list):
        return list(result)
    return [result]


def expected_change(observation: dict[str, Any]) -> str | None:
    """Documented behavior change that applies to this observation, if any."""
    function, case = observation["function"], observation["case"]
    if case in NON_FINITE_CASES and uses_close(observation):
        return "MI-C01"
    if function == "hmm._ema" and case == "length-0":
        return "MI-C07"
    if case in GAP_CASES and function in {
        "confluence._ema_numpy",
        "hmm._ema",
        "ma_crossover._rolling_mean",
    }:
        return "MI-C06"
    if case in {"gap-close-inside", "gap-bar-inside"} and function in {
        "rsi_macd._ema",
        "rsi_macd.compute_macd",
    }:
        return "MI-C05"
    return None


def same_value(old: Any, new: Any, *, exact: bool) -> bool:
    if isinstance(old, float) and not math.isfinite(old):
        return new is None  # MI-C02: undefined values are None
    if old is None or new is None or isinstance(old, bool) or isinstance(new, bool):
        return old == new
    if exact:
        return bool(old == new)
    return math.isclose(old, new, rel_tol=REL_TOL, abs_tol=ABS_TOL)
