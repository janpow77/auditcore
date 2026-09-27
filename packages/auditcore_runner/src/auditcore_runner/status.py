"""Machine status for humans, the web UI and external regulators (JSON file + Prometheus).

Status file (read-only contract for external tools): ``~/.local/state/auditcore-runner/status.json``.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

from . import github, install, nachfrage, pool
from .hardware import HostFacts
from .profile import Profile, state_dir
from .profile_io import CURRENT_SCHEMA, content_hash, write_atomic

STATUS_SCHEMA = "auditcore-runner/status/1"


def status_path() -> Path:
    return state_dir() / "status.json"


def active_instances(runner_class: str) -> int:
    try:
        result = subprocess.run(
            [
                "systemctl",
                "--user",
                "list-units",
                "--state=active",
                "--plain",
                "--no-legend",
                install.unit_name(runner_class, None).replace("@.", "@*."),
            ],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0
    return sum(1 for line in result.stdout.splitlines() if line.strip())


def _runner_counts(profile: Profile, runners: list[github.RunnerInfo]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {name: {"registriert": 0, "belegt": 0} for name in profile.classes}
    for runner in runners:
        if not runner.name.startswith(profile.runner_prefix()):
            continue
        name = github.class_of(runner.labels, profile)
        if name in counts:
            counts[name]["registriert"] += 1
            counts[name]["belegt"] += int(runner.busy)
    return counts


def unknown_runners(profile: Profile, runners: list[github.RunnerInfo]) -> list[str]:
    """Registered runners no configured machine owns – a warning sign (rogue registrations)."""
    return sorted(r.name for r in runners if not r.name.startswith(profile.known_prefixes()))


def unknown_details(profile: Profile, runners: list[github.RunnerInfo]) -> list[dict[str, object]]:
    """Unknown registrations with what they could take: a class match means they can steal our jobs."""
    return [
        {
            "name": r.name,
            "id": r.runner_id,
            "online": r.online,
            "belegt": r.busy,
            "labels": list(r.labels),
            "passt_zu_klasse": github.class_of(r.labels, profile),
        }
        for r in sorted(runners, key=lambda r: r.name)
        if not r.name.startswith(profile.known_prefixes())
    ]


def seen_path() -> Path:
    return state_dir() / "unbekannte_runner.json"


def new_unknown(names: list[str], path: Path | None = None) -> list[str]:
    """Names not reported before; remembers the current set (a vanished runner is reported again later)."""
    target = path or seen_path()
    try:
        seen = set(json.loads(target.read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError):
        seen = set()
    write_atomic(target, json.dumps(sorted(names)) + "\n")
    return sorted(set(names) - seen)


def _queue(demand: nachfrage.Demand | None, name: str) -> dict[str, object]:
    entry = demand.classes.get(name) if demand and demand.fresh() else None
    if entry is None:
        return {"warteschlange": None}
    result: dict[str, object] = {
        "warteschlange": entry.waiting,
        "warteschlange_quelle": demand.source if demand else "",
    }
    if entry.target is not None:
        result["nachfrage_soll"] = entry.target
    if entry.scale_set:
        result["scale_set"] = entry.scale_set
    if entry.statistics:
        result["scale_set_statistik"] = entry.statistics
    return result


def collect(profile: Profile, facts: HostFacts, client: github.Client | None) -> dict[str, object]:
    """Full status; GitHub numbers are omitted (null) when unreachable."""
    runners: list[github.RunnerInfo] | None = None
    if client is not None:
        try:
            runners = github.list_runners(client, profile.target)
        except github.GitHubError:
            runners = None
    counts = _runner_counts(profile, runners) if runners is not None else {}
    current = pool.load(profile.pool_path())
    demand = nachfrage.load()
    classes: dict[str, object] = {}
    for name, settings in sorted(profile.classes.items()):
        classes[name] = {
            "aktiv": settings.enabled,
            "max": settings.max_instances,
            "soll": current.targets.get(name) if current else None,
            "gruende": current.reasons.get(name, []) if current else [],
            "instanzen_aktiv": active_instances(name),
            **(counts.get(name) or {"registriert": None, "belegt": None}),
            **_queue(demand, name),
        }
    return {
        "schema": STATUS_SCHEMA,
        "zeit": datetime.now().astimezone().isoformat(timespec="seconds"),
        "rechner": profile.host,
        "profil_schema": CURRENT_SCHEMA,
        "profil_version": profile.version,
        "profil_hash": content_hash(profile),
        "aenderung": {"zeit": profile.change.time, "quelle": profile.change.source, "wer": profile.change.who},
        "sync": profile.sync,
        "ziel": profile.target.name,
        "soll_quelle": profile.source.kind,
        "backend": profile.backend,
        "hardware": facts.as_dict(),
        "klassen": classes,
        "image_vorhanden": install.image_present(profile.image),
        "netz_vorhanden": install.network_present(profile.network.name) if profile.network.enabled else None,
        "netzsperre_aktiv": install.FIREWALL_MARKER.exists() if profile.network.enabled else None,
        "unbekannte_runner": unknown_runners(profile, runners) if runners is not None else None,
        "unbekannte_runner_details": unknown_details(profile, runners) if runners is not None else None,
        "github_rest_kontingent": client.remaining if client else None,
    }


def write(status: dict[str, object], path: Path | None = None) -> Path:
    target = path or status_path()
    write_atomic(target, json.dumps(status, indent=2, ensure_ascii=False) + "\n")
    return target


def _metric(lines: list[str], name: str, value: object, labels: dict[str, str] | None = None) -> None:
    if isinstance(value, bool):
        value = int(value)
    if not isinstance(value, (int, float)):
        return
    rendered = ",".join(f'{k}="{v}"' for k, v in (labels or {}).items())
    lines.append(f"{name}{{{rendered}}} {value}" if rendered else f"{name} {value}")


def prometheus(status: dict[str, object]) -> str:
    """Prometheus text exposition of the status."""
    lines = [
        "# HELP auditcore_runner_instances Runner-Instanzen je Klasse und Zustand",
        "# TYPE auditcore_runner_instances gauge",
    ]
    host = str(status.get("rechner", ""))
    classes = status.get("klassen")
    for name, entry in classes.items() if isinstance(classes, dict) else []:
        if isinstance(entry, dict):
            for state in ("max", "soll", "instanzen_aktiv", "registriert", "belegt", "warteschlange", "nachfrage_soll"):
                _metric(
                    lines,
                    "auditcore_runner_instances",
                    entry.get(state),
                    {"rechner": host, "klasse": name, "zustand": state},
                )
    _metric(lines, "auditcore_runner_image_present", status.get("image_vorhanden"), {"rechner": host})
    _metric(lines, "auditcore_runner_firewall_active", status.get("netzsperre_aktiv"), {"rechner": host})
    _metric(lines, "auditcore_runner_github_rate_remaining", status.get("github_rest_kontingent"), {"rechner": host})
    unknown = status.get("unbekannte_runner")
    if isinstance(unknown, list):
        _metric(lines, "auditcore_runner_unknown_registered", len(unknown), {"rechner": host})
    details = status.get("unbekannte_runner_details")
    if isinstance(details, list):
        matching = [d for d in details if isinstance(d, dict) and d.get("passt_zu_klasse")]
        _metric(lines, "auditcore_runner_unknown_matching_class", len(matching), {"rechner": host})
    return "\n".join(lines) + "\n"
