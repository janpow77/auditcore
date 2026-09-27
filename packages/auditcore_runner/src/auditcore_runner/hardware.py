"""Detect the host resources a runner profile is sized against."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

NVIDIA_QUERY = "index,uuid,name,memory.total"


@dataclass(frozen=True)
class Gpu:
    """One NVIDIA card as reported by nvidia-smi."""

    index: int
    uuid: str
    name: str
    vram_mb: int


@dataclass(frozen=True)
class HostFacts:
    """CPU, memory and GPU facts of one machine."""

    hostname: str
    cpu_count: int
    memory_mb: int
    swap_total_mb: int
    swap_used_mb: int
    gpus: tuple[Gpu, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, object]:
        """JSON-ready representation (German keys like the profile file)."""
        return {
            "rechner": self.hostname,
            "kerne": self.cpu_count,
            "speicher_mb": self.memory_mb,
            "swap_mb": self.swap_total_mb,
            "swap_belegt_mb": self.swap_used_mb,
            "gpus": [{"index": g.index, "uuid": g.uuid, "name": g.name, "vram_mb": g.vram_mb} for g in self.gpus],
        }


def parse_meminfo(text: str) -> dict[str, int]:
    """Values of /proc/meminfo in MiB."""
    values: dict[str, int] = {}
    for line in text.splitlines():
        key, _, rest = line.partition(":")
        parts = rest.split()
        if parts and parts[0].isdigit():
            values[key.strip()] = int(parts[0]) // 1024
    return values


def parse_nvidia_csv(text: str) -> tuple[Gpu, ...]:
    """Cards from ``nvidia-smi --query-gpu=index,uuid,name,memory.total`` (csv, noheader, nounits)."""
    cards: list[Gpu] = []
    for line in text.splitlines():
        columns = [c.strip() for c in line.split(",")]
        if len(columns) != 4 or not columns[0].isdigit():
            continue
        cards.append(Gpu(int(columns[0]), columns[1], columns[2], int(float(columns[3]))))
    return tuple(cards)


def query_gpus() -> tuple[Gpu, ...]:
    """Ask nvidia-smi; no driver or no card means no GPUs."""
    if shutil.which("nvidia-smi") is None:
        return ()
    command = ["nvidia-smi", f"--query-gpu={NVIDIA_QUERY}", "--format=csv,noheader,nounits"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return ()
    return parse_nvidia_csv(result.stdout) if result.returncode == 0 else ()


def detect(meminfo: Path = Path("/proc/meminfo")) -> HostFacts:
    """Measure this machine."""
    memory = parse_meminfo(meminfo.read_text(encoding="utf-8"))
    swap_total = memory.get("SwapTotal", 0)
    return HostFacts(
        hostname=socket.gethostname().split(".")[0],
        cpu_count=os.cpu_count() or 1,
        memory_mb=memory.get("MemTotal", 0),
        swap_total_mb=swap_total,
        swap_used_mb=swap_total - memory.get("SwapFree", swap_total),
        gpus=query_gpus(),
    )
