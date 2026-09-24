"""Synthetische Donut-Testbelege aus auditcore_invoicesynth erzeugen (nur Entwicklung).

    python tools/build_donut_fixtures.py   # benötigt auditcore_invoicesynth[render]

Schreibt ``tests/fixtures/donut/*.png`` (72 dpi, sichtbar „SYNTHETISCH“) und
``tests/fixtures/donut/cases.json`` (Ziel-JSON = Gedrucktes, Metadaten,
Datensatz-Hash). Keine echten Belege (Entscheidung E4).
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from auditcore_invoicesynth import SynthConfig, build_dataset, discover_fonts, load_split

TARGET = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "donut"
WANTED = ("kopf_links", "summen_unten", "kleinunternehmer", "mehrseitig", "holdout_briefkopf")


def main() -> None:
    fonts = discover_fonts(families=["DejaVu Sans", "DejaVu Serif"])
    config = SynthConfig(
        seed=2026,
        counts={"train": 40, "test_layout_holdout": 4},
        dpi_choices=(72,),
        augment_share=0.0,
        error_share=0.0,
    )
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "ds"
        manifest = build_dataset(config, out, fonts)
        rows = load_split(out, "train") + load_split(out, "test_layout_holdout")
        chosen: dict[str, list[dict[str, object]]] = {}
        for row in rows:
            layout = str(row["meta"]["layout"])
            sample = str(row["meta"]["sample_id"])
            if layout in WANTED and (layout not in chosen or chosen[layout][0]["sample"] == sample):
                chosen.setdefault(layout, []).append({"sample": sample, **row})
        TARGET.mkdir(parents=True, exist_ok=True)
        cases = []
        for layout in WANTED:
            for row in chosen[layout]:
                split = "test_layout_holdout" if layout.startswith("holdout") else "train"
                shutil.copyfile(out / split / str(row["file_name"]), TARGET / str(row["file_name"]))
                cases.append(
                    {
                        "file_name": row["file_name"],
                        "gt_parse": row["gt_parse"],
                        "meta": row["meta"],
                    }
                )
    (TARGET / "cases.json").write_text(
        json.dumps(
            {
                "generator": manifest["packages"],
                "config_seed": config.seed,
                "dataset_hash": manifest["dataset_hash"],
                "fonts": manifest["fonts"],
                "cases": cases,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
