"""Real synthetic migrations, characterization and rollback verification."""

import json
import sys
from dataclasses import replace

import pytest

from auditcore.exceptions import MigrationBlocked
from auditcore.tools.apprefactor.characterization import characterize, compare
from auditcore.tools.apprefactor.engine import (
    REQUIRED_VERIFICATION,
    ApplicationRefactorer,
    compatibility_wrapper,
    replace_imports,
    source_digest,
    verify,
)
from auditcore.tools.apprefactor.models import CharacterizationCase
from auditcore.tools.common import digest
from auditcore.tools.policy import evidence_binding
from auditcore.tools.policy.framework import context_from_project


def _attest_synthetic_fixture(provider, root):
    """Bind synthetic unit-test attestations; not evidence for any real application."""
    from auditcore.tools.common import write_json

    binding = evidence_binding(root, provider.artifact, context_from_project(root))
    write_json(
        root / ".auditcore/policy-evidence.json",
        {
            identifier: {
                "status": "VERIFIED",
                "references": ["synthetic migration fixture only"],
                "source_commit": provider.load_requirements().commit_sha,
                **binding,
            }
            for identifier in ("F-07", "F-09")
        },
    )


def test_import_replacement_preserves_aliases_comments_and_other_symbols():
    source = (
        "# comment\n"
        "from legacy import normalize as clean, other\n"
        'x = "from legacy import normalize"\n'
    )
    result = replace_imports(source, "legacy", "auditcore.documents", "normalize")
    assert "from legacy import other" in result
    assert "from auditcore.documents import normalize as clean" in result
    assert "# comment" in result and '"from legacy import normalize"' in result


def test_wrapper_preserves_call_signature():
    source = "def f(x, /, y=2, *args, z=3, **kwargs):\n    return x\n"
    result = compatibility_wrapper(source, "f", "auditcore.documents:f")
    assert "def f(x, /, y=2, *args, z=3, **kwargs)" in result
    assert "_auditcore_target(x, y, *args, z=z, **kwargs)" in result


def test_characterization_and_mismatch(git_project):
    root = git_project
    (root / "shared.py").write_text("def normalize(value):\n    return value.upper()\n")
    cases = [
        CharacterizationCase("whitespace", [" hello "], {}),
        CharacterizationCase("empty", [""], {}),
        CharacterizationCase("invalid", [None], {}),
    ]
    golden = root / "golden.json"
    result = characterize(root, "legacy:normalize", cases, golden, root / "legacy.py")
    assert result["outcomes"][0]["value"] == "hello"
    assert result["outcomes"][2]["exception"] == "builtins.AttributeError"
    assert (
        compare(root, "shared:normalize", golden, root / "shared.py").status == "MIGRATION_BLOCKED"
    )


def test_missing_verification_not_pass(git_project):
    result = verify(git_project, {})
    assert result["status"] == "MIGRATION_BLOCKED"
    assert all(r["status"] == "NOT_EXECUTED" for r in result["checks"].values())


@pytest.fixture
def migration(git_project, policy_provider, library_context, monkeypatch):
    root = git_project
    (root / "shared.py").write_text("def normalize(value):\n    return value.strip()\n")
    golden = root / "golden.json"
    characterize(
        root,
        "legacy:normalize",
        [CharacterizationCase("spaces", [" x "], {})],
        golden,
        root / "legacy.py",
    )
    source = policy_provider.load_requirements()
    policy_provider._loaded = replace(source, source_status="POLICY_SOURCE_CURRENT")
    refactorer = ApplicationRefactorer(policy_provider)
    original_plan = refactorer.plan

    def bound_plan(root, *args, **kwargs):
        _attest_synthetic_fixture(policy_provider, root)
        return original_plan(root, *args, **kwargs)

    def bound_verification(root, commands):
        result = verify(root, commands)
        if result["status"] == "PASS":
            _attest_synthetic_fixture(policy_provider, root)
        return result

    monkeypatch.setattr(refactorer, "plan", bound_plan)
    monkeypatch.setattr("auditcore.tools.apprefactor.engine.verify", bound_verification)
    plan = refactorer.plan(root)
    plan.files_to_change = ["legacy.py"]
    plan.wrappers_to_create = [
        {
            "path": "legacy.py",
            "symbol": "normalize",
            "target": "shared:normalize",
            "target_root": str(root),
            "target_file": str(root / "shared.py"),
            "characterization": "golden.json",
        }
    ]
    command = [sys.executable, "-c", 'from legacy import normalize; assert normalize(" x ") == "x"']
    plan.verification_commands = {category: command for category in REQUIRED_VERIFICATION}
    return refactorer, plan, root


