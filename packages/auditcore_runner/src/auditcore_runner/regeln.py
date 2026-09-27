"""Pure scaling rules: signals + profile → target instances per class.

No I/O here. The built-in autoscaler (target source ``lokal``) and external
regulators apply exactly these functions, so a decision can
be reproduced and tested from recorded signals.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .profile import GPU_CLASSES, Profile, RunnerClass, Scaling


@dataclass(frozen=True)
class ThermalState:
    """Snapshot of the optional thermal/throttling source."""

    throttling: bool = False
    hottest_c: float = 0.0
    limit_c: float = 0.0
    quiet: bool = False


@dataclass(frozen=True)
class Signals:
    """Everything the rules look at; ``None`` means "unknown", never "zero"."""

    cpu_count: int
    load_1m: float
    memory_available_mb: int
    swap_used_mb: int
    swap_in_per_s: float | None = None
    temperature_c: float | None = None
    idle_seconds: float | None = None
    locked: bool = False
    gamemode: bool = False
    user_gpus: frozenset[str] = field(default_factory=frozenset)
    gpu_free_vram: dict[str, int] = field(default_factory=dict)
    user_priority: bool = False
    thermal: ThermalState | None = None
    queued: dict[str, int] = field(default_factory=dict)
    busy: dict[str, int] = field(default_factory=dict)
    hour: int = 12


@dataclass
class Decision:
    targets: dict[str, int] = field(default_factory=dict)
    reasons: dict[str, list[str]] = field(default_factory=dict)
    urgent: set[str] = field(default_factory=set)

    def cap(self, name: str, value: int, reason: str, urgent: bool = False) -> None:
        """Lower a target; urgent caps skip the hysteresis hold time."""
        if value < self.targets[name]:
            self.targets[name] = max(value, 0)
            self.reasons.setdefault(name, []).append(reason)
            if urgent:
                self.urgent.add(name)


def user_active(signals: Signals, scaling: Scaling) -> bool:
    """Active = recent input and not locked; unknown idle time counts as active.

    Only relevant when interactive use has priority (``vorrang_interaktiv``)."""
    if signals.locked:
        return False
    if signals.idle_seconds is None:
        return True
    return signals.idle_seconds < scaling.idle_minutes * 60


def in_full_power_window(hour: int, scaling: Scaling) -> bool:
    """Configured window without interactive caps; equal bounds mean "no window"."""
    start, end = scaling.full_power_from_hour, scaling.full_power_to_hour
    if start == end:
        return False
    return start <= hour < end if start < end else hour >= start or hour < end


def _demand(name: str, signals: Signals, scaling: Scaling, maximum: int) -> tuple[int, str]:
    """Queue-driven target: running jobs + waiting jobs + a small idle reserve."""
    if name not in signals.queued and name not in signals.busy:
        return maximum, "keine Warteschlangen-Daten: Maximum"
    wanted = signals.busy.get(name, 0) + signals.queued.get(name, 0) + scaling.spare_idle_runners
    return min(wanted, maximum), f"Bedarf {wanted} (belegt + wartend + Reserve)"


def _card_usable(card_index: int, uuid: str, need_mb: int, signals: Signals, profile: Profile, active: bool) -> bool:
    """Usable unless the user needs it (always wins) or VRAM is short; cards are shared by VRAM."""
    if signals.user_priority or uuid in signals.user_gpus:
        return False
    scaling = profile.scaling
    if scaling.interactive_priority and card_index in scaling.interactive_cards:
        idle = signals.idle_seconds
        if signals.gamemode or active or idle is None or idle < scaling.interactive_card_idle_minutes * 60:
            return False
    free = signals.gpu_free_vram.get(uuid)
    return free is None or free >= need_mb


def _gpu_free(profile: Profile, name: str, signals: Signals, active: bool) -> int:
    need = profile.classes[name].vram_mb
    return sum(
        1 for card in profile.gpus_of(name) if _card_usable(card.index, card.uuid, need, signals, profile, active)
    )


def _memory_caps(decision: Decision, name: str, signals: Signals, scaling: Scaling) -> None:
    """Memory pressure = active swapping in or little free RAM; idle swapped pages do not count."""
    busy = signals.busy.get(name, 0)
    if signals.swap_in_per_s is not None and signals.swap_in_per_s > scaling.swap_in_max_per_s:
        decision.cap(name, busy, f"Swap-Einlagerung {signals.swap_in_per_s:.0f} Seiten/s", True)
    if signals.memory_available_mb < scaling.min_free_memory_gb * 1024:
        decision.cap(name, busy, f"nur {signals.memory_available_mb // 1024} GB RAM frei", True)
    if scaling.swap_lock_gb and signals.swap_used_mb >= scaling.swap_lock_gb * 1024:
        decision.cap(name, busy, f"Swap {signals.swap_used_mb // 1024} GB ≥ Sperre", True)


def _pressure_caps(decision: Decision, name: str, signals: Signals, scaling: Scaling) -> None:
    busy = signals.busy.get(name, 0)
    _memory_caps(decision, name, signals, scaling)
    if signals.cpu_count and signals.load_1m / signals.cpu_count > scaling.load_per_core_max:
        decision.cap(name, busy, f"Last je Kern {signals.load_1m / signals.cpu_count:.2f} zu hoch", True)
    temperature = signals.temperature_c
    if temperature is not None and temperature >= scaling.temperature_max_c:
        decision.cap(name, busy, f"Temperatur {temperature:.0f} °C ≥ Grenze", True)


def _thermal_caps(decision: Decision, name: str, settings: RunnerClass, signals: Signals, scaling: Scaling) -> None:
    thermal = signals.thermal
    if thermal is None or not scaling.thermal.enabled:
        return
    busy = signals.busy.get(name, 0)
    near = thermal.limit_c and thermal.hottest_c >= thermal.limit_c - scaling.thermal.margin_c
    if thermal.throttling or near:
        decision.cap(name, busy, "Thermik: Drosselung oder Temperatur nahe der Grenze", True)
    if thermal.quiet:
        decision.cap(name, settings.cap_quiet(), "Thermik-Quelle im Leise-Modus", True)


def _activity_caps(decision: Decision, name: str, signals: Signals, profile: Profile) -> None:
    scaling = profile.scaling
    active = scaling.interactive_priority and user_active(signals, scaling)
    if name in GPU_CLASSES:
        decision.cap(name, _gpu_free(profile, name, signals, active), "freie Karten (Nutzer-Vorrang, VRAM)", True)
        return
    if not scaling.interactive_priority or in_full_power_window(signals.hour, scaling):
        return
    if signals.gamemode:
        decision.cap(name, min(1, profile.classes[name].max_instances), "Spielmodus aktiv", True)
    elif active:
        share = math.floor(profile.classes[name].max_instances * scaling.share_while_active)
        decision.cap(name, max(1, share), "interaktive Nutzung hat Vorrang")


def _floor(decision: Decision, profile: Profile, name: str) -> int:
    settings, priority = profile.classes[name], profile.priority_of(name)
    return max(settings.min_instances, priority.minimum if priority else 0)


def _apply_priorities(decision: Decision, profile: Profile, signals: Signals) -> None:
    """Scarce capacity: lower preemptible classes (highest rank number first) down to their minimum."""
    budget = signals.cpu_count - profile.reserve_cpus
    ranked = sorted(
        (p for p in profile.priorities if p.name in profile.classes and p.preemptible),
        key=lambda p: -p.rank,
    )

    def demand() -> int:
        return sum(profile.classes[n].cpus * t for n, t in decision.targets.items() if profile.classes[n].enabled)

    for priority in ranked:
        name = priority.name
        while demand() > budget and decision.targets[name] > max(
            _floor(decision, profile, name), signals.busy.get(name, 0)
        ):
            decision.targets[name] -= 1
            if f"Vorrang anderer Klassen (Rang {priority.rank})" not in decision.reasons[name]:
                decision.reasons[name].append(f"Vorrang anderer Klassen (Rang {priority.rank})")


def decide(profile: Profile, signals: Signals) -> Decision:
    """Target per enabled class; disabled classes get 0."""
    decision = Decision()
    for name, settings in sorted(profile.classes.items()):
        if not settings.enabled:
            decision.targets[name] = 0
            decision.reasons[name] = ["Klasse ausgeschaltet"]
            continue
        target, why = _demand(name, signals, profile.scaling, settings.max_instances)
        decision.targets[name] = target
        decision.reasons[name] = [why]
        _activity_caps(decision, name, signals, profile)
        _pressure_caps(decision, name, signals, profile.scaling)
        _thermal_caps(decision, name, settings, signals, profile.scaling)
        floor = _floor(decision, profile, name)
        if name not in decision.urgent and decision.targets[name] < floor:
            decision.targets[name] = floor
            decision.reasons[name].append(f"Mindestzahl {floor}")
    _apply_priorities(decision, profile, signals)
    return decision


def smooth(
    previous: dict[str, int],
    proposed: dict[str, int],
    held_since: dict[str, float],
    now: float,
    hold_seconds: int,
    urgent: frozenset[str] = frozenset(),
) -> dict[str, int]:
    """Hysteresis: raise at once, lower only after the lower value held long enough.

    ``held_since`` records per class since when the proposal has been below the
    previous target; it is updated in place.
    """
    result: dict[str, int] = {}
    for name, value in proposed.items():
        before = previous.get(name, value)
        if value >= before or name in urgent:
            held_since.pop(name, None)
            result[name] = value
            continue
        since = held_since.setdefault(name, now)
        result[name] = value if now - since >= hold_seconds else before
    return result
