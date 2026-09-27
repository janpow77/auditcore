"""Demand file: jobs waiting per class, written by the scale set listener or the local regulator.

Contract ``auditcore-runner/nachfrage/1`` in ``~/.local/state/auditcore-runner/nachfrage.json``::

    {"schema": "auditcore-runner/nachfrage/1", "quelle": "scaleset", "zeit_unix": 1790000000,
     "klassen": {"cpu": {"warteschlange": 2, "soll": 3, "statistik": {...}}}}

``warteschlange`` feeds the status JSON (external regulators need not ask
GitHub themselves). ``soll`` is only present with the scale set backend:
supervisors then also stay below it. A file older than :data:`FRESH_SECONDS`
is ignored, so a dead listener never blocks runners.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from .profile import state_dir
from .profile_io import write_atomic

SCHEMA = "auditcore-runner/nachfrage/1"
FRESH_SECONDS = 300


def demand_path() -> Path:
    return state_dir() / "nachfrage.json"


@dataclass(frozen=True)
class ClassDemand:
    waiting: int
    target: int | None = None
    statistics: dict[str, int] = field(default_factory=dict)
    scale_set: str = ""


@dataclass(frozen=True)
class Demand:
    source: str
    written: float
    classes: dict[str, ClassDemand]

    def fresh(self, now: float | None = None) -> bool:
        return (now if now is not None else time.time()) - self.written <= FRESH_SECONDS


def to_json(demand: Demand) -> dict[str, object]:
    classes: dict[str, object] = {}
    for name, entry in sorted(demand.classes.items()):
        item: dict[str, object] = {"warteschlange": entry.waiting}
        if entry.target is not None:
            item["soll"] = entry.target
        if entry.statistics:
            item["statistik"] = entry.statistics
        if entry.scale_set:
            item["scale_set"] = entry.scale_set
        classes[name] = item
    return {"schema": SCHEMA, "quelle": demand.source, "zeit_unix": int(demand.written), "klassen": classes}


def _number(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def parse(data: object) -> Demand | None:
    if not isinstance(data, dict) or data.get("schema") != SCHEMA or not isinstance(data.get("klassen"), dict):
        return None
    classes: dict[str, ClassDemand] = {}
    for name, entry in data["klassen"].items():
        if not isinstance(entry, dict):
            continue
        statistics = entry.get("statistik")
        classes[str(name)] = ClassDemand(
            _number(entry.get("warteschlange")) or 0,
            _number(entry.get("soll")),
            {str(k): v for k, v in statistics.items() if isinstance(v, int)} if isinstance(statistics, dict) else {},
            str(entry.get("scale_set", "")),
        )
    written = data.get("zeit_unix")
    return Demand(str(data.get("quelle", "")), float(written) if isinstance(written, int) else 0.0, classes)


def load(path: Path | None = None) -> Demand | None:
    try:
        return parse(json.loads((path or demand_path()).read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return None


def save(demand: Demand, path: Path | None = None) -> Path:
    target = path or demand_path()
    write_atomic(target, json.dumps(to_json(demand), indent=2, ensure_ascii=False) + "\n")
    return target


def merge(update: Demand, path: Path | None = None) -> Path:
    """Replace the classes in ``update`` and keep the others (one writer per class)."""
    current = load(path)
    classes = dict(current.classes) if current and current.source == update.source else {}
    classes.update(update.classes)
    return save(Demand(update.source, update.written, classes), path)
