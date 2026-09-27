"""Collect the local signals the scaling rules need. Every probe is failure-tolerant:
an unavailable source yields ``None`` (unknown) rather than an optimistic value."""

from __future__ import annotations

import http.client
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from .hardware import parse_meminfo
from .profile import ThermalSource
from .regeln import ThermalState

IDLE_REPLY = re.compile(r"uint64\s+(\d+)")
# Home directory of the user inside the official GitHub runner image: processes there are our runners.
RUNNER_HOME = "/home/runner"


def _run(command: list[str], timeout: float = 5.0) -> str | None:
    if shutil.which(command[0]) is None:
        return None
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout if result.returncode == 0 else None


def load_1m(path: Path = Path("/proc/loadavg")) -> float:
    return float(path.read_text(encoding="utf-8").split()[0])


def memory(path: Path = Path("/proc/meminfo")) -> tuple[int, int]:
    """(available MiB, swap used MiB)."""
    values = parse_meminfo(path.read_text(encoding="utf-8"))
    swap_used = values.get("SwapTotal", 0) - values.get("SwapFree", 0)
    return values.get("MemAvailable", 0), max(swap_used, 0)


def swap_in_pages(path: Path = Path("/proc/vmstat")) -> int:
    """Cumulative pages swapped in since boot (``pswpin``)."""
    for line in path.read_text(encoding="utf-8").splitlines():
        key, _, value = line.partition(" ")
        if key == "pswpin" and value.strip().isdigit():
            return int(value)
    return 0


def cpu_temperature(root: Path = Path("/sys/class/hwmon")) -> float | None:
    """Hottest CPU sensor (k10temp, coretemp, zenpower) in °C."""
    hottest: float | None = None
    for sensor in root.glob("hwmon*"):
        name = (sensor / "name").read_text(encoding="utf-8").strip() if (sensor / "name").exists() else ""
        if name not in {"k10temp", "coretemp", "zenpower"}:
            continue
        for reading in sensor.glob("temp*_input"):
            try:
                value = int(reading.read_text(encoding="utf-8")) / 1000
            except (OSError, ValueError):
                continue
            hottest = value if hottest is None else max(hottest, value)
    return hottest


def parse_idle_reply(text: str) -> float | None:
    match = IDLE_REPLY.search(text)
    return int(match.group(1)) / 1000 if match else None


def gnome_idle_seconds() -> float | None:
    reply = _run(
        [
            "gdbus",
            "call",
            "--session",
            "--dest",
            "org.gnome.Mutter.IdleMonitor",
            "--object-path",
            "/org/gnome/Mutter/IdleMonitor/Core",
            "--method",
            "org.gnome.Mutter.IdleMonitor.GetIdletime",
        ]
    )
    return parse_idle_reply(reply) if reply else None


def parse_loginctl(text: str, now: datetime) -> tuple[float | None, bool]:
    """(idle seconds, locked) from ``loginctl show-session -p IdleHint -p IdleSinceHint -p LockedHint``."""
    values = dict(line.split("=", 1) for line in text.splitlines() if "=" in line)
    locked = values.get("LockedHint") == "yes"
    if values.get("IdleHint") != "yes":
        return 0.0, locked
    since = values.get("IdleSinceHint", "0")
    if since.isdigit() and int(since) > 0:
        return max(now.timestamp() - int(since) / 1_000_000, 0.0), locked
    return None, locked


def seat_session() -> str | None:
    listing = _run(["loginctl", "list-sessions", "--no-legend"])
    for line in (listing or "").splitlines():
        columns = line.split()
        if len(columns) >= 4 and "seat0" in columns:
            return columns[0]
    return None


def activity() -> tuple[float | None, bool]:
    """Idle seconds and lock state: GNOME first, logind as fallback."""
    session = seat_session()
    locked = False
    idle_hint: float | None = None
    if session:
        text = _run(["loginctl", "show-session", session, "-p", "IdleHint", "-p", "IdleSinceHint", "-p", "LockedHint"])
        if text:
            idle_hint, locked = parse_loginctl(text, datetime.now())
    gnome = gnome_idle_seconds()
    return (gnome if gnome is not None else idle_hint), locked


