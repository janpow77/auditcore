"""CLI commands for checks: ``lokal``, ``befunde``, ``workflows``, ``image``, ``messen``, ``hook``."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from . import codemods, github, image, measure, profile_io, workflows
from .hardware import detect
from .profile import default_profile_path
from .werkzeuge import aufgaben, bericht, einstellungen
from .werkzeuge.ausfuehren import Runner, last_result_path, run_fixes, run_profile
from .werkzeuge.befunde import deduplicate, load_baseline, only_new, save_baseline, to_sarif
from .werkzeuge.katalog import Registry
from .werkzeuge.modell import apply_machine_settings, load_codemods, load_repo_profiles
from .werkzeuge.parser import actionlint, sarif


def _image(args: argparse.Namespace) -> str:
    if args.host:
        return ""
    path = Path(args.profil) if args.profil else default_profile_path()
    return profile_io.load(path).image if path.exists() else "auditcore-runner:local"


def cmd_local(args: argparse.Namespace) -> int:
    root = Path(args.pfad).resolve()
    profiles = load_repo_profiles(root)
    if args.pruefprofil not in profiles:
        print(f"unbekanntes Prüfprofil: {args.pruefprofil} ({', '.join(sorted(profiles))})", file=sys.stderr)
        return 2
    selected = apply_machine_settings(profiles[args.pruefprofil], einstellungen.load().get(args.pruefprofil, {}))
    runner, registry = Runner(root, _image(args)), Registry()
    if args.beheben or selected.autofix:
        run_fixes(runner, registry, selected, load_codemods(root))
    document = run_profile(runner, registry, selected, use_cache=not args.ohne_cache)
    last_result_path().parent.mkdir(parents=True, exist_ok=True)
    last_result_path().write_text(json.dumps(document, ensure_ascii=False) + "\n", encoding="utf-8")
    for tool in document["werkzeuge"] if isinstance(document["werkzeuge"], list) else []:
        print(
            f"{tool['werkzeug']:<11} {tool['status']:<9} {tool['befunde']:>4} Befunde  {tool['sekunden']:>6} s"
            f"{'  (Cache)' if tool['aus_cache'] else ''}  {tool['meldung']}"
        )
    findings = bericht.findings_from_documents([document])
    print(f"\n{len(findings)} Befunde, Bericht: auditcore-runner befunde")
    return 1 if findings else 0


def cmd_findings(args: argparse.Namespace) -> int:
    source = Path(args.ergebnis) if args.ergebnis else last_result_path()
    findings = deduplicate(bericht.findings_from_documents([json.loads(source.read_text(encoding="utf-8"))]))
    if args.baseline_setzen:
        save_baseline(Path(args.baseline_setzen), findings)
        print(f"Baseline mit {len(findings)} Befunden geschrieben.")
        return 0
    new = only_new(findings, load_baseline(Path(args.baseline))) if args.baseline else findings
    if args.sarif:
        Path(args.sarif).write_text(json.dumps(to_sarif(new), indent=2) + "\n", encoding="utf-8")
    if args.aufgabenpaket:
        package = aufgaben.build(args.paket_id, args.aufgabentyp, Path(args.pfad).resolve(), new)
        target = Path(args.aufgabenpaket)
        target.write_text(aufgaben.render(package), encoding="utf-8")
        print(aufgaben.command(package, target, args.art), file=sys.stderr)
    print(bericht.render(new, args.max, args.budget), end="")
    return 1 if new else 0


def _external(command: list[str], parse: object, cwd: Path) -> list[workflows.WorkflowFinding]:
    if shutil.which(command[0]) is None or not callable(parse):
        return []
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=300, check=False)
    return [
        workflows.WorkflowFinding(Path(f.path).name, "-", f"{f.tool}:{f.rule}", f"Zeile {f.line}: {f.message}")
        for f in parse(result.stdout)
    ]


def cmd_workflows(args: argparse.Namespace) -> int:
    target = Path(args.pfad)
    try:
        findings = workflows.check_directory(target, tuple(args.runner_variable))
    except workflows.MissingExtraError as error:
        print(f"Fehler: {error}", file=sys.stderr)
        return 2
    if not args.ohne_extern:
        cwd = target if target.is_dir() else target.parent
        findings += _external(["zizmor", "--format", "sarif", "--no-progress", str(target)], sarif, cwd)
        findings += _external(["actionlint", "-format", "{{json .}}"], actionlint, cwd.parent.parent)
    if args.json:
        print(json.dumps([f.as_dict() for f in findings], indent=2, ensure_ascii=False))
    else:
        for finding in findings:
            print(f"{finding.workflow} / {finding.job}: [{finding.rule}] {finding.message}")
        print(f"{len(findings)} Befund(e).")
    return 1 if findings else 0


def cmd_image(args: argparse.Namespace) -> int:
    profile = profile_io.load(Path(args.profil) if args.profil else default_profile_path())
    client = github.Client(github.resolve_token(profile.auth))
    latest = image.latest_release(client)
    report = image.VersionStatus(image.image_version(profile.image), latest, datetime.now(UTC))
    print(json.dumps(report.as_dict(), indent=2, ensure_ascii=False))
    if args.aktion == "pruefen":
        return 0 if report.state in {"aktuell", "frist"} else 1
    if report.state == "aktuell" and not args.erzwingen:
        return 0
    command = image.build_command(
        profile.image, image.base_digest(latest.version) if not args.trockenlauf else "<digest>"
    )
    print("$ " + " ".join(command))
    return 0 if args.trockenlauf else subprocess.run(command, check=False).returncode


def cmd_measure(args: argparse.Namespace) -> int:
    since = datetime.now(UTC) - timedelta(days=args.tage)
    runs = measure.fetch_runs(args.repo, args.tage) if args.repo else []
    stats = measure.workflow_stats(runs)
    claude = measure.claude_usage(Path.home() / ".claude" / "projects", since)
    codex = measure.codex_usage(Path.home() / ".codex" / "sessions", since)
    if args.format == "json":
        text = json.dumps(
            {
                "workflows": [s.__dict__ for s in stats],
                "claude": claude,
                "codex": codex,
                "otel": measure.otel_usage(Path(args.otel_datei)) if args.otel_datei else {},
            },
            indent=2,
            ensure_ascii=False,
            default=dict,
        )
    else:
        text = measure.render_markdown(detect().hostname, args.tage, stats, claude, codex)
    if args.ausgabe:
        Path(args.ausgabe).write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


HOOK = """# auditcore-runner: vor dem Push dieselben Prüfungen wie in der CI (prek/pre-commit)
-   repo: local
    hooks:
    -   id: auditcore-runner-schnell
        name: auditcore-runner lokal schnell
        entry: auditcore-runner lokal schnell
        language: system
        pass_filenames: false
        stages: [pre-push]
