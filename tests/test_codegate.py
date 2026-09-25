"""Code-quality ratchet on synthetic mini repositories (no real package data)."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from auditcore.tools.quality.codegate_cli import main
from auditcore.tools.quality.codegate_js import measure_js_package
from auditcore.tools.quality.codegate_python import PackageMeasurement, is_non_english
from auditcore.tools.quality.codegate_ratchet import update_baseline

CLEAN = '"""Clean module."""\n\n\ndef add(left: int, right: int) -> int:\n    return left + right\n'


def complex_function(name: str = "tangled") -> str:
    branches = "".join(f"    if value == {i}:\n        return {i}\n" for i in range(12))
    return f"def {name}(value: int) -> int:\n{branches}    return -1\n"


def make_package(root: Path, name: str, body: str = CLEAN) -> Path:
    package = root / "packages" / name
    source = package / "src" / name
    source.mkdir(parents=True, exist_ok=True)
    (package / "pyproject.toml").write_text(f'[project]\nname = "{name}"\n')
    (source / "__init__.py").write_text('"""Package."""\n')
    (source / "core.py").write_text(body)
    return source / "core.py"


def gate(root: Path, *extra: str) -> int:
    return main(["check", "--root", str(root), "--skip-mypy", *extra])


def baseline(root: Path) -> dict[str, dict[str, dict[str, int]]]:
    return json.loads((root / "quality/baseline.json").read_text())["packages"]


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    make_package(tmp_path, "auditcore_demo", CLEAN + "\n\n" + complex_function())
    assert gate(tmp_path, "--init-baseline") == 0
    assert baseline(tmp_path)["auditcore_demo"]["metrics"]["complexity_over_10"] == 1
    return tmp_path


def test_unchanged_state_passes(repo: Path) -> None:
    assert gate(repo) == 0


def test_increase_fails(repo: Path) -> None:
    module = repo / "packages/auditcore_demo/src/auditcore_demo/core.py"
    module.write_text(module.read_text() + "\n\n" + complex_function("second"))
    assert gate(repo) == 1
    assert gate(repo, "--update-baseline") == 1, "update must never raise the baseline"
    assert baseline(repo)["auditcore_demo"]["metrics"]["complexity_over_10"] == 1


def test_decrease_without_baseline_update_fails_then_update_passes(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (repo / "packages/auditcore_demo/src/auditcore_demo/core.py").write_text(CLEAN)
    assert gate(repo) == 1
    assert "--update-baseline" in capsys.readouterr().out
    assert gate(repo, "--update-baseline") == 0
    assert baseline(repo)["auditcore_demo"]["metrics"]["complexity_over_10"] == 0
    assert gate(repo) == 0


def test_new_package_must_meet_all_standards(repo: Path) -> None:
    make_package(repo, "auditcore_fresh", "from typing import Any\n\n\nX: Any = 1\n")
    assert gate(repo) == 1
    assert gate(repo, "--update-baseline") == 1
    assert baseline(repo)["auditcore_fresh"]["metrics"]["any_usages"] == 0


def test_new_clean_package_passes_without_registration(repo: Path) -> None:
    make_package(repo, "auditcore_fresh")
    assert gate(repo, "--package", "auditcore_fresh") == 0
    assert gate(repo) == 0


def test_removed_package_requires_baseline_update(repo: Path) -> None:
    shutil.rmtree(repo / "packages/auditcore_demo")
    assert gate(repo) == 1
    assert gate(repo, "--update-baseline") == 0
    assert "auditcore_demo" not in baseline(repo)


def test_size_any_and_identifier_metrics(tmp_path: Path) -> None:
    long_body = "\n".join(f"    total += {i}" for i in range(70))
    body = (
        "from typing import Any\n\n\n"
        f"def summe_berechnen(values: Any) -> int:\n    total = 0\n{long_body}\n    return total\n"
        + "\n"
        * 350
    )
    make_package(tmp_path, "auditcore_demo", body)
    output = tmp_path / "report.json"
    assert gate(tmp_path, "--output", str(output)) == 1
    metrics = json.loads(output.read_text())["packages"]["auditcore_demo"]["metrics"]
    assert metrics["modules_over_400_lines"] == 1
    assert metrics["functions_over_60_lines"] == 1
    assert metrics["any_usages"] == 1
    assert metrics["non_english_identifiers"] == 1


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
        check=True,
        capture_output=True,
    )


def test_baseline_raise_needs_visible_justification(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _git(repo, "init", "-q")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "base")
    module = repo / "packages/auditcore_demo/src/auditcore_demo/core.py"
    module.write_text(module.read_text() + "\n\n" + complex_function("second"))
    path = repo / "quality/baseline.json"
    data = json.loads(path.read_text())
    data["packages"]["auditcore_demo"]["metrics"]["complexity_over_10"] = 2
    path.write_text(json.dumps(data))
    assert gate(repo, "--compare-ref", "HEAD") == 1
    assert "ohne ausnahme_begruendung" in capsys.readouterr().out
    entry = data["packages"]["auditcore_demo"]
    entry["ausnahme_begruendung"] = {"complexity_over_10": "Parser-Zustandsautomat, Ticket 1"}
    path.write_text(json.dumps(data))
    assert gate(repo, "--compare-ref", "HEAD") == 0
    assert "ANHEBUNG 1 -> 2, begründet" in capsys.readouterr().out


def test_tool_version_change_is_reported_not_silent() -> None:
    measurement = PackageMeasurement("auditcore_demo", "python", {"mypy_strict_errors": 3})
    old = {
        "schema_version": 1,
        "tool_versions": {"mypy": "1.0"},
        "packages": {"auditcore_demo": {"metrics": {"mypy_strict_errors": 1}}},
    }
    new = update_baseline(old, [measurement], {"mypy": "2.0"}, complete=True)
    entry = new["packages"]["auditcore_demo"]  # type: ignore[index]
    assert entry["metrics"]["mypy_strict_errors"] == 3
    assert "mypy 1.0 -> 2.0" in entry["ausnahme_begruendung"]["mypy_strict_errors"]


def test_js_packages_are_measured(tmp_path: Path) -> None:
    package = tmp_path / "packages-js" / "editor"
    (package / "src").mkdir(parents=True)
    (package / "package.json").write_text("{}")
    (package / "src/a.ts").write_text(
        "/* eslint-disable */\n"
        "const a: any = 1\n"
        "// eslint-disable-next-line @typescript-eslint/no-explicit-any -- external API\n"
        "const b: any = 2\n"
        "// eslint-disable-next-line no-console\n" + "\n" * 400
    )
    (package / "src/View.vue").write_text("<template></template>\n" * 260)
    (package / "node_modules").mkdir()
    (package / "node_modules/huge.js").write_text("x\n" * 900)
    metrics = measure_js_package(package, tmp_path).metrics
    assert metrics == {
        "files_over_400_lines": 1,
        "vue_sfc_over_250_lines": 1,
        "eslint_file_disables": 1,
        "eslint_unjustified_line_disables": 1,
        "explicit_any": 1,
    }
    assert gate(tmp_path) == 1


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("parse_amount", False),
        ("RequestQueue", False),
        ("vram_peak_gib", False),
        ("parse_betrag", True),
        ("KoordinatenFehler", True),
        ("pruefe_laufparameter", True),
        ("größe", True),
        ("_ist_folge", True),
    ],
)
def test_identifier_heuristic(name: str, expected: bool) -> None:
    assert is_non_english(name) is expected


def test_mypy_strict_errors_are_counted(tmp_path: Path) -> None:
    pytest.importorskip("mypy")
    make_package(tmp_path, "auditcore_demo", "def untyped(value):\n    return value\n")
    output = tmp_path / "report.json"
    assert main(["check", "--root", str(tmp_path), "--output", str(output)]) == 1
    metrics = json.loads(output.read_text())["packages"]["auditcore_demo"]["metrics"]
    assert metrics["mypy_strict_errors"] >= 1


def test_first_baseline_against_reference_without_baseline_is_bootstrap(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    make_package(tmp_path, "auditcore_demo", complex_function())
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "before gate")
    assert gate(tmp_path, "--init-baseline") == 0
    assert gate(tmp_path, "--compare-ref", "HEAD") == 0
    assert "Erstanlage der Baseline" in capsys.readouterr().out
    assert gate(tmp_path, "--compare-ref", "no-such-ref") == 2
