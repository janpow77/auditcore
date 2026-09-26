"""Betrieb: VRAM-Startprüfung, systemd-Vorlage und FlowAgent-Jobbeschreibung.

Der FlowAgent ist der einzige GPU-Weg (Grundsatz vom 28.08.2026, Plan 2c-bis):
Der Job wird an den Spoke ``janpow-ai`` mit der Fähigkeit ``train:donut``
adressiert. Ist janpow-ai offline, bleibt der Job wartend – ein Rückfall auf die
NUC ist eine ausdrückliche Wahl (Profil ``donut_train_8gb``), kein Automatismus.
"""

from __future__ import annotations

import shlex
import subprocess  # nosec B404 - nur fest verdrahteter nvidia-smi-Aufruf ohne Shell
from collections.abc import Callable
from typing import Any

from auditcore_invoicesynth.train.profiles import GpuInfo, Topology, TrainConfig

TRAIN_IMAGE = "ghcr.io/janpow77/auditcore-donut-train:cu128"
NVIDIA_SMI = [
    "nvidia-smi",
    "--query-gpu=index,name,memory.total,memory.free",
    "--format=csv,noheader,nounits",
]


class InsufficientVram(RuntimeError):
    """Trainingsstart verweigert: zu wenig freier Grafikspeicher (kein OOM mitten im Lauf)."""


def parse_nvidia_smi(output: str, host: str = "localhost") -> list[GpuInfo]:
    gpus = []
    for line in output.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 4:
            continue
        gpus.append(GpuInfo(int(parts[0]), parts[1], int(parts[2]), int(parts[3]), host))
    return gpus