"""


def cmd_hook(args: argparse.Namespace) -> int:
    """Print (or append) a prek/pre-commit hook; prek itself installs it."""
    config = Path(args.pfad) / ".pre-commit-config.yaml"
    if args.schreiben and not config.exists():
        config.write_text("repos:\n" + HOOK, encoding="utf-8")
        print(f"{config} angelegt. Aktivieren: prek install --hook-type pre-push")
        return 0
    print(HOOK if config.exists() else "repos:\n" + HOOK, end="")
    return 0


def cmd_codemod(args: argparse.Namespace) -> int:
    """Apply one structural codemod only after the configured verification passes."""
    try:
        result = codemods.run(args.engine, args.rezept, Path(args.pfad))
    except codemods.CodemodError as error:
        print(f"Codemod blockiert: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result.as_dict(), indent=2, ensure_ascii=False))
    return 0


WORKFLOW_TEMPLATES = ("runner-wahl",)


def cmd_workflow_template(args: argparse.Namespace) -> int:
    from importlib.resources import files

    text = files("auditcore_runner").joinpath("data", "workflows", f"{args.name}.yml").read_text(encoding="utf-8")
    if not args.ziel:
        print(text, end="")
        return 0
    target = Path(args.ziel) / f"{args.name}.yml"
    if target.exists() and not args.ueberschreiben:
        print(f"Fehler: {target} existiert (--ueberschreiben)", file=sys.stderr)
        return 1
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    print(f"geschrieben: {target}")
    return 0


def add_tool_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    codemod = sub.add_parser("codemod", help="ast-grep/LibCST-Codemod transaktional anwenden")
    codemod.add_argument("engine", choices=("ast-grep", "libcst"))
    codemod.add_argument("rezept", help="Regeldatei (ast-grep) oder Codemod-Modul (LibCST)")
    codemod.add_argument("--pfad", default=".")
    codemod.set_defaults(func=cmd_codemod)
    local = sub.add_parser("lokal", help="Prüfprofil lokal ausführen (Runner-Image oder --host)")
    local.add_argument("pruefprofil")
    local.add_argument("--pfad", default=".")
    local.add_argument("--host", action="store_true", help="Werkzeuge des Hosts statt des Images")
    local.add_argument("--beheben", action="store_true", help="zuerst Autofixer ausführen")
    local.add_argument("--ohne-cache", action="store_true")
    local.set_defaults(func=cmd_local)
    findings = sub.add_parser("befunde", help="kompakter Bericht, SARIF, Baseline, Aufgabenpaket")
    findings.add_argument("--ergebnis", help="Ergebnisdatei (Standard: letzter lokaler Lauf)")
    findings.add_argument("--baseline", help="nur Befunde, die nicht in dieser Baseline stehen")
    findings.add_argument("--baseline-setzen", help="aktuelle Befunde als Baseline schreiben")
    findings.add_argument("--sarif", help="SARIF-Ausgabedatei")
    findings.add_argument("--max", type=int, default=200)
    findings.add_argument("--budget", type=int, default=0, help="Token-Budget des Berichts")
    findings.add_argument("--aufgabenpaket", help="Aufgabenpaket-Datei für einen Agentenlauf")
    findings.add_argument("--paket-id", default="befunde")
    findings.add_argument("--aufgabentyp", default="befunde-beheben")
    findings.add_argument("--art", choices=aufgaben.KINDS, default="claude")
    findings.add_argument("--pfad", default=".")
    findings.set_defaults(func=cmd_findings)
    flows = sub.add_parser("workflows", help="GitHub-Workflows prüfen").add_subparsers(dest="aktion", required=True)
    check = flows.add_parser("pruefen")
    check.add_argument("pfad", nargs="?", default=".github/workflows")
    check.add_argument("--json", action="store_true")
    check.add_argument("--ohne-extern", action="store_true", help="ohne zizmor/actionlint")
    check.add_argument("--runner-variable", action="append", default=[], help="z. B. MY_RUNNER: nur in runs-on erlaubt")
    check.set_defaults(func=cmd_workflows)
    template = flows.add_parser("vorlage", help="Workflow-Vorlage des Pakets ausgeben oder kopieren")
    template.add_argument("name", choices=WORKFLOW_TEMPLATES)
    template.add_argument("--ziel", help="Verzeichnis, z. B. .github/workflows (sonst Ausgabe auf stdout)")
    template.add_argument("--ueberschreiben", action="store_true")
    template.set_defaults(func=cmd_workflow_template)
    image_parser = sub.add_parser("image", help="Runner-Image prüfen und aktualisieren")
    image_parser.add_argument("aktion", choices=["pruefen", "aktualisieren"])
    image_parser.add_argument("--erzwingen", action="store_true")
    image_parser.add_argument("--trockenlauf", action="store_true")
    image_parser.set_defaults(func=cmd_image)
    measure_parser = sub.add_parser("messen", help="CI-Dauern und Token-Verbrauch messen")
    measure_parser.add_argument("--repo", help="<owner>/<repo> für CI-Dauern (gh)")
    measure_parser.add_argument("--tage", type=int, default=14)
    measure_parser.add_argument("--format", choices=["md", "json"], default="md")
    measure_parser.add_argument("--ausgabe")
    measure_parser.add_argument("--otel-datei", help="OTLP-JSON-Datei mit Claude-Code-Metriken")
    measure_parser.set_defaults(func=cmd_measure)
    hook = sub.add_parser("hook", help="prek/pre-commit-Hook für den Push")
    hook.add_argument("--pfad", default=".")
    hook.add_argument("--schreiben", action="store_true")
    hook.set_defaults(func=cmd_hook)
