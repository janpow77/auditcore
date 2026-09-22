"""Capture actual flowstat ``run_benford`` behavior before extraction.

Run with an interpreter that provides the flowstat numeric pins
(numpy 1.26.2, pandas 2.1.3, scipy 1.11.4)::

    python -I tools/capture_flowstat_benford.py <flowstat>/backend \
        tests/fixtures/flowstat_benford_observed.json

Only ``app/services/analysis_core_service.py`` is loaded, directly from its
file and after verifying its Git blob; no application package, database or
network is used. All inputs are synthetic.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

SOURCE_REPOSITORY = "janpow77/flowstat"
SOURCE_COMMIT = "d665ac221f50ba1f465b7337bdd4aa218d78ec8a"
SOURCE_PATH = "app/services/analysis_core_service.py"
SOURCE_BLOB = "f1d01534e7678fe65aa6eee1131fb52985614e7d"


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
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return {"$float": repr(value)}
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backend", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--migrated", action="store_true")
    args = parser.parse_args()
    source = args.backend.resolve() / SOURCE_PATH
    blob = git_blob(source)
    head = subprocess.run(
        ["git", "-C", str(args.backend), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if not args.migrated and (blob != SOURCE_BLOB or head != SOURCE_COMMIT):
        raise SystemExit("Source is not the pinned flowstat revision")
    if args.migrated:
        sys.path.insert(0, str(args.backend.resolve()))
    spec = importlib.util.spec_from_file_location("legacy_analysis_core", source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    import numpy as np
    import pandas as pd
    import scipy
    from scipy import stats

    cases: list[dict[str, Any]] = []

    def observe(name: str, column: list[Any] | None, parameters: dict[str, Any]) -> None:
        frame = pd.DataFrame({"betrag": column}) if column is not None else pd.DataFrame()
        before = frame.copy()
        try:
            output = plain(module.run_benford(frame, parameters))
            exception = None
        except Exception as exc:  # noqa: BLE001 - characterization records every error
            output = None
            exception = {"type": type(exc).__name__, "message": str(exc)}
        if not frame.equals(before):
            raise AssertionError(f"{name}: input frame mutated")
        coerced = pd.to_numeric(frame["betrag"], errors="coerce") if column is not None else None
        cases.append(
            {
                "name": name,
                "values": plain(column),
                "dtype": str(frame["betrag"].dtype) if column is not None else None,
                "coerced": plain(coerced.tolist()) if coerced is not None else None,
                "coerced_dtype": str(coerced.dtype) if coerced is not None else None,
                "parameters": parameters,
                "output": output,
                "exception": exception,
            }
        )

    rng = np.random.default_rng(20260922)
    lognormal = [float(v) for v in np.round(rng.lognormal(7, 2, 500), 2)]
    integers = [int(v) for v in rng.integers(1, 100000, 400)]
    for digit in (1, 2):
        observe(f"lognormal-{digit}", lognormal, {"valueColumn": "betrag", "digit": digit})
        observe(f"integers-{digit}", integers, {"valueColumn": "betrag", "digit": digit})
        observe(
            f"small-ints-{digit}",
            [1, 2, 3, 5, 9, 12, 15, 99, 100, 7],
            {"valueColumn": "betrag", "digit": digit},
        )
        observe(
            f"same-as-float-{digit}",
            [1.0, 2.0, 3.0, 5.0, 9.0, 12.0, 15.0, 99.0, 100.0, 7.0],
            {"valueColumn": "betrag", "digit": digit},
        )
        observe(
            f"mixed-nan-{digit}",
            [1, 2, None, 5, 17, 230, 4500],
            {"valueColumn": "betrag", "digit": digit},
        )
        observe(
            f"negative-zero-{digit}",
            [-123.5, 0, 0.0, -0.004, 47, -9, 3.3],
            {"valueColumn": "betrag", "digit": digit},
        )
        observe(
            f"strings-{digit}",
            ["123", "abc", "4,5", "6.7", "", "89"],
            {"valueColumn": "betrag", "digit": digit},
        )
        observe(
            f"scientific-{digit}",
            [1e-05, 2.5e-07, 1.5e20, 3.14e16, 12.5, 0.1],
            {"valueColumn": "betrag", "digit": digit},
        )
        observe(f"single-{digit}", [42], {"valueColumn": "betrag", "digit": digit})
        observe(f"all-zero-{digit}", [0, 0, 0], {"valueColumn": "betrag", "digit": digit})
        observe(f"booleans-{digit}", [True, False, True], {"valueColumn": "betrag", "digit": digit})
        observe(
            f"cent-values-{digit}",
            [0.01, 0.05, 0.1, 0.19, 1.01, 10.1],
            {"valueColumn": "betrag", "digit": digit},
        )
    observe("default-digit", integers[:50], {"valueColumn": "betrag"})
    observe("digit-3", integers[:50], {"valueColumn": "betrag", "digit": 3})
    observe("digit-string", integers[:50], {"valueColumn": "betrag", "digit": "1"})
    observe("digit-float", integers[:50], {"valueColumn": "betrag", "digit": 1.0})
    observe("missing-parameter", integers[:5], {})
    observe("missing-column", integers[:5], {"valueColumn": "fehlt"})
    observe("empty-frame", None, {"valueColumn": "betrag"})
    observe("empty-column", [], {"valueColumn": "betrag"})

    # Raw chi-square reference values for the stdlib implementation.
    chisquare = []
    for _ in range(40):
        size = int(rng.integers(2, 95))
        observed = [int(v) for v in rng.integers(0, 60, size)]
        total = sum(observed) or 1
        weights = rng.random(size) + 0.05
        expected = [float(w / weights.sum() * total) for w in weights]
        try:
            stat, p = stats.chisquare(f_obs=observed, f_exp=expected)
            chisquare.append(
                {
                    "observed": observed,
                    "expected": expected,
                    "statistic": float(stat),
                    "p_value": float(p),
                    "exception": None,
                }
            )
        except Exception as exc:  # noqa: BLE001
            chisquare.append(
                {
                    "observed": observed,
                    "expected": expected,
                    "statistic": None,
                    "p_value": None,
                    "exception": {"type": type(exc).__name__, "message": str(exc)},
                }
            )
    report = {
        "status": "OBSERVED",
        "scope": "LOCAL_LEGACY_CHARACTERIZATION_NOT_METHOD_VALIDATION",
        "source": {
            "repository": SOURCE_REPOSITORY,
            "commit": SOURCE_COMMIT if not args.migrated else head,
            "path": f"backend/{SOURCE_PATH}",
            "git_blob": blob,
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "migrated": args.migrated,
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
        },
        "cases": cases,
        "chisquare": chisquare,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {
                "status": "OBSERVED",
                "cases": len(cases),
                "exceptions": sum(c["exception"] is not None for c in cases),
                "chisquare": len(chisquare),
            }
        )
    )


if __name__ == "__main__":
    main()
