"""Capture the actual krypto indicator behavior before extraction.

Run with an interpreter that provides polars (>= 1.21, the first release with
``min_samples``) and numpy::

    python -I tools/capture_krypto_indicators.py <krypto checkout> \
        tests/fixtures/krypto_indicators_observed.json.gz

``backend/app/services/indicators/base.py`` imports only ``math`` and
``polars``; it is loaded unchanged from its file after verifying the pinned
Git blob. The scoring and regime modules import SQLAlchemy and ORM models, so
only the named, unchanged top-level functions are compiled from their verified
blobs (AST extraction) and executed with numpy. No application package,
database or network is used. All time series are synthetic and generated with
a fixed seed.
"""

from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import importlib.util
import json
import math
import platform
import random
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

REPOSITORY = "janpow77/krypto"
COMMIT = "34d601726227f913548a118e144de5519eee0f3f"
BASE = ("backend/app/services/indicators/base.py", "1bad05faad43915662f87971ef0d8ae55a1b4fe0")
EXTRACTED = {
    "rsi_macd": (
        "backend/app/services/scoring/rsi_macd.py",
        "a3e8960b35f650c10e24451786d57fba404ae764",
        ["compute_rsi", "_ema", "compute_macd"],
    ),
    "confluence": (
        "backend/app/services/scoring/confluence.py",
        "52af074e196f454ce2715d316131841157de58cc",
        ["_ema_numpy"],
    ),
    "hmm": (
        "backend/app/services/regime/hmm.py",
        "2ae11f35cd4a87ab74395a0a589dbfcab4f15d4e",
        ["_ema", "_annualized_vol"],
    ),
    "ma_crossover": (
        "backend/app/services/scoring/ma_crossover.py",
        "1266032a8d8eaf96576095eb815d3f7a70d973e1",
        ["_rolling_mean"],
    ),
}


