from __future__ import annotations

from pathlib import Path

import pytest

from auditcore_runner.hardware import Gpu, HostFacts

WORKSTATION_GPUS = (
    Gpu(0, "GPU-00000000-0000-0000-0000-000000000000", "Karte 0 (Beispiel)", 16384),
    Gpu(1, "GPU-11111111-1111-1111-1111-111111111111", "Karte 1 (Beispiel)", 16384),
)


@pytest.fixture
def workstation_facts() -> HostFacts:
    """A workstation with 32 threads, 64 GB and two 16-GB cards (matches the example template)."""
    return HostFacts("workstation", 32, 64 * 1024, 8 * 1024, 0, WORKSTATION_GPUS)


@pytest.fixture
def server_facts() -> HostFacts:
    gpu = Gpu(0, "GPU-22222222-2222-2222-2222-222222222222", "Karte (Beispiel)", 8192)
    return HostFacts("server", 20, 62 * 1024, 32 * 1024, 16 * 1024, (gpu,))


@pytest.fixture(autouse=True)
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Never touch the real ~/.config, ~/.local/state or ~/.cache."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(home / ".local" / "state"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(home / ".cache"))
    monkeypatch.delenv("AUDITCORE_RUNNER_PROFILE", raising=False)
    return home
