"""Benchmark: Flowstat red flags over a synthetic Belegliste, record path vs column path.

(a) ``evaluate(frame.to_dict("records"))`` as Flowstat's ``_red_flags`` calls it,
(b) ``evaluate_frame_columns(frame)`` (vectorised, no records). Both must give
the same overview; the script aborts otherwise. Data are synthetic and
seed-fixed. Run once normally and once with ``AUDITCORE_COMPUTE_DISABLE_JIT=1``
for the path without Numba::

    python tools/benchmark_columns.py [--rows 100000 500000] [--repeat 3] [--seed 20261003]
"""

from __future__ import annotations

import argparse
import os
import platform
import time
from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd
from auditcore_compute import engine_report

from auditcore_risk import evaluate, load_profile
from auditcore_risk.frame import evaluate_frame_columns

PROFILE = load_profile("audit_designer.flowstat_belegliste", "2026.10.1")


def synthetic_frame(count: int, seed: int) -> pd.DataFrame:
    """Belegliste in the normalised column contract (float amounts, datetime64 dates)."""
    rng = np.random.default_rng(seed)
    amount = rng.integers(1_000, 30_000_000, size=count) / 100.0
    amount[rng.random(count) < 0.05] = rng.integers(1, 60, size=1)[0] * 1000.0
    cut = np.where(rng.random(count) < 0.1, rng.integers(1, 50_000, size=count) / 100.0, 0.0)
    accepted = np.round(amount - cut, 2)
    accepted[rng.random(count) < 0.01] += 0.01  # edge of the tolerance
    invoice = pd.Timestamp("2024-01-01") + pd.to_timedelta(rng.integers(0, 700, count), "D")
    payment = invoice + pd.to_timedelta(rng.integers(-5, 60, count), "D")
    payment = payment.where(rng.random(count) > 0.03)
    suppliers = np.array([f"Lieferant {i}" for i in range(2_000)], dtype=object)
    return pd.DataFrame(
        {
            "projektbetrag": amount,
            "kuerzungsbetrag": cut,
            "anerkannter_betrag": accepted,
            "rechnungsdatum": invoice,
            "zahlungsdatum": payment,
            "rechnungsnummer": [f"R-{k}" for k in rng.integers(0, count, size=count)],
            "rechnungssteller": suppliers[rng.zipf(1.6, size=count) % 2_000],
            "kuerzungsgrund": np.where(cut > 0, np.where(rng.random(count) < 0.9, "Abzug", ""), ""),
            "vergabe": np.where(rng.random(count) < 0.8, "V-1", ""),
            "direktvergabe": rng.choice(np.array(["ja", "nein", ""], dtype=object), size=count),
        }
    )


def best_of(call: Callable[[], Any], repeat: int) -> float:
    """Fastest of ``repeat`` wall-clock runs in seconds."""
    timings = []
    for _ in range(repeat):
        start = time.perf_counter()
        call()
        timings.append(time.perf_counter() - start)
    return min(timings)


def records_path(frame: pd.DataFrame) -> list[dict[str, object]]:
    """Overview over ``to_dict("records")`` (the call pattern of Flowstat)."""
    columns = [str(c) for c in frame.columns]
    result = evaluate(frame.to_dict("records"), PROFILE, columns=columns)
    return [dict(s) for s in result.summary]


def column_path(frame: pd.DataFrame) -> list[dict[str, object]]:
    """Overview over the column path."""
    return [dict(s) for s in evaluate_frame_columns(frame, PROFILE).summary]


def measure(count: int, seed: int, repeat: int) -> str:
    """One table row: rows, record path, its ``to_dict`` share, column path, factor."""
    frame = synthetic_frame(count, seed)
    if records_path(frame) != column_path(frame):
        raise SystemExit("Spalten- und Datensatzpfad liefern verschiedene Übersichten")
    to_dict = best_of(lambda: frame.to_dict("records"), 1)
    old = best_of(lambda: records_path(frame), 1)
    new = best_of(lambda: column_path(frame), repeat)
    return f"| {count:,} | {old:.2f} | {to_dict:.2f} | {new:.3f} | {old / new:.0f} |".replace(
        ",", "."
    )


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rows", type=int, nargs="+", default=[100_000, 500_000])
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20261003)
    args = parser.parse_args()
    rows = [measure(count, args.seed, args.repeat) for count in args.rows]
    modes = sorted({info.mode for info in engine_report()})
    print(
        f"Python {platform.python_version()}, NumPy {np.__version__}, pandas {pd.__version__}, "
        f"Kernel-Pfad {'/'.join(modes)}, "
        f"AUDITCORE_COMPUTE_DISABLE_JIT={os.environ.get('AUDITCORE_COMPUTE_DISABLE_JIT', '-')}"
    )
    print("| Zeilen | Datensatzpfad [s] | davon to_dict [s] | Spaltenpfad [s] | Faktor |")
    print("|---:|---:|---:|---:|---:|")
    print("\n".join(rows))


if __name__ == "__main__":
    main()
