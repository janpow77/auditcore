"""Datensatz im Donut-Format: Bilder, ``metadata.jsonl`` je Satz, Manifest, Hash.

Aufbau::

    dataset/
      manifest.json                 # Versionen, Seed, Plan, Schriften, SHA-256 je Datei, Hash
      train/metadata.jsonl          # {"file_name": "...png", "ground_truth": "{\\"gt_parse\\": …}"}
      validation/ test_synthetic/ test_layout_holdout/

Datensatz-Hash = SHA-256 über die sortierten Zeilen ``Pfad<TAB>SHA-256`` aller
Dateien außer ``manifest.json``. Gleicher Seed, gleiche Konfiguration, gleiche
Schriftdateien und gleiche Pillow-/zlib-Version ergeben denselben Hash; die
Versionen stehen deshalb im Manifest.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import timedelta
from importlib import metadata
from pathlib import Path
from random import Random
from types import ModuleType
from typing import Any, cast

from auditcore_common.hashing import canonical_sha256, sha256_file, sha256_text
from auditcore_invoicegenerator import InvoiceScenario

from auditcore_invoicesynth.enrich import SynthInvoice, enrich
from auditcore_invoicesynth.fonts import FontSet
from auditcore_invoicesynth.formats import AmountStyle, CurrencyStyle, DateStyle
from auditcore_invoicesynth.labels import SYNTHETIC_FOOTER, SYNTHETIC_MARKER, Language
from auditcore_invoicesynth.layouts import (
    HOLDOUT_LAYOUTS,
    TRAINING_LAYOUTS,
    Variant,
    expansion,
)
from auditcore_invoicesynth.plan import SPLITS, SampleSpec, SynthConfig, plan_dataset
from auditcore_invoicesynth.schema import SCHEMA_VERSION, TASK_TOKEN, nest_fields, ordered

MANIFEST = "manifest.json"
FORMAT = "auditcore-invoicesynth/donut-dataset/1"


class DatasetError(ValueError):
    """Ausgabeverzeichnis belegt oder Datensatz beschädigt."""


@dataclass(frozen=True)
class PreparedSample:
    spec: SampleSpec
    invoice: SynthInvoice
    variant: Variant


def _version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "UNKNOWN"


def prepare_samples(config: SynthConfig, specs: list[SampleSpec]) -> list[PreparedSample]:
    """Generator-Datensätze erzeugen und anreichern (ohne Pillow)."""
    scenarios = {
        country: InvoiceScenario(config.seed + offset, base_date=config.base_date, country=country)
        for offset, country in enumerate(("DE", "AT"))
    }
    counters = dict.fromkeys(scenarios, 0)
    prepared: list[PreparedSample] = []
    for spec in specs:
        counters[spec.country] += 1
        record = scenarios[spec.country].generate(counters[spec.country])
        rng = Random(spec.seed)
        invoice = enrich(
            record,
            rng=rng,
            vat_scheme=spec.vat_scheme,
            kind="credit_note" if spec.kind == "credit_note" else "invoice",
            errors=spec.errors,
            expand_positions=expansion(spec.layout, len(record["line_items"])),
            invoice_date=config.base_date + timedelta(days=rng.randrange(-180, 181)),
        )
        variant = Variant.choose(
            rng,
            language=cast(Language, spec.language),
            country=invoice.country,
            amount_style=cast(AmountStyle, spec.amount_style),
            currency_style=cast(CurrencyStyle, spec.currency_style),
            date_style=cast(DateStyle, spec.date_style),
            rate_variant=spec.rate_variant,
            iban_grouped=spec.iban_grouped,
        )
        prepared.append(PreparedSample(spec, invoice, variant))
    return prepared


def dataset_hash(files: dict[str, str]) -> str:
    return sha256_text("".join(f"{path}\t{digest}\n" for path, digest in sorted(files.items())))


def _runtime() -> dict[str, str]:
    runtime = {"pillow": "UNKNOWN", "zlib": "UNKNOWN", "freetype2": "UNKNOWN"}
    try:
        import PIL
        from PIL import features

        runtime["pillow"] = PIL.__version__
        runtime["zlib"] = str(features.version("zlib"))
        runtime["freetype2"] = str(features.version("freetype2"))
    except ImportError:  # pragma: no cover - ohne Extra
        pass
    return runtime


def _meta(sample: PreparedSample, page: int, pages: int) -> dict[str, Any]:
    spec, invoice = sample.spec, sample.invoice
    return {
        "sample_id": spec.sample_id,
        "page": page,
        "pages": pages,
        "layout": spec.layout,
        "font_family": spec.font_family,
        "dpi": spec.dpi,
        "language": spec.language,
        "country": invoice.country,
        "vat_scheme": invoice.vat_scheme,
        "kind": invoice.kind,
        "errors": list(invoice.errors),
        "augmented": spec.augment is not None,
        "correct_total": f"{invoice.total:.2f}",
        "synthetic": True,
    }


def build_dataset(
    config: SynthConfig,
    output: Path,
    fonts: FontSet,
    *,
    progress: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    """Datensatz schreiben und Manifest zurückgeben; das Zielverzeichnis muss leer sein."""
    from auditcore_invoicesynth.render import _pil

    if output.exists() and any(output.iterdir()):
        raise DatasetError(f"Ausgabeverzeichnis ist nicht leer: {output}")
    _, _, image_font = _pil()
    specs = plan_dataset(config, fonts.families)
    samples = prepare_samples(config, specs)
    output.mkdir(parents=True, exist_ok=True)
    rows: dict[str, list[str]] = {split: [] for split in SPLITS}
    images: dict[str, int] = dict.fromkeys(SPLITS, 0)
    used_families: set[str] = set()
    for number, sample in enumerate(samples, 1):
        used_families.add(sample.spec.font_family)
        for line in _write_sample(sample, output, fonts, image_font):
            rows[sample.spec.split].append(line)
            images[sample.spec.split] += 1
        if progress is not None:
            progress(number, len(samples))
    for split, lines in rows.items():
        if lines:
            (output / split).mkdir(exist_ok=True)
            (output / split / "metadata.jsonl").write_text(
                "".join(line + "\n" for line in lines), encoding="utf-8"
            )
    manifest = _manifest(config, output, fonts, specs, used_families, images)
    (output / MANIFEST).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _write_sample(
    sample: PreparedSample, output: Path, fonts: FontSet, image_font: ModuleType
) -> Iterator[str]:
    """Seiten eines Belegs rendern, prüfen, ggf. verfremden und speichern.

    Liefert je gespeicherter Seite die ``metadata.jsonl``-Zeile, erst nachdem das
    Bild geschrieben ist.
    """
    from auditcore_invoicesynth.augment import augment_page
    from auditcore_invoicesynth.render import render_pages

    spec = sample.spec
    pages = render_pages(
        sample.invoice,
        sample.variant,
        spec.layout,
        fonts,
        family=spec.font_family,
        dpi=spec.dpi,
        base_size_pt=spec.font_size_pt,
    )
    directory = output / spec.split
    directory.mkdir(exist_ok=True)
    for page_no, page in enumerate(pages, 1):
        texts = " ".join(page.texts)
        if SYNTHETIC_MARKER not in texts or SYNTHETIC_FOOTER not in texts:
            raise DatasetError(f"Synthetik-Kennzeichnung fehlt: {spec.sample_id}")
        image = page.image
        if spec.augment is not None:
            stamp_font = image_font.truetype(
                str(fonts.path(spec.font_family, "bold")), max(8, spec.dpi // 6)
            )
            image = augment_page(image, spec.augment, spec.seed + page_no, stamp_font=stamp_font)
        name = spec.sample_id + (f"-p{page_no}" if len(pages) > 1 else "") + ".png"
        image.save(directory / name, format="PNG", compress_level=6)
        ground_truth = {
            "gt_parse": ordered(nest_fields(page.fields)),
            "meta": _meta(sample, page_no, len(pages)),
        }
        yield json.dumps(
            {"file_name": name, "ground_truth": json.dumps(ground_truth, ensure_ascii=False)},
            ensure_ascii=False,
        )


def _manifest(
    config: SynthConfig,
    output: Path,
    fonts: FontSet,
    specs: list[SampleSpec],
    used_families: set[str],
    images: dict[str, int],
) -> dict[str, Any]:
    """Manifest mit Versionen, Plan, Schriften und SHA-256 aller geschriebenen Dateien."""
    files = {
        path.relative_to(output).as_posix(): sha256_file(path)
        for path in sorted(output.rglob("*"))
        if path.is_file() and path.name != MANIFEST
    }
    return {
        "format": FORMAT,
        "target_schema": SCHEMA_VERSION,
        "task_token": TASK_TOKEN,
        "synthetic": True,
        "synthetic_marking": {"header": SYNTHETIC_MARKER, "footer": SYNTHETIC_FOOTER},
        "decisions": "DONUT_OCR_PLAN.md Abschnitt 6: E2 MIT, E3 kein CORD, E4 keine echten "
        "Belege, E5 fiktive prüfziffer-gültige Kennungen, E8 nur Kopf-/Summenfelder",
        "packages": {
            name: _version(name)
            for name in (
                "auditcore_invoicesynth",
                "auditcore_invoicegenerator",
                "auditcore_dummygenerator",
            )
        },
        "runtime": _runtime(),
        "config": config.to_dict(),
        "layouts": {"training": list(TRAINING_LAYOUTS), "holdout": list(HOLDOUT_LAYOUTS)},
        "split_rules": (
            "Holdout-Vorlagen und Holdout-Schriften nur in test_layout_holdout; "
            "Einzelseed je Beleg = SHA-256(seed:sample_id)"
        ),
        "fonts": fonts.describe(sorted(used_families)),
        "splits": {
            split: {"samples": sum(1 for s in specs if s.split == split), "images": images[split]}
            for split in SPLITS
        },
        "files": files,
        "dataset_hash": dataset_hash(files),
    }


@dataclass(frozen=True)
class Verification:
    ok: bool
    dataset_hash: str
    expected_hash: str
    missing: tuple[str, ...]
    unexpected: tuple[str, ...]
    changed: tuple[str, ...]


def verify_dataset(directory: Path) -> Verification:
    """Dateien und Hash gegen das Manifest prüfen (ohne Pillow)."""
    manifest_path = directory / MANIFEST
    if not manifest_path.is_file():
        raise DatasetError(f"Manifest fehlt: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("format") != FORMAT:
        raise DatasetError("Unbekanntes Datensatzformat")
    expected: dict[str, str] = manifest["files"]
    actual = {
        path.relative_to(directory).as_posix(): sha256_file(path)
        for path in sorted(directory.rglob("*"))
        if path.is_file() and path.name != MANIFEST and not path.is_symlink()
    }
    missing = tuple(sorted(set(expected) - set(actual)))
    unexpected = tuple(sorted(set(actual) - set(expected)))
    changed = tuple(sorted(p for p in set(expected) & set(actual) if expected[p] != actual[p]))
    digest = dataset_hash(actual)
    return Verification(
        ok=not (missing or unexpected or changed)
        and digest == manifest["dataset_hash"] == dataset_hash(expected),
        dataset_hash=digest,
        expected_hash=str(manifest["dataset_hash"]),
        missing=missing,
        unexpected=unexpected,
        changed=changed,
    )


def load_split(directory: Path, split: str) -> list[dict[str, Any]]:
    """``metadata.jsonl`` eines Satzes lesen: ``file_name``, ``gt_parse``, ``meta``."""
    path = directory / split / "metadata.jsonl"
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        ground_truth = json.loads(record["ground_truth"])
        rows.append(
            {
                "file_name": record["file_name"],
                "gt_parse": ground_truth["gt_parse"],
                "meta": ground_truth.get("meta", {}),
            }
        )
    return rows


def plan_summary(config: SynthConfig, families: tuple[str, ...]) -> dict[str, Any]:
    """Plan und Ziel-JSON-Vorschau ohne Bilder (Kern ohne Extras)."""
    specs = plan_dataset(config, families)
    layouts: dict[str, int] = {}
    for spec in specs:
        layouts[spec.layout] = layouts.get(spec.layout, 0) + 1
    plan_hash = canonical_sha256([s.to_dict() for s in specs], compact=False, ensure_ascii=True)
    return {
        "samples": len(specs),
        "splits": {split: sum(1 for s in specs if s.split == split) for split in SPLITS},
        "layouts": dict(sorted(layouts.items())),
        "plan_sha256": plan_hash,
    }
