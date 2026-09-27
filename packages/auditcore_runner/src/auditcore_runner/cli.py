"""Command line ``auditcore-runner``."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import replace
from importlib.resources import files
from pathlib import Path

from . import __version__, anwenden, backend, github, install, pool, profile_io, status
from .commands_scaleset import add_scaleset_commands
from .commands_tools import add_tool_commands
from .hardware import HostFacts, detect
from .profile import Profile, default_profile_path
from .propose import propose
from .validation import validate


def _profile_path(args: argparse.Namespace) -> Path:
    return Path(args.profil) if args.profil else default_profile_path()


def _print_json(data: object) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


TEMPLATES = ("workstation-2gpu", "server-cpu")


def from_template(name: str, facts: HostFacts, target: str) -> Profile:
    """A neutral example profile adapted to this machine (host name and detected cards)."""
    text = files("auditcore_runner").joinpath("data", "beispiele", f"{name}.json").read_text(encoding="utf-8")
    template = profile_io.from_json(json.loads(text))
    detected = propose(facts, target).gpus
    classes = {name: settings for name, settings in template.classes.items()}
    gpu_classes = {g.runner_class for g in detected}
    for name in [n for n in classes if n.startswith("gpu-") and n not in gpu_classes]:
        classes.pop(name)
    chosen = replace(template.target, name=target or template.target.name)
    return replace(template, host=facts.hostname, target=chosen, classes=classes, gpus=detected)


def cmd_detect(args: argparse.Namespace) -> int:
    facts = detect()
    suggestion = (
        from_template(args.vorlage, facts, args.ziel or "") if args.vorlage else propose(facts, args.ziel or "")
    )
    problems = validate(suggestion, facts)
    _print_json(
        {
            "hardware": facts.as_dict(),
            "profil": profile_io.to_json(suggestion),
            "probleme": [p.as_dict() for p in problems],
        }
    )
    if args.speichern:
        path = profile_io.save(suggestion, _profile_path(args))
        print(f"Profil gespeichert: {path}", file=sys.stderr)
    return 1 if problems else 0


def _read_input(value: str | None, fallback: Path) -> object:
    if value == "-":
        return json.load(sys.stdin)
    return json.loads(Path(value or fallback).read_text(encoding="utf-8"))


def cmd_check_profile(args: argparse.Namespace) -> int:
    path = _profile_path(args)
    _, result = anwenden.evaluate(_read_input(args.datei, path), path, detect())
    if args.json:
        _print_json(result)
    else:
        for problem in result["probleme"] if isinstance(result["probleme"], list) else []:
            print(f"{problem['feld']}: {problem['meldung']}")
        for change in result["aenderungen"] if isinstance(result["aenderungen"], list) else []:
            print(change["diff"], end="")
        print("Profil in Ordnung." if result["gueltig"] else "Profil hat Fehler.")
    return 0 if result["gueltig"] else 1


def cmd_apply_profile(args: argparse.Namespace) -> int:
    path = _profile_path(args)
    result = anwenden.apply(
        _read_input(args.datei, path),
        path,
        detect(),
        source=args.quelle,
        who=args.wer,
        expected_version=args.erwartete_version,
        run=not args.trockenlauf,
    )
    if args.json:
        _print_json(result)
    else:
        print(result.get("meldung") or f"Version {result.get('version')} angewendet.")
    if result.get("konflikt"):
        return 3
    return 0 if result.get("angewendet") and not result.get("fehler") else 1


def cmd_schema(args: argparse.Namespace) -> int:
    print(
        files("auditcore_runner").joinpath("data", "schemas", "profil.schema.json").read_text(encoding="utf-8"), end=""
    )
    return 0


def _print_install_notes(profile: Profile) -> None:
    for unit in install.legacy_units():
        print(f"Hinweis: alte Unit {unit} registriert ebenfalls Runner; nach dem Umstieg abschalten.", file=sys.stderr)
    if profile.network.enabled:
        print(f"Netzsperre (einmalig, mit root): {install.firewall_command()}")
    for hint in install.hints(profile):
        print(f"Hinweis: {hint}")


def cmd_install(args: argparse.Namespace) -> int:
    path = _profile_path(args)
    profile = profile_io.load(path)
    problems = validate(profile, detect())
    if problems:
        for problem in problems:
            print(f"Fehler {problem.field}: {problem.message}", file=sys.stderr)
        return 1
    changes = install.plan(profile, path)
    steps = install.docker_steps(
        profile, install.image_present(profile.image), install.network_present(profile.network.name)
    )
    steps += install.instance_steps(profile)
    for change in changes:
        if change.changed:
            print(change.diff() or f"neu: {change.path}")
    for step in steps:
        print(f"$ {step.text()}    # {step.reason}")
    _print_install_notes(profile)
    if args.trockenlauf:
        return 0
    install.write_changes(changes)
    errors = install.run_steps(steps)
    for error in errors:
        print(f"Fehler: {error}", file=sys.stderr)
    return 1 if errors else 0


def cmd_uninstall(args: argparse.Namespace) -> int:
    steps = install.uninstall_steps() + (install.volume_steps() if args.volumes else [])
    paths = install.uninstall_files(args.alles)
    for step in steps:
        print(f"$ {step.text()}")
    for path in paths:
        print(f"entfernen: {path}")
    print("Netzsperre entfernen (falls installiert): sudo /usr/local/sbin/auditcore-ci-firewall entfernen")
    print("Scale-Sets (Backend „scaleset“) danach löschen: auditcore-runner scaleset loeschen")
    print("Egress-Zeitgeber (falls installiert): sudo systemctl disable --now auditcore-ci-egress.timer")
    if args.trockenlauf:
        return 0
    errors = install.run_steps(steps)
    install.remove_paths(paths)
    return 1 if errors else 0


def _client(args: argparse.Namespace) -> github.Client | None:
    if args.ohne_github:
        return None
    try:
        return github.Client(github.resolve_token(profile_io.load(_profile_path(args)).auth))
    except (github.GitHubError, OSError):
        return None


def cmd_status(args: argparse.Namespace) -> int:
    current = status.collect(profile_io.load(_profile_path(args)), detect(), _client(args))
    if args.schreiben:
        status.write(current)
    if not args.still:
        _print_json(current)
    unknown = current.get("unbekannte_runner")
    if isinstance(unknown, list):
        for name in status.new_unknown([str(n) for n in unknown]):
            print(f"WARNUNG: unbekannte Runner-Registrierung {name!r} – nicht von diesem Profil", file=sys.stderr)
        if unknown and args.streng:
            return 4
    return 0


def cmd_target(args: argparse.Namespace) -> int:
    profile = profile_io.load(_profile_path(args))
    path = profile.pool_path()
    if path is None:
        print("Soll-Quelle ist „statisch“: es gilt das Maximum aus dem Profil.")
        return 0
    if args.setzen:
        current = pool.load(path) or pool.Pool({})
        targets = {**current.targets, **pool.parse_assignments(args.setzen)}
        pool.save(pool.Pool(targets, source="auditcore-runner/hand"), path)
    loaded = pool.load(path)
    _print_json(pool.to_json(loaded) if loaded else {"hinweis": f"{path} existiert nicht"})
    return 0


def cmd_supervisor(args: argparse.Namespace) -> int:  # pragma: no cover - replaces the process
    path = _profile_path(args)
    profile = profile_io.load(path)
    backend.backend(profile.backend).serve(profile, path, args.klasse, args.nummer)
    return 0


def cmd_token(args: argparse.Namespace) -> int:
    print(github.resolve_token(profile_io.load(_profile_path(args)).auth))
    return 0


def cmd_gpu_choose(args: argparse.Namespace) -> int:
    """Print the card for the next job of a GPU class; exit 3 when none is usable now."""
    from . import gpu

    profile = profile_io.load(_profile_path(args))
    if args.klasse not in profile.classes:
        print(f"Fehler: Klasse {args.klasse!r} fehlt im Profil", file=sys.stderr)
        return 2
    uuid = gpu.choose(profile, args.klasse, gpu.observe(profile))
    if uuid is None:
        return 3
    if args.platz:
        gpu.reserve(args.platz, uuid)
    print(uuid)
    return 0


def cmd_gpu_release(args: argparse.Namespace) -> int:
    from . import gpu

    gpu.release(args.platz)
    return 0


def cmd_gpu_check(args: argparse.Namespace) -> int:
    """Exit 1 when the user needs the card now (the running job is evicted)."""
    from . import gpu

    profile = profile_io.load(_profile_path(args))
    return 1 if gpu.must_evict(args.uuid, gpu.observe(profile)) else 0


def cmd_regulator(args: argparse.Namespace) -> int:  # pragma: no cover - endless loop
    from .autoscaler import run_forever

    profile = profile_io.load(_profile_path(args))
    run_forever(profile, _client(args))
    return 0


def cmd_ui(args: argparse.Namespace) -> int:  # pragma: no cover - blocking server
    from .web import App, serve

    app = App(_profile_path(args), apply_enabled=not args.trockenlauf)
    print(f"auditcore-runner UI: http://{args.adresse}:{args.port}/")
    serve(app, args.adresse, args.port, args.lesend_an or "")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="auditcore-runner", description="Self-hosted GitHub-Runner und lokale Prüfbank"
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--profil", help="Profildatei (Standard ~/.config/auditcore-runner/profil.json)")
    sub = parser.add_subparsers(dest="befehl", required=True)
    _add_profile_commands(sub)
    _add_runner_commands(sub)
    add_tool_commands(sub)
    add_scaleset_commands(sub)
    return parser


def _add_profile_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    group = sub.add_parser("profil", help="Profil dieses Rechners").add_subparsers(dest="aktion", required=True)
    detect_parser = group.add_parser("erkennen", help="Hardware messen und Profil vorschlagen")
    detect_parser.add_argument("--ziel", help="Repository <owner>/<repo>")
    detect_parser.add_argument("--vorlage", choices=TEMPLATES, help="neutrale Vorlage, an diesen Rechner angepasst")
    detect_parser.add_argument("--speichern", action="store_true")
    detect_parser.set_defaults(func=cmd_detect)
    check = group.add_parser("pruefen", help="Profil prüfen und Diff zum aktiven Profil zeigen")
    check.add_argument("--datei", help="zu prüfendes Profil (Pfad oder - für stdin; Standard: aktives Profil)")
    check.add_argument("--json", action="store_true")
    check.set_defaults(func=cmd_check_profile)
    apply = group.add_parser("anwenden", help="Profil prüfen, speichern und anwenden (laufende Jobs bleiben)")
    apply.add_argument("--datei", required=True, help="Profil (Pfad oder - für stdin)")
    apply.add_argument(
        "--erwartete-version", type=int, help="Konflikt melden, wenn das aktive Profil eine andere Version hat"
    )
    apply.add_argument("--quelle", choices=["lokal", "flow-agent"], default="lokal")
    apply.add_argument("--wer", default="cli")
    apply.add_argument("--json", action="store_true")
    apply.add_argument("--trockenlauf", action="store_true", help="speichern und Dateien schreiben, aber keine Befehle")
    apply.set_defaults(func=cmd_apply_profile)
    group.add_parser("schema", help="JSON-Schema des Profils ausgeben").set_defaults(func=cmd_schema)


def _add_runner_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    group = sub.add_parser("runner", help="Runner installieren und steuern").add_subparsers(
        dest="aktion", required=True
    )
    install_parser = group.add_parser("install", help="Units, Image und Netz aus dem Profil")
    install_parser.add_argument("--trockenlauf", action="store_true")
    install_parser.set_defaults(func=cmd_install)
    uninstall = group.add_parser("uninstall", help="alles dieses Pakets entfernen")
    uninstall.add_argument("--alles", action="store_true", help="auch Profil, Zustand und root-Skripte")
    uninstall.add_argument("--volumes", action="store_true", help="auch Cache-Volumes")
    uninstall.add_argument("--trockenlauf", action="store_true")
    uninstall.set_defaults(func=cmd_uninstall)
    status_parser = group.add_parser("status", help="Status (JSON) für Menschen und externe Werkzeuge")
    status_parser.add_argument("--schreiben", action="store_true", help=f"nach {status.status_path()} schreiben")
    status_parser.add_argument("--still", action="store_true")
    status_parser.add_argument("--ohne-github", action="store_true")
    status_parser.add_argument("--streng", action="store_true", help="Exit 4 bei unbekannten Registrierungen")
    status_parser.set_defaults(func=cmd_status)
    target = group.add_parser("soll", help="Soll-Datei lesen oder setzen (KLASSE=ZAHL)")
    target.add_argument("setzen", nargs="*")
    target.set_defaults(func=cmd_target)
    supervisor = sub.add_parser("supervisor", help="eine Runner-Instanz (von systemd gestartet)")
    supervisor.add_argument("klasse")
    supervisor.add_argument("nummer", type=int)
    supervisor.set_defaults(func=cmd_supervisor)
    gpu_group = sub.add_parser("gpu", help="Karte je Job wählen und prüfen (für den Supervisor)").add_subparsers(
        dest="aktion", required=True
    )
    choose = gpu_group.add_parser("waehlen", help="freieste erlaubte Karte ausgeben (Exit 3: keine frei)")
    choose.add_argument("klasse")
    choose.add_argument("--platz", help="Reservierung für diese Instanz (z. B. gpu-16gb-1), bis der Container läuft")
    choose.set_defaults(func=cmd_gpu_choose)
    release = gpu_group.add_parser("freigeben", help="Reservierung einer Instanz aufheben")
    release.add_argument("platz")
    release.set_defaults(func=cmd_gpu_release)
    check_gpu = gpu_group.add_parser("pruefen", help="Exit 1, wenn die Karte geräumt werden muss")
    check_gpu.add_argument("uuid")
    check_gpu.set_defaults(func=cmd_gpu_check)
    regulator = sub.add_parser("regler", help="lokaler Autoskalierer (Soll-Quelle „lokal“)")
    regulator.add_argument("--ohne-github", action="store_true")
    regulator.set_defaults(func=cmd_regulator)
    sub.add_parser("token", help="GitHub-Token gemäß Profil ausgeben (für den Supervisor)").set_defaults(func=cmd_token)
    ui = sub.add_parser("ui", help="lokale Oberfläche und JSON-API")
    ui.add_argument("--adresse", default="127.0.0.1")
    ui.add_argument("--port", type=int, default=7860)
    ui.add_argument("--lesend-an", help="zusätzliche, nur lesende Adresse (z. B. Tailscale)")
    ui.add_argument("--trockenlauf", action="store_true", help="Anwenden ausschalten")
    ui.set_defaults(func=cmd_ui)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (profile_io.ProfileFormatError, pool.PoolFormatError, github.GitHubError, FileNotFoundError) as error:
        print(f"Fehler: {error}", file=sys.stderr)
        return 2
