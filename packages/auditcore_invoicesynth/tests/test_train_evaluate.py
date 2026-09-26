"""Bewertung nach dem Training: Kandidat und Donut-CORD mit einem Befehl."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from auditcore_invoicesynth.dataset import load_split
from auditcore_invoicesynth.schema import to_sequence
from auditcore_invoicesynth.train import CheckpointManager
from auditcore_invoicesynth.train import evaluate as train_eval


def _echo_predictor(dataset: Path) -> Any:
    truth: dict[str, dict[str, Any]] = {}
    for split in ("test_synthetic", "test_layout_holdout"):
        for row in load_split(dataset, split):
            truth[row["file_name"]] = row["gt_parse"]

    def make(directory: Path, *, prompt: str, **_: Any) -> Any:
        def predict(path: Path) -> str:
            gt = truth[path.name]
            if prompt == train_eval.CORD_PROMPT:
                return f"{prompt}<s_total><s_total_price>{gt['total']}</s_total_price></s_total>"
            return to_sequence(gt)

        return predict

    return make


def test_one_command_evaluation_with_cord_comparison(
    small_dataset: tuple[Path, dict[str, Any]], tmp_path: Path
) -> None:
    dataset, _ = small_dataset
    out = tmp_path / "eval/report.json"
    code = train_eval.main(
        [
            "--dataset",
            str(dataset),
            "--model-dir",
            str(tmp_path),
            "--cord-model-dir",
            str(tmp_path),
            "--out",
            str(out),
        ],
        make_predictor=_echo_predictor(dataset),
    )
    assert code == 0
    report = json.loads(out.read_text())
    own = report["results"]["kandidat"]["test_layout_holdout"]
    assert own["document_rate"] == 1.0 and own["acceptance"]["passed"]
    cord = report["results"]["donut_cord"]["test_synthetic"]
    assert cord["fields"]["total"]["accuracy"] == 1.0 and cord["document_rate"] == 0.0
    assert (tmp_path / "eval/report.donut_cord.test_synthetic.jsonl").is_file()


def test_cord_mapping_and_checkpoint_choice(tmp_path: Path) -> None:
    parse = train_eval.parse_output(
        "<s_cord-v2><s_menu><s_nm>A</s_nm></s_menu><s_sub_total><s_subtotal_price>10,00"
        "</s_subtotal_price><s_tax_price>1,90</s_tax_price></s_sub_total>"
        "<s_total><s_total_price>11,90</s_total_price></s_total></s>",
        cord=True,
    )
    assert parse == {"total": "11,90", "net_amount": "10,00", "vat_lines": [{"amount": "1,90"}]}
    assert train_eval.cord_to_invoice({"total": "x"}) == {}
    manager = CheckpointManager(tmp_path, run_id="r", dataset_hash="d", config_hash="c")
    for step in (2, 4):
        manager.save(step, lambda d: (d / "w").write_text("x"), {})
    (tmp_path / "checkpoint-00000004/w").write_text("kaputt")
    assert train_eval.latest_checkpoint(tmp_path).name == "checkpoint-00000002"
    with pytest.raises(FileNotFoundError):
        train_eval.latest_checkpoint(tmp_path / "leer")


def test_rejects_changed_dataset(
    small_dataset: tuple[Path, dict[str, Any]], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    dataset, manifest = small_dataset
    broken = tmp_path / "ds"
    broken.mkdir()
    (broken / "manifest.json").write_text(json.dumps({**manifest, "dataset_hash": "0" * 64}))
    argv = ["--dataset", str(broken), "--model-dir", str(tmp_path), "--out", str(tmp_path / "r")]
    assert train_eval.main(argv) == 2
    assert "Fehler" in capsys.readouterr().err


def test_tiny_checkpoint_evaluates_end_to_end(
    small_dataset: tuple[Path, dict[str, Any]], tmp_path: Path
) -> None:
    """Echter Donut-Checkpoint (winzig, CPU) → Vorhersagen → Bericht."""
    pytest.importorskip("torch")
    pytest.importorskip("transformers")
    dataset, _ = small_dataset
    run_dir = tmp_path / "run"
    train = [
        sys.executable,
        "-m",
        "auditcore_invoicesynth.train.cli",
        "--profile",
        "cpu_smoke",
        "--dataset",
        str(dataset),
        "--run-dir",
        str(run_dir),
        "--tiny",
        "--max-steps",
        "2",
    ]
    subprocess.run(train, capture_output=True, text=True, check=True)  # noqa: S603
    out = tmp_path / "report.json"
    evaluate = [
        sys.executable,
        "-m",
        "auditcore_invoicesynth.train.evaluate",
        "--dataset",
        str(dataset),
        "--run-dir",
        str(run_dir),
        "--limit",
        "1",
        "--max-length",
        "16",
        "--out",
        str(out),
    ]
    subprocess.run(evaluate, capture_output=True, text=True, check=True)  # noqa: S603
    report = json.loads(out.read_text())
    assert report["model_dir"].endswith("checkpoint-00000002")
    assert report["results"]["kandidat"]["test_synthetic"]["documents"] == 1
