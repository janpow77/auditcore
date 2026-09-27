from __future__ import annotations

import json
from dataclasses import replace
from importlib.resources import files
from pathlib import Path

import pytest

from auditcore_runner import anwenden, backend, cli, gpu, install, profile_io
from auditcore_runner.hardware import HostFacts
from auditcore_runner.profile import Profile
from auditcore_runner.signals import GpuUse

CARD0 = "GPU-00000000-0000-0000-0000-000000000000"
CARD1 = "GPU-11111111-1111-1111-1111-111111111111"


@pytest.fixture
def workstation() -> Profile:
    text = files("auditcore_runner").joinpath("data", "beispiele", "workstation-2gpu.json").read_text(encoding="utf-8")
    return profile_io.from_json(json.loads(text))


def state(**overrides: object) -> gpu.CardState:
    base = gpu.CardState(GpuUse({CARD0: 16000, CARD1: 16000}, frozenset(), {}), {}, frozenset(), False, 3600.0)
    return replace(base, **overrides)  # type: ignore[arg-type]


def test_choose_picks_the_freest_usable_card(workstation: Profile) -> None:
    assert gpu.choose(workstation, "gpu-16gb", state()) in {CARD0, CARD1}
    tight = state(use=GpuUse({CARD0: 16000, CARD1: 9000}, frozenset(), {}))
    assert gpu.choose(workstation, "gpu-16gb", tight) == CARD0
    reserved = state(reserved={CARD0: 2})  # zwei eigene Runner à 6000 MB belegen Karte 0 schon
    assert gpu.choose(workstation, "gpu-16gb", reserved) == CARD1


def test_user_priority_and_interactive_card(workstation: Profile) -> None:
    assert gpu.choose(workstation, "gpu-16gb", state(user_idle_seconds=30.0)) == CARD1
    assert (
        gpu.choose(workstation, "gpu-16gb", state(use=GpuUse({}, frozenset({CARD1}), {}), user_idle_seconds=30.0))
        is None
    )
    assert gpu.choose(workstation, "gpu-16gb", state(user_priority=True)) is None
    assert gpu.must_evict(CARD1, state(blocked=frozenset({CARD1})))
    assert not gpu.must_evict(CARD0, state())


def test_backend_marks_gpu_classes(workstation: Profile) -> None:
    jit = backend.backend("jit")
    assert jit.environment(workstation, "gpu-16gb", 1)["AUDITCORE_RUNNER_GPU_CLASS"] == "1"
    assert jit.environment(workstation, "cpu-gross", 1)["AUDITCORE_RUNNER_GPU_CLASS"] == ""
    with pytest.raises(KeyError):
        backend.backend("scale-set")


def test_apply_versions_and_conflicts(
    workstation: Profile, workstation_facts: HostFacts, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(install, "image_present", lambda image: True)
    monkeypatch.setattr(install, "network_present", lambda name: True)
    path = tmp_path / "profil.json"
    raw = profile_io.to_json(workstation)
    first = anwenden.apply(raw, path, workstation_facts, source="flow-agent", who="zentrale", run=False)
    assert first["angewendet"] and first["version"] == 1
    saved = profile_io.load(path)
    assert saved.change.source == "flow-agent" and saved.change.who == "zentrale"
    conflict = anwenden.apply(raw, path, workstation_facts, source="lokal", who="ui", expected_version=0, run=False)
    assert conflict["konflikt"] and not conflict["angewendet"] and "Version 1" in str(conflict["meldung"])
    second = anwenden.apply(raw, path, workstation_facts, source="lokal", who="ui", expected_version=1, run=False)
    assert second["version"] == 2
    broken = profile_io.to_json(replace(workstation, reserve_cpus=30))
    refused = anwenden.apply(broken, path, workstation_facts, source="lokal", who="cli", run=False)
    assert not refused["angewendet"] and not refused["gueltig"] and profile_io.load(path).version == 2


def test_evaluate_shows_diff_without_writing(
    workstation: Profile, workstation_facts: HostFacts, tmp_path: Path
) -> None:
    _, result = anwenden.evaluate(profile_io.to_json(workstation), tmp_path / "p.json", workstation_facts)
    assert result["gueltig"] and result["aktive_version"] is None
    assert any("p.json" in c["datei"] for c in result["aenderungen"])  # type: ignore[union-attr, index]
    assert not (tmp_path / "p.json").exists()


def test_gpu_cli_choose_and_check(
    workstation: Profile, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "profil.json"
    profile_io.save(workstation, path)
    current = {"state": state(use=GpuUse({CARD0: 16000, CARD1: 9000}, frozenset(), {}))}
    monkeypatch.setattr(gpu, "observe", lambda profile: current["state"])
    assert cli.main(["--profil", str(path), "gpu", "waehlen", "gpu-16gb"]) == 0
    assert capsys.readouterr().out.strip() == CARD0
    assert cli.main(["--profil", str(path), "gpu", "pruefen", CARD0]) == 0
    current["state"] = state(user_priority=True)
    assert cli.main(["--profil", str(path), "gpu", "waehlen", "gpu-16gb"]) == 3
    assert cli.main(["--profil", str(path), "gpu", "pruefen", CARD0]) == 1
    assert cli.main(["--profil", str(path), "gpu", "waehlen", "gibt-es-nicht"]) == 2
