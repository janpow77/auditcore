"""Every lint rule: catalog integrity plus its positive and negative examples."""

from __future__ import annotations

from pathlib import Path

import pytest
from helper_contracts_support import node_or_skip

from auditcore.tools.helpers.lint import function_findings, run_lint, suppressed_rules
from auditcore.tools.helpers.model import PYTHON, TYPESCRIPT, FunctionInfo, SourceFile
from auditcore.tools.helpers.pyscan import scan_python
from auditcore.tools.helpers.rules import (
    KINDS,
    Rule,
    balanced_args,
    call_hits,
    file_hits,
    innermost,
    load_rules,
    regex_hits,
)
from auditcore.tools.helpers.scan import Inventory
from auditcore.tools.helpers.tsscan import scan_typescript

RULES = load_rules()
EXAMPLES = [
    pytest.param(rule, polarity, index, id=f"{rule.id}-{polarity}-{index}")
    for rule in RULES
    for polarity in ("positive", "negative")
    for index, _ in enumerate(rule.examples.get(polarity, []))
]


def test_catalog_is_consistent() -> None:
    ids = [rule.id for rule in RULES]
    assert len(ids) == len(set(ids))
    for rule in RULES:
        assert rule.kind in KINDS
        assert rule.message and rule.remedy and rule.title, rule.id
        assert set(rule.spec) <= {PYTHON, TYPESCRIPT}, rule.id
        if rule.kind != "probe":
            assert rule.examples.get("positive"), f"{rule.id}: Positivbeispiel fehlt"
            assert rule.examples.get("negative"), f"{rule.id}: Negativbeispiel fehlt"
        for language in rule.spec:
            for key in ("patterns", "body_all", "body_none", "when_all", "unless_any"):
                rule.patterns(language, key)


def _source(language: str, code: str) -> SourceFile:
    return SourceFile("example.py" if language == PYTHON else "example.ts", language, code)


def _functions(file: SourceFile, tmp_path: Path) -> list[FunctionInfo]:
    if file.language == PYTHON:
        return scan_python(file)
    node_or_skip()
    (tmp_path / file.path).write_text(file.text, encoding="utf-8")
    functions, errors = scan_typescript(tmp_path, [file.path])
    assert not errors
    return functions


def hits(rule: Rule, file: SourceFile, tmp_path: Path) -> int:
    if rule.kind == "regex":
        return len(list(regex_hits(rule, file)))
    if rule.kind == "call":
        return len(list(call_hits(rule, file)))
    if rule.kind == "file":
        return len(list(file_hits(rule, file)))
    return len(list(function_findings(rule, _functions(file, tmp_path))))


@pytest.mark.parametrize(("rule", "polarity", "index"), EXAMPLES)
def test_rule_examples(rule: Rule, polarity: str, index: int, tmp_path: Path) -> None:
    example = rule.examples[polarity][index]
    file = _source(str(example["language"]), str(example["code"]))
    found = hits(rule, file, tmp_path)
    if polarity == "positive":
        assert found >= 1, f"{rule.id} erkennt das Positivbeispiel nicht"
    else:
        assert found == 0, f"{rule.id} meldet das Negativbeispiel"


def test_balanced_args_spans_lines_and_nesting() -> None:
    text = "fmt(a, { day: f(x), timeZone: 'Europe/Berlin' }) + rest"
    assert balanced_args(text, 4) == "a, { day: f(x), timeZone: 'Europe/Berlin' }"


def test_multiline_intl_options_with_timezone_pass() -> None:
    rule = next(r for r in RULES if r.id == "HC-DATE-01")
    code = (
        "const f = new Intl.DateTimeFormat('de-DE', {\n"
        "  day: '2-digit',\n  timeZone: 'Europe/Berlin',\n})\n"
    )
    assert not list(call_hits(rule, _source(TYPESCRIPT, code)))


def test_comment_lines_are_ignored() -> None:
    rule = next(r for r in RULES if r.id == "HC-DATE-02")
    assert not list(regex_hits(rule, _source(TYPESCRIPT, "// new Date('2026-01-31')\n")))


def test_suppression_comment_needs_rule_id() -> None:
    file = _source(TYPESCRIPT, "// auditcore-helpers: ignore HC-ERR-02, HC-DATE-01 Grund\nx()\n")
    assert suppressed_rules(file, 2) == {"HC-ERR-02", "HC-DATE-01"}
    assert suppressed_rules(file, 3) == set()


def test_innermost_function_gets_the_finding() -> None:
    outer = FunctionInfo(TYPESCRIPT, "a.tsx", "Grid", "declaration", 1, 20, 50, "h1", "x")
    inner = FunctionInfo(TYPESCRIPT, "a.tsx", "parse", "variable", 3, 6, 40, "h2", "y")
    other = FunctionInfo(TYPESCRIPT, "b.tsx", "Grid", "declaration", 1, 20, 50, "h1", "x")
    assert innermost([outer, inner, other]) == [inner, other]


def test_disabled_rules_are_not_run(tmp_path: Path) -> None:
    file = _source(TYPESCRIPT, "const d = new Date('2026-01-31')\n")
    inventory = Inventory(tmp_path, [file], [])
    active = [r for r in RULES if r.id == "HC-DATE-02"]
    assert len(run_lint(inventory, None, {}, rules=active).findings) == 1
    result = run_lint(inventory, None, {"HC-DATE-02": "Altlast, Umstellung geplant"}, rules=active)
    assert result.findings == [] and result.disabled
