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
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from random import Random
from typing import Any, Protocol

from auditcore_invoicesynth.train.checkpoint import CheckpointManager, CheckpointPolicy
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
) -> TrainResult:
    """Training bis ``max_steps``/Epochenende; setzt am neuesten gültigen Checkpoint fort.

    ``stop_after_step`` bricht (nur für Tests/Rauchtests) nach diesem Schritt ohne
    Checkpoint ab und simuliert damit einen Stromausfall.
    """
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
    backend.setup(config, samples)
    main = backend.rank == 0
    checkpoint = manager.latest()
    start = 0
    if checkpoint is not None:
        backend.load(checkpoint.path)
        start = checkpoint.step
    if main:
        _truncate_log(run_dir, start)
    result = TrainResult(run_id, start, start, resumed_from=checkpoint.step if checkpoint else None)
    policy = CheckpointPolicy(
        config.checkpoint_every_steps, config.checkpoint_every_minutes * 60, clock
    )
    last = total_steps(config, samples, backend.world_size)
    per_epoch = max(1, math.ceil(samples / config.effective_batch(backend.world_size)))
    for step in range(start + 1, last + 1):
        batches = step_batches(config, samples, step, backend.world_size)
        loss = backend.train_step(batches)
        result.losses[step] = loss
        result.final_step = step
        if main:
            record = {
                "step": step,
                "epoch": (step - 1) // per_epoch,
                "loss": round(loss, 8),
                "vram_peak_gib": backend.vram_peak_gib(),
                "temperature_c": temperature(),
                "time": round(wall(), 3),
            }
            with (run_dir / LOG).open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, sort_keys=True) + "\n")
        if stop_after_step is not None and step >= stop_after_step:
            return result
        if policy.due(step) or step == last:
            if main:
                manager.save(step, backend.save, {"step": step, "samples": samples})
                result.checkpoints.append(step)
            backend.barrier()
            policy.saved()
        if step_delay:
            time.sleep(step_delay)
    return result


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

    def setup(self, config: TrainConfig, samples: int) -> None:
        self.rng = Random(config.seed)
        self.lr = min(0.05, config.learning_rate * 1000)

    @staticmethod
    def _sample(index: int) -> tuple[float, float]:
        x = (index % 17) / 17.0
        return x, 3.0 * x + 0.5

    def train_step(self, microbatches: list[list[int]]) -> float:
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

    def barrier(self) -> None:
        return None
