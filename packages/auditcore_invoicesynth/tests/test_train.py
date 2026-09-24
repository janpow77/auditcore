"""Etappe E3 (vorbereitet): Profile, Rechenort, atomare Checkpoints, Wiederaufnahme."""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from auditcore_invoicesynth.train import (
    PROFILES,
    CheckpointManager,
    GpuInfo,
    InsufficientVram,
    MockBackend,
    ResumeMismatch,
    check_free_vram,
    choose_topology,
    flowagent_job,
    parse_nvidia_smi,
    render_systemd_unit,
    run_training,
)
from auditcore_invoicesynth.train.cli import run_id_for
from auditcore_invoicesynth.train.loop import epoch_order, step_batches

MOCK = replace(PROFILES["cpu_smoke"], max_steps=12, checkpoint_every_steps=4)
GIB = 1024


def gpu(
    index: int, name: str, total_gib: float, free_gib: float, host: str = "janpow-ai"
) -> GpuInfo:
    return GpuInfo(index, name, int(total_gib * GIB), int(free_gib * GIB), host)


# --------------------------------------------------------------------------- Profile/Rechenort
def test_profiles_match_the_plan() -> None:
    janpow = PROFILES["donut_train_janpow_ai"]
    small = PROFILES["donut_train_8gb"]
    for config in PROFILES.values():
        config.validate()
    assert janpow.base_model_revision == "a959cf33c20e09215873e338299c900f57047c61"
    assert janpow.precision == small.precision == "bf16"
    assert small.per_device_batch == 1 and small.effective_batch() == 16
    assert janpow.effective_batch(world_size=2) == 16
    assert small.min_free_vram_gib == 6.5 and small.gradient_checkpointing
    assert janpow.checkpoint_every_steps == 200 and janpow.checkpoint_every_minutes == 15
    assert janpow.config_hash != small.config_hash
    assert replace(janpow).config_hash == janpow.config_hash
    with pytest.raises(ValueError):
        replace(janpow, precision="fp16").validate()


def test_topology_ddp_parallel_single_and_offline() -> None:
    config = PROFILES["donut_train_janpow_ai"]
    offline = choose_topology(config, [])
    assert offline.mode == "unavailable" and "ausdrücklich" in offline.reason
    same = choose_topology(config, [gpu(0, "RTX 5070 Ti", 16, 15.5), gpu(1, "RTX 5070 Ti", 16, 15)])
    assert same.mode == "ddp" and same.runs[0]["nproc_per_node"] == 2
    mixed = choose_topology(config, [gpu(0, "RTX 5070 Ti", 16, 15.5), gpu(1, "RTX 4090", 24, 23)])
    assert mixed.mode == "parallel"
    sizes = [tuple(run["config"]["image_size"]) for run in mixed.runs]
    assert sizes == [(1280, 960), (1536, 1152)]
    assert mixed.runs[0]["config_sha256"] != mixed.runs[1]["config_sha256"]
    one = choose_topology(config, [gpu(0, "RTX 5070 Ti", 16, 15.5), gpu(1, "GTX", 8, 7)])
    assert one.mode == "single" and one.gpus == (0,)
    nuc = choose_topology(PROFILES["donut_train_8gb"], [gpu(0, "RTX 5060 Laptop", 8, 6.1, "nuc")])
    assert nuc.mode == "unavailable"  # xtts belegt ≈ 1,9 GiB → erst pausieren (E7)


def test_vram_check_and_nvidia_smi_parsing() -> None:
    parsed = parse_nvidia_smi("0, NVIDIA GeForce RTX 5060 Laptop GPU, 8151, 6200\n", host="nuc")
    assert parsed == [GpuInfo(0, "NVIDIA GeForce RTX 5060 Laptop GPU", 8151, 6200, "nuc")]
    with pytest.raises(InsufficientVram, match="xtts"):
        check_free_vram(PROFILES["donut_train_8gb"], probe=lambda: parsed)
    ok = [GpuInfo(0, "x", 8151, 7000)]
    assert check_free_vram(PROFILES["donut_train_8gb"], probe=lambda: ok) == ok
    assert check_free_vram(PROFILES["cpu_smoke"], probe=lambda: []) == []


