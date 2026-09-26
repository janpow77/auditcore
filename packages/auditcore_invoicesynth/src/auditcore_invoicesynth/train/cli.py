"""Trainingswerkzeug: ``python -m auditcore_invoicesynth.train.cli`` (auch über ``torchrun``).

Beispiele::

    # Rechenort/Topologie und FlowAgent-Job aus Telemetrie planen
    python -m auditcore_invoicesynth.train.cli --profile donut_train_janpow_ai \\
        --dataset ds/ --plan --gpus-json gpus.json
    # CPU-Rauchtest mit winzigem Modell (kein echtes Training)
    python -m auditcore_invoicesynth.train.cli --profile cpu_smoke --dataset ds/ \\
        --run-dir runs/smoke --tiny
    # Training (setzt automatisch am neuesten gültigen Checkpoint fort)
    torchrun --nproc_per_node=2 -m auditcore_invoicesynth.train.cli \\
        --profile donut_train_janpow_ai --dataset ds/ --run-dir runs/r1 --base-model-dir base/
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

from auditcore_invoicesynth.dataset import DatasetError, load_split, verify_dataset
from auditcore_invoicesynth.train.checkpoint import ResumeMismatch
from auditcore_invoicesynth.train.loop import MockBackend, TrainBackend, run_training
from auditcore_invoicesynth.train.ops import (
    InsufficientVram,
    check_free_vram,
    flowagent_job,
    probe_local_gpus,
    render_systemd_unit,
)
from auditcore_invoicesynth.train.profiles import PROFILES, GpuInfo, TrainConfig, choose_topology


def run_id_for(dataset_hash: str, config_hash: str) -> str:
    """Stabile Lauf-ID: Neustart desselben Auftrags findet seine Checkpoints wieder."""
    return hashlib.sha256(f"{dataset_hash}:{config_hash}".encode()).hexdigest()[:16]


def _print(data: object) -> None:
    sys.stdout.write(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="auditcore-invoicesynth-train")
    parser.add_argument("--profile", required=True, choices=sorted(PROFILES))
    parser.add_argument("--dataset")
    parser.add_argument("--split", default="train")
    parser.add_argument("--run-dir")
    parser.add_argument("--run-id")
    parser.add_argument("--base-model-dir")
    parser.add_argument("--base-model-sha256")
    parser.add_argument("--tiny", action="store_true", help="winziges Modell (Rauchtest)")
    parser.add_argument("--backend", choices=("torch", "mock"), default="torch")
    parser.add_argument("--max-steps", type=int)
    parser.add_argument("--stop-after-step", type=int, help="Abbruch simulieren (Test)")
    parser.add_argument("--step-delay", type=float, default=0.0)
    parser.add_argument("--check-vram", action="store_true")
    parser.add_argument("--plan", action="store_true", help="Topologie + FlowAgent-Job")
    parser.add_argument("--gpus-json", help="Telemetrie [{index,name,memory_total_mib,...}]")
    parser.add_argument("--systemd-unit", action="store_true")
    parser.add_argument("--python", default=sys.executable)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    config = PROFILES[args.profile]
    if args.max_steps:
        config = replace(config, max_steps=args.max_steps)
    try:
        if args.check_vram:
            usable = check_free_vram(config)
            _print({"ok": True, "gpus": [g.__dict__ for g in usable]})
            return 0
        if args.systemd_unit:
            sys.stdout.write(_systemd_unit(args, config))
            return 0
        if not args.dataset:
            parser.error("--dataset erforderlich")
        dataset = Path(args.dataset)
        verification = verify_dataset(dataset)
        if not verification.ok:
            raise DatasetError("Datensatz weicht vom Manifest ab")
        run_id = args.run_id or run_id_for(verification.dataset_hash, config.config_hash)
        if args.plan:
            _print(_plan(args, config, dataset, verification.dataset_hash, run_id))
            return 0
        if not args.run_dir:
            parser.error("--run-dir erforderlich")
        _print(_train(parser, args, config, dataset, verification.dataset_hash, run_id))
        return 0
    except (DatasetError, ResumeMismatch, InsufficientVram, ValueError) as exc:
        sys.stderr.write(f"Fehler: {exc}\n")
        return 2


def _systemd_unit(args: argparse.Namespace, config: TrainConfig) -> str:
    return render_systemd_unit(
        config,
        python=args.python,
        dataset=args.dataset or "DATASET",
        run_dir=args.run_dir or "RUN_DIR",
        base_model_dir=args.base_model_dir or "BASE_MODEL_DIR",
        pause_units=("xtts.service",) if args.profile == "donut_train_8gb" else (),
    )


def _plan(
    args: argparse.Namespace, config: TrainConfig, dataset: Path, dataset_hash: str, run_id: str
) -> dict[str, Any]:
    """Topologie aus Telemetrie (Datei oder lokale Abfrage) und FlowAgent-Job."""
    if args.gpus_json:
        raw = json.loads(Path(args.gpus_json).read_text(encoding="utf-8"))
        gpus = [GpuInfo(**item) for item in raw]
    else:
        gpus = probe_local_gpus()
    topology = choose_topology(config, gpus)
    return flowagent_job(
        config,
        topology,
        dataset_hash=dataset_hash,
        dataset_uri=str(dataset.resolve()),
        run_id=run_id,
    )


def _train(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
    config: TrainConfig,
    dataset: Path,
    dataset_hash: str,
    run_id: str,
) -> dict[str, object]:
    run_dir = Path(args.run_dir)
    samples = len(load_split(dataset, args.split))
    backend = _backend(parser, args, config, dataset, run_dir)
    result = run_training(
        backend,
        config,
        samples=samples,
        run_dir=run_dir,
        run_id=run_id,
        dataset_hash=dataset_hash,
        stop_after_step=args.stop_after_step,
        step_delay=args.step_delay,
    )
    return {
        "run_id": run_id,
        "resumed_from": result.resumed_from,
        "final_step": result.final_step,
        "checkpoints": result.checkpoints,
        "losses": {str(k): v for k, v in result.losses.items()},
    }


def _backend(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
    config: TrainConfig,
    dataset: Path,
    run_dir: Path,
) -> TrainBackend:
    if args.backend == "mock":
        return MockBackend()
    check_free_vram(config)
    from auditcore_invoicesynth.train.torch_backend import TorchDonutBackend, build_tiny_base

    base = Path(args.base_model_dir) if args.base_model_dir else None
    if args.tiny:
        rank = os.environ.get("RANK", "0")
        base = build_tiny_base(run_dir / f"tiny-base-rank{rank}", config.image_size)
    if base is None:
        parser.error("--base-model-dir (lokales donut-base) oder --tiny erforderlich")
    return TorchDonutBackend(
        dataset, base, split=args.split, base_model_sha256=args.base_model_sha256
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
