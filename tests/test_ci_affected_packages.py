from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "ci_affected_packages.py"
SPEC = importlib.util.spec_from_file_location("ci_affected_packages", SCRIPT)
assert SPEC and SPEC.loader
affected = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(affected)


def _package(root: Path, name: str, module: str, test: bool = True) -> Path:
    package = root / "packages" / name
    (package / "src" / name).mkdir(parents=True)
    (package / "pyproject.toml").write_text(f'[project]\nname = "{name}"\nversion = "0.1.0"\n')
    (package / "src" / name / f"{module}.py").write_text("value = 1\n")
    (package / "tests").mkdir()
    if test:
        (package / "tests" / f"test_{module}.py").write_text("def test_value(): assert True\n")
    return package


def test_module_test_is_selected_before_package_suite(tmp_path: Path) -> None:
    package = _package(tmp_path, "auditcore_demo", "preise")
    files = ["packages/auditcore_demo/src/auditcore_demo/preise.py"]
    assert affected.select_tests(tmp_path, files) == [package / "tests" / "test_preise.py"]


def test_missing_module_test_falls_back_to_package_suite(tmp_path: Path) -> None:
    package = _package(tmp_path, "auditcore_demo", "preise", test=False)
    files = ["packages/auditcore_demo/src/auditcore_demo/preise.py"]
    assert affected.select_tests(tmp_path, files) == [package / "tests"]