def test_flowagent_job_and_systemd_unit() -> None:
    config = PROFILES["donut_train_janpow_ai"]
    waiting = flowagent_job(
        config,
        choose_topology(config, []),
        dataset_hash="h" * 64,
        dataset_uri="/data/ds",
        run_id="r1",
    )
    assert waiting["status"] == "WAITING_FOR_COMPUTE" and waiting["fallback"] is None
    assert waiting["target"] == {"spoke": "janpow-ai", "capabilities": ["train:donut", "gpu"]}
    ddp = choose_topology(config, [gpu(0, "A", 16, 16), gpu(1, "A", 16, 16)])
    job = flowagent_job(config, ddp, dataset_hash="h" * 64, dataset_uri="/data/ds", run_id="r1")
    assert job["status"] == "READY" and job["runs"][0]["command"][:2] == [
        "torchrun",
        "--nproc_per_node=2",
    ]
    assert job["base_model"]["offline"] and job["environment"]["HF_HUB_OFFLINE"] == "1"
    json.dumps(job)
    unit = render_systemd_unit(
        PROFILES["donut_train_8gb"],
        python="/opt/venv/bin/python",
        dataset="/d",
        run_dir="/r",
        base_model_dir="/b",
        pause_units=("xtts.service",),
    )
    for needle in (
        "Restart=on-failure",
        "--check-vram",
        "stop xtts.service",
        "start xtts.service",
        "HF_HUB_OFFLINE=1",
        "--run-dir /r",
    ):
        assert needle in unit


# --------------------------------------------------------------------------- Checkpoints
def _write(content: str):  # type: ignore[no-untyped-def]
    def write(directory: Path) -> None:
        (directory / "model.bin").write_text(content)
        (directory / "sub").mkdir()
        (directory / "sub/optimizer.bin").write_text(content * 2)

    return write


def test_checkpoints_are_atomic_verified_and_pruned(tmp_path: Path) -> None:
    manager = CheckpointManager(
        tmp_path, run_id="r", dataset_hash="d", config_hash="c", save_total_limit=2
    )
    for step in (2, 4, 6):
        manager.save(step, _write(f"s{step}"), {"step": step})
    assert sorted(p.name for p in tmp_path.glob("checkpoint-*")) == [
        "checkpoint-00000004",
        "checkpoint-00000006",
    ]
    (tmp_path / "checkpoint-00000008.tmp").mkdir()  # Stromausfall beim Schreiben
    (tmp_path / "checkpoint-00000008.tmp/model.bin").write_text("halb")
    (tmp_path / "checkpoint-00000006/model.bin").write_text("kaputt")  # Bitfehler
    latest = manager.latest()
    assert latest is not None and latest.step == 4
    rejected = sorted(p.name for p in (tmp_path / "rejected").iterdir())
    assert "checkpoint-00000008.tmp" in rejected and "checkpoint-00000006" in rejected
    assert (tmp_path / "rejected/checkpoint-00000006.reason").read_text().startswith("Prüfsummen")
    other = CheckpointManager(tmp_path, run_id="r", dataset_hash="anderer", config_hash="c")
    with pytest.raises(ResumeMismatch):
        other.latest()


# --------------------------------------------------------------------------- Wiederaufnahme
def test_data_order_is_deterministic() -> None:
    assert epoch_order(10, 1, 0) == epoch_order(10, 1, 0) != epoch_order(10, 1, 1)
    batches = step_batches(MOCK, 7, 3, 1)
    assert len(batches) == MOCK.grad_accum and all(len(b) == 1 for b in batches)


def _run(run_dir: Path, **kwargs: Any) -> tuple[Any, MockBackend]:
    backend = MockBackend()
    result = run_training(
        backend, MOCK, samples=9, run_dir=run_dir, run_id="r", dataset_hash="d", **kwargs
    )
    return result, backend


def test_power_loss_resume_matches_uninterrupted_run(tmp_path: Path) -> None:
    reference, ref_backend = _run(tmp_path / "ref")
    assert reference.final_step == 12 and reference.checkpoints == [4, 8, 12]
    first, _ = _run(tmp_path / "run", stop_after_step=6)
    assert first.checkpoints == [4]
    partial = tmp_path / "run/checkpoint-00000008.tmp"
    partial.mkdir()
    (partial / "model.json").write_text("{")
    resumed, backend = _run(tmp_path / "run")
    assert resumed.resumed_from == 4
    assert {**first.losses, **resumed.losses} == reference.losses
    assert backend.weights == ref_backend.weights and backend.lr == ref_backend.lr
    log = [json.loads(line) for line in (tmp_path / "run/train-log.jsonl").read_text().splitlines()]
    assert [r["step"] for r in log] == list(range(1, 13))
    assert [r["loss"] for r in log] == [round(reference.losses[s], 8) for s in range(1, 13)]
    moved = (tmp_path / "run/rejected/train-log.after-checkpoint.jsonl").read_text().splitlines()
    assert [json.loads(line)["step"] for line in moved] == [5, 6]


