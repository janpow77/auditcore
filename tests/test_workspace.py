"""Static workspace catalogs are isolated, persistent and bound to all package inputs."""

import json

import pytest

from auditcore.tools.consolidator.cli import main
from auditcore.tools.consolidator.packages import PackageWorkspace


def project(root, name, dependencies=()):
    root.mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text(
        '[build-system]\nrequires = []\nbuild-backend = "example.backend"\n'
        f'[project]\nname = "{name}"\nversion = "1.2.3"\n'
        f"dependencies = {json.dumps(list(dependencies))}\n"
    )
    source = root / "src" / name.replace("-", "_")
    source.mkdir(parents=True)
    (source / "__init__.py").write_text("def calculate(value: int) -> int:\n    return value + 1\n")
    return root


def test_inventory_separate_packages_api_graph_and_unknown_context(tmp_path):
    project(tmp_path, "platform")
    project(tmp_path / "packages" / "alpha", "example_alpha")
    project(tmp_path / "packages" / "beta", "example-beta", ["example_alpha>=1"])
    workspace = PackageWorkspace(tmp_path)
    result = workspace.inventory()
    assert result["status"] == "REVIEW_REQUIRED"
    assert len(result["packages"]) == 3
    by_name = {p["canonical_name"]: p for p in result["packages"]}
    assert by_name["example-alpha"]["dependencies"] == []
    assert "example_alpha.calculate" in by_name["example-alpha"]["import_api"]
    assert not any("example_alpha" in key for key in by_name["platform"]["import_api"])
    assert by_name["example-alpha"]["applicability"]["context"]["personal_data"] == "UNKNOWN"
    assert result["internal_dependencies"] == [
        {
            "consumer": "example-beta",
            "provider": "example-alpha",
            "group": "runtime",
            "conditional": "FALSE",
        }
    ]
    assert workspace.status()["status"] == "CURRENT"
    assert workspace.inventory()["snapshot_id"] == result["snapshot_id"]
    (tmp_path / "packages/alpha/src/example_alpha/__init__.py").write_text("VALUE = 2\n")
    assert workspace.status()["status"] == "STALE"
    updated = workspace.inventory()
    assert updated["snapshot_id"] != result["snapshot_id"]
    assert len(list((workspace.state / "snapshots").glob("*.json"))) == 2


@pytest.mark.parametrize("duplicate", ["Example.Alpha", "example-alpha"])
def test_duplicate_canonical_distribution_names_rejected(tmp_path, duplicate):
    project(tmp_path, "example_alpha")
    project(tmp_path / "packages" / "other", duplicate)
    with pytest.raises(ValueError, match="Duplicate canonical"):
        PackageWorkspace(tmp_path).inventory()


def test_configuration_evidence_requirements_and_consumers(tmp_path):
    project(tmp_path, "platform")
    (tmp_path / "context.json").write_text('{"artifact_type":"library"}')
    (tmp_path / "origin.json").write_text('{"commit_sha":"observed-revision"}')
    (tmp_path / "requirements.txt").write_text("example_alpha==1.0\n-r shared.txt\n")
    (tmp_path / "auditcore-workspace.toml").write_text(
        '[workspace]\nversion=1\nmembers=["."]\n[[package]]\npath="."\n'
        'source_roots=["src"]\napplicability="context.json"\nprovenance="origin.json"\n'
        'consumers=["owner/application"]\n'
    )
    result = PackageWorkspace(tmp_path).inventory()["packages"][0]
    assert result["consumers"] == ["owner/application"]
    assert result["consumer_status"] == "DECLARED_NOT_VERIFIED"
    assert result["applicability"]["profiles"] == ["LIBRARY"]
    assert result["applicability"]["policy_evaluation"] == "NOT_EXECUTED"
    assert result["requirements_files"][0]["declarations"][1]["name"] == "UNKNOWN"


def test_cycles_fail_but_conditional_dependencies_are_not_assumed_active(tmp_path):
    project(tmp_path, "alpha", ["beta>=1"])
    project(tmp_path / "packages" / "beta", "beta", ["alpha"])
    assert PackageWorkspace(tmp_path).inventory()["status"] == "FAIL"
    assert PackageWorkspace(tmp_path).status()["status"] == "FAIL"
    manifest = tmp_path / "packages/beta/pyproject.toml"
    manifest.write_text(
        manifest.read_text().replace('["alpha"]', "[\"alpha; python_version < '3.0'\"]")
    )
    result = PackageWorkspace(tmp_path).inspect()
    assert result["runtime_cycles"] == []
    assert result["conditional_dependencies_status"] == "REVIEW_REQUIRED"


def test_member_and_source_symlink_escapes_are_rejected(tmp_path):
    root = project(tmp_path / "workspace", "platform")
    outside = project(tmp_path / "outside", "outside")
    (root / "auditcore-workspace.toml").write_text('[workspace]\nmembers=["../outside"]\n')
    with pytest.raises(ValueError):
        PackageWorkspace(root).inspect()
    (root / "auditcore-workspace.toml").unlink()
    (root / "src/platform/leak.py").symlink_to(outside / "src/outside/__init__.py")
    with pytest.raises(ValueError):
        PackageWorkspace(root).inspect()


