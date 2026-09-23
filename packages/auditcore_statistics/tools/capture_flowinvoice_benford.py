"""Execute flowinvoice ``BenfordsLawAnalyzer.analyze`` and record inputs/outputs.

The pinned ``benfords_law.py`` (blob-verified) imports only ``math``,
``collections``, ``decimal`` and its ``BenfordResult`` model; the analyzer is
loaded from the checkout with a minimal stand-in package for ``.models`` taken
from the pinned ``models.py``. No database or network is touched::

    python tools/capture_flowinvoice_benford.py <flowinvoice checkout> \
        tests/fixtures/flowinvoice_benford_observed.json

All amounts are synthetic.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import random
import subprocess
import sys
import types
from decimal import Decimal
from pathlib import Path
from typing import Any

COMMIT = "fb2d18568d2eaf64574d131ceae51a936b9aac02"
BASE = "backend/app/services/fraud_detection/"
FILES = {
    BASE + "benfords_law.py": "77bf2b1e003634a9f52b079a6eb9c52d2a41a7e5",
    BASE + "models.py": "e960f32633874444b9ddc0f323dd54f5b0242e59",
}


def git_blob(raw: bytes) -> str:
    header = b"blob " + str(len(raw)).encode() + b"\0"
    return hashlib.sha1(header + raw, usedforsecurity=False).hexdigest()


def load(checkout: Path) -> Any:
    package = types.ModuleType("fraudpkg")
    package.__path__ = [str(checkout / BASE)]
    sys.modules["fraudpkg"] = package
    for name in ("models", "benfords_law"):
        spec = importlib.util.spec_from_file_location(
            f"fraudpkg.{name}", checkout / BASE / f"{name}.py"
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"fraudpkg.{name}"] = module
        spec.loader.exec_module(module)
    return sys.modules["fraudpkg.benfords_law"]


def encode(value: Any) -> Any:
    if isinstance(value, Decimal):
        return {"$decimal": str(value)}
    if isinstance(value, float) and value != value:
        return {"$float": "nan"}
    return value


def samples(seed: int) -> list[tuple[str, list[Any]]]:
    rng = random.Random(seed)
    out: list[tuple[str, list[Any]]] = [
        ("leer", []),
        ("klein", [123.4, 56, 7.89]),
        ("grenze-49", [rng.lognormvariate(6, 2) for _ in range(49)]),
        ("grenze-50", [rng.lognormvariate(6, 2) for _ in range(50)]),
        (
            "sonderwerte",
            [
                0,
                0.0,
                None,
                float("nan"),
                -125.5,
                "12.5",
                "12,5",
                "abc",
                Decimal("0.004"),
                Decimal("987.65"),
                True,
                1e-9,
            ]
            * 6,
        ),
    ]
    for k in range(60):
        kind = k % 4
        n = rng.choice([50, 80, 150, 400, 1200])
        if kind == 0:
            values: list[Any] = [round(rng.lognormvariate(6, 2), 2) for _ in range(n)]
        elif kind == 1:
            values = [round(rng.uniform(100, 999), 2) for _ in range(n)]
        elif kind == 2:
            values = [rng.choice([1000, 2000, 5000, 9000, 900]) for _ in range(n)]
        else:
            values = [Decimal(str(round(rng.lognormvariate(4, 1.5), 2))) for _ in range(n)]
        out.append((f"zufall-{k:02d}", values))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--seed", type=int, default=20260923)
    args = parser.parse_args()
    checkout = args.checkout.resolve()
    head = subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if head != COMMIT:
        raise SystemExit(f"checkout is at {head}, expected {COMMIT}")
    for path, blob in FILES.items():
        if git_blob((checkout / path).read_bytes()) != blob:
            raise SystemExit(f"{path} does not match the pinned blob")
    module = load(checkout)
    analyzer = module.BenfordsLawAnalyzer()
    cases = []
    for name, values in samples(args.seed):
        result = analyzer.analyze(values)
        data = {
            k: getattr(result, k)
            for k in (
                "is_anomalous",
                "chi_square_statistic",
                "p_value",
                "critical_value",
                "observed_distribution",
                "expected_distribution",
                "sample_size",
                "anomalous_digits",
                "interpretation",
                "degrees_of_freedom",
                "significance_level",
                "null_hypothesis_rejected",
                "sample_size_sufficient",
            )
        }
        data["observed_distribution"] = {
            str(k): v for k, v in data["observed_distribution"].items()
        }
        data["expected_distribution"] = {
            str(k): v for k, v in data["expected_distribution"].items()
        }
        cases.append({"name": name, "amounts": [encode(v) for v in values], "result": data})
    document = {
        "source": {
            "repository": "janpow77/flowinvoice",
            "commit": COMMIT,
            "files": FILES,
            "symbols": [
                "BenfordsLawAnalyzer.analyze",
                "_extract_first_digit",
                "_chi_square_p_value",
                "BENFORD_EXPECTED",
            ],
        },
        "environment": {"python": platform.python_version()},
        "cases": cases,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, ensure_ascii=False) + "\n")
    print(f"{len(cases)} Benford cases -> {args.output}")


if __name__ == "__main__":
    main()
