"""Vorbereitetes Donut-Nachtraining (Plan 2c/2c-bis, Etappe E3).

Kern ohne schwere Abhängigkeiten: Profile ``donut_train_janpow_ai`` und
``donut_train_8gb``, Rechenort-/Topologiewahl aus GPU-Telemetrie, atomare
Checkpoints mit Prüfsummen, deterministische Wiederaufnahme, Laufprotokoll,
systemd-Vorlage und FlowAgent-Jobbeschreibung. Die Torch-Anbindung
(``torch_backend``) benötigt das Extra ``train``.
"""

from auditcore_invoicesynth.train.checkpoint import (
    Checkpoint,
    CheckpointManager,
    CheckpointPolicy,
    ResumeMismatch,
)
from auditcore_invoicesynth.train.loop import MockBackend, TrainBackend, TrainResult, run_training
from auditcore_invoicesynth.train.ops import (
    InsufficientVram,
    check_free_vram,
    flowagent_job,
    parse_nvidia_smi,
    render_systemd_unit,
)
from auditcore_invoicesynth.train.profiles import (
    PROFILES,
    GpuInfo,
    Topology,
    TrainConfig,
    choose_topology,
)

__all__ = [
    "PROFILES",
    "Checkpoint",
    "CheckpointManager",
    "CheckpointPolicy",
    "GpuInfo",
    "InsufficientVram",
    "MockBackend",
    "ResumeMismatch",
    "Topology",
    "TrainBackend",
    "TrainConfig",
    "TrainResult",
    "check_free_vram",
    "choose_topology",
    "flowagent_job",
    "parse_nvidia_smi",
    "render_systemd_unit",
    "run_training",
]