def test_cli_inventory_and_stale_status(tmp_path, capsys):
    project(tmp_path / "workspace", "platform")
    base = ["--state-dir", str(tmp_path / "state"), "packages"]
    assert main(base + ["status", str(tmp_path / "workspace")]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "NOT_INVENTORIED"
    assert main(base + ["inventory", str(tmp_path / "workspace")]) == 0
    capsys.readouterr()
    assert main(base + ["status", str(tmp_path / "workspace")]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "CURRENT"


def test_state_inside_project_is_not_a_source_change(tmp_path):
    project(tmp_path, "platform")
    workspace = PackageWorkspace(tmp_path, tmp_path / "custom-state")
    workspace.inventory()
    assert workspace.status()["status"] == "CURRENT"


def test_dynamic_version_and_invalid_python_remain_explicit(tmp_path):
    project(tmp_path, "platform")
    manifest = tmp_path / "pyproject.toml"
    manifest.write_text(manifest.read_text().replace('version = "1.2.3"', 'dynamic = ["version"]'))
    (tmp_path / "src/platform/__init__.py").write_text("def broken(:\n")
    package = PackageWorkspace(tmp_path).inspect()["packages"][0]
    assert package["version"] == "UNKNOWN"
    assert package["metadata_status"] == "REVIEW_REQUIRED"
    assert package["api_status"] == "PARTIAL"


def test_requirement_credentials_are_not_persisted(tmp_path):
    credential = "synthetic-value-for-test"
    project(tmp_path, "platform", [f"external @ https://user:{credential}@example.invalid/pkg.whl"])
    result = PackageWorkspace(tmp_path).inventory()
    assert credential not in json.dumps(result)
    assert result["packages"][0]["dependencies"][0]["status"] == "REVIEW_REQUIRED"


def test_configured_evidence_outside_project_affects_its_hash(tmp_path):
    project(tmp_path, "platform")
    project(tmp_path / "packages/other", "other")
    (tmp_path / "context.json").write_text('{"artifact_type":"library"}')
    (tmp_path / "auditcore-workspace.toml").write_text(
        '[[package]]\npath="packages/other"\napplicability="context.json"\n'
    )
    workspace = PackageWorkspace(tmp_path)
    before = workspace.inventory()["packages"][1]["source_sha256"]
    (tmp_path / "context.json").write_text('{"artifact_type":"service"}')
    after = workspace.inspect()["packages"][1]["source_sha256"]
    assert after != before
    assert workspace.status()["status"] == "STALE"


def test_internal_regular_file_alias_binds_content_and_target(tmp_path):
    project(tmp_path, "platform")
    package = project(tmp_path / "packages/other", "other")
    for directory in (tmp_path, package):
        (directory / "docs").mkdir()
        (directory / "docs/spec.md").write_text("Observed specification\n")
        (directory / "SPEC.md").symlink_to("docs/spec.md")
    workspace = PackageWorkspace(tmp_path)
    report = workspace.inventory()
    for item in report["packages"]:
        assert item["files"]["SPEC.md"] == item["files"]["docs/spec.md"]
        assert item["symlinks"]["SPEC.md"]["target"] == "docs/spec.md"
    assert workspace.status()["status"] == "CURRENT"
    (package / "docs/spec.md").write_text("Changed specification\n")
    assert workspace.status()["status"] == "STALE"
    workspace.inventory()
    (package / "docs/equal.md").write_text("Changed specification\n")
    workspace.inventory()
    (package / "SPEC.md").unlink()
    (package / "SPEC.md").symlink_to("docs/equal.md")
    assert workspace.status()["status"] == "STALE"


@pytest.mark.parametrize("kind", ["broken", "directory", "external", "other_package"])
def test_file_alias_exceptions_and_directory_links_still_fail(tmp_path, kind):
    root = project(tmp_path / "workspace", "platform")
    outside = project(tmp_path / "outside", "outside")
    other = project(root / "packages/other", "other")
    targets = {
        "broken": root / "missing",
        "directory": root / "src",
        "external": outside / "pyproject.toml",
        "other_package": other / "pyproject.toml",
    }
    (root / "ALIAS").symlink_to(targets[kind])
    with pytest.raises(ValueError):
        PackageWorkspace(root).inspect()


def test_cli_validation_detail_does_not_expose_sensitive_paths(tmp_path, capsys):
    root = project(tmp_path / "workspace", "platform")
    sensitive_name = "synthetic-private-credential-file"
    (root / sensitive_name).symlink_to(tmp_path / "missing-sensitive-target")
    assert main(["packages", "inventory", str(root)]) == 2
    output = capsys.readouterr().out
    report = json.loads(output)
    assert report["detail"] == "Project contains a broken or cyclic file symlink"
    assert sensitive_name not in output
    assert "missing-sensitive-target" not in output
