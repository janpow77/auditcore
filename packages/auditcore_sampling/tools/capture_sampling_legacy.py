"""Capture actual MUS/SRS behavior of flowstat and audit-portal before extraction.

Run with an interpreter providing numpy 1.26.2, pandas 2.1.3 and scipy 1.11.4::

    python -I tools/capture_sampling_legacy.py <flowstat>/backend <audit-portal>/backend \
        tests/fixtures/sampling_legacy_observed.json.gz

Both ``sampling_service.py`` files are loaded directly from their paths after
verifying the pinned Git blobs; no application package, database or network.
Random draws of the legacy code come from NumPy. The tool records the exact
start value / generator output for every seed so the deterministic parts
(sizes, cumulative selection, allocation) can be replayed without NumPy.
"""

from __future__ import annotations

import argparse
import contextlib
import gzip
import hashlib
import importlib.util
import json
import math
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

SOURCES = {
    "flowstat": {
        "repository": "janpow77/flowstat",
        "commit": "d665ac221f50ba1f465b7337bdd4aa218d78ec8a",
        "path": "app/services/sampling_service.py",
        "blob": "c2423b1efab65f1eb1118b97f6eebe83348be706",
    },
    "portal": {
        "repository": "janpow77/audit-portal",
        "commit": "d8eefa426826bdecb67036774f3128ae05e7d0d0",
        "path": "app/modules/flowstat/services/sampling_service.py",
        "blob": "2358a38fc9c4b0ff414018b54ed7bf31f4f422fe",
    },
}


