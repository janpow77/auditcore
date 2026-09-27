"""Package-wise coverage ratchet."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from auditcore.tools.quality.codegate_cli import main


def write_repository(root: Path, coverage: float = 75.0) -> Path:
    """Create one discovered package and a matching coverage.py report."""
    source = root / "packages/auditcore_demo/src/auditcore_demo"
    source.mkdir(parents=True)
    (root / "packages/auditcore_demo/pyproject.toml").write_text("[project]\nname='demo'\n")
    (source / "core.py").write_text("value = 1\n")
    (root / "quality").mkdir()
    baseline = {
        "schema_version": 1,
        "tool_versions": {},
        "packages": {"auditcore_demo": {"metrics": {}, "coverage_percent": coverage}},
    }
    (root / "quality/baseline.json").write_text(json.dumps(baseline))
    report = {
        "files": {
            "packages/auditcore_demo/src/auditcore_demo/core.py": {
                "summary": {"covered_lines": 3, "num_statements": 4, "percent_covered": 75.0}
            },
            "tests/test_core.py": {
                "summary": {"covered_lines": 20, "num_statements": 20, "percent_covered": 100.0}
            },
        }
    }
    path = root / "coverage.json"
    path.write_text(json.dumps(report))
    return path


def coverage_gate(root: Path, report: Path, *extra: str) -> int:
    return main(["coverage", "--root", str(root), "--coverage", str(report), *extra])


def test_package_coverage_matches_and_ignores_tests(tmp_path: Path) -> None:
    report = write_repository(tmp_path)
    assert coverage_gate(tmp_path, report) == 0


def test_regression_fails(tmp_path: Path) -> None:
    report = write_repository(tmp_path, 80.0)
    assert coverage_gate(tmp_path, report) == 1


def test_improvement_requires_baseline_update(tmp_path: Path) -> None:
    report = write_repository(tmp_path, 70.0)
    assert coverage_gate(tmp_path, report) == 1
    assert coverage_gate(tmp_path, report, "--update-baseline") == 0
    baseline = json.loads((tmp_path / "quality/baseline.json").read_text())
    assert baseline["packages"]["auditcore_demo"]["coverage_percent"] == 75.0


def test_new_package_must_start_at_full_coverage(tmp_path: Path) -> None:
    report = write_repository(tmp_path)
    baseline_path = tmp_path / "quality/baseline.json"
    baseline = json.loads(baseline_path.read_text())
    del baseline["packages"]["auditcore_demo"]
    baseline["packages"]["auditcore_seeded"] = {"metrics": {}, "coverage_percent": 50.0}
    baseline_path.write_text(json.dumps(baseline))
    assert coverage_gate(tmp_path, report, "--update-baseline") == 1
    updated = json.loads(baseline_path.read_text())
    assert updated["packages"]["auditcore_demo"]["coverage_percent"] == 100.0


def test_baseline_lowering_needs_justification(tmp_path: Path) -> None:
    report = write_repository(tmp_path)
    baseline = json.loads((tmp_path / "quality/baseline.json").read_text())
    reference = {**baseline, "packages": {"auditcore_demo": {"coverage_percent": 80.0}}}
    git = ["git", "-C", str(tmp_path), "-c", "user.name=t", "-c", "user.email=t@invalid"]
    subprocess.run([*git, "init", "-q"], check=True)
    (tmp_path / "quality/baseline.json").write_text(json.dumps(reference))
    subprocess.run([*git, "add", "."], check=True)
    subprocess.run([*git, "commit", "-qm", "baseline"], check=True)
    (tmp_path / "quality/baseline.json").write_text(json.dumps(baseline))
    assert coverage_gate(tmp_path, report, "--compare-ref", "HEAD") == 1
    baseline["packages"]["auditcore_demo"]["coverage_ausnahme_begruendung"] = "bewusste Ausnahme"
    (tmp_path / "quality/baseline.json").write_text(json.dumps(baseline))
    assert coverage_gate(tmp_path, report, "--compare-ref", "HEAD") == 0
