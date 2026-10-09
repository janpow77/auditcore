"""Diagnosesätze (nur Bewertung, nie Training): T2-gemischt, T2b und T2c.

* ``test_layout_holdout_shuffled`` (T2-gemischt): Vorlagen und Schrift des
  Layout-Holdouts T2, aber Kopfdaten-Reihenfolge je Beleg gemischt und
  Lieferdatum teils weggelassen (Ziehung aus :func:`variety.choose_variety`).
  Beschriftungen bleiben wie in T2; prüft, ob ein Modell Beschriftungen statt
  Positionen liest.
* ``test_layout_holdout_b`` (T2b): eigene Vorlage ``holdout_b_tabelle`` und
  eigene Schrift ``URW Gothic``, beide in keinem anderen Satz.
* ``test_layout_holdout_c`` (T2c): zwei eigene Vorlagen (``holdout_c_brief``,
  ``holdout_c_balken``) und eigene Schrift ``C059``, in keinem anderen Satz.
  Versiegelter Unbekannt-Test: T2/T2b gelten ab Stufe 7 als bekannt, T2c wird
  erst zur Abschlussbewertung von Stufe 7 angesehen.

``build_diagnostics`` schreibt nur diese Sätze in ein eigenes Verzeichnis mit
eigenem Manifest im Format der übrigen Datensätze; ``verify`` und
``train.evaluate --dataset <verzeichnis> --splits <satz>`` lesen es unverändert.
Bestehende Datensätze und deren Hashes bleiben unberührt.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path

from auditcore_common.hashing import sha256_file

from auditcore_invoicesynth import dataset as ds
from auditcore_invoicesynth.fonts import (
    HOLDOUT_B_FONT_FAMILIES,
    HOLDOUT_C_FONT_FAMILIES,
    FontSet,
)
from auditcore_invoicesynth.layouts import HOLDOUT_B_LAYOUTS, HOLDOUT_C_LAYOUTS, HOLDOUT_LAYOUTS
from auditcore_invoicesynth.plan import SampleSpec, SynthConfig, plan_dataset, sample_seed
from auditcore_invoicesynth.variety import choose_variety, variety_rng

SHUFFLED = "test_layout_holdout_shuffled"
HOLDOUT_B = "test_layout_holdout_b"
HOLDOUT_C = "test_layout_holdout_c"
SET_ALIASES = {"shuffled": SHUFFLED, "holdout_b": HOLDOUT_B, "holdout_c": HOLDOUT_C}


@dataclass(frozen=True)
class DiagnosticSet:
    layouts: tuple[str, ...]
    fonts: tuple[str, ...]
    shuffle_meta: bool
    purpose: str


DIAGNOSTIC_SETS: dict[str, DiagnosticSet] = {
    SHUFFLED: DiagnosticSet(
        HOLDOUT_LAYOUTS,
        ("DejaVu Serif",),
        True,
        "T2-Vorlagen und -Schrift, Kopfdaten-Reihenfolge gemischt, Lieferdatum teils weggelassen",
    ),
    HOLDOUT_B: DiagnosticSet(
        HOLDOUT_B_LAYOUTS,
        HOLDOUT_B_FONT_FAMILIES,
        False,
        "Neue Vorlage und Schrift, in keinem Trainings-, Validierungs- oder T1/T2-Satz",
    ),
    HOLDOUT_C: DiagnosticSet(
        HOLDOUT_C_LAYOUTS,
        HOLDOUT_C_FONT_FAMILIES,
        False,
        "Versiegelter Unbekannt-Test: eigene Vorlagen und Schrift, in keinem anderen Satz",
    ),
}


@dataclass(frozen=True)
class DiagnosticConfig:
    seed: int = 42
    base_date: date = date(2026, 1, 15)
    count: int = 500
    sets: tuple[str, ...] = (SHUFFLED, HOLDOUT_B)
    dpi_choices: tuple[int, ...] = (150, 200, 300)

    def validate(self) -> None:
        unknown = [name for name in self.sets if name not in DIAGNOSTIC_SETS]
        if unknown or not self.sets:
            raise ValueError(f"Diagnosesätze nur aus {sorted(DIAGNOSTIC_SETS)}: {unknown}")
        if self.count < 1:
            raise ValueError("Anzahl je Diagnosesatz mindestens 1")

    def to_dict(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "base_date": self.base_date.isoformat(),
            "count": self.count,
            "sets": list(self.sets),
            "dpi_choices": list(self.dpi_choices),
        }


def resolve_sets(text: str) -> tuple[str, ...]:
    """Kommaliste (Kurz- oder Satzname) in Satznamen übersetzen."""
    names = [SET_ALIASES.get(part.strip(), part.strip()) for part in text.split(",")]
    return tuple(dict.fromkeys(name for name in names if name))


def _set_config(config: DiagnosticConfig, name: str) -> SynthConfig:
    """Eigener Seed je Satz, damit die Belege nicht die Einzelseeds von T2 teilen."""
    spec = DIAGNOSTIC_SETS[name]
    return SynthConfig(
        seed=sample_seed(config.seed, name) % 2**31,
        base_date=config.base_date,
        counts={"test_layout_holdout": config.count},
        dpi_choices=config.dpi_choices,
        holdout_layouts=spec.layouts,
        holdout_font_families=spec.fonts,
    )


def plan_diagnostics(
    config: DiagnosticConfig, families: tuple[str, ...]
) -> list[tuple[SynthConfig, list[SampleSpec]]]:
    """Plan je Satz; fehlt die Satzschrift, bricht der Plan ab (kein stiller Ersatz)."""
    config.validate()
    plans = []
    for name in config.sets:
        missing = [f for f in DIAGNOSTIC_SETS[name].fonts if f not in families]
        if missing:
            raise ValueError(f"Schrift für {name} fehlt: {missing}")
        synth = _set_config(config, name)
        specs = [
            replace(spec, split=name, sample_id=f"{name}-{spec.index:06d}")
            for spec in plan_dataset(synth, families)
        ]
        plans.append((synth, specs))
    return plans


def prepare_diagnostics(
    config: DiagnosticConfig, families: tuple[str, ...]
) -> list[ds.PreparedSample]:
    """Belege erzeugen; T2-gemischt erhält nur Reihenfolge und Lieferdatum aus ``v2``."""
    prepared: list[ds.PreparedSample] = []
    for synth, specs in plan_diagnostics(config, families):
        for sample in ds.prepare_samples(synth, specs):
            if DIAGNOSTIC_SETS[sample.spec.split].shuffle_meta:
                sample = _shuffled(sample)
            prepared.append(sample)
    return prepared


def _shuffled(sample: ds.PreparedSample) -> ds.PreparedSample:
    variety = choose_variety(
        variety_rng(sample.spec.seed),
        language=sample.variant.language,
        credit_note=sample.invoice.kind == "credit_note",
    )
    variety = replace(variety, due_in_text=False, vat_id_under_name=False)
    return replace(sample, variant=replace(sample.variant, variety=variety))


def build_diagnostics(
    config: DiagnosticConfig, output: Path, fonts: FontSet, *, workers: int = 1
) -> dict[str, object]:
    """Diagnosesätze rendern und Manifest schreiben (gleiches Format wie ``build``)."""
    if output.exists() and any(output.iterdir()):
        raise ds.DatasetError(f"Ausgabeverzeichnis ist nicht leer: {output}")
    samples = prepare_diagnostics(config, fonts.families)
    output.mkdir(parents=True, exist_ok=True)
    rows: dict[str, list[str]] = {name: [] for name in config.sets}
    rendered = ds._rendered_samples(samples, output, fonts, workers)
    for sample, lines in zip(samples, rendered, strict=True):
        rows[sample.spec.split].extend(lines)
    for name, metadata_lines in rows.items():
        (output / name / "metadata.jsonl").write_text(
            "".join(line + "\n" for line in metadata_lines), encoding="utf-8"
        )
    manifest = _manifest(config, output, fonts, samples, rows)
    (output / ds.MANIFEST).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _manifest(
    config: DiagnosticConfig,
    output: Path,
    fonts: FontSet,
    samples: list[ds.PreparedSample],
    rows: dict[str, list[str]],
) -> dict[str, object]:
    files = {
        path.relative_to(output).as_posix(): sha256_file(path)
        for path in sorted(output.rglob("*"))
        if path.is_file() and path.name != ds.MANIFEST
    }
    used = sorted({s.spec.font_family for s in samples})
    return {
        "format": ds.FORMAT,
        "kind": "diagnostics",
        "evaluation_only": True,
        "synthetic": True,
        "packages": {"auditcore_invoicesynth": ds._version("auditcore_invoicesynth")},
        "runtime": ds._runtime(),
        "config": config.to_dict(),
        "sets": {
            name: {
                "purpose": DIAGNOSTIC_SETS[name].purpose,
                "layouts": list(DIAGNOSTIC_SETS[name].layouts),
                "fonts": list(DIAGNOSTIC_SETS[name].fonts),
                "samples": sum(1 for s in samples if s.spec.split == name),
                "images": len(rows[name]),
            }
            for name in config.sets
        },
        "fonts": fonts.describe(used),
        "files": files,
        "dataset_hash": ds.dataset_hash(files),
    }
