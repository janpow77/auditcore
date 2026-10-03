"""Benchmark: quota and plausibility checks on 500,000 synthetic booking rows.

Compares (a) a naive CPython loop over Python ints, (b) NumPy vectorised int64
code, (c) the public auditcore_compute API with the compiled kernels and (d)
the same kernels forced to Python. All variants must produce identical
results; the script aborts otherwise. Data are synthetic and seed-fixed.

    python tools/benchmark.py [--rows 500000] [--repeat 5] [--seed 20261003]
"""

from __future__ import annotations

import argparse
import os
import platform
import time
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from auditcore_compute import engine_info, use_python
from auditcore_compute._duplicates import reconcile_kernel
from auditcore_compute._outliers import threshold_kernel
from auditcore_compute._quotas import quota_kernel, share_kernel
from auditcore_compute.finance import check_quota, share_cents
from auditcore_compute.validation import exceeds_threshold, reconcile

Ints = npt.NDArray[np.int64]
RATES = ((2, 5), (1, 2), (3, 5), (3, 4), (17, 20))  # 40 %, 50 %, 60 %, 75 %, 85 %
MAX_RATE = (3, 4)  # synthetic maximum funding rate of 75 %
TOLERANCE = 100  # 1 euro
THRESHOLD = 25_000_000  # 250,000 euros


@dataclass(frozen=True)
class Rows:
    """Synthetic booking rows as int64 cent buffers."""

    eligible: Ints
    numerators: Ints
    denominators: Ints
    expected: Ints
    actual: Ints


def synthetic_rows(count: int, seed: int) -> Rows:
    """Seed-fixed eligible amounts, per-row rates and actual amounts with noise."""
    generator = np.random.default_rng(seed)
    eligible = generator.integers(1, 50_000_000, size=count, dtype=np.int64)
    choice = generator.integers(0, len(RATES), size=count)
    numerators = np.array([RATES[c][0] for c in range(len(RATES))], dtype=np.int64)[choice]
    denominators = np.array([RATES[c][1] for c in range(len(RATES))], dtype=np.int64)[choice]
    noise = generator.integers(-500, 501, size=count, dtype=np.int64)
    noise[generator.random(count) < 0.9] = 0
    return Rows(eligible, numerators, denominators, eligible.copy(), eligible + noise)


# (a) naive CPython -----------------------------------------------------------------


def cpython_quota(eligible: list[int], nums: list[int], dens: list[int]) -> tuple[list[int], ...]:
    """Naive loop: funding share (half away from zero) and maximum-rate status."""
    shares, status = [], []
    for amount, num, den in zip(eligible, nums, dens, strict=True):
        product = amount * num
        share = (2 * abs(product) + den) // (2 * den)
        share = -share if product < 0 else share
        shares.append(share)
        status.append(2 if share * MAX_RATE[1] > amount * MAX_RATE[0] else 0)
    return shares, status


def cpython_plausibility(
    expected: list[int], actual: list[int]
) -> tuple[list[int], list[int], list[bool]]:
    """Naive loop: difference, status and threshold flag per row."""
    differences: list[int] = []
    status: list[int] = []
    large: list[bool] = []
    for target, value in zip(expected, actual, strict=True):
        delta = value - target
        differences.append(delta)
        status.append(0 if delta == 0 else (1 if abs(delta) <= TOLERANCE else 2))
        large.append(value > THRESHOLD)
    return differences, status, large


# (b) NumPy vectorised --------------------------------------------------------------


def numpy_quota(rows: Rows) -> tuple[npt.NDArray[np.generic], ...]:
    """Vectorised int64 version of the quota check."""
    product = rows.eligible * rows.numerators
    share = (2 * np.abs(product) + rows.denominators) // (2 * rows.denominators)
    share = np.where(product < 0, -share, share)
    above = share * MAX_RATE[1] > rows.eligible * MAX_RATE[0]
    return share, np.where(above, 2, 0).astype(np.int8)


def numpy_plausibility(rows: Rows) -> tuple[npt.NDArray[np.generic], ...]:
    """Vectorised int64 version of the plausibility check."""
    delta = rows.actual - rows.expected
    status = np.where(delta == 0, 0, np.where(np.abs(delta) <= TOLERANCE, 1, 2)).astype(np.int8)
    return delta, status, rows.actual > THRESHOLD


# (c)/(d) auditcore_compute ---------------------------------------------------------


def compute_quota(rows: Rows) -> tuple[npt.NDArray[np.generic], ...]:
    """Quota check with the auditcore_compute kernels (per-row rates)."""
    share = np.zeros(rows.eligible.shape, dtype=np.int64)
    share_kernel(rows.eligible, rows.numerators, rows.denominators, share)
    bounds = np.array([0, 0, 1, 1, MAX_RATE[0], MAX_RATE[1]], dtype=np.int64)
    points = np.zeros(rows.eligible.shape, dtype=np.int64)
    status = np.zeros(rows.eligible.shape, dtype=np.int8)
    quota_kernel(share, rows.eligible, bounds, points, status)
    return share, status


