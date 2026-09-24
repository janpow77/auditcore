"""Trainingsprofile und Wahl des Rechenorts (Plan 2c und 2c-bis, Entscheidung E7).

* ``donut_train_janpow_ai`` – Hauptort janpow-ai (zwei GPUs über den FlowAgent):
  gleiche Kartenklasse mit ≥ 16 GiB → DDP (``torchrun --nproc_per_node=2``),
  ungleiche Karten → zwei unabhängige Läufe (Bildgröße 1280×960 und 1536×1152),
  Auswahl später per Bewertung.
* ``donut_train_8gb`` – ausdrücklicher Rückfall NUC (RTX 5060 Laptop, 8 GiB):
  Batch 1, Akkumulation 16, Gradient Checkpointing, optional 8-bit-AdamW; Start
  nur mit ≥ 6,5 GiB freiem VRAM (xtts vorher pausieren, E7).
* ``cpu_smoke`` – winziges Modell für den CPU-Rauchtest, kein echtes Training.

Ist janpow-ai nicht erreichbar, meldet ``choose_topology`` den Rechenort als
``unavailable``; es gibt kein stilles Ausweichen auf die NUC.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, replace
from typing import Any

#: Startmodell (Plan Abschnitt 1): MIT, feste Hugging-Face-Revision.
BASE_MODEL = "naver-clova-ix/donut-base"
BASE_MODEL_REVISION = "a959cf33c20e09215873e338299c900f57047c61"


@dataclass(frozen=True)
class TrainConfig:
    profile: str
    base_model: str = BASE_MODEL
    base_model_revision: str = BASE_MODEL_REVISION
    image_size: tuple[int, int] = (1280, 960)
    max_length: int = 512
    precision: str = "bf16"
    gradient_checkpointing: bool = True
    optimizer: str = "adamw"
    per_device_batch: int = 2
    grad_accum: int = 8
    learning_rate: float = 3e-5
    warmup_steps: int = 300
    scheduler: str = "cosine"
    epochs: int = 6
    max_steps: int | None = None
    seed: int = 42
    checkpoint_every_steps: int = 200
    checkpoint_every_minutes: float = 15.0
    save_total_limit: int = 3
    min_free_vram_gib: float = 6.5
    early_stopping_patience: int = 2
    distributed: str = "auto"
    max_grad_norm: float = 1.0

    def validate(self) -> None:
        if self.precision not in {"bf16", "fp32"}:
            raise ValueError("precision: bf16 oder fp32")
        if self.optimizer not in {"adamw", "adamw8bit"}:
            raise ValueError("optimizer: adamw oder adamw8bit")
        if self.distributed not in {"auto", "ddp", "parallel", "single"}:
            raise ValueError("distributed: auto, ddp, parallel oder single")
        for name in (
            "per_device_batch",
            "grad_accum",
            "epochs",
            "checkpoint_every_steps",
            "save_total_limit",
            "max_length",
        ):
            if getattr(self, name) < 1:
                raise ValueError(f"{name} muss ≥ 1 sein")
        if self.max_steps is not None and self.max_steps < 1:
            raise ValueError("max_steps muss ≥ 1 sein")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["image_size"] = list(self.image_size)
        return data

    @property
    def config_hash(self) -> str:
        """SHA-256 der Konfiguration; muss beim Wiederaufnehmen übereinstimmen."""
        payload = json.dumps(self.to_dict(), sort_keys=True).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def effective_batch(self, world_size: int = 1) -> int:
        return self.per_device_batch * self.grad_accum * world_size


PROFILES: dict[str, TrainConfig] = {
    "donut_train_janpow_ai": TrainConfig(
        profile="donut_train_janpow_ai",
        per_device_batch=4,
        grad_accum=2,
        optimizer="adamw",
        min_free_vram_gib=14.0,
        distributed="auto",
    ),
    "donut_train_8gb": TrainConfig(
        profile="donut_train_8gb",
        per_device_batch=1,
        grad_accum=16,
        optimizer="adamw8bit",
        min_free_vram_gib=6.5,
        distributed="single",
    ),
    "cpu_smoke": TrainConfig(
        profile="cpu_smoke",
        image_size=(64, 48),
        max_length=96,
        precision="fp32",
        gradient_checkpointing=False,
        per_device_batch=1,
        grad_accum=2,
        learning_rate=1e-3,
        warmup_steps=1,
        epochs=1,
        max_steps=6,
        checkpoint_every_steps=2,
        min_free_vram_gib=0.0,
        distributed="single",
    ),
}


@dataclass(frozen=True)
class GpuInfo:
    """Telemetrie einer Karte (FlowAgent-Spoke oder ``nvidia-smi``)."""

    index: int
    name: str
    memory_total_mib: int
    memory_free_mib: int
    host: str = "janpow-ai"


@dataclass(frozen=True)
class Topology:
    mode: str  # ddp | parallel | single | unavailable
    host: str
    gpus: tuple[int, ...]
    runs: tuple[dict[str, Any], ...]
    reason: str


def choose_topology(config: TrainConfig, gpus: list[GpuInfo]) -> Topology:
    """Rechenaufteilung aus der Telemetrie; nie stiller Rückfall auf einen anderen Rechner."""
    config.validate()
    usable = [g for g in gpus if g.memory_free_mib / 1024 >= config.min_free_vram_gib]
    host = gpus[0].host if gpus else "janpow-ai"
    if not usable:
        return Topology(
            "unavailable",
            host,
            (),
            (),
            "Rechenort nicht verfügbar (offline oder zu wenig freier VRAM); Rückfall auf die "
            "NUC nur ausdrücklich mit Profil donut_train_8gb",
        )
    base = {"profile": config.profile, "config_sha256": config.config_hash}
    if len(usable) == 1 or config.distributed == "single":
        gpu = usable[0]
        return Topology(
            "single", host, (gpu.index,), ({**base, "gpu": gpu.index},), "eine geeignete Karte"
        )
    first, second = usable[0], usable[1]
    same_class = first.name == second.name and first.memory_total_mib == second.memory_total_mib
    big = min(first.memory_total_mib, second.memory_total_mib) >= 16 * 1024
    if config.distributed in {"auto", "ddp"} and same_class and big:
        return Topology(
            "ddp",
            host,
            (first.index, second.index),
            ({**base, "nproc_per_node": 2, "gpus": [first.index, second.index]},),
            "gleiche Kartenklasse mit ≥ 16 GiB: DDP",
        )
    larger = replace(config, image_size=(1536, 1152), seed=config.seed + 1)
    return Topology(
        "parallel",
        host,
        (first.index, second.index),
        (
            {**base, "gpu": first.index, "config": config.to_dict()},
            {
                "profile": config.profile,
                "config_sha256": larger.config_hash,
                "gpu": second.index,
                "config": larger.to_dict(),
            },
        ),
        "ungleiche Karten: zwei unabhängige Läufe (1280×960 und 1536×1152), Auswahl per "
        "Bewertung (2d)",
    )
