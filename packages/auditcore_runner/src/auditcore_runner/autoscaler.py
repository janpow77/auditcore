"""Built-in autoscaler for target source ``lokal``: signals → rules → pool file."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime

from . import github, pool, signals
from .hardware import detect
from .profile import Profile
from .regeln import Decision, Signals, decide, smooth


def collect(profile: Profile, client: github.Client | None, swap_in_per_s: float | None = None) -> Signals:
    """Measure everything the rules use; GitHub data is optional."""
    facts = detect()
    available, swap_used = signals.memory()
    idle, locked = signals.activity()
    cards = signals.gpu_use(profile.scaling.gpu_shared_services)
    external = pool.load(profile.pool_path()) if profile.source.kind == "datei" else None
    queued: dict[str, int] = {}
    busy: dict[str, int] = {}
    if client is not None:
        try:
            runners = github.list_runners(client, profile.target)
            busy = github.busy_by_class(runners, profile, profile.runner_prefix())
            queued = github.queued_by_class(client, profile)
        except github.GitHubError:
            queued, busy = {}, {}
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
