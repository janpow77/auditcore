"""Betrieb: VRAM-Startprüfung, systemd-Vorlage und FlowAgent-Jobbeschreibung.

Der FlowAgent ist der einzige GPU-Weg (Grundsatz vom 28.08.2026, Plan 2c-bis):
Der Job wird an den Spoke ``janpow-ai`` mit der Fähigkeit ``train:donut``
adressiert. Ist janpow-ai offline, bleibt der Job wartend – ein Rückfall auf die
NUC ist eine ausdrückliche Wahl (Profil ``donut_train_8gb``), kein Automatismus.
"""

from __future__ import annotations

import shlex
import subprocess  # nosec B404 - nur fest verdrahteter nvidia-smi-Aufruf ohne Shell
import time
from collections.abc import Callable, Mapping
from typing import Any

from auditcore_invoicesynth.train.profiles import PROFILES, GpuInfo, Topology, TrainConfig

TRAIN_IMAGE = "ghcr.io/janpow77/auditcore-donut-train:cu128"
NVIDIA_SMI = [
    "nvidia-smi",
    "--query-gpu=index,name,memory.total,memory.free",
    "--format=csv,noheader,nounits",
]


NVIDIA_SMI_TEMPERATURE = [
    "nvidia-smi",
    "--query-gpu=temperature.gpu",
    "--format=csv,noheader,nounits",
]
#: Felder, die ein Lauf gegenüber seinem Profil per Kommandozeile überschreiben darf.
OVERRIDABLE = ("image_size", "seed", "epochs", "per_device_batch", "grad_accum", "max_steps")


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


class GpuTemperature:
    """Temperatur der ersten sichtbaren Karte, höchstens alle ``interval_s`` abgefragt."""

    def __init__(
        self,
        interval_s: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
        query: Callable[[], str | None] | None = None,
    ) -> None:
        self.interval_s = interval_s
        self.clock = clock
        self.query = query or _query_temperature
        self.last: float | None = None
        self.checked: float | None = None

    def __call__(self) -> float | None:
        now = self.clock()
        if self.checked is None or now - self.checked >= self.interval_s:
            self.checked = now
            output = self.query()
            try:
                self.last = float(output.strip().splitlines()[0]) if output else None
            except (ValueError, IndexError):
                self.last = None
        return self.last


def _query_temperature() -> str | None:
    try:
        completed = subprocess.run(  # nosec B603 - feste Argumente, keine Shell
            NVIDIA_SMI_TEMPERATURE, capture_output=True, text=True, timeout=10, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return completed.stdout if completed.returncode == 0 else None


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


def override_args(config: TrainConfig) -> list[str]:
    """Kommandozeilen-Schalter für Abweichungen des Laufs von seinem Profil."""
    base = PROFILES.get(config.profile)
    args: list[str] = []
    for name in OVERRIDABLE:
        value = getattr(config, name)
        if base is not None and getattr(base, name) == value or value is None:
            continue
        flag = "--" + name.replace("_", "-")
        args += [flag, "x".join(map(str, value)) if name == "image_size" else str(value)]
    return args


def train_command(
    config: TrainConfig,
    *,
    dataset: str,
    run_dir: str,
    base_model_dir: str,
    nproc: int = 1,
    base_model_sha256: str | None = None,
) -> list[str]:
    """Aufruf des Trainingswerkzeugs (bei DDP über ``torchrun``) mit Profil-Abweichungen."""
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
        *override_args(config),
    ]
    if base_model_sha256:
        args += ["--base-model-sha256", base_model_sha256]
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


def _run_config(config: TrainConfig, run: Mapping[str, object]) -> TrainConfig:
    data = run.get("config")
    if not isinstance(data, dict) or not data:
        return config
    return TrainConfig(**{**data, "image_size": tuple(data["image_size"])})


def _job_runs(
    config: TrainConfig,
    topology: Topology,
    *,
    run_id: str,
    dataset_dir: str,
    run_root: str,
    base_model_dir: str,
    base_model_sha256: str | None,
) -> list[dict[str, object]]:
    runs = []
    for number, run in enumerate(topology.runs or ({},)):
        run_config = _run_config(config, run)
        suffix = f"-{number}" if len(topology.runs) > 1 else ""
        run_dir = f"{run_root}/{run_id}{suffix}"
        runs.append(
            {
                "gpus": run.get("gpus", [run["gpu"]] if "gpu" in run else []),
                "config": run_config.to_dict(),
                "config_sha256": run_config.config_hash,
                "command": train_command(
                    run_config,
                    dataset=dataset_dir,
                    run_dir=run_dir,
                    base_model_dir=base_model_dir,
                    nproc=int(run.get("nproc_per_node", 1)),
                    base_model_sha256=base_model_sha256,
                ),
                "run_dir": run_dir,
                "progress": f"{run_dir}/progress.json",
            }
        )
    return runs


