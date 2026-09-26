"""``lint``: apply the declarative rules to the sources and functions of a repository."""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, field

from auditcore.tools.helpers.cases import CaseLibrary
from auditcore.tools.helpers.catalog import normalised_name
from auditcore.tools.helpers.model import Finding, FunctionInfo, SourceFile
from auditcore.tools.helpers.probe import ProbeStats, run_probe
from auditcore.tools.helpers.rules import (
    Hit,
    Rule,
    call_hits,
    file_hits,
    function_matches,
    innermost,
    load_rules,
    regex_hits,
)
from auditcore.tools.helpers.scan import Inventory

SUPPRESS = re.compile(r"auditcore-helpers:\s*ignore\s+([A-Z0-9-]+(?:\s*,\s*[A-Z0-9-]+)*)")
FILE_KINDS = {"regex": regex_hits, "call": call_hits, "file": file_hits}


@dataclass
class LintResult:
    """Findings plus everything that was deliberately not reported."""

    findings: list[Finding] = field(default_factory=list)
    suppressed: list[Finding] = field(default_factory=list)
    disabled: dict[str, str] = field(default_factory=dict)
    probe: ProbeStats = field(default_factory=ProbeStats)
    rules: list[Rule] = field(default_factory=list)


def suppressed_rules(file: SourceFile, line: int) -> set[str]:
    """Rule IDs switched off by a comment on ``line`` or the line before."""
    found: set[str] = set()
    for number in (line - 1, line):
        match = SUPPRESS.search(file.line_text(number))
        if match:
            found.update(item.strip() for item in match.group(1).split(","))
    return found


def _finding(rule: Rule, file: SourceFile, hit: Hit) -> Finding:
    return Finding(
        rule.id, file.path, hit.line, rule.message, hit.snippet, rule.severity, hit.anchor
    )


def file_findings(rule: Rule, files: list[SourceFile]) -> Iterator[Finding]:
    """Findings of text-based rules."""
    matcher = FILE_KINDS[rule.kind]
    for file in files:
        if rule.applies(file.language):
            for hit in matcher(rule, file):
                yield _finding(rule, file, hit)


def function_findings(rule: Rule, functions: list[FunctionInfo]) -> Iterator[Finding]:
    """Findings of function rules, attributed to the innermost matching function."""
    matching = [
        f
        for f in functions
        if rule.applies(f.language) and function_matches(rule, f, normalised_name(f.name))
    ]
    for function in innermost(matching):
        snippet = function.source.splitlines()[0].strip() if function.source else function.name
        message = f"{rule.message} ({function.name})"
        anchor = f"{rule.id}:{function.name}:{function.body_hash}"
        yield Finding(
            rule.id, function.path, function.line, message, snippet, rule.severity, anchor
        )


def _raw_findings(
    rule: Rule, inventory: Inventory, library: CaseLibrary | None, result: LintResult
) -> list[Finding]:
    if rule.kind in FILE_KINDS:
        return list(file_findings(rule, inventory.files))
    if rule.kind == "function":
        return list(function_findings(rule, inventory.functions))
    if library is None:
        return []
    findings, stats = run_probe(rule, inventory.functions, library, inventory.root)
    result.probe.candidates += stats.candidates
    result.probe.isolated += stats.isolated
    result.probe.not_isolated.extend(stats.not_isolated)
    return findings


def run_lint(
    inventory: Inventory,
    library: CaseLibrary | None,
    disabled: dict[str, str],
    *,
    rules: list[Rule] | None = None,
) -> LintResult:
    """Run every enabled rule; probe rules need the case library."""
    active = rules if rules is not None else load_rules()
    result = LintResult(disabled=dict(disabled), rules=active)
    by_path = {file.path: file for file in inventory.files}
    for rule in active:
        if rule.id in disabled:
            continue
        for finding in _raw_findings(rule, inventory, library, result):
            file = by_path.get(finding.path)
            if file is not None and rule.id in suppressed_rules(file, finding.line):
                result.suppressed.append(finding)
            else:
                result.findings.append(finding)
    result.findings.sort(key=lambda f: (f.path, f.line, f.rule))
    return result
