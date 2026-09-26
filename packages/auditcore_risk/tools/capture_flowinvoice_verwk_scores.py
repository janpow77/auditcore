"""Record the scoring steps of flowinvoice VerwK (Verwaltungskontrolle) scores.

The unchanged, blob-verified functions run on synthetic data from the
flowinvoice demo generator (``generate_demo``) and on synthetic Mittelabruf
frames; a ``sys.settrace`` hook reads their local variables at fixed source
lines, so inputs and outputs of the scoring step come from the original
execution itself:

* ``rbvk_wibank_scorer.score_mittelabrufe`` at the ``stage = …`` line: the
  normalised Mittelabruf row ``r``, the history aggregates ``prior_k``,
  ``prior_q``, ``prior_families``, whether the beneficiary had no earlier
  project (``len(vh) == 0``), the points ``score`` and criteria ``flags``;
* ``exante_score._features`` at ``return f``: the ex-ante inputs and the seven
  indicators;
* ``exante_score.kalibriere_und_score`` after the class assignment: weights
  (calibrated or fallback), score, class and detail; and the comparison
  ``heuristik_score`` with the dictionaries it looks values up in.

Run with the VerwK environment of flowinvoice (``requirements-verwk.txt``,
Python 3.12 like ``Dockerfile.verwk``)::

    PYTHONPATH=<flowinvoice>/backend python tools/capture_flowinvoice_verwk_scores.py \
        <flowinvoice checkout> tests/fixtures/flowinvoice_verwk_scores_observed.json

All data are synthetic.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib
import inspect
import json
import math
import os
import platform
import random
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

COMMIT = "fb2d18568d2eaf64574d131ceae51a936b9aac02"
BASE = "backend/app/verwk/pipeline/"
FILES = {
    BASE + "rbvk_wibank_scorer.py": "24e04c04d8d98ae033c5d78508a29d4c900be4d1",
    BASE + "exante_score.py": "1f05d3f7a00d65b17ba79c7812fa05b52f8bccba",
}
RA_WIBANK = "backend/app/pipeline/rbvk_wibank_scorer.py"
RA_EXANTE = "backend/app/pipeline/exante_score.py"
WIBANK_FIELDS = [
    "verbundvorhaben",
    "fpg",
    "hat_bau",
    "hat_absch",
    "hat_sachleist",
    "beihilfefrei",
    "trennungsrechnung_erforderlich",
    "projekt_budget",
    "brutto",
    "offene_auflagen",
    "oeffentlich_rechtlich",
    "oeffentlicher_auftraggeber",
    "hat_vergabe",
    "eu_vergaberelevant",
    "n_direct",
    "hat_sach",
    "abruf_anteil",
]
EXANTE_FIELDS = ["brutto", "laufzeit_monate", "erw_ma", "fpgq", "grp_v", "an_risiko"]
HEUR_FIELDS = ["brutto", "kuerzungsquote", "laufzeit_monate", "ma", "belege", "gruppe", "fpg"]


def git_blob(raw: bytes) -> str:
    header = b"blob " + str(len(raw)).encode() + b"\0"
    return hashlib.sha1(header + raw, usedforsecurity=False).hexdigest()


def plain(value: Any) -> Any:
    """JSON value keeping NaN distinguishable; numpy scalars unwrapped."""
    if hasattr(value, "item") and not isinstance(value, list | dict | str):
        with contextlib.suppress(ValueError, AttributeError):
            value = value.item()
    if isinstance(value, float) and math.isnan(value):
        return {"$float": "nan"}
    if isinstance(value, set | frozenset):
        return sorted(plain(v) for v in value)
    if isinstance(value, list | tuple):
        return [plain(v) for v in value]
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if value is None or isinstance(value, bool | int | float | str):
        return value
    return str(value)


def line_of(func: Any, startswith: str) -> int:
    lines, first = inspect.getsourcelines(func)
    for offset, text in enumerate(lines):
        if text.strip().startswith(startswith):
            return first + offset
    raise SystemExit(f"line {startswith!r} not found in {func.__name__}")


class Tracer:
    """Reads locals of chosen functions at chosen lines."""

    def __init__(self, targets: dict[Any, tuple[int, Any]]) -> None:
        self.targets = {func.__code__: (line, handler) for func, (line, handler) in targets.items()}

    def __call__(self, frame: Any, event: str, arg: Any) -> Any:
        if event == "call" and frame.f_code in self.targets:
            line, handler = self.targets[frame.f_code]

            def local(frame: Any, event: str, arg: Any) -> Any:
                if event == "line" and frame.f_lineno == line:
                    handler(frame.f_locals)
                return local

            return local
        return None


def synthetic_ma_frames(seed: int, count: int) -> list[tuple[Any, Any]]:
    import pandas as pd

    rng = random.Random(seed)
    truthy = [True, False, "ja", "nein", "x", "", None, 1, 0, "EU-weit", "Hochschule"]
    frames = []
    for _ in range(count):
        rows, belege = [], []
        groups = [f"G{g}" for g in range(rng.randint(1, 4))]
        for i in range(rng.randint(2, 12)):
            group = rng.choice(groups)
            antrag = f"{group}-A{rng.randint(1, 3)}"
            year = rng.choice([2022, 2023, 2024, 2025])
            ma = f"{antrag}-MA{i}_v{rng.randint(1, 3)}"
            rows.append(
                {
                    "MA": ma,
                    "antrag": antrag,
                    "Gruppennummer": group,
                    "eingang": f"{year}-{rng.randint(1, 12):02d}-15",
                    "fpg": rng.choice(["1000", "1003", "1008", "1009", "1010", "2000", 1008]),
                    "brutto": rng.choice(
                        [
                            50_000.0,
                            1_600_000.0,
                            5_000_000.0,
                            6_000_000.0,
                            round(rng.uniform(10_000, 900_000), 2),
                        ]
                    ),
                    "kuerzung": rng.choice([0.0, 0.0, round(rng.uniform(100, 90_000), 2)]),
                    "bewilligungsrahmen": rng.choice([None, 0, 2_000_000.0, 100_000.0]),
                    "verbundvorhaben": rng.choice(truthy),
                    "beihilfefrei": rng.choice(truthy),
                    "trennungsrechnung_erforderlich": rng.choice(truthy),
                    "offene_auflagen": rng.choice(truthy),
                    "oeffentlich_rechtlich": rng.choice(truthy),
                    "oeffentlicher_auftraggeber": rng.choice(truthy),
                    "hochschule": rng.choice(truthy),
                    "eu_vergaberelevant": rng.choice(truthy),
                    "vergabeverfahren": rng.choice(["", "EU-weit offen", "national", None]),
                }
            )
            for _ in range(rng.randint(0, 90 if rng.random() < 0.2 else 6)):
                belege.append(
                    {
                        "MA": ma,
                        "antrag": antrag,
                        "kostenart_auswertung_bezeichnung": rng.choice(
                            [
                                "Bauleistung",
                                "Personal",
                                "Abschreibung",
                                "Sachleistung",
                                "Sachkosten",
                                "Gemeinkostenpauschale",
                                "Investition Anlage",
                            ]
                        ),
                        "vergabenummer": rng.choice(["", "V-1", None]),
                        "vergabeverfahren": rng.choice(["", "EU", None]),
                        "bruttobetrag": round(rng.uniform(100, 20_000), 2),
                        "abweichungen_betrag": rng.choice([0.0, round(rng.uniform(0, 500), 2)]),
                    }
                )
        frames.append(
            (
                pd.DataFrame(rows),
                pd.DataFrame(
                    belege,
                    columns=[
                        "MA",
                        "antrag",
                        "kostenart_auswertung_bezeichnung",
                        "vergabenummer",
                        "vergabeverfahren",
                        "bruttobetrag",
                        "abweichungen_betrag",
                    ],
                ),
            )
        )
    return frames


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    parser.add_argument("output", type=Path)
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
    wibank = importlib.import_module("app.verwk.pipeline.rbvk_wibank_scorer")
    exante = importlib.import_module("app.verwk.pipeline.exante_score")
    settings = importlib.import_module("app.verwk.core.config").settings
    wibank_rows: list[dict[str, Any]] = []
    exante_runs: list[dict[str, Any]] = []
    features: list[dict[str, Any]] = []

    def on_wibank(loc: dict[str, Any]) -> None:
        r = loc["r"]
        record = {k: plain(r.get(k)) for k in WIBANK_FIELDS if k in r.index}
        record.update(
            {
                "prior_k": plain(loc["prior_k"]),
                "prior_q": plain(loc["prior_q"]),
                "prior_families": plain(sorted(loc["prior_families"])),
                "erstes_vorhaben": len(loc["vh"]) == 0,
            }
        )
        wibank_rows.append(
            {
                "record": record,
                "score": int(loc["score"]),
                "flags": {str(k): bool(v) for k, v in loc["flags"].items()},
            }
        )

    def on_features(loc: dict[str, Any]) -> None:
        vh, f = loc["vh"], loc["f"]
        for idx in vh.index:
            features.append(
                {
                    "record": {k: plain(vh.at[idx, k]) for k in EXANTE_FIELDS},
                    "indicators": {c: int(f.at[idx, c]) for c in f.columns},
                }
            )

    def on_kalibrierung(loc: dict[str, Any]) -> None:
        f = loc["f"]
        heur_rows = []
        df_vh, grp_n, fpg_r = loc["df_vh"], loc["grp_n"], loc["fpg_r"]
        fpg_q = loc["df_fpg"].set_index("fpg")["kuerzungsquote"].to_dict()
        for idx in df_vh.index:
            row = {k: plain(df_vh.at[idx, k]) for k in HEUR_FIELDS}
            row["gruppe_vorhaben"] = plain(grp_n.get(df_vh.at[idx, "gruppe"], 1))
            row["fpg_quote"] = plain(fpg_q.get(df_vh.at[idx, "fpg"], 0))
            row["fpg_rueckgabequote"] = plain(fpg_r.get(df_vh.at[idx, "fpg"], 0))
            heur_rows.append({"record": row, "score": int(loc["heur"].at[idx])})
        exante_runs.append(
            {
                "mode": loc["kalibrierungsmodus"],
                "fallback": bool(loc["ex_ante_fallback"]),
                "weights": {k: int(v) for k, v in loc["wmap"].items()},
                "rows": [
                    {
                        "indicators": {c: int(f.at[i, c]) for c in f.columns},
                        "score": int(loc["score"].at[i]),
                        "class": str(loc["klasse"].at[i]),
                        "detail": list(loc["detail"].at[i]),
                    }
                    for i in f.index
                ],
                "heuristik": heur_rows,
            }
        )

    tracer = Tracer(
        {
            wibank.score_mittelabrufe: (line_of(wibank.score_mittelabrufe, "stage = "), on_wibank),
            exante._features: (line_of(exante._features, "return f"), on_features),
            exante.kalibriere_und_score: (
                line_of(exante.kalibriere_und_score, "yv = "),
                on_kalibrierung,
            ),
        }
    )
    build_levels = importlib.import_module("app.verwk.pipeline.aggregation").build_levels
    load_raw = importlib.import_module("app.verwk.pipeline.belegquelle").load_raw
    add_payee_columns = importlib.import_module(
        "app.verwk.pipeline.payee_normalizer"
    ).add_payee_columns
    generate_demo = importlib.import_module("app.verwk.services.demo_generator").generate_demo

    demo_runs = []
    with tempfile.TemporaryDirectory() as tmp:
        for seed, vorhaben in ((20260923, 40), (7, 25), (42, 60)):
            directory = Path(tmp) / f"demo-{seed}"
            generate_demo(
                {"seed": seed, "vorhaben": vorhaben, "start_jahr": 2023, "end_jahr": 2026},
                directory,
            )
            settings.pseudonymized_data_dir = str(directory)
            os.environ["PSEUDONYMIZED_DATA_DIR"] = str(directory)
            sys.settrace(tracer)
            try:
                levels = build_levels(add_payee_columns(load_raw(), fuzzy=False))
                wibank.score_mittelabrufe(levels["df_ma"], levels["df_belege"], {})
            finally:
                sys.settrace(None)
            demo_runs.append({"seed": seed, "vorhaben": vorhaben})
        settings.pseudonymized_data_dir = None
        for ma, bel in synthetic_ma_frames(20260923, 60):
            sys.settrace(tracer)
            try:
                wibank.score_mittelabrufe(ma, bel, {})
            finally:
                sys.settrace(None)
    import numpy
    import pandas

    statsmodels = importlib.import_module("statsmodels")

    document = {
        "source": {"repository": "janpow77/flowinvoice", "commit": COMMIT, "files": FILES},
        "also_present_in": {
            "janpow77/riskanalysis@b5c523b": {
                RA_WIBANK: "6ebd3a2ce56db09228ea770fe681089dc0c4391f",
                RA_EXANTE: "bc1725b5fdbca689275e9890e707eb4d90953023",
                "difference": "Importpfade/Closure bzw. eine ungenutzte Zeile; fachlich gleich",
            }
        },
        "environment": {
            "python": platform.python_version(),
            "pandas": pandas.__version__,
            "numpy": numpy.__version__,
            "statsmodels": statsmodels.__version__,
        },
        "demo_runs": demo_runs,
        "wibank": wibank_rows,
        "exante_features": features,
        "exante": exante_runs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, ensure_ascii=False) + "\n")
    print(
        f"{len(wibank_rows)} WIBANK rows, {len(features)} ex-ante feature rows, "
        f"{len(exante_runs)} calibration runs -> {args.output}"
    )


if __name__ == "__main__":
    main()
