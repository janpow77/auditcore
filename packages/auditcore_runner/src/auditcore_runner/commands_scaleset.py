"""CLI group ``scaleset``: listener, JIT configuration and clean-up for the scale set backend."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import nachfrage, profile_io, scaleset_listener
from .profile import Profile, default_profile_path


def _profile(args: argparse.Namespace) -> Profile:
    return profile_io.load(Path(args.profil) if args.profil else default_profile_path())


def cmd_listen(args: argparse.Namespace) -> int:  # pragma: no cover - endless loop
    profile = _profile(args)
    if profile.backend != "scaleset":
        print("Hinweis: Profil nutzt nicht das Backend „scaleset“; der Listener liefert nur die Nachfrage.")
    scaleset_listener.run_forever(profile, lambda text: print(text, file=sys.stderr, flush=True))
    return 0


def cmd_jit(args: argparse.Namespace) -> int:
    """JIT configuration for the supervisor (stdout only; never logged)."""
    config = scaleset_listener.jit_config(_profile(args), args.klasse, args.name)
    print(json.dumps(config))
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    scaleset_listener.client_for(_profile(args)).remove_runner(args.runner_id)
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    profile = _profile(args)
    demand = nachfrage.load()
    rows: dict[str, object] = {}
    for name in sorted(profile.classes):
        entry = demand.classes.get(name) if demand else None
        rows[name] = {
            "scale_set": profile.scale_set_name(name),
            "soll": entry.target if entry else None,
            "warteschlange": entry.waiting if entry else None,
            "statistik": entry.statistics if entry else {},
        }
    fresh = bool(demand and demand.fresh())
    print(json.dumps({"backend": profile.backend, "nachfrage_aktuell": fresh, "klassen": rows}, indent=2))
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    """Delete this machine's scale sets (after ``runner uninstall``); running jobs are not touched."""
    profile = _profile(args)
    api = scaleset_listener.client_for(profile)
    group = api.runner_group_id(profile.scale_set.runner_group)
    for name in sorted(args.klasse or profile.classes):
        scale_set_id = api.find_scale_set(profile.scale_set_name(name), group)
        if scale_set_id is None:
            continue
        if args.trockenlauf:
            print(f"würde löschen: {profile.scale_set_name(name)} ({scale_set_id})")
        else:
            api.delete_scale_set(scale_set_id)
            print(f"gelöscht: {profile.scale_set_name(name)}")
    return 0


def add_scaleset_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    group = sub.add_parser("scaleset", help="Backend „scaleset“: Listener, JIT, Aufräumen").add_subparsers(
        dest="aktion", required=True
    )
    group.add_parser("lauschen", help="Listener für alle aktiven Klassen (von systemd gestartet)").set_defaults(
        func=cmd_listen
    )
    jit = group.add_parser("jit", help="JIT-Konfiguration aus dem Scale-Set (für den Supervisor)")
    jit.add_argument("klasse")
    jit.add_argument("name")
    jit.set_defaults(func=cmd_jit)
    remove = group.add_parser("entfernen", help="Runner-Registrierung im Scale-Set löschen")
    remove.add_argument("runner_id", type=int)
    remove.set_defaults(func=cmd_remove)
    group.add_parser("anzeigen", help="Scale-Sets, Soll und Warteschlange je Klasse").set_defaults(func=cmd_show)
    delete = group.add_parser("loeschen", help="Scale-Sets dieses Rechners löschen")
    delete.add_argument("--klasse", action="append")
    delete.add_argument("--trockenlauf", action="store_true")
    delete.set_defaults(func=cmd_delete)
