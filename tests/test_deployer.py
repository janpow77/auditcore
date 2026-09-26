"""Build real Debian fixtures; no host installation or external network required."""

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from auditcore.exceptions import MigrationBlocked
from auditcore.tools.apprefactor.engine import REQUIRED_VERIFICATION, source_digest
from auditcore.tools.common import digest, run, write_json
from auditcore.tools.deployer.apt import AptRepository
from auditcore.tools.deployer.build import DeploymentBuilder, systemd_unit
from auditcore.tools.deployer.models import ApplicationDeploymentProfile
from auditcore.tools.deployer.validation import inspect_package, validate_sbom


@pytest.fixture
def package_project(git_project):
    root = git_project
    (root / "src").mkdir()
    (root / "src/main.py").write_text('"""Synthetic package test application."""\nprint("ready")\n')
    profile = ApplicationDeploymentProfile(
        application="auditcore-fixture",
        version="1.0.0",
        source_commit=run(["git", "rev-parse", "HEAD"], root).strip(),
        source_digest=source_digest(root),
        entrypoint=["/usr/bin/python3", "-m", "main"],
        source_date_epoch=1700000000,
        shared_library_versions={"auditcore": "0.1.0"},
    )
    write_json(root / "auditcore-deploy.json", asdict(profile))
    profile.source_digest = source_digest(root)
    write_json(root / "auditcore-deploy.json", asdict(profile))
    handoff = {
        "status": "READY_FOR_DEPLOYMENT",
        "source_digest": source_digest(root),
        "policy": {"overall_status": "PASS", "source_status": "POLICY_SOURCE_CURRENT"},
        "tests": {"checks": {k: {"status": "PASS"} for k in REQUIRED_VERIFICATION}},
        "deployment_checks": {
            k: {
                "status": "PASS",
                "reference": "synthetic fixture",
                "reason": "test-only controlled input",
            }
            for k in (
                "protection_need",
                "service_user",
                "permissions",
                "secrets",
                "configuration",
                "logging",
                "backup_restore",
                "network",
                "proxy",
                "health",
                "dependencies",
                "sbom",
                "supply_chain",
                "updates",
            )
        },
    }
    write_json(root / ".auditcore/deployment-handoff.json", handoff)
    return root, profile


def test_deb_build_layout_manifest_and_reproducibility(package_project, tmp_path):
    root, _ = package_project
    builder = DeploymentBuilder()
    first = builder.build_application(root, tmp_path / "first")
    second = builder.build_application(root, tmp_path / "second")
    assert first.sha256 == second.sha256
    result = inspect_package(Path(first.package))
    assert "usr/lib/systemd/system/auditcore-fixture.service" in result["contents"]
    assert "etc/auditcore-fixture" in result["contents"]
    assert first.release_status == "NOT_EXECUTED"
    binding = validate_sbom(Path(first.sbom), Path(first.package), Path(first.manifest))
    assert binding["artifact_binding"] == "PASS"
    manifest = json.loads(Path(first.manifest).read_text())
    manifest["package_sha256"] = "wrong"
    write_json(Path(first.manifest), manifest)
    assert (
        validate_sbom(Path(first.sbom), Path(first.package), Path(first.manifest))["status"]
        == "FAIL"
    )


def test_deployment_missing_handoff_blocked(package_project, tmp_path):
    root, _ = package_project
    (root / ".auditcore/deployment-handoff.json").unlink()
    with pytest.raises(MigrationBlocked):
        DeploymentBuilder().build_application(root, tmp_path / "dist")


def test_stale_deployment_source_blocked(package_project):
    root, _ = package_project
    (root / "src/main.py").write_text("changed = True\n")
    assert "Stale source evidence" in DeploymentBuilder().plan(root).blockers


def test_package_scripts_no_download_or_data_removal(package_project, tmp_path):
    root, _ = package_project
    result = DeploymentBuilder().build_application(root, tmp_path / "dist")
    control = tmp_path / "control"
    run(["dpkg-deb", "--control", result.package, str(control)])
    for name in ("postinst", "prerm", "postrm"):
        text = (control / name).read_text()
        assert not any(word in text for word in ("pip install", "npm", "curl", "wget", "rm -rf"))
        assert text.startswith("#!/bin/sh\nset -eu")


