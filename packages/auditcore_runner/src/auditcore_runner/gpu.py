"""Dynamic GPU assignment: a GPU runner takes whichever allowed card is free when a job starts.

Cards are shared by VRAM with configured services (``gpu_dienste_teilen``); the
user always has priority – a card with a user process, a card blocked by the
regulator, or a global ``nutzer_vorrang`` is never given out, and a running
job on such a card is evicted.

Choosing and starting are two steps: ``gpu waehlen --platz <klasse-n>`` records
a reservation (under the supervisor's lock) that counts like a running
container until the container carries the slot label or the reservation is
released or older than :data:`RESERVATION_SECONDS`. Access inside the
container uses CDI (``--device nvidia.com/gpu=<UUID>``).
"""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from . import pool, signals
from .profile import Profile, state_dir
from .profile_io import write_atomic

RESERVATION_SECONDS = 600
SLOT_LABEL = "auditcore-runner.platz"
GPU_LABEL = "auditcore-runner.gpu"


@dataclass(frozen=True)
class CardState:
    use: signals.GpuUse
    reserved: dict[str, int]
    blocked: frozenset[str]
    user_priority: bool
    user_idle_seconds: float | None


def reservation_dir() -> Path:
    return state_dir() / "gpu-reservierungen"


def reserve(slot: str, uuid: str, now: float | None = None) -> None:
    record = {"uuid": uuid, "zeit": now if now is not None else time.time()}
    write_atomic(reservation_dir() / f"{slot}.json", json.dumps(record) + "\n", 0o600)


def release(slot: str) -> None:
    (reservation_dir() / f"{slot}.json").unlink(missing_ok=True)


def reservations(now: float | None = None) -> dict[str, str]:
    """Slot → card of fresh reservations."""
    moment = now if now is not None else time.time()
    found: dict[str, str] = {}
    for path in sorted(reservation_dir().glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(record, dict) and moment - float(record.get("zeit", 0)) <= RESERVATION_SECONDS:
            found[path.stem] = str(record.get("uuid", ""))
    return found


def our_containers() -> dict[str, str]:
    """Running runner containers: slot (or container id) → card UUID, from the supervisor's labels."""
    template = f'{{{{.ID}}}} {{{{.Label "{GPU_LABEL}"}}}} {{{{.Label "{SLOT_LABEL}"}}}}'
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"label={GPU_LABEL}", "--format", template],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {}
    found: dict[str, str] = {}
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            found[parts[2] if len(parts) > 2 else parts[0]] = parts[1]
    return found


def reserved_per_card(containers: dict[str, str], reserved: dict[str, str]) -> dict[str, int]:
    """Consumers per card; a slot counts once whether it is reserved, running or both."""
    counts: dict[str, int] = {}
    for uuid in {**reserved, **containers}.values():
        counts[uuid] = counts.get(uuid, 0) + 1
    return counts


def observe(profile: Profile) -> CardState:
    external = pool.load(profile.pool_path())
    idle, locked = signals.activity()
    return CardState(
        use=signals.gpu_use(profile.scaling.gpu_shared_services),
        reserved=reserved_per_card(our_containers(), reservations()),
        blocked=frozenset(external.blocked_cards) if external else frozenset(),
        user_priority=bool(external and external.user_priority),
        user_idle_seconds=None if idle is None and not locked else (float("inf") if locked else idle),
    )


def must_evict(uuid: str, state: CardState) -> bool:
    """True when the user needs this card now."""
    return state.user_priority or uuid in state.blocked or uuid in state.use.user_cards


def choose(profile: Profile, runner_class: str, state: CardState) -> str | None:
    """The allowed card with the most free VRAM after our own reservations, or None."""
    need = profile.classes[runner_class].vram_mb
    best: tuple[int, str] | None = None
    for card in profile.gpus_of(runner_class):
        if must_evict(card.uuid, state):
            continue
        idle, scaling = state.user_idle_seconds, profile.scaling
        interactive = scaling.interactive_priority and card.index in scaling.interactive_cards
        if interactive and (idle is None or idle < scaling.interactive_card_idle_minutes * 60):
            continue
        free = state.use.free_vram.get(card.uuid, card.vram_mb) - state.reserved.get(card.uuid, 0) * need
        if free >= need and (best is None or free > best[0]):
            best = (free, card.uuid)
    return best[1] if best else None
