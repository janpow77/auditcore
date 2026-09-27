"""auditcore-codegate: binding code-quality ratchet for all auditcore packages.

``auditcore-codegate check`` measures every package, compares against
``quality/baseline.json`` and fails when a metric grows, when an improvement is
not recorded in the baseline, or when a baseline raise lacks a justification.
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass
from pathlib import Path
from subprocess import CalledProcessError

from auditcore.tools.quality.codegate import (
    discover_packages,
    measure,
    select_packages,
    tool_versions,
)
from auditcore.tools.quality.codegate_coverage import (
    compare_coverage,
    compare_coverage_reference,
    read_package_coverage,
    update_coverage,
)
from auditcore.tools.quality.codegate_python import PackageMeasurement, ToolError
from auditcore.tools.quality.codegate_ratchet import (
    Verdict,
    baseline_from_git,
    compare,
    initial_baseline,
    load_baseline,
    raises,
    update_baseline,
    write_baseline,
)
from auditcore.tools.quality.codegate_report import collect
from auditcore.tools.quality.codegate_report import render_markdown as render_findings

DEFAULT_BASELINE = Path("quality/baseline.json")


def build_parser() -> argparse.ArgumentParser:
    """Define the ``check`` subcommand and its options."""
    parser = argparse.ArgumentParser(prog="auditcore-codegate", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="Pflicht-Gate: Code-Qualitätsmaßstäbe per Ratchet")
    check.add_argument("--root", type=Path, default=Path.cwd())
    check.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    check.add_argument("--package", action="append", default=[], help="Nur dieses Paket")
    check.add_argument("--skip-mypy", action="store_true", help="Schnelllauf (pre-commit)")
    check.add_argument("--compare-ref", help="Git-Revision für die Anhebungsprüfung")
    check.add_argument("--update-baseline", action="store_true", help="Baseline absenken")
    check.add_argument("--init-baseline", action="store_true", help="Erstanlage")
    check.add_argument("--format", choices=["text", "json", "markdown"], default="text")
    check.add_argument("--output", type=Path, help="JSON-Bericht zusätzlich schreiben")
    check.add_argument("--summary", type=Path, help="Markdown-Bericht anhängen")
    coverage = sub.add_parser("coverage", help="Paketweise Testabdeckung per Ratchet")
    coverage.add_argument("--root", type=Path, default=Path.cwd())
    coverage.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    coverage.add_argument("--coverage", type=Path, required=True, help="coverage.py-JSON")
    coverage.add_argument("--package", action="append", default=[], help="Nur dieses Paket")
    coverage.add_argument("--compare-ref", help="Git-Revision für die Absenkungsprüfung")
    coverage.add_argument("--update-baseline", action="store_true", help="Baseline anheben")
    coverage.add_argument("--output", type=Path, help="JSON-Bericht schreiben")
    coverage.add_argument("--summary", type=Path, help="Markdown-Bericht anhängen")
    report = sub.add_parser("report", help="Kompakter Befundbericht für PRs und Agenten")
    report.add_argument("--root", type=Path, default=Path.cwd())
    report.add_argument("--junit", type=Path, action="append", default=[], help="JUnit-XML")
    report.add_argument("--gate", type=Path, help="JSON-Bericht von 'check --output'")
    report.add_argument("--coverage", type=Path, help="coverage.py-JSON (--cov-report=json)")
    report.add_argument("--api-compare-ref", help="Git-Revision für den API-Vergleich")
    report.add_argument("--output", type=Path, default=Path("report.json"))
    report.add_argument("--markdown", type=Path, default=Path("report.md"))
    report.add_argument("--summary", type=Path, help="Markdown zusätzlich anhängen")
    return parser


def _status(verdicts: list[Verdict]) -> str:
    if any(verdict.status == "FAIL" for verdict in verdicts):
        return "FAIL"
    return "WARN" if any(verdict.status == "WARN" for verdict in verdicts) else "PASS"


def build_report(
    measurements: list[PackageMeasurement],
    verdicts: list[Verdict],
    versions: dict[str, str],
    baseline_path: Path,
) -> dict[str, object]:
    """Assemble the machine-readable gate report."""
    return {
        "scope": "AUDITCORE_CODE_QUALITY_GATE",
        "status": _status(verdicts),
        "baseline": baseline_path.as_posix(),
        "tool_versions": versions,
        "packages": {
            m.name: {
                "kind": m.kind,
                "metrics": dict(sorted(m.metrics.items())),
                "findings": [finding.to_dict() for finding in m.findings],
            }
            for m in measurements
        },
        "verdicts": [verdict.to_dict() for verdict in verdicts if verdict.status != "PASS"],
    }


def render_text(
    status: object, measurements: list[PackageMeasurement], verdicts: list[Verdict]
) -> str:
    """Render a readable console report."""
    lines = [f"Code-Qualitäts-Gate: {status}"]
    for measurement in measurements:
        metrics = ", ".join(f"{k}={v}" for k, v in sorted(measurement.metrics.items()) if v)
        lines.append(f"  {measurement.name}: {metrics or 'alle Maßstäbe erfüllt'}")
    for verdict in verdicts:
        if verdict.status != "PASS":
            lines.append(f"{verdict.status} {verdict.package} {verdict.metric}: {verdict.message}")
    return "\n".join(lines)


def render_markdown(report: dict[str, object], verdicts: list[Verdict]) -> str:
    """Render a Markdown summary (CI step summary)."""
    lines = [f"## Code-Qualitäts-Gate: {report['status']}", ""]
    open_items = [verdict for verdict in verdicts if verdict.status != "PASS"]
    if open_items:
        lines += ["| Status | Paket | Metrik | Befund |", "|---|---|---|---|"]
        lines += [f"| {v.status} | {v.package} | {v.metric} | {v.message} |" for v in open_items]
    else:
        lines.append("Alle Pakete halten ihre Baseline ein.")
    return "\n".join(lines) + "\n"


def _baseline_path(args: argparse.Namespace) -> Path:
    path: Path = args.baseline
    return path if path.is_absolute() else args.root / path


def _write_updates(
    args: argparse.Namespace, measurements: list[PackageMeasurement], versions: dict[str, str]
) -> None:
    path = _baseline_path(args)
    complete = not args.package
    if args.init_baseline:
        if path.exists():
            raise ValueError("Baseline existiert bereits; nur --update-baseline ist zulässig")
        write_baseline(path, initial_baseline(measurements, versions))
    elif args.update_baseline:
        current = load_baseline(path)
        write_baseline(path, update_baseline(current, measurements, versions, complete=complete))


@dataclass(frozen=True)
class GateResult:
    """Everything the gate emits."""

    report: dict[str, object]
    verdicts: list[Verdict]
    measurements: list[PackageMeasurement]


def evaluate(args: argparse.Namespace) -> GateResult:
    """Measure, optionally update the baseline, and compare."""
    root = args.root.resolve()
    args.root = root
    found = discover_packages(root)
    selected = select_packages(found, args.package)
    with_mypy = not args.skip_mypy
    measurements = measure(root, selected, found, with_mypy)
    versions = tool_versions(with_mypy)
    _write_updates(args, measurements, versions)
    path = _baseline_path(args)
    baseline = load_baseline(path)
    verdicts = compare(measurements, baseline, versions, complete=not args.package)
    if args.compare_ref:
        if not path.is_relative_to(root):
            raise ValueError("--compare-ref requires a baseline inside the repository")
        relative = path.relative_to(root).as_posix()
        verdicts += raises(baseline, baseline_from_git(root, args.compare_ref, relative))
    shown = path.relative_to(root) if path.is_relative_to(root) else path
    report = build_report(measurements, verdicts, versions, shown)
    return GateResult(report, verdicts, measurements)


def _emit(args: argparse.Namespace, result: GateResult) -> None:
    report, verdicts = result.report, result.verdicts
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    if args.summary:
        with args.summary.open("a", encoding="utf-8") as handle:
            handle.write(render_markdown(report, verdicts))
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    elif args.format == "markdown":
        print(render_markdown(report, verdicts))
    else:
        print(render_text(report["status"], result.measurements, verdicts))


def run_report(args: argparse.Namespace) -> int:
    """Write report.json and report.md; the report itself never fails the build."""
    api = (args.root.resolve(), args.api_compare_ref) if args.api_compare_ref else None
    findings = collect(args.junit, args.gate, args.coverage, api)
    markdown = render_findings(findings)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(findings.to_dict(), indent=2, ensure_ascii=False) + "\n")
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.write_text(markdown, encoding="utf-8")
    if args.summary:
        with args.summary.open("a", encoding="utf-8") as handle:
            handle.write(markdown)
    print(markdown)
    return 0


def run_coverage(args: argparse.Namespace) -> int:
    """Evaluate package coverage and optionally record improvements."""
    root = args.root.resolve()
    baseline_path = args.baseline if args.baseline.is_absolute() else root / args.baseline
    coverage_path = args.coverage if args.coverage.is_absolute() else root / args.coverage
    selected = set(args.package) or None
    current = read_package_coverage(root, coverage_path, selected)
    baseline = load_baseline(baseline_path)
    if args.update_baseline:
        baseline = update_coverage(baseline, current)
        write_baseline(baseline_path, baseline)
    verdicts = compare_coverage(current, baseline, selected)
    if args.compare_ref:
        relative = baseline_path.relative_to(root).as_posix()
        verdicts += compare_coverage_reference(
            baseline, baseline_from_git(root, args.compare_ref, relative), selected
        )
    status = _status(verdicts)  # type: ignore[arg-type]
    report = {
        "scope": "AUDITCORE_COVERAGE_GATE",
        "status": status,
        "baseline": baseline_path.relative_to(root).as_posix(),
        "packages": current,
        "verdicts": [verdict.to_dict() for verdict in verdicts if verdict.status != "PASS"],
    }
    if args.output:
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    lines = [f"## Coverage-Ratchet: {status}", ""]
    lines += [
        f"- {v.status} {v.package}: {v.baseline:.2f}% → {v.current:.2f}% ({v.message})"
        for v in verdicts
        if v.status != "PASS"
    ] or ["Alle Pakete halten ihre Coverage-Baseline ein."]
    markdown = "\n".join(lines) + "\n"
    if args.summary:
        with args.summary.open("a", encoding="utf-8") as handle:
            handle.write(markdown)
    print(markdown)
    return 1 if status == "FAIL" else 0


def main(argv: list[str] | None = None) -> int:
    """Run the gate; exit 0 = PASS/WARN, 1 = FAIL, 2 = not executable."""
    args = build_parser().parse_args(argv)
    if args.command == "coverage":
        try:
            return run_coverage(args)
        except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
            print(f"Coverage-Ratchet nicht ausführbar: {error}", file=sys.stderr)
            return 2
    if args.command == "report":
        try:
            return run_report(args)
        except (ValueError, OSError, ElementTree.ParseError, CalledProcessError) as error:
            print(f"Befundbericht nicht erstellbar: {error}", file=sys.stderr)
            return 2
    try:
        result = evaluate(args)
    except (ToolError, ValueError, OSError) as error:
        print(f"Code-Qualitäts-Gate nicht ausführbar: {error}", file=sys.stderr)
        return 2
    _emit(args, result)
    return 1 if result.report["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
