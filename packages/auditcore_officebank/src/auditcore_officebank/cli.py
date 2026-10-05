"""Kommandozeile ``auditcore-officebank`` (Befehle deutsch, wie beim Runner).

Etappe 0 bietet ``status`` und ``konfig pruefen|schema``. Alle übrigen Gruppen
sind angelegt und enden mit Exit 3 und einem Hinweis auf ihre Etappe. Jede
Ausgabe läuft durch :func:`~auditcore_officebank.masking.mask_secrets`.

Rückgabewerte: 0 erfolgreich, 2 Konfigurationsfehler, 3 noch nicht umgesetzt.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from importlib.resources import files
from pathlib import Path

from . import __version__
from .config import (
    DEFAULT_HOST_PROFILE,
    HostProfile,
    ProjectConfig,
    load_host_profile,
    load_project,
)
from .errors import ConfigError, StageNotImplemented
from .masking import mask_secrets
from .stages import IMPLEMENTED_STAGE, STAGES, planned_groups, require

EXIT_CONFIG = 2
EXIT_NOT_IMPLEMENTED = 3


def _say(text: str, *, error: bool = False) -> None:
    print(mask_secrets(text), file=sys.stderr if error else sys.stdout)


def build_parser() -> argparse.ArgumentParser:
    """Parser mit allen geplanten Befehlsgruppen."""
    parser = argparse.ArgumentParser(
        prog="auditcore-officebank",
        description="Office-, VBA- und VM-Prüfbank (Gates, Gast, Build, Abnahme, Lieferung).",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    groups = parser.add_subparsers(dest="group", required=True, metavar="befehl")
    groups.add_parser("status", help="Etappen und verfügbare Befehle anzeigen")
    config = groups.add_parser("konfig", help="Rechnerprofil und Projektdatei")
    actions = config.add_subparsers(dest="action", required=True, metavar="aktion")
    check = actions.add_parser("pruefen", help="Rechnerprofil und/oder Projektdatei prüfen")
    check.add_argument("--rechner", type=Path, nargs="?", const=DEFAULT_HOST_PROFILE)
    check.add_argument("--projekt", type=Path)
    schema = actions.add_parser("schema", help="JSON-Schema ausgeben")
    schema.add_argument("art", choices=("rechner", "projekt"))
    for group in planned_groups():
        planned = groups.add_parser(group, help=f"geplant (Etappe {_stage_number(group)})")
        planned.add_argument("rest", nargs=argparse.REMAINDER)
    return parser


def _stage_number(group: str) -> int:
    return next(stage.number for stage in STAGES if group in stage.groups)


def _status() -> int:
    for stage in STAGES:
        state = "verfügbar" if stage.number <= IMPLEMENTED_STAGE else "geplant"
        _say(f"Etappe {stage.number} {stage.title}: {', '.join(stage.groups)} – {state}")
    return 0


def _describe_host(profile: HostProfile) -> str:
    endpoints = ", ".join(sorted(profile.endpoints)) or "keine"
    return (
        f"Rechnerprofil gültig: VM „{profile.vm_name}“ ({profile.vm_backend}), "
        f"MCP-Endpunkte: {endpoints}, Upload-Ziele: {len(profile.upload_targets)}"
    )


def _describe_project(project: ProjectConfig) -> str:
    return (
        f"Projektdatei gültig: {project.code} ({project.host}), "
        f"{len(project.modules)} Module, Lint-Profil {project.lint_profile}"
    )


def _check(args: argparse.Namespace) -> int:
    if args.rechner is None and args.projekt is None:
        _say("Nichts geprüft: --rechner und/oder --projekt angeben.", error=True)
        return EXIT_CONFIG
    if args.rechner is not None:
        _say(_describe_host(load_host_profile(args.rechner)))
    if args.projekt is not None:
        _say(_describe_project(load_project(args.projekt)))
    return 0


def _schema(kind: str) -> int:
    resource = files("auditcore_officebank").joinpath("data", "schemas", f"{kind}.schema.json")
    _say(resource.read_text(encoding="utf-8").rstrip())
    return 0


def _dispatch(args: argparse.Namespace) -> int:
    require(args.group)
    if args.group == "status":
        return _status()
    if args.action == "pruefen":
        return _check(args)
    return _schema(args.art)


def main(argv: Sequence[str] | None = None) -> int:
    """Einstiegspunkt der CLI; gibt den Exitcode zurück."""
    args = build_parser().parse_args(argv)
    try:
        return _dispatch(args)
    except ConfigError as exc:
        _say(f"Konfigurationsfehler: {exc}", error=True)
        return EXIT_CONFIG
    except StageNotImplemented as exc:
        _say(str(exc), error=True)
        return EXIT_NOT_IMPLEMENTED
