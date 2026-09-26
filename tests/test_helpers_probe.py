"""Probe rules execute detected helpers standalone (BeleglisteGrid, time zones)."""

from __future__ import annotations

from pathlib import Path

from helper_contracts_support import CASES, FIXTURES, node_or_skip

from auditcore.tools.helpers.cases import load_cases
from auditcore.tools.helpers.lint import run_lint
from auditcore.tools.helpers.model import PYTHON, SourceFile
from auditcore.tools.helpers.probe import run_probe
from auditcore.tools.helpers.pyrunner import decode, encode
from auditcore.tools.helpers.pyscan import scan_python
from auditcore.tools.helpers.rules import load_rules
from auditcore.tools.helpers.scan import collect

LIBRARY = load_cases(CASES)
RULES = {rule.id: rule for rule in load_rules()}


def test_python_parser_is_executed_against_the_contract(tmp_path: Path) -> None:
    code = (
        "def to_betrag(text):\n    value = float(text.replace(',', '.'))\n    return value\n\n"
        "def parse_zahl(text):\n    return float(UNKNOWN(text).replace(',', '.'))\n"
    )
    functions = scan_python(SourceFile("n.py", PYTHON, code))
    findings, stats = run_probe(RULES["HC-NUM-10"], functions, LIBRARY, tmp_path)
    assert stats.candidates == 2 and stats.isolated == 1
    assert "parse_zahl" in stats.not_isolated[0]
    [finding] = findings
    assert "to_betrag" in finding.message and "1234.56" in finding.message


def test_fixture_bugs_are_found_by_execution() -> None:
    node_or_skip()
    inventory = collect(FIXTURES / "buggy", [])
    result = run_lint(inventory, LIBRARY, {})
    by_rule: dict[str, set[str]] = {}
    for finding in result.findings:
        by_rule.setdefault(finding.rule, set()).add(finding.path)
    assert "frontend/src/components/BeleglisteGrid.tsx" in by_rule["HC-NUM-10"]
    assert by_rule["HC-DATE-10"] == {
        "frontend/src/lib/format.ts",
        "frontend/src/views/ListView.vue",
    }
    grid = next(f for f in result.findings if f.rule == "HC-NUM-10" and "Grid" in f.path)
    assert "1.234 statt 1234.56" in grid.message
    date = next(f for f in result.findings if f.rule == "HC-DATE-10" and f.path.endswith(".ts"))
    assert "America/New_York" in date.message and "30.01.2026" in date.message
    assert [f.rule for f in result.suppressed] == ["HC-ERR-02"]
    assert result.probe.isolated == result.probe.candidates


def test_runner_value_encoding_round_trip() -> None:
    decoded = decode(
        [{"$nan": True}, {"$date": "2026-01-31T23:30:00Z"}, {"$error": "x"}, {"a": [1]}]
    )
    assert isinstance(decoded, list)
    assert encode(decoded[0]) == {"$nan": True}
    assert encode(decoded[1]) == {"$date": "2026-01-31T23:30:00+00:00"}
    assert encode(decoded[3]) == {"a": [1]}
    assert encode(object()).startswith("<object")
