"""Dynamic GPU assignment: a GPU runner takes whichever allowed card is free when a job starts.

Cards are shared by VRAM with configured services (``gpu_dienste_teilen``); the
user always has priority – a card with a user process, a card blocked by the
regulator, or a global ``nutzer_vorrang`` is never given out, and a running
job on such a card is evicted.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

from . import pool, signals
from .profile import Profile


@dataclass(frozen=True)
class CardState:
    use: signals.GpuUse
    reserved: dict[str, int]
    blocked: frozenset[str]
    user_priority: bool
    user_idle_seconds: float | None


def our_containers() -> dict[str, int]:
    """Running runner containers per card UUID (label set by the supervisor)."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "label=auditcore-runner.gpu", "--format", '{{.Label "auditcore-runner.gpu"}}'],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {}
    counts: dict[str, int] = {}
    for uuid in result.stdout.split():
        counts[uuid] = counts.get(uuid, 0) + 1
    return counts


def observe(profile: Profile) -> CardState:
    external = pool.load(profile.pool_path())
    idle, locked = signals.activity()
    return CardState(
        use=signals.gpu_use(profile.scaling.gpu_shared_services),
        reserved=our_containers(),
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