def test_systemd_rejects_injection_and_root(package_project):
    _, profile = package_project
    assert "NoNewPrivileges=true" in systemd_unit(profile)
    profile.service_user = "root"
    with pytest.raises(ValueError):
        systemd_unit(profile)
    profile.service_user = "safe"
    profile.entrypoint = ["/usr/bin/python3", "bad\nExecStart=evil"]
    with pytest.raises(ValueError):
        systemd_unit(profile)


def test_unsigned_apt_not_publishable(package_project, tmp_path):
    root, _ = package_project
    dist = tmp_path / "dist"
    result = DeploymentBuilder().build_application(root, dist)
    repository = AptRepository()
    apt = repository.build(dist)
    assert apt.status == "REVIEW_REQUIRED" and not apt.signed
    assert digest(Path(result.package).read_bytes()) in (dist / "Packages").read_text()
    with pytest.raises(ValueError):
        repository.publish(dist, tmp_path / "publish")


def test_apt_release_has_rfc2822_date(package_project, tmp_path, monkeypatch):
    """apt warns „Invalid 'Date' entry in Release file“ without the field."""
    root, _ = package_project
    dist = tmp_path / "dist"
    DeploymentBuilder().build_application(root, dist)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1790380800")
    AptRepository().build(dist)
    fields = dict(
        line.split(": ", 1) for line in (dist / "Release").read_text().splitlines() if ": " in line
    )
    assert fields["Date"] == "Sat, 26 Sep 2026 00:00:00 GMT"
    monkeypatch.delenv("SOURCE_DATE_EPOCH")
    AptRepository().build(dist)
    assert (dist / "Release").read_text().count("\nDate: ") == 1


def test_cyclonedx_invalid_schema_rejected():
    from auditcore.tools.quality.supplychain import validate_schema

    assert (
        validate_schema(
            {
                "bomFormat": "CycloneDX",
                "specVersion": "1.6",
                "components": [{"type": "invented", "name": "bad"}],
            }
        )["status"]
        == "FAIL"
    )


def test_wheel_hash_and_architecture_rejected(package_project, tmp_path):
    root, profile = package_project
    (root / "wheels").mkdir()
    wheel = root / "wheels/fake-1.0-py3-none-any.whl"
    wheel.write_bytes(b"synthetic-not-a-wheel")
    profile.strategy = "WHEELHOUSE"
    profile.wheelhouse = "wheels"
    profile.wheel_hashes = {wheel.name: "wrong"}
    profile.python_requirements = ["fake==1.0"]
    with pytest.raises(ValueError, match="digest"):
        DeploymentBuilder()._runtime(root, tmp_path / "stage", profile)


@pytest.mark.parametrize("strategy", ["WHEELHOUSE", "BUNDLED_VENV"])
def test_offline_runtime_installs_and_executes_hashed_wheel(package_project, tmp_path, strategy):
    import os
    import subprocess
    import zipfile

    root, profile = package_project
    wheelhouse = root / "wheels"
    wheelhouse.mkdir()
    wheel = wheelhouse / "auditcore_fixture-1.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("auditcore_fixture.py", "VALUE = 42\n")
        archive.writestr(
            "auditcore_fixture-1.0.dist-info/METADATA",
            "Metadata-Version: 2.1\nName: auditcore-fixture\nVersion: 1.0\n",
        )
        archive.writestr(
            "auditcore_fixture-1.0.dist-info/WHEEL",
            "Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
        )
        archive.writestr("auditcore_fixture-1.0.dist-info/RECORD", "")
    profile.strategy = strategy
    profile.wheelhouse = "wheels"
    profile.wheel_hashes = {wheel.name: digest(wheel.read_bytes())}
    profile.python_requirements = ["auditcore-fixture==1.0"]
    stage = tmp_path / "stage"
    DeploymentBuilder()._runtime(root, stage, profile)
    runtime = stage / "opt/auditcore-fixture/runtime"
    python = runtime / "bin/python3" if strategy == "BUNDLED_VENV" else Path("/usr/bin/python3")
    packages = runtime / "site-packages" if strategy == "BUNDLED_VENV" else runtime
    result = subprocess.run(
        [str(python), "-c", "import auditcore_fixture; print(auditcore_fixture.VALUE)"],
        env={**os.environ, "PYTHONPATH": str(packages)},
        capture_output=True,
        check=True,
        text=True,
    )
    assert result.stdout.strip() == "42"
    if strategy == "BUNDLED_VENV":
        assert "include-system-site-packages = false" in (runtime / "pyvenv.cfg").read_text()
