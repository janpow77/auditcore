"""Ratchet of helper findings and the ``auditcore-helpers`` command line."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from helper_contracts_support import copy_fixture

from auditcore.tools.helpers.cli import main
from auditcore.tools.helpers.ratchet import (
    compare,
    initial_baseline,
    raises,
    status_of,
    update_baseline,
)


def test_new_and_fixed_keys_fail_until_baseline_is_lowered() -> None:
    baseline = initial_baseline(Counter({"a": 2, "b": 1}))
    assert status_of(compare(Counter({"a": 2, "b": 1}), baseline, {})) == "PASS"
    assert status_of(compare(Counter({"a": 2, "b": 1, "c": 1}), baseline, {})) == "FAIL"
    assert status_of(compare(Counter({"a": 1, "b": 1}), baseline, {})) == "FAIL"
    lowered = update_baseline(baseline, Counter({"a": 1, "c": 5}))
    assert lowered["entries"] == {"a": 1}, "update must never add or raise entries"


def test_baseline_raise_needs_justification() -> None:
    reference = initial_baseline(Counter({"a": 1}))
    raised = initial_baseline(Counter({"a": 2}))
    assert status_of(raises(raised, reference)) == "FAIL"
    raised["ausnahme_begruendung"] = {"a": "Altcode übernommen, Umstellung in #123"}
    assert status_of(raises(raised, reference)) == "WARN"


def _check(repo: Path, *extra: str) -> int:
    empty_library = repo.parent / "keine-bibliothek"
    empty_library.mkdir(exist_ok=True)
    args = [
        "check",
        str(repo),
        "--no-node",
        "--library-root",
        str(empty_library),
        "--format",
        "json",
    ]
    return main([*args, *extra])


def test_check_cycle_on_fixture(tmp_path: Path, capsys) -> None:
    repo = copy_fixture("buggy", tmp_path)
    manifest = repo / ".auditcore/helpers.json"
    data = json.loads(manifest.read_text())
    data["bindings"] = [b for b in data["bindings"] if b["language"] == "python"]
    manifest.write_text(json.dumps(data))
    assert _check(repo) == 1, "without baseline the standard is 0"
    assert _check(repo, "--init-baseline") == 0
    assert _check(repo, "--init-baseline") == 2, "second initialisation is refused"
    assert _check(repo) == 0
    module = repo / "backend/app/numbers.py"
    module.write_text(module.read_text() + '\n\ndef label(v):\n    return f"{v:.2f} EUR"\n')
    assert _check(repo) == 1, "a new hand-made euro format is red"
    module.write_text(module.read_text().replace('return f"{value:.2f} €"', "return str(value)"))
    capsys.readouterr()
    assert _check(repo, "--update-baseline") == 1, "the new finding still is not accepted"
    report = json.loads(capsys.readouterr().out)
    assert report["ratchet"]["status"] == "FAIL"
    module.write_text(module.read_text().replace('return f"{v:.2f} EUR"', "return str(v)"))
    assert _check(repo) == 0


def test_improvement_forces_baseline_update(tmp_path: Path) -> None:
    repo = copy_fixture("buggy", tmp_path)
    (repo / ".auditcore/helpers.json").unlink()
    assert _check(repo, "--init-baseline") == 0
    module = repo / "backend/app/numbers.py"
    module.write_text(module.read_text().replace("csv.writer(", "csv.writer(guard_formula, "))
    assert _check(repo) == 1, "an improvement must be recorded"
    assert _check(repo, "--update-baseline") == 0
    assert _check(repo) == 0


def test_report_files_and_commands(tmp_path: Path, capsys) -> None:
    repo = copy_fixture("buggy", tmp_path)
    output, markdown, summary = tmp_path / "r.json", tmp_path / "r.md", tmp_path / "s.md"
    code = main(
        [
            "lint",
            str(repo),
            "--no-node",
            "--output",
            str(output),
            "--markdown",
            str(markdown),
            "--summary",
            str(summary),
            "--strict",
        ]
    )
    assert code == 1
    report = json.loads(output.read_text())
    assert report["scope"] == "AUDITCORE_HELPER_CONTRACTS"
    assert {f["rule"] for f in report["lint"]["findings"]} >= {
        "HC-NUM-02",
        "HC-CSV-01",
        "HC-MONEY-01",
    }
    assert "### Lint" in markdown.read_text() and summary.read_text()
    assert main(["scan", str(repo), "--no-node", "--library-root", str(tmp_path)]) == 0
    assert main(["rules"]) == 0
    assert "HC-NUM-01" in capsys.readouterr().out
    assert main(["check", str(repo), "--no-node", "--cases", str(tmp_path / "fehlt")]) == 2