def git_blob(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def plain(value: Any) -> Any:
    """JSON value; floats keep their exact repr, NaN/inf are tagged."""
    import numpy as np

    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if isinstance(value, np.ndarray):
        return [plain(v) for v in value.tolist()]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return {"$float": repr(value)}
    return value


# --------------------------------------------------------------------------- #
# Synthetic, seeded OHLCV series
# --------------------------------------------------------------------------- #
Bars = dict[str, list[Any]]


def walk(seed: int, length: int, start: float = 100.0, digits: int | None = None) -> Bars:
    rng = random.Random(seed)
    close: list[Any] = []
    high: list[Any] = []
    low: list[Any] = []
    volume: list[Any] = []
    price = start
    for _ in range(length):
        opening = price
        price = price * math.exp(rng.gauss(0.0005, 0.03))
        top = max(opening, price) * (1 + abs(rng.gauss(0, 0.01)))
        bottom = min(opening, price) * (1 - abs(rng.gauss(0, 0.01)))
        vol = math.exp(rng.gauss(10, 0.6))
        if digits is not None:
            price, top, bottom, vol = (round(v, digits) for v in (price, top, bottom, vol))
        close.append(price)
        high.append(top)
        low.append(bottom)
        volume.append(vol)
    return {"high": high, "low": low, "close": close, "volume": volume}


def from_close(close: list[Any], spread: float = 1.0, volume: float = 1000.0) -> Bars:
    return {
        "high": [None if c is None else c + spread for c in close],
        "low": [None if c is None else c - spread for c in close],
        "close": list(close),
        "volume": [volume] * len(close),
    }


def with_values(bars: Bars, column: str, changes: dict[int, Any]) -> Bars:
    out = {k: list(v) for k, v in bars.items()}
    for index, value in changes.items():
        out[column][index] = value
    return out


def series_cases() -> dict[str, Bars]:
    cases: dict[str, Bars] = {
        "walk-300": walk(1, 300),
        "walk-60-pipeline-lookback": walk(2, 60),
        "walk-120-rounded-2": walk(3, 120, digits=2),
        "walk-80-microcap": walk(4, 80, start=3.2e-6),
        "walk-80-btc": walk(5, 80, start=64000.0, digits=2),
    }
    for length in (0, 1, 2, 3, 13, 14, 15, 27, 28, 29, 30):
        cases[f"length-{length}"] = walk(10 + length, length)
    cases["flat"] = from_close([100.0] * 40)
    cases["rising"] = from_close([100.0 + 2 * i for i in range(40)])
    cases["falling"] = from_close([200.0 - 2 * i for i in range(40)])
    cases["alternating"] = from_close([100.0 + (i % 2) for i in range(40)])
    cases["step-breakout"] = {
        "high": [10.5] * 24 + [15.5],
        "low": [9.5] * 24 + [14.5],
        "close": [10.0] * 24 + [15.0],
        "volume": [100.0] * 24 + [300.0],
    }
    base = walk(6, 45)
    cases["gap-close-inside"] = with_values(base, "close", {5: None, 20: None})
    cases["gap-bar-inside"] = with_values(
        with_values(with_values(base, "close", {20: None}), "high", {20: None}), "low", {20: None}
    )
    cases["gap-leading"] = with_values(
        with_values(with_values(base, "close", {0: None, 1: None, 2: None}), "high", {0: None}),
        "low",
        {0: None},
    )
    cases["gap-volume"] = with_values(base, "volume", {30: None})
    cases["zero-price"] = with_values(base, "close", {10: 0.0})
    cases["negative-price"] = with_values(base, "close", {10: -5.0})
    cases["nan-close"] = with_values(base, "close", {7: float("nan")})
    cases["inf-close"] = with_values(base, "close", {7: float("inf")})
    cases["high-below-low"] = with_values(with_values(base, "high", {12: 50.0}), "low", {12: 150.0})
    cases["zero-volume"] = with_values(base, "volume", {i: 0.0 for i in range(10, 35)})
    return cases


# --------------------------------------------------------------------------- #
# Parameter grid per original function
# --------------------------------------------------------------------------- #
BASE_CALLS: list[tuple[str, str, dict[str, Any]]] = [
    *(("returns", "close", {"periods": p}) for p in (1, 4, 24, 0, -1)),
    ("log_returns", "close", {}),
    *(("sma", "close", {"n": n}) for n in (1, 3, 20, 0)),
    *(("ema", "close", {"n": n}) for n in (1, 3, 12, 20, 26, 50, 0)),
    *(("rsi", "close", {"n": n}) for n in (1, 3, 14, 0)),
    *(("atr", "hlc", {"n": n}) for n in (1, 3, 14, 0)),
    *(("adx", "hlc", {"n": n}) for n in (1, 3, 14, 0)),
    ("historical_volatility", "close", {"n": 20, "annualization_factor": 365.0}),
    ("historical_volatility", "close", {"n": 3, "annualization_factor": 1.0}),
    ("historical_volatility", "close", {"n": 20, "annualization_factor": 8760.0}),
    ("historical_volatility", "close", {"n": 1, "annualization_factor": 365.0}),
    *(("volume_factor", "volume", {"n": n}) for n in (3, 20)),
    *(("zscore", "close", {"n": n}) for n in (3, 20, 1)),
    ("zscore", "volume", {"n": 20}),
    *(("normalized_range", "close", {"n": n}) for n in (3, 20, 1)),
    ("breakout", "close+volume", {"n": 3, "vf_threshold": 1.5}),
    ("breakout", "close+volume", {"n": 20, "vf_threshold": 1.8}),
    ("breakout", "close+volume", {"n": 0, "vf_threshold": 1.8}),
]

VARIANT_CALLS: list[tuple[str, str, dict[str, Any]]] = [
    *(("rsi_macd.compute_rsi", "close", {"period": p}) for p in (3, 14)),
    *(("rsi_macd._ema", "close", {"period": p}) for p in (3, 12, 26)),
    ("rsi_macd.compute_macd", "close", {}),
    ("rsi_macd.compute_macd", "close", {"fast": 3, "slow": 6, "signal": 3}),
    *(("confluence._ema_numpy", "close", {"n": n}) for n in (3, 20, 50)),
    *(("hmm._ema", "close", {"span": s}) for s in (3, 50)),
    *(("hmm._annualized_vol", "hmm_log_returns", {"window": w}) for w in (3, 20)),
    *(("ma_crossover._rolling_mean", "close", {"window": w}) for w in (3, 20, 50)),
]


def load_base(root: Path) -> Any:
    path = root / BASE[0]
    if git_blob(path) != BASE[1]:
        raise SystemExit(f"{BASE[0]} is not the pinned blob")
    spec = importlib.util.spec_from_file_location("krypto_indicators_base", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_extracted(root: Path) -> dict[str, dict[str, Callable[..., Any]]]:
    import numpy as np

    out: dict[str, dict[str, Callable[..., Any]]] = {}
    for key, (relative, blob, names) in EXTRACTED.items():
        path = root / relative
        if git_blob(path) != blob:
            raise SystemExit(f"{relative} is not the pinned blob")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in set(names)]
        if {n.name for n in nodes} != set(names):
            raise SystemExit(f"{relative}: missing {set(names) - {n.name for n in nodes}}")
        module = ast.Module(body=nodes, type_ignores=[])
        namespace: dict[str, Any] = {
            "np": np,
            "math": math,
            "Sequence": list,
            "__name__": f"krypto_{key}",
        }
        exec(compile(module, str(path), "exec"), namespace)  # noqa: S102 - pinned source
        out[key] = {name: namespace[name] for name in names}
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("krypto", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    root = args.krypto.resolve()
    head = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    if head != COMMIT:
        raise SystemExit(f"krypto checkout is at {head}, expected {COMMIT}")

    import numpy as np
    import polars as pl

    base = load_base(root)
    variants = load_extracted(root)

    def series(name: str, values: list[Any]) -> Any:
        return pl.Series(name, values, dtype=pl.Float64)

    def dump_series(value: Any) -> dict[str, Any]:
        return {"name": value.name, "dtype": str(value.dtype), "values": plain(value.to_list())}

    cases = series_cases()
    observed: list[dict[str, Any]] = []
    for case_name, bars in cases.items():
        for function, inputs, params in BASE_CALLS:
            high = series("high", bars["high"])
            low = series("low", bars["low"])
            close = series("close", bars["close"])
            volume = series("volume", bars["volume"])
            if inputs == "close":
                positional: tuple[Any, ...] = (close,)
            elif inputs == "volume":
                positional = (volume,)
            elif inputs == "hlc":
                positional = (high, low, close)
            else:
                positional = (close, volume)
            try:
                result = getattr(base, function)(*positional, **params)
                if isinstance(result, tuple):
                    output: Any = [dump_series(r) for r in result]
                else:
                    output = dump_series(result)
                exception = None
            except Exception as exc:  # noqa: BLE001 - characterization records every error
                output = None
                exception = {"type": type(exc).__name__, "message": str(exc)}
            observed.append(
                {
                    "case": case_name,
                    "function": function,
                    "inputs": inputs,
                    "parameters": params,
                    "output": output,
                    "exception": exception,
                }
            )

        closes = np.asarray([np.nan if v is None else v for v in bars["close"]], dtype=float)
        hmm_log = np.zeros_like(closes)
        if closes.size > 1:
            with np.errstate(all="ignore"):
                hmm_log[1:] = np.log(closes[1:] / np.maximum(closes[:-1], 1e-12))
        for function, inputs, params in VARIANT_CALLS:
            module, name = function.split(".")
            argument: Any
            if name in {"compute_rsi", "compute_macd"}:
                argument = [np.nan if v is None else v for v in bars["close"]]
            elif inputs == "hmm_log_returns":
                argument = hmm_log.copy()
            else:
                argument = closes.copy()
            try:
                with np.errstate(all="ignore"):
                    result = variants[module][name](argument, **params)
                exception = None
                output = plain(result)
            except Exception as exc:  # noqa: BLE001
                output = None
                exception = {"type": type(exc).__name__, "message": str(exc)}
            observed.append(
                {
                    "case": case_name,
                    "function": function,
                    "inputs": inputs,
                    "parameters": params,
                    "output": output,
                    "exception": exception,
                }
            )

    report = {
        "status": "OBSERVED",
        "scope": "LOCAL_LEGACY_CHARACTERIZATION_NOT_METHOD_VALIDATION",
        "source": {
            "repository": REPOSITORY,
            "commit": COMMIT,
            "files": {
                BASE[0]: {"git_blob": BASE[1], "loaded": "module"},
                **{
                    rel: {"git_blob": blob, "loaded": "ast:" + ",".join(names)}
                    for rel, blob, names in EXTRACTED.values()
                },
            },
        },
        "environment": {
            "python": platform.python_version(),
            "polars": pl.__version__,
            "numpy": np.__version__,
        },
        "series": {name: plain(bars) for name, bars in cases.items()},
        "observations": observed,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, ensure_ascii=False, separators=(",", ":")) + "\n"
    if args.output.suffix == ".gz":
        args.output.write_bytes(gzip.compress(text.encode("utf-8"), compresslevel=9, mtime=0))
    else:
        args.output.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "OBSERVED",
                "series": len(cases),
                "observations": len(observed),
                "exceptions": sum(o["exception"] is not None for o in observed),
                "polars": pl.__version__,
                "numpy": np.__version__,
            }
        )
    )


if __name__ == "__main__":
    main()
