"""Trainingsschleife mit deterministischer Datenreihenfolge und Wiederaufnahme.

Die Schleife kennt kein Framework: ein ``TrainBackend`` führt einen
Optimiererschritt über die übergebenen Mikrobatches aus und speichert bzw.
lädt seinen vollständigen Zustand (Modell, Optimierer, Scheduler, RNG) in ein
Verzeichnis. Die Datenreihenfolge ist je Epoche aus dem Seed bestimmt, sodass
ein wiederaufgenommener Lauf exakt dieselben Schritte sieht. Das
Laufprotokoll (JSON-Zeilen) enthält Schritt, Epoche, Loss, VRAM-Spitze und
Temperatur; Zeilen nach dem letzten Checkpoint werden beim Wiederaufnehmen
nach ``rejected/`` verschoben, damit Schrittzähler und Loss-Verlauf stimmen.
"""

from __future__ import annotations

import json
import math
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from random import Random
from typing import Any, Protocol

from auditcore_invoicesynth.train.checkpoint import CheckpointManager, CheckpointPolicy
from auditcore_invoicesynth.train.guard import NonFiniteLoss, ProgressFile, StepFailed
from auditcore_invoicesynth.train.profiles import TrainConfig

LOG = "train-log.jsonl"


class TrainBackend(Protocol):
    world_size: int
    rank: int

    def setup(self, config: TrainConfig, samples: int) -> None: ...

    def train_step(self, microbatches: list[list[int]]) -> float: ...

    def save(self, directory: Path) -> None: ...

    def load(self, directory: Path) -> None: ...

    def vram_peak_gib(self) -> float | None: ...

    def barrier(self) -> None: ...


def epoch_order(samples: int, seed: int, epoch: int) -> list[int]:
    """Deterministische Permutation je Epoche."""
    order = list(range(samples))
    Random(f"{seed}:{epoch}").shuffle(order)
    return order


def step_batches(config: TrainConfig, samples: int, step: int, world_size: int) -> list[list[int]]:
    """Mikrobatches des (1-basierten) Optimiererschritts für alle Ränge zusammen."""
    per_step = config.effective_batch(world_size)
    steps_per_epoch = max(1, math.ceil(samples / per_step))
    epoch, position = divmod(step - 1, steps_per_epoch)
    order = epoch_order(samples, config.seed, epoch)
    start = position * per_step
    indices = [order[(start + k) % samples] for k in range(per_step)]
    size = config.per_device_batch
    return [indices[i : i + size] for i in range(0, per_step, size)]


def total_steps(config: TrainConfig, samples: int, world_size: int) -> int:
    """``max_steps`` bestimmt die Länge ausdrücklich (auch über Epochen hinweg)."""
    if config.max_steps:
        return config.max_steps
    per_epoch = max(1, math.ceil(samples / config.effective_batch(world_size)))
    return config.epochs * per_epoch


@dataclass
class TrainResult:
    run_id: str
    start_step: int
    final_step: int
    losses: dict[int, float] = field(default_factory=dict)
    resumed_from: int | None = None
    checkpoints: list[int] = field(default_factory=list)


def _truncate_log(run_dir: Path, keep_until: int) -> None:
    log = run_dir / LOG
    if not log.is_file():
        return
    keep: list[str] = []
    drop: list[str] = []
    for line in log.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        (keep if record.get("step", 0) <= keep_until else drop).append(line)
    if drop:
        rejected = run_dir / "rejected"
        rejected.mkdir(exist_ok=True)
        with (rejected / "train-log.after-checkpoint.jsonl").open("a", encoding="utf-8") as out:
            out.write("".join(line + "\n" for line in drop))
    log.write_text("".join(line + "\n" for line in keep), encoding="utf-8")


