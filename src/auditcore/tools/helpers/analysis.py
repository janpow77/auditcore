"""Run scan, lint and contracts for one repository and build the JSON report."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from auditcore.tools.helpers.cases import CaseLibrary, find_cases_dir, load_cases
from auditcore.tools.helpers.contracts import BindingRun, run_contracts
from auditcore.tools.helpers.lint import LintResult, run_lint
from auditcore.tools.helpers.manifest import DEFAULT_MANIFEST, Manifest, load_manifest
from auditcore.tools.helpers.model import PYTHON, TYPESCRIPT, HelperToolError
from auditcore.tools.helpers.scan import ScanResult, collect, run_scan

SCAN, LINT, CONTRACTS = "scan", "lint", "contracts"
ALL_STEPS = (SCAN, LINT, CONTRACTS)
TOP_DUPLICATES = 25


@dataclass
class Options:
    """What to analyse and where the shared data lives."""

    root: Path
    steps: tuple[str, ...] = ALL_STEPS
    manifest: Path | None = None
    cases: Path | None = None
    library_root: Path | None = None
    with_node: bool = True


@dataclass
class Analysis:
    """Results of the requested steps."""

    root: Path
    manifest: Manifest
    scan: ScanResult | None = None
    lint: LintResult | None = None
    contracts: list[BindingRun] | None = None
    library: CaseLibrary | None = None
    errors: list[str] = field(default_factory=list)


def default_library_root(cases_dir: Path) -> Path | None:
    """The auditcore checkout that holds the cases directory, if it has packages."""
    root = cases_dir.resolve().parent.parent
    return root if (root / "packages").is_dir() else None


def _library_root(options: Options, library: CaseLibrary | None) -> Path | None:
    if options.library_root is not None:
        return options.library_root
    if library is not None:
        return default_library_root(library.directory)
    try:
        return default_library_root(find_cases_dir(options.cases))
    except HelperToolError:
        return None


def analyse(options: Options) -> Analysis:
    """Run the requested steps."""
    root = options.root.resolve()
    manifest = load_manifest(options.manifest or root / DEFAULT_MANIFEST)
    needs_cases = CONTRACTS in options.steps or LINT in options.steps
    library = load_cases(find_cases_dir(options.cases)) if needs_cases else None
    analysis = Analysis(root, manifest, library=library)
    inventory = collect(root, list(manifest.excludes), with_ts=options.with_node)
    analysis.errors.extend(inventory.errors)
    if SCAN in options.steps:
        analysis.scan = run_scan(
            inventory, _library_root(options, library), with_ts=options.with_node
        )
    if LINT in options.steps:
        analysis.lint = run_lint(inventory, library, manifest.disabled_rules)
    if CONTRACTS in options.steps and library is not None:
        analysis.contracts = run_contracts(manifest, library, root)
    return analysis


def ratchet_counts(analysis: Analysis) -> tuple[Counter[str], dict[str, str]]:
    """Line-independent keys of everything that counts against the baseline."""
    counts: Counter[str] = Counter()
    labels: dict[str, str] = {}
    if analysis.scan is not None:
        for match in analysis.scan.ratcheted:
            counts[match.key] += 1
            labels[match.key] = (
                f"{match.function.path}:{match.function.line} {match.function.name} – "
                f"existiert schon in {match.library} ({match.symbol})"
            )
    if analysis.lint is not None:
        for finding in analysis.lint.findings:
            counts[finding.key] += 1
            labels[finding.key] = f"{finding.rule} {finding.path}:{finding.line} {finding.message}"
    for run in analysis.contracts or []:
        for key, violation in zip(run.keys(), run.violations, strict=True):
            counts[key] += 1
            where = f"{run.binding.contract} ({run.binding.id}) {violation.case}"
            labels[key] = f"Vertrag {where}: {violation.detail}"
    return counts, labels


def _scan_json(scan: ScanResult) -> dict[str, object]:
    functions = scan.inventory.functions
    return {
        "functions": {
            PYTHON: sum(f.language == PYTHON for f in functions),
            TYPESCRIPT: sum(f.language == TYPESCRIPT for f in functions),
        },
        "files": len(scan.inventory.files),
        "library_root": str(scan.library_root) if scan.library_root else None,
        "library_matches": [match.to_dict() for match in scan.matches],
        "duplicate_groups": len(scan.duplicates),
        "top_duplicates": [group.to_dict() for group in scan.duplicates[:TOP_DUPLICATES]],
    }


def _lint_json(lint: LintResult) -> dict[str, object]:
    by_rule = Counter(finding.rule for finding in lint.findings)
    return {
        "rules": [
            {"id": r.id, "title": r.title, "severity": r.severity, "findings": by_rule.get(r.id, 0)}
            for r in lint.rules
        ],
        "findings": [finding.to_dict() for finding in lint.findings],
        "suppressed": [finding.to_dict() for finding in lint.suppressed],
        "disabled": lint.disabled,
        "probe": {
            "candidates": lint.probe.candidates,
            "isolated": lint.probe.isolated,
            "not_isolated": lint.probe.not_isolated,
        },
    }


def to_json(analysis: Analysis) -> dict[str, object]:
    """Machine-readable report of all executed steps."""
    report: dict[str, object] = {
        "scope": "AUDITCORE_HELPER_CONTRACTS",
        "root": str(analysis.root),
        "app": analysis.manifest.app or analysis.root.name,
        "manifest": str(analysis.manifest.path) if analysis.manifest.path else None,
        "errors": analysis.errors,
    }
    if analysis.library is not None:
        report["cases"] = {
            name: {"version": c.version, "status": c.status}
            for name, c in analysis.library.contracts.items()
        }
    if analysis.scan is not None:
        report["scan"] = _scan_json(analysis.scan)
    if analysis.lint is not None:
        report["lint"] = _lint_json(analysis.lint)
    if analysis.contracts is not None:
        report["contracts"] = [run.to_dict() for run in analysis.contracts]
    return report
