"""Compact findings report for pull requests (``auditcore-codegate report``).

Agents and reviewers read this report instead of the source: failing tests with a
minimal trace, architecture-test failures, ratchet verdicts, coverage and public API
breaks against a git revision. The Markdown form is capped at ``MAX_LINES`` lines.
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
import xml.etree.ElementTree as ElementTree
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path

from auditcore.tools.quality.codegate import discover_packages
from auditcore.tools.quality.scanners import api_snapshot

MAX_LINES = 200
MAX_TRACE_LINES = 3
ARCHITECTURE_TESTS = ("test_architecture", "test_workflow_runner_guard", "test_warnings_usage")
LOCATION = re.compile(r"^(?P<file>[^\s:]+\.py):(?P<line>\d+):")
LOW_COVERAGE = 50.0

Snapshot = dict[str, dict[str, str]]


@dataclass(frozen=True)
class FailedTest:
    """One failed or errored test case, reduced to what is needed to fix it."""

    test: str
    kind: str
    location: str
    message: str
    trace: list[str]

    @property
    def architecture(self) -> bool:
        return any(marker in self.test for marker in ARCHITECTURE_TESTS)


@dataclass(frozen=True)
class ApiChange:
    """A public symbol that was removed, changed or added against the revision."""

    symbol: str
    change: str


@dataclass
class Findings:
    """All inputs of the report in normalized form."""

    tests_total: int = 0
    failures: list[FailedTest] = field(default_factory=list)
    verdicts: list[dict[str, object]] = field(default_factory=list)
    gate_status: str = "NOT_EXECUTED"
    coverage_total: float | None = None
    coverage_low: list[tuple[str, float]] = field(default_factory=list)
    api_changes: list[ApiChange] = field(default_factory=list)
    api_compared_to: str = ""

    @property
    def status(self) -> str:
        breaking = any(change.change != "added" for change in self.api_changes)
        if self.failures or self.gate_status == "FAIL" or breaking:
            return "FAIL"
        return "WARN" if self.gate_status == "WARN" else "PASS"

    def to_dict(self) -> dict[str, object]:
        """Serialize for ``report.json``."""
        return {
            "scope": "AUDITCORE_FINDINGS_REPORT",
            "status": self.status,
            "tests": {"total": self.tests_total, "failures": [asdict(f) for f in self.failures]},
            "gate": {"status": self.gate_status, "verdicts": self.verdicts},
            "coverage": {
                "total_percent": self.coverage_total,
                "low_files": [{"file": f, "percent": p} for f, p in self.coverage_low],
            },
            "api": {
                "compared_to": self.api_compared_to,
                "changes": [asdict(change) for change in self.api_changes],
            },
        }


def _trace(text: str) -> tuple[str, list[str]]:
    """Innermost repository location and the first assertion lines of a failure text."""
    location = ""
    for line in text.splitlines():
        match = LOCATION.match(line.strip())
        if match and "site-packages" not in match["file"]:
            location = f"{match['file']}:{match['line']}"
    errors = [line[2:].strip() for line in text.splitlines() if line.startswith("E ")]
    return location, [line for line in errors if line][:MAX_TRACE_LINES]


def read_junit(path: Path) -> tuple[int, list[FailedTest]]:
    """Count test cases and collect failures and errors of one JUnit XML file."""
    root = ElementTree.parse(path).getroot()
    total, failures = 0, []
    for case in root.iter("testcase"):
        total += 1
        for kind in ("failure", "error"):
            node = case.find(kind)
            if node is None:
                continue
            name = f"{case.get('classname', '')}::{case.get('name', '')}".strip(":")
            location, trace = _trace(node.text or "")
            message = (node.get("message") or "").splitlines()[0:1]
            failures.append(FailedTest(name, kind, location, "".join(message)[:200], trace))
    return total, failures


def read_gate(path: Path) -> tuple[str, list[dict[str, object]]]:
    """Status and open verdicts of a ``codegate check --output`` report."""
    report = json.loads(path.read_text(encoding="utf-8"))
    verdicts = [v for v in report.get("verdicts", []) if v.get("status") != "PASS"]
    return str(report.get("status", "NOT_EXECUTED")), verdicts


def read_coverage(path: Path, limit: int = 10) -> tuple[float, list[tuple[str, float]]]:
    """Total coverage and the least covered files of a coverage.py JSON report."""
    report = json.loads(path.read_text(encoding="utf-8"))
    total = float(report["totals"]["percent_covered"])
    files = [
        (name, float(data["summary"]["percent_covered"]))
        for name, data in report.get("files", {}).items()
        if data["summary"].get("num_statements", 0) > 0
    ]
    low = sorted((f for f in files if f[1] < LOW_COVERAGE), key=lambda f: f[1])
    return total, [(name, round(percent, 1)) for name, percent in low[:limit]]


def _git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments], cwd=root, capture_output=True, text=True, check=True
    )
    return result.stdout


def _python_roots(root: Path) -> list[Path]:
    return [p.path for p in discover_packages(root) if p.kind == "python"]


def _sources_at(root: Path, ref: str | None) -> dict[str, str]:
    """Public Python sources of all packages, keyed relative to their ``src`` directory."""
    sources: dict[str, str] = {}
    for src in _python_roots(root):
        relative = src.relative_to(root).as_posix()
        if ref is None:
            files = {p.relative_to(src).as_posix(): p for p in src.rglob("*.py")}
            sources.update({k: v.read_text(encoding="utf-8") for k, v in files.items()})
            continue
        for name in _git(root, "ls-tree", "-r", "--name-only", ref, "--", relative).split():
            if name.endswith(".py"):
                key = name.removeprefix(relative + "/")
                sources[key] = _git(root, "show", f"{ref}:{name}")
    return sources


def _snapshot(sources: dict[str, str]) -> Snapshot:
    parseable = {}
    for path, text in sources.items():
        try:
            ast.parse(text)
        except SyntaxError:
            continue
        parseable[path] = text
    return api_snapshot(parseable)


def diff_api(before: Snapshot, after: Snapshot) -> list[ApiChange]:
    """Removed and changed public symbols (breaks) plus added ones (information)."""
    changes = [ApiChange(name, "removed") for name in before if name not in after]
    changed = [name for name in before if name in after and before[name] != after[name]]
    changes += [ApiChange(name, "changed") for name in changed]
    changes += [ApiChange(name, "added") for name in after if name not in before]
    return sorted(changes, key=lambda change: (change.change != "removed", change.symbol))


def api_changes(root: Path, ref: str) -> list[ApiChange]:
    """Compare the public API of the working tree with ``ref``."""
    return diff_api(_snapshot(_sources_at(root, ref)), _snapshot(_sources_at(root, None)))


def collect(
    junit: Iterable[Path],
    gate: Path | None,
    coverage: Path | None,
    api: tuple[Path, str] | None,
) -> Findings:
    """Read all available inputs; missing inputs stay ``NOT_EXECUTED``/empty."""
    findings = Findings()
    for path in junit:
        total, failures = read_junit(path)
        findings.tests_total += total
        findings.failures += failures
    if gate is not None:
        findings.gate_status, findings.verdicts = read_gate(gate)
    if coverage is not None:
        findings.coverage_total, findings.coverage_low = read_coverage(coverage)
    if api is not None:
        root, ref = api
        findings.api_changes = api_changes(root, ref)
        findings.api_compared_to = ref
    return findings


def _failure_lines(failures: list[FailedTest], title: str) -> list[str]:
    if not failures:
        return []
    lines = [f"### {title} ({len(failures)})", ""]
    for failure in failures:
        where = f" – `{failure.location}`" if failure.location else ""
        lines.append(f"- **{failure.test}** ({failure.kind}){where}")
        lines += [f"  - `{line[:160]}`" for line in failure.trace or [failure.message]]
    return lines + [""]


def _gate_lines(findings: Findings) -> list[str]:
    lines = [f"### Ratchet: {findings.gate_status}", ""]
    for verdict in findings.verdicts:
        lines.append(
            f"- {verdict.get('status')} {verdict.get('package')} {verdict.get('metric')}: "
            f"{verdict.get('baseline')} → {verdict.get('current')} ({verdict.get('message')})"
        )
    return lines + [""]


def _coverage_lines(findings: Findings) -> list[str]:
    if findings.coverage_total is None:
        return []
    lines = [f"### Coverage: {findings.coverage_total:.1f} %", ""]
    lines += [f"- {name}: {percent} %" for name, percent in findings.coverage_low]
    return lines + [""]


def _api_lines(findings: Findings) -> list[str]:
    if not findings.api_compared_to:
        return []
    breaks = [c for c in findings.api_changes if c.change != "added"]
    added = len(findings.api_changes) - len(breaks)
    lines = [f"### Öffentliche API gegen {findings.api_compared_to}", ""]
    lines += [f"- {c.change}: `{c.symbol}`" for c in breaks]
    lines.append(f"- neu: {added} Symbole" if added else "- keine neuen Symbole")
    return lines + [""]


def render_markdown(findings: Findings, max_lines: int = MAX_LINES) -> str:
    """Compact Markdown report, truncated to ``max_lines`` lines."""
    architecture = [f for f in findings.failures if f.architecture]
    tests = [f for f in findings.failures if not f.architecture]
    lines = [
        f"## Befundbericht: {findings.status}",
        "",
        f"Tests: {findings.tests_total}, fehlgeschlagen: {len(findings.failures)}",
        "",
    ]
    lines += _failure_lines(architecture, "Architektur- und Regeltests")
    lines += _failure_lines(tests, "Fehlgeschlagene Tests")
    lines += _gate_lines(findings) + _coverage_lines(findings) + _api_lines(findings)
    if len(lines) > max_lines:
        hidden = len(lines) - (max_lines - 1)
        lines = lines[: max_lines - 1] + [f"… {hidden} weitere Zeilen in report.json"]
    return "\n".join(lines).rstrip() + "\n"
