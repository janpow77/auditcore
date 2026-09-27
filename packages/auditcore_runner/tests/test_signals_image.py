from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from auditcore_runner import image, signals
from auditcore_runner.autoscaler import swap_rate
from auditcore_runner.profile import ThermalSource


def test_parsers_of_local_probes(tmp_path: Path) -> None:
    assert signals.parse_idle_reply("(uint64 125000,)") == 125.0
    assert signals.parse_idle_reply("Fehler") is None
    now = datetime(2026, 9, 27, 12, 0, tzinfo=UTC)
    since = int((now - timedelta(minutes=20)).timestamp() * 1_000_000)
    idle, locked = signals.parse_loginctl(f"IdleHint=yes\nIdleSinceHint={since}\nLockedHint=no", now)
    assert idle == 1200.0 and not locked
    assert signals.parse_loginctl("IdleHint=no\nLockedHint=yes", now) == (0.0, True)
    use = signals.parse_gpu_use(
        "GPU-a, 12000\nGPU-b, 3000\nGPU-c, 16000\n",
        "GPU-a, /usr/bin/blender\nGPU-b, /home/runner/_work/venv/bin/python\nGPU-c, /usr/bin/model-server\n",
        ("model-server",),
    )
    assert use.user_cards == frozenset({"GPU-a"}) and use.runner_cards == {"GPU-b": 1}
    assert use.free_vram == {"GPU-a": 12000, "GPU-b": 3000, "GPU-c": 16000}
    vmstat = tmp_path / "vmstat"
    vmstat.write_text("pgpgin 5\npswpin 1234\npswpout 9\n", encoding="utf-8")
    assert signals.swap_in_pages(vmstat) == 1234
    assert swap_rate((0.0, 100), (10.0, 300)) == 20.0


def test_thermal_source_with_field_mapping() -> None:
    data = {
        "betrieb": {"modus": "leise"},
        "grenzen": {"a": 62.0, "b": 75.0},
        "karten": [{"temp": 55.0, "gedrosselt": False}, {"temp": 48.0}],
        "cpu": {"temp": 70.5, "gedrosselt": 4551},
    }
    source = ThermalSource(
        enabled=True,
        url="http://127.0.0.1:1/",
        throttling_paths=("karten[*].gedrosselt", "cpu.gedrosselt"),
        temperature_paths=("karten[*].temp", "cpu.temp"),
        limit_paths=("grenzen.a", "grenzen.b"),
        mode_path="betrieb.modus",
        quiet_value="leise",
    )
    state = signals.parse_thermal(data, source)
    assert state is not None and state.throttling and state.quiet and state.hottest_c == 70.5 and state.limit_c == 62.0
    assert signals.parse_thermal("kaputt", source) is None
    assert signals.resolve(data, "karten[*].temp") == [55.0, 48.0]
    assert signals.thermal_state(ThermalSource()) is None


def test_runner_version_rules() -> None:
    now = datetime(2026, 9, 27, tzinfo=UTC)
    release = image.Release((2, 338, 0), now - timedelta(days=5))
    assert image.VersionStatus((2, 337, 0), release, now).state == "frist"
    assert image.VersionStatus((2, 337, 0), release, now + timedelta(days=30)).state == "abgelaufen"
    assert image.VersionStatus((2, 338, 0), release, now).state == "aktuell"
    assert image.VersionStatus((2, 300, 0), None, now).state == "abgelaufen"
    assert image.VersionStatus(None, release, now).as_dict()["zustand"] == "unbekannt"
    assert image.parse_version("v2.337.0") == (2, 337, 0)
