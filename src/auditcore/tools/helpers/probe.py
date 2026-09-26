"""Probe rules: execute detected helpers standalone.

A probe candidate is a top-level or nested function (no method) whose
normalised name and body match the rule. It is executed without its app: only
standard-library imports, literal module constants and module-level functions
it references are available. Functions that need more are reported as "not
isolated" and skipped, never as findings.

Two comparisons exist: against the expectations of the rule's contract
(default), or - with ``timezones`` in the spec - between runs in different
process time zones, which reveals time-zone dependent date formatting
independently of the output format.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from auditcore.tools.helpers.cases import Case, CaseLibrary
from auditcore.tools.helpers.catalog import normalised_name
from auditcore.tools.helpers.compare import Outcome, compare, show
from auditcore.tools.helpers.contracts import build_args, describe_input
from auditcore.tools.helpers.execute import RunResult, run_python, run_typescript
from auditcore.tools.helpers.model import (
    PYTHON,
    Finding,
    FunctionInfo,
    as_dict,
    as_list,
    as_str,
    str_list,
)
from auditcore.tools.helpers.rules import Rule, function_matches

MAX_DEVIATIONS_SHOWN = 4


@dataclass
class ProbeStats:
    """Counts for the report."""

    candidates: int = 0
    isolated: int = 0
    not_isolated: list[str] = field(default_factory=list)


def candidates(rule: Rule, functions: list[FunctionInfo]) -> list[FunctionInfo]:
    """Functions that the probe rule wants to execute."""
    return [
        function
        for function in functions
        if rule.applies(function.language)
        and function.kind != "method"
        and "." not in function.name
        and function_matches(rule, function, normalised_name(function.name))
    ]


def probe_cases(rule: Rule, language: str, library: CaseLibrary) -> list[Case]:
    """Contract cases selected by the rule for one language."""
    contract = library.contract(rule.contract)
    select = as_dict(rule.option(language, "select"))
    tags = str_list(rule.option(language, "tags"))
    return [
        case
        for case in contract.cases
        if case.selected(select, tags, []) and (not case.languages or language in case.languages)
    ]


def _request(functions: list[FunctionInfo], calls: list[dict[str, object]]) -> dict[str, object]:
    entries = [
        {
            "id": str(i),
            "name": f.name,
            "kind": f.kind,
            "source": f.source,
            "prelude": list(f.prelude),
        }
        for i, f in enumerate(functions)
    ]
    return {"mode": "probe", "functions": entries, "calls": calls}


def _execute(language: str, request: dict[str, object], root: Path, timezone: str) -> RunResult:
    if language == PYTHON:
        return run_python(request, cwd=root, timezone=timezone)
    return run_typescript(request, cwd=root, timezone=timezone)


def _contract_deviations(
    result: str, cases: list[Case], runs: list[dict[str, object]]
) -> list[str]:
    results = as_dict(runs[0].get("results"))
    deviations = []
    for case in cases:
        passed, detail = compare(result, case.expect, Outcome.from_json(results.get(case.id)))
        if not passed:
            deviations.append(f"{describe_input(case)} → {detail}")
    return deviations


def _timezone_deviations(
    zones: list[str], cases: list[Case], runs: list[dict[str, object]]
) -> list[str]:
    deviations = []
    for case in cases:
        outcomes = [Outcome.from_json(as_dict(run.get("results")).get(case.id)) for run in runs]
        shown = [o.error if o.error is not None else show(o.value) for o in outcomes]
        if len(set(shown)) > 1:
            pairs = ", ".join(f"{zone}: {text}" for zone, text in zip(zones, shown, strict=True))
            deviations.append(f"{describe_input(case)} → {pairs}")
    return deviations


def _finding(rule: Rule, function: FunctionInfo, deviations: list[str]) -> Finding:
    shown = "; ".join(deviations[:MAX_DEVIATIONS_SHOWN])
    extra = len(deviations) - MAX_DEVIATIONS_SHOWN
    more = f" (+{extra} weitere)" if extra > 0 else ""
    return Finding(
        rule=rule.id,
        path=function.path,
        line=function.line,
        message=f"{rule.message}: {function.name}: {shown}{more}",
        snippet=function.source.splitlines()[0].strip() if function.source else function.name,
        severity=rule.severity,
        anchor=f"{rule.id}:{function.name}:{function.body_hash}",
    )


@dataclass
class _Group:
    rule: Rule
    language: str
    functions: list[FunctionInfo]
    cases: list[Case]
    zones: list[str]


def _run_group(group: _Group, library: CaseLibrary, root: Path, stats: ProbeStats) -> list[Finding]:
    contract = library.contract(group.rule.contract)
    args = tuple(as_list(group.rule.option(group.language, "args")))
    calls: list[dict[str, object]] = [
        {"id": c.id, "args": build_args(args, contract.params, c)} for c in group.cases
    ]
    request = _request(group.functions, calls)
    raws = [_execute(group.language, request, root, zone) for zone in group.zones]
    stats.candidates += len(group.functions)
    findings = []
    for index, function in enumerate(group.functions):
        runs = [as_dict(raw.results.get(str(index))) for raw in raws]
        failed = next((run for run in runs if run.get("isolated") is not True), None)
        if failed is not None:
            reason = as_str(failed.get("reason"), raws[0].load_error or "nicht ausführbar")
            stats.not_isolated.append(f"{function.path}:{function.line} {function.name}: {reason}")
            continue
        stats.isolated += 1
        if len(group.zones) > 1:
            deviations = _timezone_deviations(group.zones, group.cases, runs)
        else:
            deviations = _contract_deviations(contract.result, group.cases, runs)
        if deviations:
            findings.append(_finding(group.rule, function, deviations))
    return findings


def run_probe(
    rule: Rule, functions: list[FunctionInfo], library: CaseLibrary, root: Path
) -> tuple[list[Finding], ProbeStats]:
    """Execute every candidate of a probe rule and report deviations as findings."""
    stats = ProbeStats()
    findings: list[Finding] = []
    selected = candidates(rule, functions)
    for language in sorted({f.language for f in selected}):
        zones = str_list(rule.option(language, "timezones")) or [library.probe_timezone]
        group = _Group(
            rule,
            language,
            [f for f in selected if f.language == language],
            probe_cases(rule, language, library),
            zones,
        )
        findings.extend(_run_group(group, library, root, stats))
    return findings, stats