def probe_local_gpus(host: str = "localhost") -> list[GpuInfo]:
    """Lokale Telemetrie über ``nvidia-smi``; ohne Treiber leere Liste."""
    try:
        completed = subprocess.run(  # nosec B603 - feste Argumente, keine Shell
            NVIDIA_SMI, capture_output=True, text=True, timeout=20, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return []
    return parse_nvidia_smi(completed.stdout, host) if completed.returncode == 0 else []


def check_free_vram(
    config: TrainConfig, probe: Callable[[], list[GpuInfo]] = probe_local_gpus
) -> list[GpuInfo]:
    """Karten mit mindestens ``min_free_vram_gib`` frei; sonst ``InsufficientVram``."""
    if config.min_free_vram_gib <= 0:
        return []
    gpus = probe()
    usable = [g for g in gpus if g.memory_free_mib / 1024 >= config.min_free_vram_gib]
    if not usable:
        free = ", ".join(f"GPU {g.index}: {g.memory_free_mib / 1024:.1f} GiB" for g in gpus)
        raise InsufficientVram(
            f"Weniger als {config.min_free_vram_gib} GiB frei ({free or 'keine GPU'}); "
            "andere GPU-Dienste (z. B. xtts) vorher pausieren"
        )
    return usable


def train_command(
    config: TrainConfig, *, dataset: str, run_dir: str, base_model_dir: str, nproc: int = 1
) -> list[str]:
    """Aufruf des Trainingswerkzeugs (bei DDP über ``torchrun``)."""
    args = [
        "-m",
        "auditcore_invoicesynth.train.cli",
        "--profile",
        config.profile,
        "--dataset",
        dataset,
        "--run-dir",
        run_dir,
        "--base-model-dir",
        base_model_dir,
    ]
    if nproc > 1:
        return ["torchrun", f"--nproc_per_node={nproc}", *args]
    return ["python", *args]


def render_systemd_unit(
    config: TrainConfig,
    *,
    python: str,
    dataset: str,
    run_dir: str,
    base_model_dir: str,
    pause_units: tuple[str, ...] = (),
) -> str:
    """``systemd --user``-Dienst ``auditcore-donut-train.service`` mit Wiederaufnahme.

    ``Restart=on-failure`` nimmt nach Absturz/Neustart am neuesten gültigen
    Checkpoint wieder auf (gleiche Lauf-ID/Konfiguration im Laufverzeichnis).
    ``pause_units`` (z. B. xtts auf der NUC, Entscheidung E7) werden vorher gestoppt.
    """
    command = train_command(config, dataset=dataset, run_dir=run_dir, base_model_dir=base_model_dir)
    command[0] = python
    pre = "".join(f"ExecStartPre=-/usr/bin/systemctl --user stop {unit}\n" for unit in pause_units)
    post = "".join(
        f"ExecStopPost=-/usr/bin/systemctl --user start {unit}\n" for unit in pause_units
    )
    check = shlex.join(
        [
            python,
            "-m",
            "auditcore_invoicesynth.train.cli",
            "--profile",
            config.profile,
            "--check-vram",
        ]
    )
    return (
        "[Unit]\n"
        "Description=auditcore Donut-Nachtraining (Profil "
        f"{config.profile}, wiederaufnehmbar)\n"
        "After=network-online.target\n"
        "StartLimitIntervalSec=0\n\n"
        "[Service]\n"
        "Type=simple\n"
        "Environment=PYTHONUNBUFFERED=1\n"
        "Environment=HF_HUB_OFFLINE=1\n"
        "Environment=TRANSFORMERS_OFFLINE=1\n"
        f"{pre}"
        f"ExecStartPre={check}\n"
        f"ExecStart={shlex.join(command)}\n"
        f"{post}"
        "Restart=on-failure\n"
        "RestartSec=120\n"
        "TimeoutStopSec=300\n"
        "KillSignal=SIGINT\n\n"
        "[Install]\n"
        "WantedBy=default.target\n"
    )


def flowagent_job(
    config: TrainConfig,
    topology: Topology,
    *,
    dataset_hash: str,
    dataset_uri: str,
    run_id: str,
    checkpoint_dir: str = "/srv/auditcore/donut/runs",
    base_model_dir: str = "/srv/auditcore/donut/base/donut-base",
    mirror: str | None = "nuc:/srv/auditcore/donut/runs",
    image: str = TRAIN_IMAGE,
) -> dict[str, Any]:
    """Jobbeschreibung für die Flow-Agent Control Plane (``agent.flowaudit.de``)."""
    runs = []
    for number, run in enumerate(topology.runs or ({},)):
        run_config = run.get("config") or config.to_dict()
        run_dir = f"{checkpoint_dir}/{run_id}" + (f"-{number}" if len(topology.runs) > 1 else "")
        nproc = int(run.get("nproc_per_node", 1))
        runs.append(
            {
                "gpus": run.get("gpus", [run["gpu"]] if "gpu" in run else []),
                "config": run_config,
                "config_sha256": run.get("config_sha256", config.config_hash),
                "command": train_command(
                    config,
                    dataset=f"/data/{dataset_hash}",
                    run_dir=run_dir,
                    base_model_dir=base_model_dir,
                    nproc=nproc,
                ),
                "run_dir": run_dir,
            }
        )
    return {
        "kind": "train:donut",
        "schema": "auditcore-invoicesynth/flowagent-job/1",
        "run_id": run_id,
        "target": {"spoke": topology.host, "capabilities": ["train:donut", "gpu"]},
        "fallback": None,
        "fallback_note": "Rückfall auf die NUC nur ausdrücklich (Profil donut_train_8gb)",
        "status": "READY" if topology.mode != "unavailable" else "WAITING_FOR_COMPUTE",
        "topology": {"mode": topology.mode, "gpus": list(topology.gpus), "reason": topology.reason},
        "image": image,
        "dataset": {
            "sha256": dataset_hash,
            "uri": dataset_uri,
            "verify": "auditcore-invoicesynth verify",
        },
        "base_model": {
            "id": config.base_model,
            "revision": config.base_model_revision,
            "dir": base_model_dir,
            "offline": True,
        },
        "runs": runs,
        "resume": "auto (neuester gültiger Checkpoint, gleiche Lauf-ID)",
        "checkpoint_mirror": mirror,
        "telemetry": ["step", "loss", "vram_peak_gib", "temperature_c"],
        "environment": {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"},
    }
