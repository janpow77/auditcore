"""Backend switch, CDI/GPU reservations, egress scripts, status queue and the decision workflow."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import replace
from importlib.resources import files
from pathlib import Path

import jsonschema
import pytest
import yaml

from auditcore_runner import backend, cli, github, gpu, install, nachfrage, profile_io, status
from auditcore_runner.hardware import HostFacts
from auditcore_runner.profile import Profile
from auditcore_runner.propose import propose
from auditcore_runner.validation import validate

CARD = "GPU-00000000-0000-0000-0000-000000000000"


def base(facts: HostFacts) -> Profile:
    return replace(propose(facts, "owner/repo"), host="build-01")


def test_profile_round_trip_keeps_new_fields(workstation_facts: HostFacts) -> None:
    profile = replace(base(workstation_facts), backend="scaleset", gpu_access="gpus")
    profile = replace(profile, network=replace(profile.network, egress="allowlist", egress_hosts=("pypi.org",)))
    schema = json.loads(files("auditcore_runner").joinpath("data", "schemas", "profil.schema.json").read_text())
    jsonschema.validate(profile_io.to_json(profile), schema)
    again = profile_io.from_json(json.loads(profile_io.dumps(profile)))
    assert again.backend == "scaleset" and again.gpu_access == "gpus"
    assert again.network.egress_hosts == ("pypi.org",) and again.scale_set_name("cpu") == "build-01-cpu"
    old = profile_io.to_json(base(workstation_facts))
    del old["gpu_zugriff"], old["scale_set"]
    assert profile_io.from_json(old).gpu_access == "cdi"


def test_validation_of_new_fields(workstation_facts: HostFacts) -> None:
    profile = base(workstation_facts)
    bad = replace(
        profile,
        backend="k8s",
        gpu_access="magie",
        network=replace(profile.network, egress="offen", egress_hosts=("nicht gültig",), egress_ports=(0,)),
    )
    fields = {p.field for p in validate(bad, workstation_facts)}
    assert {"backend", "gpu_zugriff", "netz.egress", "netz.egress_hosts", "netz.egress_ports"} <= fields
    grouped = replace(profile, backend="scaleset", scale_set=replace(profile.scale_set, runner_group="team"))
    assert "scale_set.runner_gruppe" in {p.field for p in validate(grouped, workstation_facts)}


def test_backend_environment(workstation_facts: HostFacts) -> None:
    profile = base(workstation_facts)
    name = next(iter(profile.classes))
    jit = backend.backend("jit").environment(profile, name, 1)
    scale = backend.backend("scaleset").environment(replace(profile, backend="scaleset"), name, 1)
    assert jit["AUDITCORE_RUNNER_BACKEND"] == "jit" and jit["AUDITCORE_RUNNER_DEMAND"] == ""
    assert scale["AUDITCORE_RUNNER_BACKEND"] == "scaleset" and scale["AUDITCORE_RUNNER_DEMAND"].endswith(
        "nachfrage.json"
    )
    assert scale["AUDITCORE_RUNNER_GPU_ACCESS"] == "cdi"


def test_listener_unit_only_for_scale_sets(workstation_facts: HostFacts) -> None:
    profile = base(workstation_facts)
    names = {c.path.name for c in install.plan(profile)}
    assert "auditcore-runner-scaleset.service" not in names
    assert {"auditcore-runner-image.service", "auditcore-runner-image.timer"} <= names
    scale = replace(profile, backend="scaleset")
    unit = next(c.new for c in install.plan(scale) if c.path.name == "auditcore-runner-scaleset.service")
    assert "scaleset lauschen" in unit
    assert any("auditcore-runner-scaleset.service" in s.text() for s in install.instance_steps(scale))


def test_egress_scripts(workstation_facts: HostFacts) -> None:
    profile = base(workstation_facts)
    closed = install.render_firewall(profile)
    assert "auditcore-ci-egress.timer" not in closed and 'EGRESS="aus"' in closed["auditcore-ci-firewall.sh"]
    allow = replace(profile, network=replace(profile.network, egress="allowlist", egress_hosts=("pypi.org",)))
    scripts = install.render_firewall(allow)
    firewall = scripts["auditcore-ci-firewall.sh"]
    assert "EGRESS_HOSTS=(pypi.org)" in firewall and 'EGRESS_PORTS="80,443"' in firewall
    assert (
        "--match-set" in firewall
        and "systemctl enable --now auditcore-ci-egress.timer" in scripts["firewall-installieren.sh"]
    )
    if shutil.which("shellcheck"):
        for name, text in scripts.items():
            if name.endswith(".sh"):
                result = subprocess.run(["shellcheck", "-"], input=text, text=True, capture_output=True, check=False)
                assert result.returncode == 0, name + result.stdout


def test_gpu_reservations_count_until_the_container_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    gpu.reserve("gpu-16gb-1", CARD, now=1000.0)
    gpu.reserve("gpu-16gb-2", CARD, now=0.0)
    assert gpu.reservations(now=1100.0) == {"gpu-16gb-1": CARD}
    assert gpu.reserved_per_card({}, {"gpu-16gb-1": CARD}) == {CARD: 1}
    assert gpu.reserved_per_card({"gpu-16gb-1": CARD, "abc": CARD}, {"gpu-16gb-1": CARD}) == {CARD: 2}
    gpu.release("gpu-16gb-1")
    assert gpu.reservations(now=1100.0) == {}


def test_status_reports_queue_and_unknown_runners(
    workstation_facts: HostFacts, monkeypatch: pytest.MonkeyPatch
) -> None:
    profile = base(workstation_facts)
    name = next(iter(profile.classes))
    labels = profile.classes[name].labels
    nachfrage.save(
        nachfrage.Demand("scaleset", 4_000_000_000.0, {name: nachfrage.ClassDemand(2, 3, {"laufend": 1}, "s")})
    )
    runners = [
        github.RunnerInfo(1, "build-01-a", True, False, labels),
        github.RunnerInfo(2, "fremd", True, False, labels),
        github.RunnerInfo(3, "anders", False, False, ("windows",)),
    ]
    monkeypatch.setattr(github, "list_runners", lambda client, target: runners)
    monkeypatch.setattr(status, "active_instances", lambda name: 0)
    monkeypatch.setattr(install, "image_present", lambda image: True)
    monkeypatch.setattr(install, "network_present", lambda network: True)
    monkeypatch.setattr(nachfrage.Demand, "fresh", lambda self, now=None: True)
    current = status.collect(profile, workstation_facts, github.Client("t", fetch=lambda *a: (200, {}, b"{}")))
    entry = current["klassen"][name]  # type: ignore[index]
    assert entry["warteschlange"] == 2 and entry["nachfrage_soll"] == 3
    details = current["unbekannte_runner_details"]
    assert [d["name"] for d in details] == ["anders", "fremd"]  # type: ignore[union-attr]
    assert [d["passt_zu_klasse"] for d in details] == [None, name]  # type: ignore[union-attr]
    metrics = status.prometheus(current)
    assert 'zustand="warteschlange"} 2' in metrics and "auditcore_runner_unknown_matching_class" in metrics
    assert status.new_unknown(["fremd"]) == ["fremd"] and status.new_unknown(["fremd"]) == []


def test_list_runners_reads_every_page() -> None:
    pages = {1: [{"id": i, "name": f"r{i}"} for i in range(100)], 2: [{"id": 100, "name": "r100"}]}

    def fetch(method: str, path: str, headers: dict[str, str], body: bytes | None) -> tuple[int, dict[str, str], bytes]:
        page = int(path.rsplit("page=", 1)[1])
        return 200, {}, json.dumps({"runners": pages.get(page, [])}).encode()

    runners = github.list_runners(github.Client("t", fetch=fetch), profile_target())
    assert len(runners) == 101


def profile_target() -> github.Target:
    return github.Target("repo", "owner/repo")


def test_workflow_template_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["workflows", "vorlage", "runner-wahl"]) == 0
    assert "workflow_call" in capsys.readouterr().out
    assert cli.main(["workflows", "vorlage", "runner-wahl", "--ziel", str(tmp_path)]) == 0
    assert cli.main(["workflows", "vorlage", "runner-wahl", "--ziel", str(tmp_path)]) == 1


def _decision(tmp_path: Path, runners: list[dict[str, object]] | None, **env: str) -> dict[str, str]:
    workflow = yaml.safe_load(files("auditcore_runner").joinpath("data", "workflows", "runner-wahl.yml").read_text())
    script = workflow["jobs"]["wahl"]["steps"][0]["run"]
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    fake_gh = bin_dir / "gh"
    lines = [json.dumps([*[x["name"] for x in r.get("labels", [])], r["name"]]) for r in runners or []]
    fake_gh.write_text(
        "#!/usr/bin/env bash\n"
        + ("exit 1\n" if runners is None else f"printf '%s\\n' {' '.join(repr(x) for x in lines)}\n")
    )
    fake_gh.chmod(0o755)
    output = tmp_path / "out"
    output.write_text("")
    values = {
        "EIGENE": '["self-hosted","linux"]',
        "RUECKFALL": '"ubuntu-latest"',
        "LABEL": "linux",
        "PRUEFEN": "true",
        "ZIEL": "repos/owner/repo",
        "GH_TOKEN": "t",
        "EVENT": "push",
        "HEAD_REPO": "",
        "REPO": "owner/repo",
        "ACTOR": "someone",
        **env,
    }
    environment = {**os.environ, **values, "GITHUB_OUTPUT": str(output), "PATH": f"{bin_dir}:{os.environ['PATH']}"}
    subprocess.run(["bash", "-c", script], env=environment, check=True, capture_output=True)
    return dict(line.split("=", 1) for line in output.read_text().splitlines())


@pytest.mark.skipif(not shutil.which("jq"), reason="jq fehlt")
def test_decision_workflow(tmp_path: Path) -> None:
    online = [{"name": "build-01-cpu-1", "labels": [{"name": "self-hosted"}, {"name": "linux"}]}]
    assert _decision(tmp_path, online)["runs-on"] == '["self-hosted","linux"]'
    assert _decision(tmp_path, [])["runs-on"] == '"ubuntu-latest"'
    assert _decision(tmp_path, None)["grund"] == "Runner-Liste nicht lesbar"
    fork = _decision(tmp_path, online, EVENT="pull_request", HEAD_REPO="fork/repo")
    assert fork == {"runs-on": '"ubuntu-latest"', "grund": "Fork-PR"}
    assert _decision(tmp_path, online, ACTOR="dependabot[bot]")["grund"] == "Dependabot"
    assert _decision(tmp_path, online, GH_TOKEN="")["runs-on"] == '["self-hosted","linux"]'


def test_install_hints_for_cdi_and_scale_sets(workstation_facts: HostFacts, tmp_path: Path) -> None:
    profile = base(workstation_facts)
    gpu_class = next((n for n in profile.classes if profile.gpus_of(n)), None)
    if gpu_class is None:
        pytest.skip("Vorschlag ohne GPU-Klasse")
    classes = {**profile.classes, gpu_class: replace(profile.classes[gpu_class], enabled=True)}
    profile = replace(profile, classes=classes)
    assert any("nvidia-ctk" in h for h in install.hints(profile, (tmp_path,)))
    (tmp_path / "nvidia.yaml").write_text("kind: nvidia.com/gpu\n")
    assert not any("nvidia-ctk" in h for h in install.hints(profile, (tmp_path,)))
    assert not install.hints(replace(profile, gpu_access="gpus"), (tmp_path / "leer",))
    assert any("runs-on" in h for h in install.hints(replace(profile, backend="scaleset"), (tmp_path,)))