def flowagent_job(
    config: TrainConfig,
    topology: Topology,
    *,
    dataset_hash: str,
    dataset_uri: str,
    run_id: str,
    checkpoint_dir: str = "/srv/auditcore/donut/runs",
    base_model_dir: str = "/srv/auditcore/donut/base/donut-base",
    base_model_sha256: str | None = None,
    host_mounts: dict[str, str] | None = None,
    mirror: str | None = "nuc:/home/janpow/donut/checkpoints-mirror",
    image: str = TRAIN_IMAGE,
) -> dict[str, Any]:
    """FlowAgent-Job (``agent.flowaudit.de``); ``host_mounts``: dataset/base_model/runs."""
    dataset_dir = f"/data/{dataset_hash}"
    runs = _job_runs(
        config,
        topology,
        run_id=run_id,
        dataset_dir=dataset_dir,
        run_root=checkpoint_dir,
        base_model_dir=base_model_dir,
        base_model_sha256=base_model_sha256,
    )
    return {
        "kind": "train:donut",
        "schema": "auditcore-invoicesynth/flowagent-job/2",
        "run_id": run_id,
        "target": {"spoke": topology.host, "capabilities": ["train:donut", "gpu"]},
        "fallback": None,
        "fallback_note": "Rückfall auf die NUC nur ausdrücklich (Profil donut_train_8gb)",
        "status": "READY" if topology.mode != "unavailable" else "WAITING_FOR_COMPUTE",
        "topology": {"mode": topology.mode, "gpus": list(topology.gpus), "reason": topology.reason},
        "image": image,
        "container": _container(
            host_mounts or {},
            dataset_uri=dataset_uri,
            dataset_dir=dataset_dir,
            base_model_dir=base_model_dir,
            checkpoint_dir=checkpoint_dir,
        ),
        "dataset": {
            "sha256": dataset_hash,
            "uri": dataset_uri,
            "verify": "auditcore-invoicesynth verify",
        },
        "base_model": {
            "id": config.base_model,
            "revision": config.base_model_revision,
            "dir": base_model_dir,
            "sha256": base_model_sha256,
            "offline": True,
        },
        "runs": runs,
        "exit_codes": EXIT_CODES,
        "checkpoint_mirror": mirror,
        **_JOB_STATIC,
    }


_JOB_STATIC: dict[str, object] = {
    "resume": "auto (neuester gültiger Checkpoint, gleiche Lauf-ID)",
    "progress_file": "<run_dir>/progress.json (atomar, Herzschlag in Lade-/Checkpoint-Phasen)",
    "telemetry": ["step", "loss", "vram_peak_gib", "temperature_c"],
    "environment": {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"},
}


def _container(
    hosts: Mapping[str, str],
    *,
    dataset_uri: str,
    dataset_dir: str,
    base_model_dir: str,
    checkpoint_dir: str,
) -> dict[str, object]:
    """Container-Vorgaben je Lauf: Nutzer, Stopp-Frist, Einhängepunkte (Host → Container)."""
    return {
        "user": "1000:1000",
        "ipc": "host",
        "stop_signal": "SIGTERM",
        "stop_timeout_s": 120,
        "mounts": [
            {"host": hosts.get("dataset", dataset_uri), "container": dataset_dir, "mode": "ro"},
            {"host": hosts.get("base_model"), "container": base_model_dir, "mode": "ro"},
            {"host": hosts.get("runs"), "container": checkpoint_dir, "mode": "rw"},
        ],
    }


#: Exit-Codes des Trainingswerkzeugs (für Neustart-Entscheidungen des Runners).
EXIT_CODES = {
    "0": "fertig oder nach SIGTERM mit Checkpoint beendet (zustand in progress.json)",
    "1": "unerwarteter Fehler (fehler in progress.json)",
    "2": "Aufruf-, Datensatz-, Wiederaufnahme- oder VRAM-Startprüfung gescheitert",
    "3": "Loss NaN/Inf – letzter guter Stand gesichert, nicht automatisch neu starten",
    "4": "CUDA-Speicher erschöpft – letzter guter Stand gesichert, Batch verkleinern",
    "5": "Stopp-Frist (90 s) nach SIGTERM überschritten",
    "6": "zu viele unlesbare Beispiele",
}