def run_training(
    backend: TrainBackend,
    config: TrainConfig,
    *,
    samples: int,
    run_dir: Path,
    run_id: str,
    dataset_hash: str,
    clock: Callable[[], float] = time.monotonic,
    wall: Callable[[], float] = time.time,
    temperature: Callable[[], float | None] = lambda: None,
    stop_after_step: int | None = None,
    step_delay: float = 0.0,
    progress: ProgressFile | None = None,
    stop: Callable[[], bool] = lambda: False,
) -> TrainResult:
    """Training bis ``max_steps``/Epochenende; setzt am neuesten gültigen Checkpoint fort.

    ``stop`` (z. B. ``StopRequest`` nach SIGTERM) beendet den Lauf nach dem
    laufenden Schritt mit Checkpoint. ``StepFailed`` (NaN-Loss, OOM, kaputte
    Daten) sichert den letzten guten Stand, setzt ``zustand=fehler`` und wird
    weitergereicht. ``stop_after_step`` bricht (nur für Tests/Rauchtests) nach
    diesem Schritt ohne Checkpoint ab und simuliert damit einen Stromausfall.
    """
    session = _start(
        backend, config, samples, run_dir, run_id, dataset_hash, progress, temperature, wall
    )
    start = session.last_saved
    policy = CheckpointPolicy(
        config.checkpoint_every_steps, config.checkpoint_every_minutes * 60, clock
    )
    try:
        for step in range(start + 1, session.last + 1):
            if stop():
                return session.finish("abgebrochen")
            session.run_step(step)
            if stop_after_step is not None and step >= stop_after_step:
                return session.result
            if policy.due(step) or step == session.last:
                session.checkpoint(step)
                policy.saved()
            if step_delay:
                time.sleep(step_delay)
    except StepFailed as exc:
        if exc.state_intact:
            session.checkpoint(session.result.final_step)
        session.report(zustand="fehler", phase="beendet", fehler=f"{type(exc).__name__}: {exc}")
        raise
    return session.finish("fertig")


def _start(
    backend: TrainBackend,
    config: TrainConfig,
    samples: int,
    run_dir: Path,
    run_id: str,
    dataset_hash: str,
    progress: ProgressFile | None,
    temperature: Callable[[], float | None],
    wall: Callable[[], float],
) -> _Session:
    """Prüfen, Modell laden, am neuesten gültigen Checkpoint fortsetzen, Stand melden."""
    config.validate()
    if samples < 1:
        raise ValueError("Datensatz ohne Beispiele")
    manager = CheckpointManager(
        run_dir,
        run_id=run_id,
        dataset_hash=dataset_hash,
        config_hash=config.config_hash,
        save_total_limit=config.save_total_limit,
    )
    report = progress if backend.rank == 0 else None
    with _busy(report, "laden"):
        backend.setup(config, samples)
        resumed_from = _resume(manager, backend)
    start = resumed_from or 0
    if backend.rank == 0:
        _truncate_log(run_dir, start)
    result = TrainResult(run_id, start, start, resumed_from=resumed_from)
    session = _Session(
        backend, config, manager, result, report, samples, run_dir, temperature, wall, start
    )
    session.report(
        zustand="laeuft",
        phase="training",
        schritt=start,
        letzter_checkpoint=resumed_from,
        schritte_gesamt=session.last,
    )
    return session


@contextmanager
def _busy(progress: ProgressFile | None, phase: str) -> Iterator[None]:
    if progress is None:
        yield
        return
    with progress.busy(phase):
        yield


@dataclass
class _Session:
    """Zustand eines Laufs: Schritt ausführen, protokollieren, sichern, melden."""

    backend: TrainBackend
    config: TrainConfig
    manager: CheckpointManager
    result: TrainResult
    progress: ProgressFile | None
    samples: int
    run_dir: Path
    temperature: Callable[[], float | None]
    wall: Callable[[], float]
    last_saved: int

    def __post_init__(self) -> None:
        self.last = total_steps(self.config, self.samples, self.backend.world_size)
        self.per_epoch = max(
            1, math.ceil(self.samples / self.config.effective_batch(self.backend.world_size))
        )

    def report(self, **fields: object) -> None:
        if self.progress is not None:
            self.progress.update(**fields)

    def run_step(self, step: int) -> None:
        batches = step_batches(self.config, self.samples, step, self.backend.world_size)
        loss = self.backend.train_step(batches)
        if not math.isfinite(loss):
            raise NonFiniteLoss(f"Loss {loss} in Schritt {step}", state_intact=False)
        self.result.losses[step] = loss
        self.result.final_step = step
        if self.backend.rank != 0:
            return
        epoch = (step - 1) // self.per_epoch
        record = _log_step(
            self.run_dir, step, epoch, loss, self.backend, self.temperature, self.wall
        )
        vram = record["vram_peak_gib"]
        self.report(
            schritt=step,
            epoche=epoch,
            loss=record["loss"],
            lr=_current_lr(self.backend),
            vram_mb=None if vram is None else round(vram * 1024),
            gpu_temp_c=record["temperature_c"],
            uebersprungene_beispiele=getattr(self.backend, "skipped_samples", 0),
        )

    def checkpoint(self, step: int) -> None:
        """Checkpoint schreiben, falls ``step`` neuer als der letzte gesicherte ist."""
        if step <= self.last_saved:
            return
        if self.backend.rank == 0:
            with _busy(self.progress, "checkpoint"):
                self.manager.save(step, self.backend.save, {"step": step, "samples": self.samples})
            self.result.checkpoints.append(step)
            self.report(letzter_checkpoint=step)
        self.backend.barrier()
        self.last_saved = step

    def finish(self, state: str) -> TrainResult:
        self.checkpoint(self.result.final_step)
        self.report(zustand=state, phase="beendet")
        return self.result


