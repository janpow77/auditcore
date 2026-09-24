from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from auditcore_invoicesynth import build_dataset, load_split, verify_dataset
from auditcore_invoicesynth.dataset import DatasetError, plan_summary
from auditcore_invoicesynth.fonts import FontSet
from auditcore_invoicesynth.identifiers import iban_valid, vat_id_valid
from auditcore_invoicesynth.layouts import HOLDOUT_LAYOUTS
from auditcore_invoicesynth.plan import SPLITS, SynthConfig
from auditcore_invoicesynth.schema import from_sequence, to_sequence


def test_same_seed_same_hash_different_seed_different_hash(
    small_dataset: tuple[Path, dict[str, Any]],
    small_config: SynthConfig,
    fonts: FontSet,
    tmp_path: Path,
) -> None:
    first, manifest = small_dataset
    again = build_dataset(small_config, tmp_path / "b", fonts)
    assert again["dataset_hash"] == manifest["dataset_hash"]
    assert (tmp_path / "b/manifest.json").read_bytes() == (first / "manifest.json").read_bytes()
    from dataclasses import replace

    other = build_dataset(replace(small_config, seed=8), tmp_path / "c", fonts)
    assert other["dataset_hash"] != manifest["dataset_hash"]


def test_donut_layout_and_manifest(small_dataset: tuple[Path, dict[str, Any]]) -> None:
    root, manifest = small_dataset
    assert manifest["synthetic"] is True
    assert set(manifest["splits"]) == set(SPLITS)
    for split in SPLITS:
        rows = load_split(root, split)
        assert rows
        for row in rows:
            assert (root / split / row["file_name"]).is_file()
            gt = row["gt_parse"]
            assert from_sequence(to_sequence(gt)) == gt
            holdout = row["meta"]["layout"] in HOLDOUT_LAYOUTS
            assert holdout == (split == "test_layout_holdout")
            if "iban" in gt:
                assert iban_valid(gt["iban"])
            vat_id = gt.get("supplier", {}).get("vat_id")
            if vat_id:
                assert vat_id_valid(vat_id)
    fonts = manifest["fonts"]
    assert fonts and all(len(f["sha256"]) == 64 and "/" not in f["file"] for f in fonts)
    raw = (root / "train/metadata.jsonl").read_text(encoding="utf-8").splitlines()[0]
    assert set(json.loads(raw)) == {"file_name", "ground_truth"}


def test_ground_truth_holds_what_is_printed(small_dataset: tuple[Path, dict[str, Any]]) -> None:
    root, _ = small_dataset
    rows = [r for split in SPLITS for r in load_split(root, split)]
    single = [r for r in rows if r["meta"]["pages"] == 1]
    assert single
    for row in single:
        gt, meta = row["gt_parse"], row["meta"]
        assert {"invoice_number", "invoice_date", "total"} <= set(gt)
        assert ("iban" in gt) == ("missing_iban" not in meta["errors"])
        assert ("vat_id" in gt["supplier"]) == ("missing_vat_id" not in meta["errors"])
        if meta["vat_scheme"] in {"de_kleinunternehmer", "de_reverse_charge"}:
            assert "vat_lines" not in gt


def test_verify_detects_tampering(
    small_dataset: tuple[Path, dict[str, Any]], tmp_path: Path
) -> None:
    import shutil

    root, _ = small_dataset
    copy = tmp_path / "copy"
    shutil.copytree(root, copy)
    assert verify_dataset(copy).ok
    image = next((copy / "train").glob("*.png"))
    image.write_bytes(image.read_bytes() + b"x")
    (copy / "train/extra.txt").write_text("x")
    result = verify_dataset(copy)
    assert not result.ok and result.changed and result.unexpected == ("train/extra.txt",)
    with pytest.raises(DatasetError):
        verify_dataset(tmp_path)


def test_refuses_non_empty_output(
    small_config: SynthConfig, fonts: FontSet, tmp_path: Path
) -> None:
    (tmp_path / "x").write_text("x")
    with pytest.raises(DatasetError):
        build_dataset(small_config, tmp_path, fonts)


def test_plan_summary_without_images() -> None:
    summary = plan_summary(SynthConfig(), ("DejaVu Sans", "DejaVu Serif"))
    assert summary["samples"] == 2000
    assert summary == plan_summary(SynthConfig(), ("DejaVu Sans", "DejaVu Serif"))
