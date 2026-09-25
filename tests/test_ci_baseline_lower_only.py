"""Autofix may only commit baseline decreases (scripts/ci_baseline_lower_only.py)."""

import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "ci_baseline_lower_only",
    Path(__file__).resolve().parents[1] / "scripts/ci_baseline_lower_only.py",
)
assert SPEC is not None and SPEC.loader is not None
script = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(script)


def baseline(mypy: str = "1.0", **metrics: int) -> dict[str, object]:
    return {
        "schema_version": 1,
        "tool_versions": {"mypy": mypy, "ruff": "0.1"},
        "packages": {"pkg": {"metrics": {"any_usages": 5, "mypy_strict_errors": 3, **metrics}}},
    }


def run(tmp_path: Path, committed: dict[str, object], updated: dict[str, object]) -> tuple:
    old, new = tmp_path / "old.json", tmp_path / "new.json"
    old.write_text(json.dumps(committed))
    new.write_text(json.dumps(updated))
    code = script.main([str(old), str(new)])
    return code, json.loads(new.read_text())


def test_decrease_is_kept(tmp_path: Path) -> None:
    code, result = run(tmp_path, baseline(), baseline(any_usages=2, mypy_strict_errors=1))
    assert code == 0
    assert result["packages"]["pkg"]["metrics"] == {"any_usages": 2, "mypy_strict_errors": 1}


def test_tool_versions_stay_and_version_bound_metric_is_not_lowered(tmp_path: Path) -> None:
    code, result = run(tmp_path, baseline(), baseline("2.0", any_usages=4, mypy_strict_errors=0))
    assert code == 0
    assert result["tool_versions"]["mypy"] == "1.0"
    assert result["packages"]["pkg"]["metrics"] == {"any_usages": 4, "mypy_strict_errors": 3}


def test_raise_with_justification_is_rejected(tmp_path: Path) -> None:
    updated = baseline("2.0", mypy_strict_errors=9)
    updated["packages"]["pkg"]["ausnahme_begruendung"] = {"mypy_strict_errors": "Werkzeugwechsel"}
    code, result = run(tmp_path, baseline(), updated)
    assert code == 1
    assert result == baseline()


def test_new_package_is_rejected(tmp_path: Path) -> None:
    updated = baseline(any_usages=1)
    updated["packages"]["neu"] = {"metrics": {"any_usages": 0}}
    code, result = run(tmp_path, baseline(), updated)
    assert code == 1
    assert result == baseline()
