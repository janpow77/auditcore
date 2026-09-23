"""Helpers shared by the replay tests: fixture access and type-preserving comparison."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).parent / "fixtures"
FILES = FIXTURES / "files"
OBSERVED = json.loads((FIXTURES / "legacy_observed.json").read_text(encoding="utf-8"))
CASES = OBSERVED["cases"]
BY_NAME = {c["name"]: c for c in CASES}


def cases(operation: str) -> list[dict[str, Any]]:
    """All recorded cases of one operation."""
    return [c for c in CASES if c["operation"] == operation]


def jsonable(value: Any) -> Any:
    """Same encoding as ``tools/capture_legacy.py``."""
    if isinstance(value, bool) or value is None or isinstance(value, (int, str)):
        return value
    if isinstance(value, float):
        return {"$float": repr(value)}
    if isinstance(value, datetime):
        return {"$datetime": value.isoformat()}
    if isinstance(value, date):
        return {"$date": value.isoformat()}
    if isinstance(value, bytes):
        return {"$bytes": value.decode("utf-8", errors="replace")}
    if is_dataclass(value) and not isinstance(value, type):
        return {"$dataclass": type(value).__name__, "fields": jsonable(asdict(value))}
    if isinstance(value, dict):
        return {"$dict": [[jsonable(k), jsonable(v)] for k, v in value.items()]}
    if isinstance(value, tuple):
        return {"$tuple": [jsonable(v) for v in value]}
    if isinstance(value, (list, set, frozenset)):
        items = list(value) if isinstance(value, list) else sorted(value, key=repr)
        return [jsonable(v) for v in items]
    return {"$repr": repr(value), "type": type(value).__name__}


def norm(value: Any) -> Any:
    """Comparable form: dataclasses as dicts, types of dates/tuples/floats kept."""
    if isinstance(value, dict):
        if "$dict" in value:
            return {norm(k): norm(v) for k, v in value["$dict"]}
        if "$float" in value:
            return ("float", float(value["$float"]))
        if "$dataclass" in value:
            return norm(value["fields"])
        if "$tuple" in value:
            return tuple(norm(v) for v in value["$tuple"])
        for tag in ("$date", "$datetime", "$bytes"):
            if tag in value:
                return (tag, value[tag])
        return {k: norm(v) for k, v in value.items()}
    if isinstance(value, list):
        return [norm(v) for v in value]
    return value


def same(mine: Any, recorded: Any) -> bool:
    """``True`` if the library output equals the recorded original output."""
    return bool(norm(jsonable(mine)) == norm(recorded))


def plain(value: Any) -> Any:
    """Recorded value as plain Python (dates as ISO text)."""
    if isinstance(value, dict):
        if "$dict" in value:
            return {plain(k): plain(v) for k, v in value["$dict"]}
        if "$float" in value:
            return float(value["$float"])
        if "$dataclass" in value:
            return plain(value["fields"])
        if "$tuple" in value:
            return tuple(plain(v) for v in value["$tuple"])
        for tag in ("$date", "$datetime", "$bytes"):
            if tag in value:
                return value[tag]
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [plain(v) for v in value]
    return value


def csv_rows(name: str) -> list[dict[str, str]]:
    """Rows of a fixture CSV as ``csv.DictReader`` yields them."""
    with (FILES / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))