def compute_plausibility(rows: Rows) -> tuple[npt.NDArray[np.generic], ...]:
    """Plausibility check with the auditcore_compute kernels."""
    count = rows.expected.shape[0]
    difference = np.zeros(count, dtype=np.int64)
    status = np.zeros(count, dtype=np.int8)
    missing = np.zeros(count, dtype=np.bool_)
    reconcile_kernel(rows.expected, rows.actual, missing, TOLERANCE, difference, status)
    large = np.zeros(count, dtype=np.bool_)
    threshold_kernel(rows.actual, THRESHOLD, False, large)
    return difference, status, large


def public_quota(rows: Rows) -> tuple[npt.NDArray[np.generic], ...]:
    """Quota check through the public API (validation included, one rate)."""
    share = share_cents(rows.eligible, "0.4")  # public API incl. validation, one rate
    return share, check_quota(share, rows.eligible, maximum="0.75").status


def public_plausibility(rows: Rows) -> tuple[npt.NDArray[np.generic], ...]:
    """Plausibility check through the public API (validation included)."""
    result = reconcile(rows.expected, rows.actual, tolerance_cents=TOLERANCE)
    return result.difference, result.status, exceeds_threshold(rows.actual, THRESHOLD)


def best_of(call: Callable[[], object], repeat: int) -> float:
    """Fastest of ``repeat`` wall-clock runs in seconds."""
    timings = []
    for _ in range(repeat):
        start = time.perf_counter()
        call()
        timings.append(time.perf_counter() - start)
    return min(timings)


def same(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    """True when all result arrays are equal as int64."""
    return all(
        np.array_equal(np.asarray(a).astype(np.int64), np.asarray(b).astype(np.int64))
        for a, b in zip(left, right, strict=True)
    )


def measure(rows: Rows, repeat: int) -> dict[str, tuple[float, float]]:
    """Check that all variants agree, then time them."""
    lists = [rows.eligible.tolist(), rows.numerators.tolist(), rows.denominators.tolist()]
    plain = [rows.expected.tolist(), rows.actual.tolist()]
    start = time.perf_counter()
    compiled = (compute_quota(rows), compute_plausibility(rows))  # includes compilation
    compile_seconds = time.perf_counter() - start
    reference = (cpython_quota(*lists), cpython_plausibility(*plain))
    with use_python():
        fallback = (compute_quota(rows), compute_plausibility(rows))
    variants = (compiled, fallback, (numpy_quota(rows), numpy_plausibility(rows)))
    if not all(same(v[0], reference[0]) and same(v[1], reference[1]) for v in variants):
        raise SystemExit("Abweichende Ergebnisse zwischen den Varianten")
    results = {
        "a) CPython-Schleife": (
            best_of(lambda: cpython_quota(*lists), repeat),
            best_of(lambda: cpython_plausibility(*plain), repeat),
        ),
        "b) NumPy vektorisiert": (
            best_of(lambda: numpy_quota(rows), repeat),
            best_of(lambda: numpy_plausibility(rows), repeat),
        ),
        "c) JIT-Kernel": (
            best_of(lambda: compute_quota(rows), repeat),
            best_of(lambda: compute_plausibility(rows), repeat),
        ),
        "c') öffentliche API (JIT, Eingabeprüfung, eine Quote)": (
            best_of(lambda: public_quota(rows), repeat),
            best_of(lambda: public_plausibility(rows), repeat),
        ),
    }
    with use_python():
        results["d) Kernel als reines Python (Rückfall)"] = (
            best_of(lambda: compute_quota(rows), 1),
            best_of(lambda: compute_plausibility(rows), 1),
        )
    results["Erstaufruf JIT (Kompilierung/Cache)"] = (compile_seconds, 0.0)
    return results


def report(results: dict[str, tuple[float, float]], rows: int) -> str:
    """Markdown table of the timings and speed-up factors."""
    base = results["a) CPython-Schleife"]
    vectorised = results["b) NumPy vektorisiert"]
    lines = [
        f"{rows:,} Zeilen".replace(",", "."),
        "",
        "| Variante | Quote [ms] | Plausibilität [ms] | Faktor ggü. CPython | Faktor ggü. NumPy |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, (quota, plausibility) in results.items():
        if name.startswith("Erstaufruf"):
            lines.append(f"| {name} | {quota * 1000:.0f} (beide zusammen) | – | – | – |")
            continue
        factor = (base[0] + base[1]) / (quota + plausibility)
        against = (vectorised[0] + vectorised[1]) / (quota + plausibility)
        lines.append(
            f"| {name} | {quota * 1000:.1f} | {plausibility * 1000:.1f} "
            f"| {factor:.1f} | {against:.2f} |"
        )
    return "\n".join(lines)


def environment() -> str:
    """Interpreter, library versions and engine path of the run."""
    info = engine_info(share_kernel)
    numba = info.numba_version or "nicht geladen"
    return (
        f"Python {platform.python_version()} ({platform.machine()}), NumPy {np.__version__}, "
        f"numba {numba}, Pfad {info.mode} ({info.reason}), CPU-Kerne {os.cpu_count()}, "
        f"NUMBA_NUM_THREADS={os.environ.get('NUMBA_NUM_THREADS', 'Standard')}"
    )


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rows", type=int, default=500_000)
    parser.add_argument("--repeat", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20261003)
    args = parser.parse_args()
    rows = synthetic_rows(args.rows, args.seed)
    results = measure(rows, args.repeat)
    print(environment())
    print(report(results, args.rows))


if __name__ == "__main__":
    main()