def test_dry_run_no_file_writes(migration):
    refactorer, plan, root = migration
    before = {str(p): digest(p.read_bytes()) for p in root.rglob("*") if p.is_file()}
    report = refactorer.apply(plan, dry_run=True)
    after = {str(p): digest(p.read_bytes()) for p in root.rglob("*") if p.is_file()}
    assert report["status"] == "DRY_RUN_COMPLETE" and before == after
    assert "_auditcore_target" in report["diffs"]["legacy.py"]


def test_actual_migration_and_verification(migration):
    refactorer, plan, root = migration
    result = refactorer.apply(plan)
    assert result["status"] == "VERIFIED"
    assert "_auditcore_target" in (root / "legacy.py").read_text()
    assert (root / ".auditcore/refactor-result.json").exists()


def test_failed_consumer_test_rolls_back(migration):
    refactorer, plan, root = migration
    original = (root / "legacy.py").read_bytes()
    plan.verification_commands["integration"] = [sys.executable, "-c", "raise SystemExit(1)"]
    with pytest.raises(MigrationBlocked):
        refactorer.apply(plan)
    assert (root / "legacy.py").read_bytes() == original


def test_stale_plan_blocked(migration):
    refactorer, plan, root = migration
    (root / "legacy.py").write_text("changed = True\n")
    with pytest.raises(MigrationBlocked, match="Source changed"):
        refactorer.apply(plan, dry_run=True)


def test_stale_golden_blocked(migration):
    refactorer, plan, root = migration
    golden = json.loads((root / "golden.json").read_text())
    golden["source_digest"] = "wrong"
    (root / "golden.json").write_text(json.dumps(golden))
    with pytest.raises(MigrationBlocked, match="stale|Source changed"):
        refactorer.apply(plan)


def test_security_boundary_not_removed(migration):
    refactorer, plan, root = migration
    (root / "legacy.py").write_text(
        "def normalize(value):\n    authorize(value)\n    return value\n"
    )
    plan.source_digest = source_digest(root)
    with pytest.raises(MigrationBlocked, match="SECURITY_OR_POLICY"):
        refactorer.apply(plan, dry_run=True)


def test_path_escape_blocked(migration):
    refactorer, plan, root = migration
    plan.wrappers_to_create[0]["path"] = "../other.py"
    with pytest.raises(ValueError):
        refactorer.apply(plan, dry_run=True)


def test_explicit_type_improvement_retains_body():
    from auditcore.tools.apprefactor.optimization import annotate_function

    source = 'def total(x):\n    """Total."""\n    return x + 1\n'
    result = annotate_function(source, "total", {"x": "int", "return": "int"})
    assert "def total(x: int) -> int:" in result
    assert "return x + 1" in result


def test_dependency_edit_round_trip(tmp_path):
    from auditcore.tools.apprefactor.optimization import edit_dependencies

    path = tmp_path / "pyproject.toml"
    path.write_text('[project]\nname = "example"\ndependencies = ["old>=1", "retained==2"]\n')
    output = edit_dependencies(path, ["old"], ["auditcore==0.1.0"])
    import tomllib

    assert tomllib.loads(output)["project"]["dependencies"] == ["retained==2", "auditcore==0.1.0"]


def test_benchmark_reports_actual_equality_and_allocations():
    from auditcore.tools.apprefactor.optimization import benchmark

    result = benchmark(sum, ([1, 2, 3],), repeat=3)
    assert result["result"] == 6 and result["seconds_per_call"] >= 0 and result["peak_bytes"] > 0


def test_dependency_extras_brackets_are_not_array_end(tmp_path):
    import tomllib

    from auditcore.tools.apprefactor.optimization import edit_dependencies

    path = tmp_path / "pyproject.toml"
    path.write_text(
        '[project]\nname="example"\ndependencies = [\n "pkg[extra]>=1", # ]\n "other",\n]\n'
    )
    result = edit_dependencies(path, ["other"], ["auditcore==0.1.0"])
    assert tomllib.loads(result)["project"]["dependencies"] == ["pkg[extra]>=1", "auditcore==0.1.0"]


