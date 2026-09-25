"""auditcore-helpers: shared helper contracts, lint rules and duplicate scan for apps.

``scan``       helper functions, duplicates, "exists in auditcore library X"
``lint``       known error patterns (declarative rules, some executed)
``contracts``  shared contract cases against the helpers named in the manifest
``check``      all three plus ratchet against ``.auditcore/helpers-baseline.json``
``toolchain``  install the Node toolchain (TypeScript compiler API, tsx)
``rules``      list the rule catalog
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from auditcore.tools.helpers.analysis import (
    ALL_STEPS,
    CONTRACTS,
    LINT,
    SCAN,
    Analysis,
    Options,
    analyse,
    ratchet_counts,
    to_json,
)
from auditcore.tools.helpers.manifest import DEFAULT_BASELINE
from auditcore.tools.helpers.model import HelperToolError, as_dict, as_list, write_json
from auditcore.tools.helpers.nodetools import ensure_toolchain, toolchain_versions
from auditcore.tools.helpers.ratchet import (
    Verdict,
    baseline_from_git,
    compare,
    empty_baseline,
    initial_baseline,
    load_baseline,
    raises,
    status_of,
    update_baseline,
    write_baseline,
)
from auditcore.tools.helpers.report import render_markdown
from auditcore.tools.helpers.rules import load_rules

STEPS = {SCAN: (SCAN,), LINT: (LINT,), CONTRACTS: (CONTRACTS,), "check": ALL_STEPS}


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("repo", type=Path, help="Wurzel des App-Repositorys")
    parser.add_argument(
        "--manifest", type=Path, help="Manifest (Standard: <repo>/.auditcore/helpers.json)"
    )
    parser.add_argument("--cases", type=Path, help="Verzeichnis contracts/common-cases")
    parser.add_argument(
        "--library-root", type=Path, help="auditcore-Checkout für den Bibliotheksabgleich"
    )
    parser.add_argument("--no-node", action="store_true", help="TS/JS/Vue nicht analysieren")
    parser.add_argument("--format", choices=["text", "json", "markdown"], default="text")
    parser.add_argument("--output", type=Path, help="JSON-Bericht schreiben")
    parser.add_argument("--markdown", type=Path, help="Markdown-Bericht schreiben")
    parser.add_argument(
        "--summary", type=Path, help="Markdown-Bericht anhängen (GITHUB_STEP_SUMMARY)"
    )


def build_parser() -> argparse.ArgumentParser:
    """Define all subcommands."""
    parser = argparse.ArgumentParser(
        prog="auditcore-helpers",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name, text in (
        (SCAN, "Hilfsfunktionen finden und klassifizieren"),
        (LINT, "Fehlmuster prüfen"),
        (CONTRACTS, "Vertragsfälle ausführen"),
    ):
        command = sub.add_parser(name, help=text)
        _common(command)
        command.add_argument("--strict", action="store_true", help="Exitcode 1 bei Befunden")
    check = sub.add_parser("check", help="Pflicht-Gate: alle Schritte mit Ratchet")
    _common(check)
    check.add_argument(
        "--baseline", type=Path, help="Standard: <repo>/.auditcore/helpers-baseline.json"
    )
    check.add_argument(
        "--update-baseline", action="store_true", help="Baseline auf den Messstand absenken"
    )
    check.add_argument("--init-baseline", action="store_true", help="Erstanlage der Baseline")
    check.add_argument("--compare-ref", help="Git-Revision für die Anhebungsprüfung der Baseline")
    check.add_argument("--no-fail", action="store_true", help="Nur berichten (nächtlicher Lauf)")
    sub.add_parser("toolchain", help="Node-Werkzeugkette installieren")
    sub.add_parser("rules", help="Regelkatalog anzeigen")
    return parser


def _options(args: argparse.Namespace) -> Options:
    return Options(
        root=args.repo,
        steps=STEPS[args.command],
        manifest=args.manifest,
        cases=args.cases,
        library_root=args.library_root,
        with_node=not args.no_node,
    )


def _baseline_path(args: argparse.Namespace, root: Path) -> Path:
    path: Path = args.baseline or DEFAULT_BASELINE
    return path if path.is_absolute() else root / path


def run_ratchet(args: argparse.Namespace, analysis: Analysis) -> dict[str, object]:
    """Apply baseline updates and compare; returns the ``ratchet`` report section."""
    path = _baseline_path(args, analysis.root)
    counts, labels = ratchet_counts(analysis)
    existing = load_baseline(path)
    if args.init_baseline:
        if existing is not None:
            raise HelperToolError("Baseline existiert bereits; nur --update-baseline ist zulässig")
        existing = initial_baseline(counts)
        write_baseline(path, existing)
    elif args.update_baseline and existing is not None:
        existing = update_baseline(existing, counts)
        write_baseline(path, existing)
    verdicts: list[Verdict] = compare(counts, existing or empty_baseline(), labels)
    if existing is None:
        verdicts.insert(
            0,
            Verdict("*", 0, 0, "WARN", "Keine Baseline vorhanden: Maßstab ist 0 (--init-baseline)"),
        )
    if args.compare_ref and existing is not None and path.is_relative_to(analysis.root):
        relative = path.relative_to(analysis.root).as_posix()
        verdicts += raises(existing, baseline_from_git(analysis.root, args.compare_ref, relative))
    return {
        "baseline": path.relative_to(analysis.root).as_posix()
        if path.is_relative_to(analysis.root)
        else str(path),
        "status": status_of(verdicts),
        "counted": sum(counts.values()),
        "verdicts": [verdict.to_dict() for verdict in verdicts],
    }


def render_text(report: dict[str, object]) -> str:
    """Short console summary."""
    lines = [f"auditcore-helpers: {report.get('app')}"]
    scan = as_dict(report.get("scan"))
    if scan:
        available = [
            m
            for m in as_list(scan.get("library_matches"))
            if as_dict(m).get("status") == "vorhanden"
        ]
        files = scan.get("files")
        lines.append(f"  Scan: {files} Dateien, {len(available)} schon in Bibliotheken vorhanden")
    lint = as_dict(report.get("lint"))
    if lint:
        lines.append(f"  Lint: {len(as_list(lint.get('findings')))} Befunde")
    runs = [as_dict(run) for run in as_list(report.get("contracts"))]
    if "contracts" in report:
        violations = sum(len(as_list(run.get("violations"))) for run in runs)
        lines.append(f"  Verträge: {len(runs)} Bindungen, {violations} Verletzungen")
    ratchet = as_dict(report.get("ratchet"))
    if ratchet:
        lines.append(f"Ratchet: {ratchet.get('status')}")
        lines += [
            f"  {as_dict(v).get('status')} {as_dict(v).get('message')}"
            for v in as_list(ratchet.get("verdicts"))
        ]
    return "\n".join(lines)


def _emit(args: argparse.Namespace, report: dict[str, object]) -> None:
    markdown = render_markdown(report)
    if args.output:
        write_json(args.output, report)
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(markdown, encoding="utf-8")
    if args.summary:
        with args.summary.open("a", encoding="utf-8") as handle:
            handle.write(markdown + "\n")
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(markdown if args.format == "markdown" else render_text(report))


def _has_findings(report: dict[str, object]) -> bool:
    lint = as_dict(report.get("lint"))
    runs = [as_dict(run) for run in as_list(report.get("contracts"))]
    return bool(as_list(lint.get("findings"))) or any(
        as_list(run.get("violations")) for run in runs
    )


def _run(args: argparse.Namespace) -> int:
    if args.command == "toolchain":
        directory = ensure_toolchain()
        print(f"{directory} {json.dumps(toolchain_versions(directory))}")
        return 0
    if args.command == "rules":
        for rule in load_rules():
            print(f"{rule.id}\t{rule.kind}\t{','.join(sorted(rule.spec))}\t{rule.title}")
        return 0
    analysis = analyse(_options(args))
    report = to_json(analysis)
    if args.command == "check":
        report["ratchet"] = run_ratchet(args, analysis)
    _emit(args, report)
    if args.command == "check":
        return 1 if report_status(report) == "FAIL" and not args.no_fail else 0
    return 1 if args.strict and _has_findings(report) else 0


def report_status(report: dict[str, object]) -> str:
    """Overall ratchet status of a ``check`` report."""
    return str(as_dict(report.get("ratchet")).get("status", "PASS"))


def main(argv: list[str] | None = None) -> int:
    """Exit 0 = PASS/WARN or report only, 1 = FAIL, 2 = not executable."""
    args = build_parser().parse_args(argv)
    try:
        return _run(args)
    except (HelperToolError, ValueError, OSError) as error:
        print(f"auditcore-helpers nicht ausführbar: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
