"""Train CLI steps in-process (the subprocess tests cover abort and resume)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from auditcore_invoicesynth.train import cli


def _json(capsys: pytest.CaptureFixture[str]) -> Any:
    return json.loads(capsys.readouterr().out)


def test_systemd_unit_and_vram_check_need_no_dataset(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["--profile", "donut_train_8gb", "--systemd-unit"]) == 0
    unit = capsys.readouterr().out
    assert "xtts.service" in unit and "DATASET" in unit
    assert cli.main(["--profile", "cpu_smoke", "--check-vram"]) == 0
    assert _json(capsys) == {"ok": True, "gpus": []}


def test_plan_from_telemetry_file(
    small_dataset: tuple[Path, dict[str, Any]], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    dataset, _ = small_dataset
    gpus = tmp_path / "gpus.json"
    gpus.write_text(
        json.dumps(
            [{"index": 0, "name": "RTX", "memory_total_mib": 32768, "memory_free_mib": 30000}]
        )
    )
    argv = ["--profile", "cpu_smoke", "--dataset", str(dataset), "--plan", "--gpus-json"]
    assert cli.main([*argv, str(gpus)]) == 0
    job = _json(capsys)
    assert json.dumps(job)  # a FlowAgent job document


def test_mock_training_in_process(
    small_dataset: tuple[Path, dict[str, Any]], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    dataset, _ = small_dataset
    argv = ["--profile", "cpu_smoke", "--backend", "mock", "--dataset", str(dataset)]
    assert cli.main([*argv, "--max-steps", "3", "--run-dir", str(tmp_path / "run")]) == 0
    result = _json(capsys)
    assert result["final_step"] == 3 and result["resumed_from"] is None
    assert sorted(result["losses"]) == ["1", "2", "3"]


def test_missing_arguments_and_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        cli.main(["--profile", "cpu_smoke"])
    assert cli.main(["--profile", "cpu_smoke", "--dataset", str(tmp_path)]) == 2
    assert "Fehler:" in capsys.readouterr().err