def gamemode_active() -> bool:
    reply = _run(["gamemoded", "-s"])
    return bool(reply) and "is active" in (reply or "")


@dataclass(frozen=True)
class GpuUse:
    """Per card: free VRAM and whether the user (not a shared service, not our runner) is on it."""

    free_vram: dict[str, int]
    user_cards: frozenset[str]
    runner_cards: dict[str, int]


def classify_process(name: str, shared_services: tuple[str, ...]) -> str:
    """``runner`` (our containers), ``dienst`` (shared service) or ``nutzer`` (has priority)."""
    if name.startswith(RUNNER_HOME):
        return "runner"
    return "dienst" if any(pattern in name for pattern in shared_services) else "nutzer"


def parse_gpu_use(free_csv: str, apps_csv: str, shared_services: tuple[str, ...]) -> GpuUse:
    """``--query-gpu=uuid,memory.free`` and ``--query-compute-apps=gpu_uuid,process_name``."""
    free: dict[str, int] = {}
    for line in free_csv.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 2 and parts[1].replace(".", "", 1).isdigit():
            free[parts[0]] = int(float(parts[1]))
    user: set[str] = set()
    runners: dict[str, int] = {}
    for line in apps_csv.splitlines():
        parts = [p.strip() for p in line.split(",", 1)]
        if len(parts) != 2 or not parts[0]:
            continue
        kind = classify_process(parts[1], shared_services)
        if kind == "nutzer":
            user.add(parts[0])
        elif kind == "runner":
            runners[parts[0]] = runners.get(parts[0], 0) + 1
    return GpuUse(free, frozenset(user), runners)


def gpu_use(shared_services: tuple[str, ...]) -> GpuUse:
    free = _run(["nvidia-smi", "--query-gpu=uuid,memory.free", "--format=csv,noheader,nounits"], 10) or ""
    apps = _run(["nvidia-smi", "--query-compute-apps=gpu_uuid,process_name", "--format=csv,noheader"], 10) or ""
    return parse_gpu_use(free, apps, shared_services)


def _number(value: object) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def resolve(data: object, path: str) -> list[object]:
    """Values at a dotted path; ``name[*]`` expands lists (``gpus[*].temp``)."""
    values = [data]
    for part in path.split("."):
        expand = part.endswith("[*]")
        key = part.removesuffix("[*]")
        nxt: list[object] = []
        for value in values:
            child = value.get(key) if isinstance(value, dict) else None
            if expand and isinstance(child, list):
                nxt.extend(child)
            elif child is not None:
                nxt.append(child)
        values = nxt
    return values


def _truthy(value: object) -> bool:
    return value not in (None, False, 0, 0.0, "", "0", "false", "aus")


def parse_thermal(data: object, source: ThermalSource) -> ThermalState | None:
    """Map an arbitrary JSON status with the configured field paths."""
    if not isinstance(data, dict):
        return None
    temps = [t for path in source.temperature_paths for t in map(_number, resolve(data, path)) if t is not None]
    limits = [t for path in source.limit_paths for t in map(_number, resolve(data, path)) if t is not None]
    throttling = any(_truthy(v) for path in source.throttling_paths for v in resolve(data, path))
    mode = resolve(data, source.mode_path) if source.mode_path else []
    return ThermalState(
        throttling=throttling,
        hottest_c=max(temps, default=0.0),
        limit_c=min(limits, default=0.0),
        quiet=bool(source.quiet_value) and any(str(v) == source.quiet_value for v in mode),
    )


def thermal_state(source: ThermalSource) -> ThermalState | None:
    """Fault-tolerant: an unreachable or malformed source means "unknown"."""
    if not source.enabled:
        return None
    parts = urlsplit(source.url)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        return None
    kind = http.client.HTTPSConnection if parts.scheme == "https" else http.client.HTTPConnection
    connection = kind(parts.hostname, parts.port, timeout=2)
    try:
        target = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
        connection.request("GET", target)
        response = connection.getresponse()
        return parse_thermal(json.loads(response.read()), source) if response.status == 200 else None
    except (OSError, ValueError):
        return None
    finally:
        connection.close()
