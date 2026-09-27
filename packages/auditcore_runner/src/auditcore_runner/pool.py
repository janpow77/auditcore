"""Target instance counts per class – the contract with an external regulator.

JSON Schema: ``data/schemas/runner-pool.schema.json``. Written by an external regulator
(target source ``datei``) or by the built-in autoscaler (``lokal``); read by
every supervisor before it registers. A missing file or class means "profile
maximum".
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .profile import CLASS_NAME
from .profile_io import write_atomic

POOL_SCHEMA = "auditcore-runner/runner-pool/1"
LEGACY_SCHEMAS = ("auditcore-pruefbank/runner-pool/1",)
MAX_TARGET = 32


class PoolFormatError(ValueError):
    """The pool file does not follow the contract."""


@dataclass(frozen=True)
class Pool:
    targets: dict[str, int]
    updated: str = ""
    source: str = ""
    reasons: dict[str, list[str]] = field(default_factory=dict)
    user_priority: bool = False
    blocked_cards: tuple[str, ...] = ()


def _target(name: str, entry: object) -> int:
    value = entry.get("soll") if isinstance(entry, dict) else None
    if not CLASS_NAME.fullmatch(name):
        raise PoolFormatError(f"klassen.{name}: ungültiger Klassenname")
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= MAX_TARGET:
        raise PoolFormatError(f"klassen.{name}.soll: ganze Zahl 0–{MAX_TARGET} erwartet")
    return value


def _reasons(entry: object) -> list[str]:
    value = entry.get("gruende", []) if isinstance(entry, dict) else []
    return [str(item) for item in value] if isinstance(value, list) else []


def parse(raw: object) -> Pool:
    if not isinstance(raw, dict) or raw.get("schema") not in (POOL_SCHEMA, *LEGACY_SCHEMAS):
        raise PoolFormatError(f"schema: erwartet {POOL_SCHEMA}")
    classes = raw.get("klassen")
    if not isinstance(classes, dict):
        raise PoolFormatError("klassen: Objekt erwartet")
    targets = {name: _target(name, entry) for name, entry in classes.items()}
    reasons = {name: _reasons(entry) for name, entry in classes.items()}
    updated = raw.get("aktualisiert")
    source = raw.get("quelle")
    blocked = raw.get("karten_gesperrt", [])
    return Pool(
        targets,
        updated if isinstance(updated, str) else "",
        source if isinstance(source, str) else "",
        {k: v for k, v in reasons.items() if v},
        raw.get("nutzer_vorrang") is True,
        tuple(str(x) for x in blocked) if isinstance(blocked, list) else (),
    )


def load(path: Path | None) -> Pool | None:
    """The pool, or None when there is no file (or no pool for static targets)."""
    if path is None or not path.exists():
        return None
    return parse(json.loads(path.read_text(encoding="utf-8")))


def to_json(pool: Pool) -> dict[str, object]:
    classes: dict[str, object] = {}
    for name, value in sorted(pool.targets.items()):
        entry: dict[str, object] = {"soll": value}
        if pool.reasons.get(name):
            entry["gruende"] = pool.reasons[name]
        classes[name] = entry
    document: dict[str, object] = {
        "schema": POOL_SCHEMA,
        "klassen": classes,
        "aktualisiert": pool.updated,
        "quelle": pool.source,
    }
    if pool.user_priority:
        document["nutzer_vorrang"] = True
    if pool.blocked_cards:
        document["karten_gesperrt"] = list(pool.blocked_cards)
    return document


def save(pool: Pool, path: Path) -> Path:
    stamped = Pool(
        pool.targets,
        pool.updated or datetime.now().astimezone().isoformat(timespec="seconds"),
        pool.source,
        pool.reasons,
        pool.user_priority,
        pool.blocked_cards,
    )
    parse(to_json(stamped))
    write_atomic(path, json.dumps(to_json(stamped), indent=2, ensure_ascii=False) + "\n")
    return path


def parse_assignments(items: list[str]) -> dict[str, int]:
    """``["cpu-gross=2", "gpu-16gb=0"]`` → mapping (CLI input)."""
    result: dict[str, int] = {}
    for item in items:
        name, sep, value = item.partition("=")
        if not sep or not value.strip().isdigit():
            raise PoolFormatError(f"{item}: Form KLASSE=ZAHL erwartet")
        result[name.strip()] = _target(name.strip(), {"soll": int(value)})
    return result
