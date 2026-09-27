"""Check and apply a profile – shared by CLI (``profil pruefen|anwenden``), web API and external tools.

Every accepted change raises ``version`` and records who changed it. An
optional expected version detects concurrent edits (local UI vs. central
management): on mismatch nothing is written and the result reports a conflict
with the diff between the active and the proposed profile.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from pathlib import Path

from . import install, profile_io
from .hardware import HostFacts
from .profile import Change, Profile
from .validation import validate


def _active(path: Path) -> Profile | None:
    return profile_io.load(path) if path.exists() else None


def evaluate(raw: object, path: Path, facts: HostFacts) -> tuple[Profile, dict[str, object]]:
    """Validation findings, file diffs and the commands apply would run (no side effects)."""
    candidate = profile_io.from_json(raw)
    active = _active(path)
    problems = validate(candidate, facts)
    profile_change = install.FileChange(path, profile_io.dumps(active) if active else None, profile_io.dumps(candidate))
    changes = [profile_change, *install.plan(candidate, path)]
    result: dict[str, object] = {
        "gueltig": not problems,
        "probleme": [p.as_dict() for p in problems],
        "aktive_version": active.version if active else None,
        "aenderungen": [{"datei": str(c.path), "diff": c.diff()} for c in changes if c.changed],
        "schritte": [s.text() for s in install.instance_steps(candidate)],
        "netzsperre_befehl": install.firewall_command() if candidate.network.enabled else None,
    }
    return candidate, result


def apply(
    raw: object,
    path: Path,
    facts: HostFacts,
    *,
    source: str,
    who: str,
    expected_version: int | None = None,
    run: bool = True,
) -> dict[str, object]:
    """Validate, detect conflicts, then save with a raised version and apply units/Docker steps."""
    candidate, result = evaluate(raw, path, facts)
    active = _active(path)
    current_version = active.version if active else 0
    if expected_version is not None and expected_version != current_version:
        return {
            **result,
            "angewendet": False,
            "konflikt": True,
            "meldung": f"Profil wurde inzwischen geändert (Version {current_version}, erwartet {expected_version}) "
            f"– zuletzt {active.change.source if active else '–'}",
        }
    if not result["gueltig"]:
        return {**result, "angewendet": False, "konflikt": False, "meldung": "Profil hat Fehler, nichts angewendet"}
    stamped = replace(
        candidate,
        version=current_version + 1,
        change=Change(datetime.now().astimezone().isoformat(timespec="seconds"), source, who),
    )
    profile_io.save(stamped, path)
    written = install.write_changes(install.plan(stamped, path))
    errors: list[str] = []
    if run:
        steps = install.docker_steps(
            stamped, install.image_present(stamped.image), install.network_present(stamped.network.name)
        )
        errors = install.run_steps([*steps, *install.instance_steps(stamped)])
    return {
        **result,
        "angewendet": True,
        "konflikt": False,
        "version": stamped.version,
        "profil_hash": profile_io.content_hash(stamped),
        "geschriebene_dateien": [str(p) for p in written],
        "fehler": errors,
    }
