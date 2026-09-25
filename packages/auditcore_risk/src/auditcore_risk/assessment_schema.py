"""Checks of a profile's own legacy aggregation block (``assessment``).

Two kinds exist: ``severity_weighted_sum`` (weights per severity) and
``points_stages`` (points per criterion and stages). Both aggregate within one
profile only.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from .base import JsonObject
from .errors import ProfileError
from .rules import KINDS
from .templates import check_template

if TYPE_CHECKING:
    from .profiles import Rule

SEVERITIES = ("INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL")

_ASSESSMENT_KEYS = frozenset(
    {
        "kind",
        "weights",
        "fallback_weight",
        "divisor",
        "cap",
        "severity_order",
        "summary",
        "source_version",
    }
)
_SUMMARY_KEYS = frozenset({"none", "one", "many", "level_words", "unknown_level"})


_POINTS_KEYS = frozenset(
    {
        "kind",
        "stages",
        "default_stage",
        "cap",
        "detail_template",
        "points_override",
        "source_version",
    }
)


def _check_points(data: JsonObject, rules: Sequence[Rule]) -> None:
    where = "assessment"
    if set(data) != _POINTS_KEYS:
        raise ProfileError(f"{where}: Felder {sorted(_POINTS_KEYS)} sind Pflicht.")
    if not all(r.points is not None for r in rules):
        raise ProfileError(f"{where}: jede Regel braucht Punkte.")
    if not isinstance(data["stages"], list):
        raise ProfileError(f"{where}: stages muss eine Liste sein.")
    minima = [s.get("min") for s in data["stages"]]
    if not all(isinstance(m, int | float) and not isinstance(m, bool) for m in minima) or (
        minima != sorted(minima, reverse=True)
    ):
        raise ProfileError(f"{where}: Stufen brauchen absteigende Mindestwerte.")
    if data["cap"] is not None and not isinstance(data["cap"], int | float):
        raise ProfileError(f"{where}: cap muss Zahl oder null sein.")
    if data["points_override"] not in ("forbidden", "allowed"):
        raise ProfileError(f"{where}: points_override muss forbidden/allowed sein.")
    if data["detail_template"] is not None:
        check_template(data["detail_template"], where)


def _check_summary_texts(data: JsonObject, where: str) -> None:
    summary = data["summary"]
    if not isinstance(summary, dict) or set(summary) != _SUMMARY_KEYS:
        raise ProfileError(f"{where}: summary braucht {sorted(_SUMMARY_KEYS)}.")
    for key in ("none", "one", "many"):
        check_template(summary[key], where)


def _check_weighted(data: JsonObject, rules: Sequence[Rule]) -> None:
    where = "assessment"
    if data["kind"] != "severity_weighted_sum":
        raise ProfileError(f"{where}: unbekannte Art {data['kind']!r}.")
    weights = data["weights"]
    if not isinstance(weights, dict) or set(weights) != set(SEVERITIES):
        raise ProfileError(f"{where}: Gewichte je Schwere {SEVERITIES} sind Pflicht.")
    numbers = [*weights.values(), data["fallback_weight"], data["divisor"], data["cap"]]
    if not all(isinstance(v, int | float) and not isinstance(v, bool) for v in numbers):
        raise ProfileError(f"{where}: Gewichte und Grenzen müssen Zahlen sein.")
    if data["divisor"] <= 0:
        raise ProfileError(f"{where}: divisor muss positiv sein.")
    if sorted(data["severity_order"]) != sorted(SEVERITIES):
        raise ProfileError(f"{where}: severity_order muss alle Schweregrade enthalten.")
    _check_summary_texts(data, where)
    if not all(r.severity is not None or KINDS[r.kind].derives_severity for r in rules):
        raise ProfileError(f"{where}: jede Regel braucht eine Schwere.")


def check_assessment(data: object, rules: Sequence[Rule]) -> None:
    """Profile-local legacy aggregation (weights/points); never across profiles."""
    if isinstance(data, dict) and data.get("kind") == "points_stages":
        _check_points(data, rules)
        return
    if not isinstance(data, dict) or set(data) != _ASSESSMENT_KEYS:
        raise ProfileError(f"assessment: Felder {sorted(_ASSESSMENT_KEYS)} sind Pflicht.")
    _check_weighted(data, rules)
