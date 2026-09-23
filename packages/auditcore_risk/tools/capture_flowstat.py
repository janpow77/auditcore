"""Execute the original Flowstat Belegliste red flags and record inputs/outputs.

Compiles only the pinned, unchanged top-level definitions
``PROCUREMENT_THRESHOLDS``, ``_jsonable`` and ``_red_flags`` (verified by Git
blob) from ``backend/app/modules/flowstat/services/belegliste_analysis_service.py``
of audit_designer; audit-portal carries the identical blob. The function is
called with frames in the normalised column contract that
``normalize_belegliste`` produces (float amounts, ``datetime64`` dates). Run it
with the versions pinned in audit_designer ``backend/requirements.txt``
(pandas 2.1.4, NumPy 1.26.2)::

    python tools/capture_flowstat.py <audit_designer checkout> <audit-portal checkout> \
        tests/fixtures/flowstat_observed.json

All values are synthetic.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import platform
import random
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PATH = "backend/app/modules/flowstat/services/belegliste_analysis_service.py"
BLOB = "d03738cb7e250e3cd838c88157992e0b4093ef35"
SOURCES = {
    "audit_designer": ("janpow77/audit_designer", "1254591156d3bdf6ccdf4050dec7713a61ad4a20"),
    "audit-portal": ("janpow77/audit-portal", "ac1ccc779db69492db0c2c154b6ec84fdd1794b1"),
}
SYMBOLS = ["PROCUREMENT_THRESHOLDS", "_jsonable", "_red_flags"]
AMOUNTS = ["projektbetrag", "kuerzungsbetrag", "anerkannter_betrag"]
DATES = ["rechnungsdatum", "zahlungsdatum"]
NAN = float("nan")


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(  # noqa: S324 - Git blob identity
        b"blob " + str(len(raw)).encode() + b"\0" + raw, usedforsecurity=False
    ).hexdigest()


def load(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    if git_blob(raw) != BLOB:
        raise SystemExit(f"{path} does not match the pinned blob")
    tree = ast.parse(raw.decode("utf-8"))

    def pinned(node: ast.stmt) -> bool:
        if isinstance(node, ast.FunctionDef):
            return node.name in SYMBOLS
        return isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id in SYMBOLS for t in node.targets
        )

    wanted = [node for node in tree.body if pinned(node)]
    if len(wanted) != len(SYMBOLS):
        raise SystemExit("missing definitions in belegliste_analysis_service.py")
    future = ast.parse("from __future__ import annotations").body
    module = ast.Module(body=[*future, *wanted], type_ignores=[])
    namespace: dict[str, Any] = {"math": math, "pd": pd, "Any": Any}
    exec(compile(module, PATH, "exec"), namespace)  # noqa: S102  # nosec B102 - pinned source
    return namespace


def encode(value: Any) -> Any:
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, float | np.floating):
        v = float(value)
        if math.isnan(v):
            return {"$float": "nan"}
        if math.isinf(v):
            return {"$float": "inf" if v > 0 else "-inf"}
        return v
    if value is pd.NaT:
        return {"$nat": True}
    if isinstance(value, pd.Timestamp):
        return {"$datetime": value.isoformat()}
    if isinstance(value, list):
        return [encode(v) for v in value]
    if isinstance(value, dict):
        return {k: encode(v) for k, v in value.items()}
    return value


def normalised_frame(rows: list[dict[str, Any]], columns: list[str]) -> pd.DataFrame:
    """Apply the coercions of ``normalize_belegliste`` to already canonical columns."""
    df = pd.DataFrame(rows, columns=columns)
    for col in AMOUNTS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in DATES:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def row(**kw: Any) -> dict[str, Any]:
    base = {
        "projektbetrag": 1234.0,
        "kuerzungsbetrag": 0.0,
        "anerkannter_betrag": 1234.0,
        "rechnungsdatum": "2024-03-01",
        "zahlungsdatum": "2024-03-15",
        "rechnungsnummer": "R-1",
        "rechnungssteller": "Lieferant A",
        "kuerzungsgrund": "",
        "vergabe": "V-1",
        "direktvergabe": "nein",
    }
    base.update(kw)
    return base


def case(name: str, rows: list[dict[str, Any]], drop: tuple[str, ...] = ()) -> dict[str, Any]:
    columns = [c for c in row() if c not in drop]
    extra = [k for r in rows for k in r if k not in columns and k not in drop]
    columns += list(dict.fromkeys(extra))
    return {
        "name": name,
        "columns": columns,
        "rows": [{k: v for k, v in r.items() if k not in drop} for r in rows],
    }


def boundary_cases() -> list[dict[str, Any]]:
    thresholds = [1000, 5000, 10000, 15000, 25000, 50000, 100000, 221000]
    amounts: list[Any] = [0.0, -1000.0, 1000.0, 2000.5, NAN, None, math.inf, 3000.0]
    for t in thresholds:
        amounts += [t * 0.9, math.nextafter(t * 0.9, 0), t - 0.01, float(t)]
    cases = [
        case(
            "rf01-rf02",
            [
                row(projektbetrag=a, anerkannter_betrag=a, rechnungsnummer=f"R-{i}")
                for i, a in enumerate(amounts)
            ],
        ),
        case(
            "rf03-rf04-daten",
            [
                row(zahlungsdatum=None, rechnungsnummer="R-1"),
                row(zahlungsdatum="2024-02-01", rechnungsdatum="2024-03-01", rechnungsnummer="R-2"),
                row(zahlungsdatum="2024-03-01", rechnungsdatum="2024-03-01", rechnungsnummer="R-3"),
                row(zahlungsdatum="kein Datum", rechnungsnummer="R-4"),
                row(rechnungsdatum=None, zahlungsdatum="2024-01-01", rechnungsnummer="R-5"),
            ],
        ),
        case(
            "rf05-dubletten",
            [
                row(rechnungsnummer="R-1", rechnungssteller="A", projektbetrag=100.0),
                row(rechnungsnummer="R-1", rechnungssteller="A", projektbetrag=100.0),
                row(rechnungsnummer="R-1", rechnungssteller="B", projektbetrag=100.0),
                row(rechnungsnummer=None, rechnungssteller="A", projektbetrag=NAN),
                row(rechnungsnummer=None, rechnungssteller="A", projektbetrag=None),
                row(rechnungsnummer="R-9", rechnungssteller=None, projektbetrag=5.0),
            ],
        ),
        case(
            "rf06-rf07-kuerzungen",
            [
                row(
                    projektbetrag=1000.0,
                    kuerzungsbetrag=100.0,
                    anerkannter_betrag=900.0,
                    kuerzungsgrund="",
                ),
                row(
                    projektbetrag=1000.0,
                    kuerzungsbetrag=100.0,
                    anerkannter_betrag=900.0,
                    kuerzungsgrund="  ",
                    rechnungsnummer="R-2",
                ),
                row(
                    projektbetrag=1000.0,
                    kuerzungsbetrag=100.0,
                    anerkannter_betrag=900.0,
                    kuerzungsgrund=None,
                    rechnungsnummer="R-3",
                ),
                row(
                    projektbetrag=1000.0,
                    kuerzungsbetrag=100.0,
                    anerkannter_betrag=900.0,
                    kuerzungsgrund="Fehlende Vergabe",
                    rechnungsnummer="R-4",
                ),
                row(
                    projektbetrag=1000.0,
                    kuerzungsbetrag=NAN,
                    anerkannter_betrag=1000.0,
                    kuerzungsgrund="",
                    rechnungsnummer="R-5",
                ),
                row(
                    projektbetrag=1000.0,
                    kuerzungsbetrag=0.0,
                    anerkannter_betrag=999.98,
                    rechnungsnummer="R-6",
                ),
                row(
                    projektbetrag=1000.0,
                    kuerzungsbetrag=0.0,
                    anerkannter_betrag=999.995,
                    rechnungsnummer="R-7",
                ),
                row(
                    projektbetrag=None,
                    kuerzungsbetrag=None,
                    anerkannter_betrag=None,
                    rechnungsnummer="R-8",
                ),
                row(
                    projektbetrag=1000.0,
                    kuerzungsbetrag=-50.0,
                    anerkannter_betrag=1050.0,
                    kuerzungsgrund=None,
                    rechnungsnummer="R-9",
                ),
            ],
        ),
        case(
            "rf08-rf09-vergabe",
            [
                row(projektbetrag=25000.0, vergabe="", rechnungsnummer="R-1"),
                row(projektbetrag=25000.01, vergabe="", rechnungsnummer="R-2"),
                row(projektbetrag=30000.0, vergabe=None, rechnungsnummer="R-3"),
                row(projektbetrag=30000.0, vergabe="nan", rechnungsnummer="R-4"),
                row(projektbetrag=30000.0, vergabe="None", rechnungsnummer="R-5"),
                row(projektbetrag=30000.0, vergabe="0", rechnungsnummer="R-6"),
                row(projektbetrag=30000.0, vergabe=" ", rechnungsnummer="R-7"),
                row(projektbetrag=30000.0, direktvergabe="Ja", rechnungsnummer="R-8"),
                row(projektbetrag=30000.0, direktvergabe="TRUE", rechnungsnummer="R-9"),
                row(projektbetrag=30000.0, direktvergabe="1", rechnungsnummer="R-10"),
                row(projektbetrag=30000.0, direktvergabe="10 Angebote", rechnungsnummer="R-11"),
                row(projektbetrag=30000.0, direktvergabe="Jahresvertrag", rechnungsnummer="R-12"),
                row(projektbetrag=30000.0, direktvergabe=None, rechnungsnummer="R-13"),
                row(projektbetrag=30000.0, direktvergabe=True, rechnungsnummer="R-14"),
                row(projektbetrag=25000.0, direktvergabe="ja", rechnungsnummer="R-15"),
            ],
        ),
        case(
            "rf10-konzentration",
            [
                row(rechnungssteller="A", projektbetrag=500.0, rechnungsnummer="R-1"),
                row(rechnungssteller="B", projektbetrag=250.0, rechnungsnummer="R-2"),
                row(rechnungssteller="C", projektbetrag=250.0, rechnungsnummer="R-3"),
            ],
        ),
        case(
            "rf10-knapp-unter",
            [
                row(rechnungssteller="A", projektbetrag=499.99, rechnungsnummer="R-1"),
                row(rechnungssteller="B", projektbetrag=500.01, rechnungsnummer="R-2"),
            ],
        ),
        case(
            "rf10-fehlende-steller",
            [
                row(rechnungssteller=None, projektbetrag=600.0, rechnungsnummer="R-1"),
                row(rechnungssteller=None, projektbetrag=100.0, rechnungsnummer="R-2"),
                row(rechnungssteller="B", projektbetrag=300.0, rechnungsnummer="R-3"),
                row(rechnungssteller="B", projektbetrag=NAN, rechnungsnummer="R-4"),
            ],
        ),
        case(
            "rf10-summe-null",
            [
                row(rechnungssteller="A", projektbetrag=100.0, rechnungsnummer="R-1"),
                row(rechnungssteller="B", projektbetrag=-100.0, rechnungsnummer="R-2"),
            ],
        ),
        case("ohne-betragsspalten", [row()], drop=("projektbetrag",)),
        case(
            "nur-betrag",
            [row(projektbetrag=5000.0)],
            drop=tuple(c for c in row() if c != "projektbetrag"),
        ),
        case("leer", [], drop=()),
    ]
    return cases


def random_cases(count: int, seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    thresholds = [1000, 5000, 10000, 15000, 25000, 50000, 100000, 221000]
    vendors = ["A", "B", "C", "D", None]
    optional = [
        "kuerzungsbetrag",
        "anerkannter_betrag",
        "rechnungsdatum",
        "zahlungsdatum",
        "rechnungsnummer",
        "rechnungssteller",
        "kuerzungsgrund",
        "vergabe",
        "direktvergabe",
    ]
    cases = []
    for k in range(count):
        rows = []
        for i in range(rng.randint(1, 30)):
            pick = rng.random()
            if pick < 0.3:
                amount: Any = float(rng.randint(1, 40) * 1000)
            elif pick < 0.5:
                amount = round(rng.choice(thresholds) * rng.uniform(0.85, 1.02), 2)
            elif pick < 0.55:
                amount = rng.choice([None, 0.0, -10.0])
            else:
                amount = round(rng.uniform(1, 60000), 2)
            cut = rng.choice([0.0, 0.0, round(rng.uniform(0, 500), 2), None])
            accepted = None if amount is None else round((amount or 0) - (cut or 0), 2)
            if rng.random() < 0.2 and accepted is not None:
                accepted += rng.choice([0.01, 0.02, 5.0])
            day = rng.randint(1, 28)
            rows.append(
                row(
                    projektbetrag=amount,
                    kuerzungsbetrag=cut,
                    anerkannter_betrag=accepted,
                    rechnungsdatum=rng.choice([f"2024-05-{day:02d}", None]),
                    zahlungsdatum=rng.choice([f"2024-05-{rng.randint(1, 28):02d}", None]),
                    rechnungsnummer=rng.choice([f"R-{i}", f"R-{i % 3}", None]),
                    rechnungssteller=rng.choice(vendors),
                    kuerzungsgrund=rng.choice(["", "Grund", None]),
                    vergabe=rng.choice(["V-1", "", None, "nan"]),
                    direktvergabe=rng.choice(["ja", "nein", None, "1"]),
                )
            )
        drop = tuple(c for c in optional if rng.random() < 0.15)
        cases.append(case(f"random-{seed}-{k:03d}", rows, drop=drop))
    return cases


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("designer", type=Path)
    parser.add_argument("portal", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--random", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20260923)
    args = parser.parse_args()
    namespaces = []
    for key, checkout in (("audit_designer", args.designer), ("audit-portal", args.portal)):
        head = subprocess.run(
            ["git", "-C", str(checkout), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        if head != SOURCES[key][1]:
            raise SystemExit(f"{key} checkout is at {head}, expected {SOURCES[key][1]}")
        namespaces.append(load(checkout / PATH))
    red_flags = namespaces[0]["_red_flags"]
    results = []
    for c in boundary_cases() + random_cases(args.random, args.seed):
        df = normalised_frame(c["rows"], c["columns"])
        out = red_flags(df)
        if namespaces[1]["_red_flags"](df.copy()) != out:
            raise SystemExit("audit-portal copy differs from audit_designer")
        results.append(
            {
                "name": c["name"],
                "columns": list(df.columns),
                "rows": encode(df.to_dict("records")),
                "exception": None,
                "red_flags": encode(out),
            }
        )
    document = {
        "sources": [
            {
                "repository": repo,
                "commit": commit,
                "path": PATH,
                "git_blob": BLOB,
                "symbols": SYMBOLS,
            }
            for repo, commit in SOURCES.values()
        ],
        "environment": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
        },
        "constants": {"PROCUREMENT_THRESHOLDS": namespaces[0]["PROCUREMENT_THRESHOLDS"]},
        "cases": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"{len(results)} Belegliste cases written to {args.output}")


if __name__ == "__main__":
    main()
