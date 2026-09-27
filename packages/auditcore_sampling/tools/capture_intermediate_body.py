"""Record the invoice draw of flowinvoice for the parity test of ``intermediate_body``.

Run with an interpreter providing numpy and pandas::

    python -I tools/capture_intermediate_body.py <flowinvoice>/backend \
        tests/fixtures/intermediate_body_observed.json.gz

The planning module ``app/verwk/pipeline/pruefplan.py`` is loaded directly
from its path after verifying the pinned Git blob; no application package,
database or network. The draw function and its ladder are found by their name
suffixes (``*_ziehung``, ``*_leiter``), the parameter keys by theirs
(``*_belegstichprobe_anteil``, ``*_eskalation``), so the tool names no
institution. For every case the tool stores the inputs, the derived seed, the
permutation the NumPy generator produced and the drawn positions with their
ladder stage. All amounts are synthetic.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import platform
import random
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

SOURCE = {
    "repository": "janpow77/flowinvoice",
    "commit": "fb2d18568d2eaf64574d131ceae51a936b9aac02",
    "path": "backend/app/verwk/pipeline/pruefplan.py",
    "blob": "08155daeacda5c841d83521f3b48b0dedfd6234a",
}


def load(backend: Path) -> ModuleType:
    path = backend / "app" / "verwk" / "pipeline" / "pruefplan.py"
    blob = subprocess.run(
        ["git", "hash-object", str(path)], check=True, capture_output=True, text=True
    ).stdout.strip()
    if blob != SOURCE["blob"]:
        raise SystemExit(f"Unerwarteter Stand {blob} von {path}")
    spec = importlib.util.spec_from_file_location("source_plan", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def by_suffix(names: Any, suffix: str) -> str:
    found = [n for n in names if n.endswith(suffix)]
    if len(found) != 1:
        raise SystemExit(f"Kein eindeutiger Name mit Endung {suffix}: {found}")
    return found[0]


def cases(rng: random.Random) -> list[dict[str, Any]]:
    result = []
    for number in range(240):
        size = rng.choice([0, 1, 2, 3, 5, 12, 40, 100, 250])
        amounts = [round(rng.lognormvariate(6, 1.4), 2) for _ in range(size)]
        if size and number % 7 == 0:
            amounts[rng.randrange(size)] = round(sum(amounts) * 2, 2)  # one dominating invoice
        rate = rng.choice([0.0, 0.05, 0.3, 1.0])
        errors = [round(a * rng.random() * 0.2, 2) if rng.random() < rate else 0.0 for a in amounts]
        result.append(
            {
                "claim": f"MA-{number:04d}",
                "base_seed": rng.choice([1, 7, 20260808, 987654321]),
                "start_share": rng.choice([0.0, 0.1, 0.25, 0.25, 0.4, 0.9, 1.0]),
                "escalate": rng.random() < 0.8,
                "amounts": amounts,
                "errors": errors,
            }
        )
    return result


def run(module: ModuleType, case: dict[str, Any]) -> dict[str, Any]:
    import numpy as np
    import pandas as pd

    draw = getattr(module, by_suffix(dir(module), "_ziehung"))
    share_key = by_suffix(module.DEFAULTS, "_belegstichprobe_anteil")
    escalate_key = by_suffix(module.DEFAULTS, "_eskalation")
    frame = pd.DataFrame(
        {
            "MA": [case["claim"]] * len(case["amounts"]),
            "bruttobetrag": case["amounts"],
            "abweichungen_betrag": case["errors"],
        }
    )
    parameters = {
        **module.DEFAULTS,
        share_key: case["start_share"],
        escalate_key: case["escalate"],
        "zufallsseed": case["base_seed"],
    }
    drawn = [int(i) for i in draw(frame, frame.index, case["claim"], parameters)]
    stage_column = by_suffix(frame.columns, "_ziehstufe") if drawn else None
    stages = [int(frame.loc[i, stage_column]) for i in drawn] if stage_column else []
    stable = int(hashlib.sha256(case["claim"].encode("utf-8")).hexdigest()[:8], 16)
    seed = case["base_seed"] + stable % 1000003
    order = [int(i) for i in np.random.default_rng(seed).permutation(len(case["amounts"]))]
    return {**case, "derived_seed": seed, "order": order, "drawn": drawn, "stages": stages}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backend", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    module = load(args.backend)
    ladder = getattr(module, by_suffix(dir(module), "_leiter"))
    starts = [0.0, 0.1, 0.25, 0.4, 0.55, 0.7, 0.85, 0.9, 1.0]
    import numpy
    import pandas

    observed = {
        "source": SOURCE,
        "environment": {
            "python": platform.python_version(),
            "numpy": numpy.__version__,
            "pandas": pandas.__version__,
        },
        "ladders": [{"start_share": s, "ladder": list(ladder(s))} for s in starts],
        "cases": [run(module, case) for case in cases(random.Random(20260926))],
    }
    args.output.write_bytes(gzip.compress(json.dumps(observed, sort_keys=True).encode(), mtime=0))
    print(f"{len(observed['cases'])} Fälle → {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
