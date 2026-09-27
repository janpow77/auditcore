"""Execute flowinvoice's Benford analyzers and record chi-square and per-digit z results.

Two pinned revisions of ``backend/app/services/fraud_detection/benfords_law.py``
are read with ``git show`` (blob-verified) and executed with their own
``models.py``; no database or network is touched::

    python tools/capture_flowinvoice_significance.py <flowinvoice checkout> \
        tests/fixtures/flowinvoice_significance_observed.json

* ``current`` (flowinvoice@06c06a8): the analyzer in production. It calls
  ``auditcore_statistics.recommended_flowinvoice_benford`` of the installed
  library (version recorded) and reports χ², p, degrees of freedom and the
  fixed critical value 15.507.
* ``original_exact`` (flowinvoice@fb2d185): the source's own χ² accumulation and
  per-digit z test (``z > 2.576``, no continuity correction), executed with
  its expectation table replaced by the exact shares log10(1 + 1/d) — the
  only change decision K10 made to the expectations.
* ``original_rounded``: the same source unchanged (three-decimal table), for
  the effect of that decision on the marked digits.

All amounts are synthetic.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import platform
import random
import subprocess
import sys
import tempfile
import types
from decimal import Decimal
from pathlib import Path
from typing import Any

BASE = "backend/app/services/fraud_detection/"
REVISIONS = {
    "current": (
        "06c06a8cf308669edef876520c94c32773d956d9",
        {
            "benfords_law.py": "b6f87541776cd3d6de0df9db27130a719bfdf61a",
            "models.py": "9bab6d61e2a9e3cf88438adfd1ecc6c18e138d30",
        },
    ),
    "original": (
        "fb2d18568d2eaf64574d131ceae51a936b9aac02",
        {
            "benfords_law.py": "77bf2b1e003634a9f52b079a6eb9c52d2a41a7e5",
            "models.py": "e960f32633874444b9ddc0f323dd54f5b0242e59",
        },
    ),
}
FIELDS = (
    "is_anomalous",
    "chi_square_statistic",
    "p_value",
    "critical_value",
    "observed_distribution",
    "sample_size",
    "anomalous_digits",
    "degrees_of_freedom",
    "significance_level",
    "sample_size_sufficient",
)


def git_blob(raw: bytes) -> str:
    header = b"blob " + str(len(raw)).encode() + b"\0"
    return hashlib.sha1(header + raw, usedforsecurity=False).hexdigest()


def load(checkout: Path, name: str, target: Path) -> Any:
    """Write the pinned files of one revision to ``target`` and import them as a package."""
    commit, files = REVISIONS[name]
    target.mkdir(parents=True)
    for file, blob in files.items():
        raw = subprocess.run(
            ["git", "-C", str(checkout), "show", f"{commit}:{BASE}{file}"],
            capture_output=True,
            check=True,
        ).stdout
        if git_blob(raw) != blob:
            raise SystemExit(f"{commit}:{BASE}{file} does not match the pinned blob")
        (target / file).write_bytes(raw)
    package = types.ModuleType(f"fi_{name}")
    package.__path__ = [str(target)]
    sys.modules[package.__name__] = package
    for module in ("models", "benfords_law"):
        spec = importlib.util.spec_from_file_location(
            f"{package.__name__}.{module}", target / f"{module}.py"
        )
        assert spec is not None and spec.loader is not None
        loaded = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = loaded
        spec.loader.exec_module(loaded)
    return sys.modules[f"{package.__name__}.benfords_law"]


def encode(value: Any) -> Any:
    if isinstance(value, Decimal):
        return {"$decimal": str(value)}
    if isinstance(value, float) and value != value:
        return {"$float": "nan"}
    return value


def samples(seed: int) -> list[tuple[str, list[Any]]]:
    """Numeric amounts only (the current analyzer rejects text and booleans)."""
    rng = random.Random(seed)
    out: list[tuple[str, list[Any]]] = [
        ("grenze-49", [round(rng.lognormvariate(6, 2), 2) for _ in range(49)]),
        ("grenze-50", [round(rng.lognormvariate(6, 2), 2) for _ in range(50)]),
        (
            "sonderwerte",
            [0, 0.0, None, float("nan"), -125.5, Decimal("0.04"), Decimal("987.65"), 7, 18.2] * 8,
        ),
    ]
    for k in range(60):
        n = rng.choice([50, 80, 150, 400, 1200])
        kind = k % 4
        if kind == 0:
            values: list[Any] = [round(rng.lognormvariate(6, 2), 2) for _ in range(n)]
        elif kind == 1:
            values = [round(rng.uniform(100, 999), 2) for _ in range(n)]
        elif kind == 2:
            values = [rng.choice([1000, 2000, 5000, 9000, 900, 1500]) for _ in range(n)]
        else:
            values = [Decimal(str(round(rng.lognormvariate(4, 1.5), 2))) for _ in range(n)]
        out.append((f"zufall-{k:02d}", values))
    return out


def fields(result: Any) -> dict[str, Any]:
    data = {k: getattr(result, k) for k in FIELDS}
    data["observed_distribution"] = {str(k): v for k, v in data["observed_distribution"].items()}
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--seed", type=int, default=20260926)
    args = parser.parse_args()
    from auditcore_statistics import __version__ as library

    with tempfile.TemporaryDirectory() as tmp:
        current = load(args.checkout.resolve(), "current", Path(tmp) / "current")
        original = load(args.checkout.resolve(), "original", Path(tmp) / "original")
        rounded_table = dict(original.BENFORD_EXPECTED)
        exact_table = {d: math.log10(1 + 1 / d) for d in range(1, 10)}
        cases = []
        for name, values in samples(args.seed):
            original.BENFORD_EXPECTED = exact_table
            exact = fields(original.BenfordsLawAnalyzer().analyze(values))
            original.BENFORD_EXPECTED = rounded_table
            rounded = fields(original.BenfordsLawAnalyzer().analyze(values))
            cases.append(
                {
                    "name": name,
                    "amounts": [encode(v) for v in values],
                    "current": fields(current.BenfordsLawAnalyzer().analyze(values)),
                    "original_exact": exact,
                    "original_rounded": rounded,
                }
            )
    document = {
        "source": {
            "repository": "janpow77/flowinvoice",
            "path": BASE + "benfords_law.py",
            "revisions": {k: {"commit": c, "files": f} for k, (c, f) in REVISIONS.items()},
            "symbols": ["BenfordsLawAnalyzer.analyze", "BENFORD_EXPECTED"],
        },
        "environment": {"python": platform.python_version(), "library": library},
        "cases": cases,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, ensure_ascii=False) + "\n")
    print(f"{len(cases)} cases -> {args.output}")


if __name__ == "__main__":
    main()
