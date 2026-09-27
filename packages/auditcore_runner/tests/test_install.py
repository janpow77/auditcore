from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import replace
from importlib.resources import files
from pathlib import Path

import pytest

from auditcore_runner import install, profile_io
from auditcore_runner.profile import Profile, TargetSource


@pytest.fixture
def workstation() -> Profile:
    text = files("auditcore_runner").joinpath("data", "beispiele", "workstation-2gpu.json").read_text(encoding="utf-8")
    return profile_io.from_json(json.loads(text))


def test_plan_renders_units_without_placeholders(workstation: Profile, tmp_path: Path) -> None:
    changes = install.plan(workstation, tmp_path / "profil.json")
    names = {c.path.name for c in changes}
    assert {
        "auditcore-runner-cpu-gross@.service",
        "auditcore-runner-gpu-16gb@.service",
        "auditcore-runner-status.timer",
        "auditcore-runner-regler.service",
        "auditcore-ci-firewall.sh",
        "firewall-installieren.sh",
    } <= names
    unit = next(c.new for c in changes if c.path.name == "auditcore-runner-cpu-gross@.service")
    assert "Nice=19" in unit and "CPUWeight=idle" in unit and "IOWeight=10" in unit
    assert "supervisor cpu-gross %i" in unit and "soll.json" in unit
    for change in changes:
        assert not re.search(r"\$\{[a-z_]+\}", change.new), change.path  # template fields are lower case


def test_firewall_script_blocks_private_ranges(workstation: Profile) -> None:
    script = install.render_firewall(workstation)["auditcore-ci-firewall.sh"]
    assert 'SUBNET="172.30.250.0/24"' in script and 'BRIDGE="br-auditcore-ci"' in script
    for net in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "100.64.0.0/10"):
        assert net in script
    assert install.firewall_command().startswith("sudo bash ") and install.firewall_command().endswith(
        "firewall-installieren.sh"
    )


@pytest.mark.skipif(shutil.which("shellcheck") is None, reason="shellcheck nicht installiert")
def test_rendered_scripts_pass_shellcheck(workstation: Profile, tmp_path: Path) -> None:
    for name, text in install.render_firewall(workstation).items():
        if name.endswith(".sh"):
            script = tmp_path / name
            script.write_text(text, encoding="utf-8")
            result = subprocess.run(["shellcheck", str(script)], capture_output=True, text=True, check=False)
            assert result.returncode == 0, result.stdout
    supervisor = files("auditcore_runner").joinpath("data", "supervisor.sh")
    result = subprocess.run(["shellcheck", str(supervisor)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout


def test_static_source_has_no_regulator_and_empty_pool(workstation: Profile, tmp_path: Path) -> None:
    static = replace(workstation, source=TargetSource("statisch"))
    changes = install.plan(static, tmp_path / "p.json")
    assert "auditcore-runner-regler.service" not in {c.path.name for c in changes}
    unit = next(c.new for c in changes if c.path.name == "auditcore-runner-cpu-gross@.service")
    assert "AUDITCORE_RUNNER_POOL=\n" in unit


def test_steps_enable_up_to_maximum_and_never_stop(workstation: Profile) -> None:
    steps = [s.text() for s in install.instance_steps(workstation)]
    assert "systemctl --user enable --now auditcore-runner-cpu-gross@3.service" in steps
    assert not any("stop" in s or "disable" in s for s in steps)
    docker = [s.text() for s in install.docker_steps(workstation, has_image=False, has_network=False)]
    assert docker[0].startswith("docker build") and "com.docker.network.bridge.name=br-auditcore-ci" in docker[1]


def test_write_changes_and_diff(workstation: Profile, tmp_path: Path) -> None:
    changes = install.plan(workstation, tmp_path / "p.json")
    written = install.write_changes(changes)
    assert written and all(path.exists() for path in written)
    assert not any(c.changed for c in install.plan(workstation, tmp_path / "p.json"))
    script = next(p for p in written if p.name == "auditcore-ci-firewall.sh")
    assert script.stat().st_mode & 0o111
    first = changes[0]
    assert first.diff().startswith("---")


def test_uninstall_lists_paths(tmp_path: Path) -> None:
    unit = install.unit_dir() / "auditcore-runner-cpu@.service"
    unit.parent.mkdir(parents=True)
    unit.write_text("x", encoding="utf-8")
    paths = install.uninstall_files(everything=True)
    assert unit in paths and any(p.name == "auditcore-runner" for p in paths)
    install.remove_paths(paths)
    assert not unit.exists()