def test_kill_9_during_training_resumes_from_last_valid_checkpoint(
    small_dataset: tuple[Path, dict[str, Any]], tmp_path: Path
) -> None:
    """Echter Prozessabbruch (SIGKILL) während des Laufs, danach Wiederaufnahme."""
    dataset, _ = small_dataset
    command = [
        sys.executable,
        "-m",
        "auditcore_invoicesynth.train.cli",
        "--profile",
        "cpu_smoke",
        "--backend",
        "mock",
        "--dataset",
        str(dataset),
        "--max-steps",
        "40",
    ]
    reference = subprocess.run(  # noqa: S603
        [*command, "--run-dir", str(tmp_path / "ref")], capture_output=True, text=True, check=True
    )
    expected = json.loads(reference.stdout)["losses"]
    run_dir = tmp_path / "run"
    process = subprocess.Popen(  # noqa: S603
        [*command, "--run-dir", str(run_dir), "--step-delay", "0.05"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    log = run_dir / "train-log.jsonl"
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if log.is_file() and len(log.read_text().splitlines()) >= 11:
            break
        time.sleep(0.01)
    os.kill(process.pid, signal.SIGKILL)
    process.wait()
    assert process.returncode == -signal.SIGKILL
    resumed = subprocess.run(  # noqa: S603
        [*command, "--run-dir", str(run_dir)], capture_output=True, text=True, check=True
    )
    result = json.loads(resumed.stdout)
    assert result["resumed_from"] is not None and result["resumed_from"] >= 10
    assert result["final_step"] == 40
    lines = [json.loads(line) for line in log.read_text().splitlines()]
    assert [r["step"] for r in lines] == list(range(1, 41))
    assert {str(r["step"]): r["loss"] for r in lines} == {
        k: round(v, 8) for k, v in expected.items()
    }
    assert run_id_for("a", "b") == run_id_for("a", "b") != run_id_for("a", "c")


def test_changed_configuration_refuses_resume(tmp_path: Path) -> None:
    _run(tmp_path, stop_after_step=5)
    with pytest.raises(ResumeMismatch):
        run_training(
            MockBackend(),
            replace(MOCK, learning_rate=1e-4),
            samples=9,
            run_dir=tmp_path,
            run_id="r",
            dataset_hash="d",
        )


# --------------------------------------------------------------------------- Torch-Rauchtest
def test_cpu_smoke_with_tiny_donut_model(
    small_dataset: tuple[Path, dict[str, Any]], tmp_path: Path
) -> None:
    """Wenige Schritte mit winzigem, zufälligem Modell auf der CPU (Extra ``train``)."""
    pytest.importorskip("torch")
    pytest.importorskip("transformers")
    pytest.importorskip("tokenizers")
    dataset, _ = small_dataset
    command = [
        sys.executable,
        "-m",
        "auditcore_invoicesynth.train.cli",
        "--profile",
        "cpu_smoke",
        "--dataset",
        str(dataset),
        "--run-dir",
        str(tmp_path / "run"),
        "--tiny",
    ]
    first = json.loads(
        subprocess.run(  # noqa: S603
            [*command, "--stop-after-step", "3"], capture_output=True, text=True, check=True
        ).stdout
    )
    assert first["checkpoints"] == [2]
    second = json.loads(
        subprocess.run(  # noqa: S603
            command, capture_output=True, text=True, check=True
        ).stdout
    )
    assert second["resumed_from"] == 2 and second["final_step"] == 6
    assert second["losses"]["3"] == pytest.approx(first["losses"]["3"], rel=1e-5)
    checkpoint = tmp_path / "run/checkpoint-00000006"
    for name in (
        "model.safetensors",
        "optimizer.pt",
        "scheduler.pt",
        "rng.pt",
        "tokenizer.json",
        "CHECKSUMS.sha256",
        "meta.json",
    ):
        assert (checkpoint / name).is_file(), name
    assert CheckpointManager.verify(checkpoint) is None
    shutil.rmtree(tmp_path / "run")
