"""Built-in autoscaler for target source ``lokal``: signals → rules → pool file."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime

from . import github, nachfrage, pool, signals
from .hardware import detect
from .profile import Profile
from .regeln import Decision, Signals, decide, smooth


def queue_and_busy(profile: Profile, client: github.Client | None) -> tuple[dict[str, int], dict[str, int]]:
    """Waiting and running jobs per class: from the scale set listener if it is fresh, else from the REST API."""
    demand = nachfrage.load() if profile.backend == "scaleset" else None
    if demand is not None and demand.fresh():
        queued = {name: entry.waiting for name, entry in demand.classes.items()}
        busy = {name: entry.statistics.get("laufend", 0) for name, entry in demand.classes.items()}
        return queued, busy
    if client is None:
        return {}, {}
    try:
        runners = github.list_runners(client, profile.target)
        return github.queued_by_class(client, profile), github.busy_by_class(runners, profile, profile.runner_prefix())
    except github.GitHubError:
        return {}, {}


def collect(profile: Profile, client: github.Client | None, swap_in_per_s: float | None = None) -> Signals:
    """Measure everything the rules use; GitHub data is optional."""
    facts = detect()
    available, swap_used = signals.memory()
    idle, locked = signals.activity()
    cards = signals.gpu_use(profile.scaling.gpu_shared_services)
    external = pool.load(profile.pool_path()) if profile.source.kind == "datei" else None
    queued, busy = queue_and_busy(profile, client)
    return Signals(
        cpu_count=facts.cpu_count,
        load_1m=signals.load_1m(),
        memory_available_mb=available,
        swap_used_mb=swap_used,
        swap_in_per_s=swap_in_per_s,
        temperature_c=signals.cpu_temperature(),
        idle_seconds=idle,
        locked=locked,
        gamemode=signals.gamemode_active(),
        user_gpus=cards.user_cards | frozenset(external.blocked_cards if external else ()),
        gpu_free_vram=cards.free_vram,
        user_priority=bool(external and external.user_priority),
        thermal=signals.thermal_state(profile.scaling.thermal),
        queued=queued,
        busy=busy,
        hour=datetime.now().hour,
    )


@dataclass
class Regulator:
    """Keeps hysteresis state between rounds."""

    profile: Profile
    client: github.Client | None = None
    previous: dict[str, int] = field(default_factory=dict)
    held_since: dict[str, float] = field(default_factory=dict)

    def round(self, measured: Signals, now: float) -> Decision:
        decision = decide(self.profile, measured)
        decision.targets = smooth(
            self.previous,
            decision.targets,
            self.held_since,
            now,
            self.profile.scaling.hold_seconds,
            frozenset(decision.urgent),
        )
        self.previous = dict(decision.targets)
        return decision

    def write(self, decision: Decision, measured: Signals) -> None:
        """Pool for the supervisors; cards the user is on are blocked so GPU jobs leave at once."""
        path = self.profile.pool_path()
        if path is not None:
            pool.save(
                pool.Pool(
                    decision.targets,
                    source="auditcore-runner/lokal",
                    reasons=decision.reasons,
                    user_priority=measured.gamemode,
                    blocked_cards=tuple(sorted(measured.user_gpus)),
                ),
                path,
            )
        if self.profile.backend != "scaleset":  # with scale sets the listener owns the demand file
            classes = {name: nachfrage.ClassDemand(count) for name, count in measured.queued.items()}
            nachfrage.save(nachfrage.Demand("regler", time.time(), classes))


def swap_rate(before: tuple[float, int], after: tuple[float, int]) -> float | None:
    """Pages swapped in per second between two ``(time, pswpin)`` samples."""
    seconds = after[0] - before[0]
    return (after[1] - before[1]) / seconds if seconds > 0 else None


def run_forever(profile: Profile, client: github.Client | None) -> None:  # pragma: no cover - loop
    regulator = Regulator(profile, client)
    sample = (time.monotonic(), signals.swap_in_pages())
    while True:
        time.sleep(profile.scaling.interval_seconds)
        current = (time.monotonic(), signals.swap_in_pages())
        measured = collect(profile, client, swap_rate(sample, current))
        sample = current
        regulator.write(regulator.round(measured, time.time()), measured)