def _current_lr(backend: TrainBackend) -> float | None:
    reader = getattr(backend, "current_lr", None)
    return float(reader()) if callable(reader) else None


def _resume(manager: CheckpointManager, backend: TrainBackend) -> int | None:
    """Neuesten gültigen Checkpoint laden; dessen Schritt oder ``None``."""
    checkpoint = manager.latest()
    if checkpoint is None:
        return None
    backend.load(checkpoint.path)
    return checkpoint.step


def _log_step(
    run_dir: Path,
    step: int,
    epoch: int,
    loss: float,
    backend: TrainBackend,
    temperature: Callable[[], float | None],
    wall: Callable[[], float],
) -> dict[str, float | None]:
    """Eine Zeile ``train-log.jsonl`` (nur Rang 0)."""
    record: dict[str, float | None] = {
        "step": step,
        "epoch": epoch,
        "loss": round(loss, 8),
        "vram_peak_gib": backend.vram_peak_gib(),
        "temperature_c": temperature(),
        "time": round(wall(), 3),
    }
    with (run_dir / LOG).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return record


class MockBackend:
    """Rein pythonisches Ersatzmodell (lineare Regression, SGD mit Momentum, LR-Abfall).

    Dient Tests und dem Stromausfall-Nachweis ohne Torch: der vollständige Zustand
    (Gewichte, Momentum, Scheduler, RNG) wird gespeichert und geladen.
    """

    world_size = 1
    rank = 0

    def __init__(self) -> None:
        self.weights = [0.0, 0.0]
        self.momentum = [0.0, 0.0]
        self.lr = 0.05
        self.rng = Random(0)
        self.calls = 0
        #: Test-Einspeisung: (Aufruf-Nr., Fehler) – Fehler vor dem Optimiererschritt.
        self.failure: tuple[int, StepFailed] | None = None

    def setup(self, config: TrainConfig, samples: int) -> None:
        self.rng = Random(config.seed)
        self.lr = min(0.05, config.learning_rate * 1000)

    @staticmethod
    def _sample(index: int) -> tuple[float, float]:
        x = (index % 17) / 17.0
        return x, 3.0 * x + 0.5

    def train_step(self, microbatches: list[list[int]]) -> float:
        self.calls += 1
        if self.failure is not None and self.failure[0] == self.calls:
            raise self.failure[1]
        grads = [0.0, 0.0]
        loss = 0.0
        count = 0
        for batch in microbatches:
            for index in batch:
                x, y = self._sample(index)
                noise = self.rng.gauss(0.0, 0.01)  # „Dropout“: verbraucht RNG-Zustand
                error = self.weights[0] * x + self.weights[1] + noise - y
                grads[0] += 2 * error * x
                grads[1] += 2 * error
                loss += error * error
                count += 1
        for i in range(2):
            self.momentum[i] = 0.9 * self.momentum[i] + grads[i] / count
            self.weights[i] -= self.lr * self.momentum[i]
        self.lr *= 0.99
        return loss / count

    def save(self, directory: Path) -> None:
        state = {"weights": self.weights, "momentum": self.momentum, "lr": self.lr}
        (directory / "model.json").write_text(json.dumps(state), encoding="utf-8")
        (directory / "rng.json").write_text(json.dumps(self.rng.getstate()), encoding="utf-8")

    def load(self, directory: Path) -> None:
        state: dict[str, Any] = json.loads((directory / "model.json").read_text(encoding="utf-8"))
        self.weights, self.momentum, self.lr = state["weights"], state["momentum"], state["lr"]
        rng_state = json.loads((directory / "rng.json").read_text(encoding="utf-8"))
        self.rng.setstate((rng_state[0], tuple(rng_state[1]), rng_state[2]))

    def vram_peak_gib(self) -> float | None:
        return None

    def current_lr(self) -> float:
        return self.lr

    def barrier(self) -> None:
        return None