def git_blob(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def plain(value: Any) -> Any:
    import numpy as np

    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return {"$float": repr(value)}
    return value


def load(name: str, backend: Path, migrated: bool) -> tuple[Any, dict[str, Any]]:
    info = SOURCES[name]
    path = backend.resolve() / info["path"]
    blob = git_blob(path)
    head = subprocess.run(
        ["git", "-C", str(backend), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    if not migrated and (blob != info["blob"] or head != info["commit"]):
        raise SystemExit(f"{name} is not the pinned revision")
    spec = importlib.util.spec_from_file_location(f"legacy_sampling_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, {
        **info,
        "observed_blob": blob,
        "head": head,
        "migrated": migrated,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("flowstat", type=Path)
    parser.add_argument("portal", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--migrated", action="store_true", help="flowstat after migration")
    args = parser.parse_args()
    if args.migrated:
        sys.path.insert(0, str(args.flowstat.resolve()))
    stat, stat_source = load("flowstat", args.flowstat, args.migrated)
    portal, portal_source = load("portal", args.portal, False)

    import numpy as np
    import pandas as pd
    import scipy

    cases: list[dict[str, Any]] = []

    def observe(
        name: str,
        operation: str,
        inputs: dict[str, Any],
        call: Any,
        extra: dict[str, Any] | None = None,
    ) -> None:
        try:
            output = plain(call())
            meta = output.get("meta") if isinstance(output, dict) else None
            if isinstance(meta, dict) and "sample_data" in meta:
                data = json.dumps(meta["sample_data"], sort_keys=True, ensure_ascii=False)
                meta["sample_data"] = {
                    "rows": len(meta["sample_data"]),
                    "sha256": hashlib.sha256(data.encode("utf-8")).hexdigest(),
                }
            exception = None
        except Exception as exc:  # noqa: BLE001 - characterization records every error
            output = None
            exception = {"type": type(exc).__name__, "message": str(exc)}
        cases.append(
            {
                "name": name,
                "operation": operation,
                "inputs": plain(inputs),
                "output": output,
                "exception": exception,
                **(extra or {}),
            }
        )

    # ------------------------------------------------------------- sizes
    for pv in (0.0, 1.0, 999.99, 250000.0, 1_000_000.0, 123456.789, -5000.0):
        for mat in (0.01, 1.0, 10.0, 5000.0, 50000.0, 0.0, -1.0):
            for rate in (0.0, 0.005, 0.01, 0.5, 0.999, 1.0, -0.1):
                for conf in (0.5, 0.8, 0.9, 0.95, 0.97, 0.99, 0.975):
                    inputs = {
                        "population_value": pv,
                        "materiality": mat,
                        "expected_error_rate": rate,
                        "confidence_level": conf,
                    }
                    for variant, fn in (
                        ("flowstat", stat._calculate_mus_sample_size),
                        ("portal", portal._calculate_mus_sample_size),
                        ("portal_legacy", portal._calculate_mus_sample_size_legacy),
                    ):
                        observe(
                            f"mus-size-{variant}-{pv}-{mat}-{rate}-{conf}",
                            f"mus_size:{variant}",
                            inputs,
                            lambda f=fn, i=inputs: f(**i),
                        )
    for n in (1, 2, 10, 100, 385, 1000, 100000, 0):
        for conf in (0.5, 0.8, 0.9, 0.95, 0.99, 0.975):
            for moe in (0.01, 0.05, 0.1, 0.5):
                for p in (0.5, 0.1, 0.0, 1.0):
                    inputs = {
                        "population_size": n,
                        "confidence_level": conf,
                        "margin_of_error": moe,
                        "expected_proportion": p,
                    }
                    for variant, fn in (
                        ("flowstat", stat._calculate_srs_sample_size),
                        ("portal", portal._calculate_srs_sample_size),
                    ):
                        observe(
                            f"srs-size-{variant}-{n}-{conf}-{moe}-{p}",
                            f"srs_size:{variant}",
                            inputs,
                            lambda f=fn, i=inputs: f(**i),
                        )

    # ------------------------------------------------------------- data sets
    np.random.seed(42)
    base = pd.DataFrame(
        {
            "id": range(1, 101),
            "amount": np.random.uniform(100, 10000, 100),
            "category": np.random.choice(["A", "B", "C"], 100),
        }
    )
    frames: dict[str, pd.DataFrame] = {
        "uniform100": base,
        "with-negative-nan": base.assign(
            amount=[
                (-v if i % 13 == 0 else (float("nan") if i % 17 == 0 else v))
                for i, v in enumerate(base["amount"])
            ]
        ),
        "certainty-item": pd.concat(
            [base.head(20), pd.DataFrame({"id": [999], "amount": [400000.0], "category": ["A"]})],
            ignore_index=True,
        ),
        "integers": pd.DataFrame(
            {
                "id": range(12),
                "amount": [120, 55, 3000, 7, 0, 999, 45000, 3, 18, 250, 1, 60000],
                "category": list("ABCABCABCABC"),
            }
        ),
        "zero": pd.DataFrame({"id": [1, 2], "amount": [0.0, 0.0], "category": ["A", "A"]}),
    }
    frame_records = {k: plain(v.to_dict(orient="list")) for k, v in frames.items()}

    def stat_start(seed: int, interval: float) -> float | None:
        np.random.seed(seed)
        return float(np.random.uniform(0, interval)) if interval > 0 else None

    for fname, frame in frames.items():
        for template, rate in (("run_mus_standard", 0.005), ("run_mus_conservative", 0.01)):
            for materiality in (50000.0, 5000.0, 30.0):
                for seed in (0, 7):
                    params = {
                        "valueColumn": "amount",
                        "materiality": materiality,
                        "confidenceLevel": 0.95,
                    }
                    values = pd.to_numeric(frame["amount"], errors="coerce")
                    try:
                        size, interval = stat._calculate_mus_sample_size(
                            values.sum(), materiality, rate, 0.95
                        )
                    except (ZeroDivisionError, ValueError):
                        interval = 0
                    start = stat_start(seed, interval)

                    def call(
                        t: str = template,
                        p: dict[str, Any] = params,
                        s: int = seed,
                        f: pd.DataFrame = frame,
                    ) -> Any:
                        np.random.seed(s)
                        return getattr(stat, t)(f, p)

                    observe(
                        f"stat-{template}-{fname}-{materiality}-{seed}",
                        f"flowstat:{template}",
                        {"frame": fname, "parameters": params, "seed": seed},
                        call,
                        {"legacy_start": start},
                    )
                    if materiality < 1000:
                        continue  # PORTAL: n in the hundreds of thousands, not informative
                    pparams = {**params, "seed": seed}
                    positive = values[values > 0]
                    psize, pinterval = (0, 0.0)
                    with contextlib.suppress(ValueError):
                        psize, pinterval = portal._calculate_mus_sample_size(
                            float(positive.sum()), materiality, rate, 0.95
                        )
                    pstart = (
                        float(np.random.default_rng(seed).uniform(0, pinterval))
                        if pinterval > 0
                        else None
                    )
                    observe(
                        f"portal-{template}-{fname}-{materiality}-{seed}",
                        f"portal:{template}",
                        {"frame": fname, "parameters": pparams, "seed": seed},
                        lambda t=template, p=pparams, f=frame: getattr(portal, t)(f, p),
                        {"legacy_start": pstart},
                    )
        # Stratified MUS (flowstat): one uniform draw per stratum in groupby order.
        for materiality in (50000.0, 5.0):
            params = {
                "valueColumn": "amount",
                "stratifyColumn": "category",
                "materiality": materiality,
                "confidenceLevel": 0.95,
            }
            values = pd.to_numeric(frame["amount"], errors="coerce")
            total = values.sum()
            np.random.seed(3)
            starts = []
            for _, group in frame.groupby("category"):
                gv = pd.to_numeric(group["amount"], errors="coerce")
                gs = gv.sum()
                try:
                    _, gi = stat._calculate_mus_sample_size(
                        gs, materiality * (gs / total), 0.005, 0.95
                    )
                except (ZeroDivisionError, ValueError):
                    gi = 0
                starts.append(float(np.random.uniform(0, gi)) if gi > 0 else None)

            def strat(p: dict[str, Any] = params, f: pd.DataFrame = frame) -> Any:
                np.random.seed(3)
                return stat.run_mus_stratified(f, p)

            observe(
                f"stat-mus-stratified-{fname}-{materiality}",
                "flowstat:run_mus_stratified",
                {"frame": fname, "parameters": params, "seed": 3},
                strat,
                {"legacy_starts": starts},
            )
        for method in ("proportional", "equal"):
            for moe in (0.05, 0.2):
                params = {
                    "stratifyColumn": "category",
                    "confidenceLevel": 0.95,
                    "marginOfError": moe,
                    "allocationMethod": method,
                }

                def srs_strat(p: dict[str, Any] = params, f: pd.DataFrame = frame) -> Any:
                    np.random.seed(5)
                    return stat.run_srs_stratified(f, p)

                observe(
                    f"stat-srs-stratified-{fname}-{method}-{moe}",
                    "flowstat:run_srs_stratified",
                    {"frame": fname, "parameters": params, "seed": 5},
                    srs_strat,
                )
        for moe in (0.05, 0.2):
            params = {"confidenceLevel": 0.95, "marginOfError": moe}

            def srs(p: dict[str, Any] = params, f: pd.DataFrame = frame) -> Any:
                np.random.seed(5)
                return stat.run_srs_standard(f, p)

            observe(
                f"stat-srs-standard-{fname}-{moe}",
                "flowstat:run_srs_standard",
                {"frame": fname, "parameters": params, "seed": 5},
                srs,
            )
    for name, params in (
        ("missing-value-column", {"materiality": 1.0}),
        ("missing-materiality", {"valueColumn": "amount"}),
        ("zero-materiality", {"valueColumn": "amount", "materiality": 0}),
        ("unknown-column", {"valueColumn": "x", "materiality": 1.0}),
    ):
        observe(
            f"stat-mus-error-{name}",
            "flowstat:run_mus_standard",
            {"frame": "uniform100", "parameters": params},
            lambda p=params: stat.run_mus_standard(base, p),
        )

    report = {
        "status": "OBSERVED",
        "scope": "LOCAL_LEGACY_CHARACTERIZATION_NOT_METHOD_VALIDATION",
        "sources": {"flowstat": stat_source, "portal": portal_source},
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
        },
        "frames": frame_records,
        "cases": cases,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(report, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    if args.output.suffix == ".gz":
        args.output.write_bytes(gzip.compress(data, mtime=0))
    else:
        args.output.write_bytes(data)
    print(
        json.dumps(
            {
                "status": "OBSERVED",
                "cases": len(cases),
                "exceptions": sum(c["exception"] is not None for c in cases),
            }
        )
    )


if __name__ == "__main__":
    main()
