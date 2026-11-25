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


def test_program_path_uses_console_script_beside_python(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    binary_dir = tmp_path / "bin"
    binary_dir.mkdir()
    executable = binary_dir / "auditcore-runner"
    executable.touch()
    monkeypatch.setattr(install.shutil, "which", lambda _name: None)
    monkeypatch.setattr(install.sys, "executable", str(binary_dir / "python"))

    assert install.program_path() == str(executable)


def test_program_path_fails_closed_without_console_script(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(install.shutil, "which", lambda _name: None)
    monkeypatch.setattr(install.sys, "executable", str(tmp_path / "bin" / "python"))

    with pytest.raises(FileNotFoundError, match="console script"):
        install.program_path()


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


def test_supervisor_checks_busy_for_all_target_scopes() -> None:
    script = files("auditcore_runner").joinpath("data", "supervisor.sh").read_text(encoding="utf-8")
    busy_query = 'busy="$(gh api "$base/actions/runners/$id" -q .busy 2>/dev/null || echo unknown)"'

    assert script.count(busy_query) == 1
    assert script.index(busy_query) < script.index('if [[ "$(cfg \'.ziel.art\')" == "repo" ]]')


@pytest.mark.skipif(not shutil.which("bash") or not shutil.which("jq"), reason="Supervisor benötigt Bash und jq")
@pytest.mark.parametrize("backend", ["jit", "scaleset"])
def test_supervisor_keeps_registration_target(tmp_path: Path, backend: str) -> None:
    script = files("auditcore_runner").joinpath("data", "supervisor.sh").read_text(encoding="utf-8")
    functions, _ = script.rsplit("\nwhile true; do", 1)
    harness = (
        functions
        + r"""
registration_base() { echo repos/example/project; }
cfg() { echo 1; }
gh() {
  cat >/dev/null
  [[ "$*" == *"repos/example/project/actions/runners/generate-jitconfig"* ]] || return 1
  echo '{"runner":{"id":42},"encoded_jit_config":"test"}'
}
program() { echo '{"runner":{"id":42},"encoded_jit_config":"test"}'; }
PROGRAM=program
container_args() { args=(); }
docker() { :; }
watch_allowed() { :; }
remove_registration() { printf '%s %s' "$1" "$2" > removed; }
run_one_job
"""
    )
    subprocess.run(
        ["bash", "-c", harness, "supervisor", "cpu", "1"],
        cwd=tmp_path,
        env={
            "PATH": "/usr/bin:/bin",
            "AUDITCORE_RUNNER_PROFILE": "test",
            "AUDITCORE_RUNNER_BACKEND": backend,
            "XDG_RUNTIME_DIR": str(tmp_path),
        },
        check=True,
    )
    assert (tmp_path / "removed").read_text() == "42 repos/example/project"


def test_supervisor_persists_cargo_cache_per_runner_instance() -> None:
    script = files("auditcore_runner").joinpath("data", "supervisor.sh").read_text(encoding="utf-8")

    assert '--init --rm --name "$container"' in script
    assert "auditcore-runner-cargo-$CLASS-$INSTANCE:/home/runner/.cargo" in script
    assert "--env CARGO_HOME=/home/runner/.cargo" in script


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


def test_supervisor_observes_container_after_delayed_creation(tmp_path: Path) -> None:
    script = files("auditcore_runner").joinpath("data", "supervisor.sh").read_text(encoding="utf-8")
    watcher = "watch_allowed() {" + script.split("watch_allowed() {", 1)[1].split("\n}", 1)[0] + "\n}"
    harness = watcher + r"""
GPU=""
sleep() { :; }
docker() {
  if [[ "$1" == inspect && ! -f created ]]; then touch created; return 1; fi
  if [[ "$1" == stop ]]; then touch stopped; fi
  return 0
}
gh() { echo false; }
cfg() { echo repo; }
registration_base() { echo repos/example/new; }
remove_registration() { [[ "$2" == repos/example/old ]]; }
log() { :; }
watch_allowed 42 runner repos/example/old "$$"
"""
    subprocess.run(["bash", "-ec", harness], cwd=tmp_path, timeout=5, check=True)
    assert (tmp_path / "stopped").exists()
