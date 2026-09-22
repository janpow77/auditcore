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
def migration(git_project, policy_provider, library_context):
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
    policy_provider.evidence = {
        identifier: {
            "status": "VERIFIED",
            "references": ["synthetic test"],
            "source_commit": source.commit_sha,
        }
        for identifier in ("F-07", "F-09")
    }
    refactorer = ApplicationRefactorer(policy_provider)
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