def test_handoff_requires_current_deployment_evidence(migration):
    from auditcore.tools.common import DEPLOYMENT_CHECKS, write_json

    refactorer, plan, root = migration
    refactorer.apply(plan)
    with pytest.raises(MigrationBlocked, match="Deployment evidence"):
        refactorer.handoff(root)
    evidence = {
        "checks": {
            name: {"status": "PASS", "reference": "synthetic", "reason": "controlled fixture"}
            for name in DEPLOYMENT_CHECKS
        }
    }
    write_json(root / "auditcore-deployment-evidence.json", evidence)
    evidence["source_digest"] = source_digest(root)
    write_json(root / "auditcore-deployment-evidence.json", evidence)
    result_path = root / ".auditcore/refactor-result.json"
    result = json.loads(result_path.read_text())
    result["source_digest"] = source_digest(root)
    write_json(result_path, result)
    _attest_synthetic_fixture(refactorer.framework, root)
    assert refactorer.handoff(root)["status"] == "READY_FOR_DEPLOYMENT"
    assert (root / ".auditcore/deployment-handoff.json").exists()
    (root / "legacy.py").write_text("changed = True\n")
    with pytest.raises(MigrationBlocked, match="stale"):
        refactorer.handoff(root)


@pytest.fixture
def class_migration(migration):
    refactorer, _, root = migration
    implementation = (
        "class TestDataGenerator:\n"
        "    def __init__(self, prefix, suffix='!'):\n"
        "        self.prefix, self.suffix = prefix, suffix\n"
        "    def generate_rows(self, count):\n"
        "        return [self.prefix + str(i) + self.suffix for i in range(count)]\n"
    )
    (root / "generator.py").write_text(implementation)
    (root / "auditcore_dummygenerator.py").write_text(implementation)
    (root / "main.py").write_text("from generator import TestDataGenerator\n")
    characterize(
        root,
        "generator:TestDataGenerator",
        [
            CharacterizationCase(
                "rows",
                [2],
                {},
                method="generate_rows",
                constructor_args=["row"],
                constructor_kwargs={"suffix": "."},
            )
        ],
        root / "class-golden.json",
        root / "generator.py",
    )
    plan = refactorer.plan(root, {"auditcore_dummygenerator": "0.1.0"})
    plan.files_to_change = ["main.py"]
    plan.imports_to_change = [
        {"path": "main.py", "old": "generator", "new": "auditcore_dummygenerator"}
    ]
    plan.characterization_checks = [
        {
            "path": "generator.py",
            "characterization": "class-golden.json",
            "target": "auditcore_dummygenerator:TestDataGenerator",
            "target_root": str(root),
            "target_file": str(root / "auditcore_dummygenerator.py"),
        }
    ]
    command = [
        sys.executable,
        "-c",
        "from main import TestDataGenerator; "
        "assert TestDataGenerator('row', suffix='.').generate_rows(2) == ['row0.', 'row1.']",
    ]
    plan.verification_commands = {category: command for category in REQUIRED_VERIFICATION}
    return refactorer, plan, root


def test_class_import_migration_without_wrapper(class_migration):
    refactorer, plan, root = class_migration
    original = (root / "generator.py").read_bytes()
    result = refactorer.apply(plan)
    assert result["status"] == "VERIFIED"
    assert result["shared_libraries"] == {"auditcore_dummygenerator": "0.1.0"}
    assert (
        root / "main.py"
    ).read_text() == "from auditcore_dummygenerator import TestDataGenerator\n"
    assert (root / "generator.py").read_bytes() == original
    assert not plan.wrappers_to_create


def test_class_import_requires_characterization(class_migration):
    refactorer, plan, root = class_migration
    plan.characterization_checks = []
    with pytest.raises(MigrationBlocked, match="characterization"):
        refactorer.apply(plan)
    assert (root / "main.py").read_text() == "from generator import TestDataGenerator\n"


def test_class_behavior_change_after_apply_rolls_back(class_migration):
    refactorer, plan, root = class_migration
    original = (root / "main.py").read_bytes()
    plan.verification_commands["quality"] = [
        sys.executable,
        "-c",
        "from pathlib import Path; p=Path('auditcore_dummygenerator.py'); "
        "p.write_text(p.read_text().replace('range(count)', 'range(count + 1)'))",
    ]
    with pytest.raises(MigrationBlocked, match="replacement behavior changed"):
        refactorer.apply(plan)
    assert (root / "main.py").read_bytes() == original


def test_plan_does_not_invent_library_version(migration):
    refactorer, _, root = migration
    assert refactorer.plan(root).target_shared_libraries == {}


def test_plan_cli_records_explicit_package(git_project, capsys):
    from auditcore.tools.apprefactor.cli import main

    assert main(["plan", str(git_project), "--library", "auditcore_fixture==1.0.0"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["target_shared_libraries"] == {"auditcore_fixture": "1.0.0"}


def test_plan_cli_rejects_unpinned_library(git_project, capsys):
    from auditcore.tools.apprefactor.cli import main

    assert main(["plan", str(git_project), "--library", "auditcore_fixture"]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "MIGRATION_BLOCKED"
