from __future__ import annotations

import json
from dataclasses import replace
from importlib.resources import files

import pytest

from auditcore_runner import profile_io
from auditcore_runner.profile import Priority, Profile, ThermalSource
from auditcore_runner.regeln import Signals, ThermalState, decide, in_full_power_window, smooth, user_active

CARD0 = "GPU-00000000-0000-0000-0000-000000000000"
CARD1 = "GPU-11111111-1111-1111-1111-111111111111"


@pytest.fixture
def workstation() -> Profile:
    text = files("auditcore_runner").joinpath("data", "beispiele", "workstation-2gpu.json").read_text(encoding="utf-8")
    return profile_io.from_json(json.loads(text))


def calm(**overrides: object) -> Signals:
    base = Signals(cpu_count=32, load_1m=2.0, memory_available_mb=40_000, swap_used_mb=0, idle_seconds=3600, hour=14)
    return replace(base, **overrides)  # type: ignore[arg-type]


def test_idle_machine_gets_maximum(workstation: Profile) -> None:
    assert decide(workstation, calm()).targets == {"cpu-gross": 3, "gpu-16gb": 2}


def test_interactive_priority_caps_and_frees_interactive_card(workstation: Profile) -> None:
    decision = decide(workstation, calm(idle_seconds=30))
    assert decision.targets == {"cpu-gross": 1, "gpu-16gb": 1}
    assert "interaktive Nutzung hat Vorrang" in decision.reasons["cpu-gross"]


def test_interactive_priority_is_off_by_default(workstation: Profile) -> None:
    neutral = replace(workstation, scaling=replace(workstation.scaling, interactive_priority=False))
    assert decide(neutral, calm(idle_seconds=30, gamemode=True)).targets == {"cpu-gross": 3, "gpu-16gb": 2}


def test_full_power_window(workstation: Profile) -> None:
    windowed = replace(workstation, scaling=replace(workstation.scaling, full_power_from_hour=22, full_power_to_hour=6))
    assert decide(windowed, calm(idle_seconds=30, hour=3)).targets["cpu-gross"] == 3
    assert in_full_power_window(23, windowed.scaling) and not in_full_power_window(12, windowed.scaling)
    assert not in_full_power_window(3, workstation.scaling)


def test_user_always_wins_on_gpus(workstation: Profile) -> None:
    decision = decide(workstation, calm(user_gpus=frozenset({CARD1})))
    assert decision.targets["gpu-16gb"] == 1 and "gpu-16gb" in decision.urgent
    assert decide(workstation, calm(user_priority=True)).targets["gpu-16gb"] == 0
    assert decide(workstation, calm(gamemode=True)).targets == {"cpu-gross": 1, "gpu-16gb": 1}


def test_cards_are_shared_by_free_vram(workstation: Profile) -> None:
    assert decide(workstation, calm(gpu_free_vram={CARD0: 4000, CARD1: 12000})).targets["gpu-16gb"] == 1


def test_unknown_idle_counts_as_active(workstation: Profile) -> None:
    assert user_active(calm(idle_seconds=None), workstation.scaling)
    assert not user_active(calm(idle_seconds=None, locked=True), workstation.scaling)


def test_memory_pressure_uses_swap_in_not_swap_used(workstation: Profile) -> None:
    assert decide(workstation, calm(swap_used_mb=17_000)).targets["cpu-gross"] == 3
    decision = decide(workstation, calm(swap_in_per_s=5000, busy={"cpu-gross": 1}))
    assert decision.targets["cpu-gross"] == 1 and "cpu-gross" in decision.urgent
    assert decide(workstation, calm(memory_available_mb=2000)).targets["cpu-gross"] == 0


def test_load_and_temperature(workstation: Profile) -> None:
    assert decide(workstation, calm(load_1m=31.0)).targets["cpu-gross"] == 0
    assert decide(workstation, calm(temperature_c=95.0, busy={"cpu-gross": 2})).targets["cpu-gross"] == 2


def test_thermal_source(workstation: Profile) -> None:
    source = ThermalSource(enabled=True, url="http://127.0.0.1:1/s", temperature_paths=("t",), quiet_value="leise")
    thermal = replace(workstation, scaling=replace(workstation.scaling, thermal=source))
    throttled = calm(thermal=ThermalState(throttling=True, hottest_c=60, limit_c=62))
    assert decide(thermal, throttled).targets["cpu-gross"] == 0
    assert decide(workstation, throttled).targets["cpu-gross"] == 3  # Quelle aus: keine Wirkung
    quiet = calm(thermal=ThermalState(hottest_c=40, limit_c=62, quiet=True))
    assert decide(thermal, quiet).targets == {"cpu-gross": 1, "gpu-16gb": 0}


def test_queue_demand_and_minimum(workstation: Profile) -> None:
    decision = decide(workstation, calm(queued={"cpu-gross": 0}, busy={"cpu-gross": 1}))
    assert decision.targets["cpu-gross"] == 2  # 1 belegt + 0 wartend + 1 Reserve
    minimum = replace(workstation.classes["cpu-gross"], min_instances=2)
    raised = replace(workstation, classes={**workstation.classes, "cpu-gross": minimum})
    assert decide(raised, calm(queued={"cpu-gross": 0}, busy={})).targets["cpu-gross"] == 2


def test_priorities_preempt_lower_ranks_when_capacity_is_short(workstation: Profile) -> None:
    small = replace(workstation, reserve_cpus=6)  # Budget 26 CPUs: 3×8 + 2×2 = 28 passt nicht
    decision = decide(small, calm())
    assert decision.targets == {"cpu-gross": 3, "gpu-16gb": 1}
    assert any("Vorrang anderer Klassen" in r for r in decision.reasons["gpu-16gb"])
    swapped = replace(small, priorities=(Priority("gpu-16gb", 1, False), Priority("cpu-gross", 2, True, 1)))
    assert decide(swapped, calm()).targets == {"cpu-gross": 2, "gpu-16gb": 2}


def test_disabled_class(workstation: Profile) -> None:
    off = replace(workstation.classes["gpu-16gb"], enabled=False)
    assert (
        decide(replace(workstation, classes={**workstation.classes, "gpu-16gb": off}), calm()).targets["gpu-16gb"] == 0
    )


def test_hysteresis() -> None:
    held: dict[str, float] = {}
    assert smooth({"cpu": 3}, {"cpu": 1}, held, 0.0, 300) == {"cpu": 3}
    assert smooth({"cpu": 3}, {"cpu": 1}, held, 299.0, 300) == {"cpu": 3}
    assert smooth({"cpu": 3}, {"cpu": 1}, held, 300.0, 300) == {"cpu": 1}
    assert smooth({"cpu": 1}, {"cpu": 3}, held, 301.0, 300) == {"cpu": 3}
    assert smooth({"cpu": 3}, {"cpu": 0}, {}, 0.0, 300, frozenset({"cpu"})) == {"cpu": 0}
