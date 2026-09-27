"""auditcore-codegate report: compact findings from JUnit, gate, coverage and API diff."""

import json
import subprocess
from pathlib import Path

from auditcore.tools.quality.codegate_cli import main
from auditcore.tools.quality.codegate_report import (
    ApiChange,
    FailedTest,
    Findings,
    collect,
    diff_api,
    gate_hits,
    read_coverage,
    read_junit,
    render_markdown,
)

JUNIT = """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest" tests="3">
  <testcase classname="tests.test_a" name="test_ok" time="0.01"/>
  <testcase classname="tests.test_a" name="test_bad" time="0.02">
    <failure message="AssertionError: assert 1 == 2">def test_bad():
&gt;       assert 1 == 2
E       assert 1 == 2
E        +  where 1 = f()

/usr/lib/python3/site-packages/x.py:9: in helper
tests/test_a.py:12: AssertionError</failure>
  </testcase>
  <testcase classname="tests.test_architecture" name="test_imports" time="0.01">
    <error message="ImportError: forbidden">E   ImportError: forbidden
src/pkg/mod.py:3: ImportError</error>
  </testcase>
</testsuite></testsuites>
"""


def write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_junit_failures_have_minimal_trace(tmp_path):
    total, failures = read_junit(write(tmp_path / "j.xml", JUNIT))
    assert total == 3
    bad, arch = failures
    assert bad.test == "tests.test_a::test_bad"
    assert bad.location == "tests/test_a.py:12"
    assert bad.trace == ["assert 1 == 2", "+  where 1 = f()"]
    assert not bad.architecture
    assert arch.kind == "error" and arch.architecture
    assert arch.location == "src/pkg/mod.py:3"


def test_coverage_lists_low_files_only(tmp_path):
    report = {
        "totals": {"percent_covered": 81.25},
        "files": {
            "a.py": {"summary": {"percent_covered": 20.0, "num_statements": 10}},
            "b.py": {"summary": {"percent_covered": 95.0, "num_statements": 10}},
            "c.py": {"summary": {"percent_covered": 0.0, "num_statements": 0}},
        },
    }
    total, low = read_coverage(write(tmp_path / "c.json", json.dumps(report)))
    assert total == 81.25
    assert low == [("a.py", 20.0)]


def test_api_diff_separates_breaks_from_additions():
    before = {"m": {"kind": "module"}, "m.f": {"signature": "a"}, "m.g": {"signature": "x"}}
    after = {"m": {"kind": "module"}, "m.f": {"signature": "a, b"}, "m.h": {"signature": ""}}
    assert diff_api(before, after) == [
        ApiChange("m.g", "removed"),
        ApiChange("m.f", "changed"),
        ApiChange("m.h", "added"),
    ]


def test_status_and_markdown_cap():
    failures = [FailedTest(f"t::{i}", "failure", "t.py:1", "boom", ["x"]) for i in range(300)]
    findings = Findings(tests_total=300, failures=failures)
    assert findings.status == "FAIL"
    markdown = render_markdown(findings, max_lines=50)
    assert len(markdown.splitlines()) == 50
    assert markdown.splitlines()[-1].startswith("…")
    assert Findings(api_changes=[ApiChange("m.h", "added")]).status == "PASS"
    assert Findings(gate_status="WARN").status == "WARN"


def test_collect_reads_gate_verdicts(tmp_path):
    gate = {
        "status": "FAIL",
        "verdicts": [
            {
                "package": "p",
                "metric": "any_usages",
                "baseline": 1,
                "current": 2,
                "status": "FAIL",
                "message": "gestiegen",
            },
            {
                "package": "q",
                "metric": "x",
                "baseline": 0,
                "current": 0,
                "status": "PASS",
                "message": "",
            },
        ],
    }
    findings = collect([], write(tmp_path / "g.json", json.dumps(gate)), None, None)
    assert findings.gate_status == "FAIL"
    assert [v["package"] for v in findings.verdicts] == ["p"]
    assert "any_usages: 1 → 2" in render_markdown(findings)


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    source = root / "src" / "auditcore"
    source.mkdir(parents=True)
    (source / "__init__.py").write_text("")
    (source / "api.py").write_text("def keep(a):\n    return a\n\ndef gone():\n    return 1\n")
    for command in (["init", "-q"], ["add", "."], ["commit", "-qm", "base"]):
        subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@t", *command], cwd=root, check=True
        )
    (source / "api.py").write_text("def keep(a, b):\n    return a\n\ndef new():\n    return 2\n")
    return root


def test_cli_writes_json_and_markdown_with_api_diff(tmp_path, capsys):
    root = _repo(tmp_path)
    junit = write(tmp_path / "j.xml", JUNIT)
    out, md, summary = tmp_path / "r.json", tmp_path / "r.md", tmp_path / "s.md"
    code = main(
        [
            "report",
            "--root",
            str(root),
            "--junit",
            str(junit),
            "--api-compare-ref",
            "HEAD",
            "--output",
            str(out),
            "--markdown",
            str(md),
            "--summary",
            str(summary),
        ]
    )
    assert code == 0
    report = json.loads(out.read_text())
    assert report["status"] == "FAIL"
    changes = {(c["symbol"], c["change"]) for c in report["api"]["changes"]}
    assert ("auditcore.api.gone", "removed") in changes
    assert ("auditcore.api.keep", "changed") in changes
    assert ("auditcore.api.new", "added") in changes
    assert md.read_text() == summary.read_text()
    assert "Architektur- und Regeltests (1)" in md.read_text()
    assert "Befundbericht: FAIL" in capsys.readouterr().out


def test_cli_reports_unreadable_input(tmp_path, capsys):
    broken = write(tmp_path / "j.xml", "<not-xml")
    assert main(["report", "--junit", str(broken), "--output", str(tmp_path / "r.json")]) == 2
    assert "nicht erstellbar" in capsys.readouterr().err


def test_gate_hits_are_line_precise_with_fix(tmp_path):
    gate = {
        "status": "FAIL",
        "verdicts": [
            {
                "package": "auditcore",
                "metric": "any_usages",
                "baseline": 1,
                "current": 2,
                "status": "FAIL",
                "message": "gestiegen",
            }
        ],
        "packages": {
            "auditcore": {
                "findings": [
                    {"metric": "any_usages", "path": "src/a.py", "line": 7, "detail": "typing.Any"},
                    {"metric": "any_usages", "path": "src/b.py", "line": 3, "detail": "typing.Any"},
                    {"metric": "complexity_over_10", "path": "src/a.py", "line": 9, "detail": "f"},
                ]
            }
        },
    }
    path = write(tmp_path / "g.json", json.dumps(gate))
    hits = gate_hits(path, {"src/a.py"})
    assert [(h.path, h.line, h.rule) for h in hits] == [("src/a.py", 7, "any_usages")]
    assert len(gate_hits(path, None)) == 2
    findings = Findings(gate_status="FAIL", rule_hits=hits)
    line = (
        "- `src/a.py:7` [any_usages] typing.Any → konkreten Typ, TypedDict oder Protocol statt Any"
    )
    assert line in render_markdown(findings)
