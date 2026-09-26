"""Hänge- und Fehlerschutz des Trainings: progress.json, SIGTERM, NaN, OOM, Daten, Job."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from auditcore_invoicesynth.train import PROFILES, GpuInfo, MockBackend, run_training
from auditcore_invoicesynth.train.guard import (
    EXIT_STOP_TIMEOUT,
    NonFiniteLoss,
    OutOfMemory,
    ProgressFile,
    StopRequest,
    TooManyBadSamples,
)
from auditcore_invoicesynth.train.ops import (
    GpuTemperature,
    flowagent_job,
    override_args,
)
from auditcore_invoicesynth.train.profiles import choose_topology

MOCK = replace(PROFILES["cpu_smoke"], max_steps=12, checkpoint_every_steps=4)
FIELDS = {
    "schritt",
    "schritte_gesamt",
    "epoche",
    "loss",
    "lr",
    "vram_mb",
    "gpu_temp_c",
    "zustand",
    "fehler",
    "letzter_checkpoint",
    "aktualisiert",
}


def _progress(run_dir: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((run_dir / "progress.json").read_text())
    return data


def _train(run_dir: Path, backend: MockBackend | None = None, **kwargs: Any) -> Any:
    return run_training(
        backend or MockBackend(),
        MOCK,
        samples=9,
        run_dir=run_dir,
        run_id="r",
        dataset_hash="d",
        progress=ProgressFile(run_dir, run_id="r"),
        **kwargs,
    )


def test_progress_file_has_runner_fields_and_is_atomic(tmp_path: Path) -> None:
    _train(tmp_path)
    progress = _progress(tmp_path)
    assert set(progress) >= FIELDS
    assert progress["zustand"] == "fertig" and progress["schritt"] == 12
    assert progress["schritte_gesamt"] == 12 and progress["letzter_checkpoint"] == 12
    assert progress["lr"] is not None and progress["fehler"] is None
    assert not list(tmp_path.glob(".progress.json.*.tmp"))


def test_heartbeat_refreshes_only_during_busy_phases(tmp_path: Path) -> None:
    ticks = iter(range(10_000))
    progress = ProgressFile(tmp_path, run_id="r", heartbeat_s=0.02, now=lambda: str(next(ticks)))
    progress.update(zustand="laeuft")
    with progress.busy("checkpoint"):
        assert _progress(tmp_path)["phase"] == "checkpoint"
        time.sleep(0.2)
    beats = int(_progress(tmp_path)["aktualisiert"])
    assert beats >= 4 and _progress(tmp_path)["phase"] == "start"
    time.sleep(0.1)
    assert int(_progress(tmp_path)["aktualisiert"]) == beats  # außerhalb: kein Herzschlag


def test_non_finite_loss_saves_last_good_state_and_fails(tmp_path: Path) -> None:
    backend = MockBackend()
    backend.failure = (7, NonFiniteLoss("Loss nan"))
    with pytest.raises(NonFiniteLoss) as caught:
        _train(tmp_path, backend)
    assert caught.value.exit_code == 3
    assert (tmp_path / "checkpoint-00000006").is_dir()  # letzter guter Schritt gesichert
    progress = _progress(tmp_path)
    assert progress["zustand"] == "fehler" and "NonFiniteLoss" in progress["fehler"]
    assert progress["letzter_checkpoint"] == 6


def test_non_finite_loss_after_update_saves_nothing_new(tmp_path: Path) -> None:
    backend = MockBackend()
    original = backend.train_step
    backend.train_step = lambda batches: (  # type: ignore[method-assign]
        float("nan") if backend.calls >= 5 else original(batches)
    )
    with pytest.raises(NonFiniteLoss):
        _train(tmp_path, backend)
    assert sorted(p.name for p in tmp_path.glob("checkpoint-*")) == ["checkpoint-00000004"]


def test_out_of_memory_exits_cleanly_with_reason(tmp_path: Path) -> None:
    backend = MockBackend()
    backend.failure = (3, OutOfMemory("CUDA-Speicher erschöpft"))
    with pytest.raises(OutOfMemory) as caught:
        _train(tmp_path, backend)
    assert caught.value.exit_code == 4
    assert (tmp_path / "checkpoint-00000002").is_dir()
    assert "CUDA-Speicher" in _progress(tmp_path)["fehler"]


def test_stop_request_checkpoints_and_resume_is_idempotent(tmp_path: Path) -> None:
    reference = _train(tmp_path / "ref")
    stop = StopRequest()
    backend = MockBackend()
    original = backend.train_step

    def step(batches: list[list[int]]) -> float:
        loss = original(batches)
        if backend.calls == 5:
            stop.trigger()
        return loss

    backend.train_step = step  # type: ignore[method-assign]
    first = _train(tmp_path / "run", backend, stop=stop)
    stop.finished()
    assert first.final_step == 5 and first.checkpoints == [4, 5]
    assert _progress(tmp_path / "run")["zustand"] == "abgebrochen"
    resumed = _train(tmp_path / "run")
    assert resumed.resumed_from == 5 and {**first.losses, **resumed.losses} == reference.losses
    again = _train(tmp_path / "run")  # nochmals starten: nichts mehr zu tun
    assert again.resumed_from == 12 and again.losses == {} and again.checkpoints == []
    assert _progress(tmp_path / "run")["zustand"] == "fertig"


def test_stop_deadline_forces_exit() -> None:
    exits: list[int] = []
    timeouts: list[bool] = []
    stop = StopRequest(
        deadline_s=0.05, on_timeout=lambda: timeouts.append(True), hard_exit=exits.append
    )
    stop.trigger()
    deadline = time.monotonic() + 5
    while not exits and time.monotonic() < deadline:
        time.sleep(0.01)
    assert exits == [EXIT_STOP_TIMEOUT] and timeouts == [True] and stop()
    finished = StopRequest(deadline_s=0.05, hard_exit=exits.append)
    finished.trigger()
    finished.finished()
    time.sleep(0.15)
    assert exits == [EXIT_STOP_TIMEOUT]


def test_sigterm_during_training_writes_checkpoint_and_exits_zero(
    small_dataset: tuple[Path, dict[str, Any]], tmp_path: Path
) -> None:
    dataset, _ = small_dataset
    run_dir = tmp_path / "run"
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
        "400",
        "--run-dir",
        str(run_dir),
    ]
    process = subprocess.Popen(  # noqa: S603
        [*command, "--step-delay", "0.05"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        progress = run_dir / "progress.json"
        if progress.is_file() and _progress(run_dir)["schritt"] >= 5:
            break
        time.sleep(0.02)
    process.send_signal(signal.SIGTERM)
    stdout, _ = process.communicate(timeout=60)
    assert process.returncode == 0
    result = json.loads(stdout)
    progress = _progress(run_dir)
    assert result["state"] == progress["zustand"] == "abgebrochen"
    assert progress["letzter_checkpoint"] == result["final_step"] < 400
    assert (run_dir / f"checkpoint-{result['final_step']:08d}").is_dir()


def test_too_many_unreadable_samples_abort(
    small_dataset: tuple[Path, dict[str, Any]], tmp_path: Path
) -> None:
    from auditcore_invoicesynth.train.torch_backend import TorchDonutBackend, weights_file

    dataset, _ = small_dataset
    backend = TorchDonutBackend(dataset, tmp_path)
    backend._skip("a.png")  # 12 Beispiele → 1 kaputtes erlaubt
    assert backend.skipped_samples == 1
    with pytest.raises(TooManyBadSamples):
        backend._skip("b.png")
    (tmp_path / "pytorch_model.bin").write_bytes(b"x")
    assert weights_file(tmp_path).name == "pytorch_model.bin"
    (tmp_path / "model.safetensors").write_bytes(b"y")
    assert weights_file(tmp_path).name == "model.safetensors"
    with pytest.raises(FileNotFoundError):
        weights_file(tmp_path / "leer")


def test_parallel_job_carries_per_run_overrides_and_mounts() -> None:
    config = replace(PROFILES["donut_train_janpow_ai"], epochs=3)
    gpus = [
        GpuInfo(0, "NVIDIA GeForce RTX 5070 Ti", 16303, 15800),
        GpuInfo(1, "NVIDIA GeForce RTX 5060 Ti", 16311, 15800),
    ]
    job = flowagent_job(
        config,
        choose_topology(config, gpus),
        dataset_hash="h" * 64,
        dataset_uri="/home/janpow/donut/datasets/pilot",
        run_id="r1",
        base_model_sha256="s" * 64,
        host_mounts={"base_model": "/home/janpow/donut/base/donut-base", "runs": "/runs"},
    )
    assert job["topology"]["mode"] == "parallel" and len(job["runs"]) == 2
    first, second = (run["command"] for run in job["runs"])
    assert "--image-size" not in first and first[first.index("--epochs") + 1] == "3"
    assert second[second.index("--image-size") + 1] == "1536x1152"
    assert second[second.index("--seed") + 1] == "43"
    assert first[-2:] == ["--base-model-sha256", "s" * 64]
    assert job["runs"][1]["run_dir"].endswith("/r1-1")
    assert job["runs"][0]["config_sha256"] != job["runs"][1]["config_sha256"]
    assert [m["host"] for m in job["container"]["mounts"]] == [
        "/home/janpow/donut/datasets/pilot",
        "/home/janpow/donut/base/donut-base",
        "/runs",
    ]
    assert override_args(PROFILES["donut_train_janpow_ai"]) == []


def test_cli_overrides_change_config_hash(
    small_dataset: tuple[Path, dict[str, Any]], tmp_path: Path
) -> None:
    from auditcore_invoicesynth.train import cli

    dataset, _ = small_dataset
    argv = ["--profile", "cpu_smoke", "--backend", "mock", "--dataset", str(dataset)]
    run_dir = tmp_path / "run"
    code = cli.main([*argv, "--run-dir", str(run_dir), "--epochs", "1", "--seed", "5"])
    assert code == 0 and _progress(run_dir)["zustand"] == "fertig"
    assert cli.main([*argv, "--run-dir", str(run_dir), "--image-size", "0x5"]) == 2


def test_gpu_temperature_is_cached() -> None:
    calls: list[int] = []
    now = [0.0]

    def query() -> str | None:
        calls.append(1)
        return "61\n"

    probe = GpuTemperature(interval_s=30, clock=lambda: now[0], query=query)
    assert probe() == 61.0 and probe() == 61.0 and len(calls) == 1
    now[0] = 31
    assert probe() == 61.0 and len(calls) == 2
    assert GpuTemperature(query=lambda: None)() is None
    assert GpuTemperature(query=lambda: "n/a")() is None


def test_signal_handlers_are_restored() -> None:
    before = signal.getsignal(signal.SIGTERM)
    stop = StopRequest().install()
    assert signal.getsignal(signal.SIGTERM) != before
    stop.finished()
    assert signal.getsignal(signal.SIGTERM) == before
    assert threading.current_thread() is threading.main_thread() and os.getpid()
