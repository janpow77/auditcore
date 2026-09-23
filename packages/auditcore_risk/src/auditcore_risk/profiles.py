"""Versioned, source-bound rule profiles.

A profile is the complete, explicit statement of one rule set: codes, labels,
rule kinds with every threshold/weight/matching parameter, the output and
summary format and the source it was characterized from. Legacy profiles
reproduce one source exactly; nothing here merges, harmonises or re-weights
profiles, and no profile is an implicit default.
"""

from __future__ import annotations

import hashlib
import json
import string
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import resources
from types import MappingProxyType
from typing import Any

from .base import WHEN_MISSING
from .errors import ProfileError
from .rules import KINDS, validate_params

SCHEMA = "auditcore_risk.profile/1"
STATUSES = frozenset({"LEGACY_CHARACTERIZED", "CANDIDATE_HUMAN_DECISION_REQUIRED", "APPROVED"})
INTERPRETATIONS = frozenset({"indicator", "descriptive_prior"})
SUMMARY_FORMATS = frozenset({"riskanalysis.red_flag_summary", "flowstat.counts", "none"})
SEVERITIES = ("INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL")
MESSAGE_PARTS = frozenset({"description", "evidence", "recommendation"})
_TOP_KEYS = frozenset(
    {
        "schema",
        "id",
        "version",
        "kind",
        "status",
        "legal_status",
        "source",
        "rules",
        "output",
        "summary",
        "open_decisions",
        "assessment",
    }
)
_RULE_KEYS = frozenset(
    {
        "code",
        "label",
        "kind",
        "params",
        "requires",
        "when_missing_columns",
        "column",
        "interpretation",
        "note",
        "origin",
        "severity",
        "messages",
        "echo_fields",
        "points",
    }
)


@dataclass(frozen=True)
class Rule:
    """One flag rule; ``params`` hold every fachliche setting explicitly."""

    code: str
    label: str
    kind: str
    params: Mapping[str, Any]
    requires: tuple[str, ...]
    when_missing_columns: str
    column: str | None
    interpretation: str
    note: str | None
    origin: Mapping[str, Any]
    severity: str | None = None
    messages: Mapping[str, Mapping[str, str]] | None = None
    echo_fields: Mapping[str, str] | None = None
    points: float | None = None

    @property
    def scope(self) -> str:
        """``record`` (flag per record) or ``dataset`` (one finding per evaluation)."""
        return KINDS[self.kind].scope


@dataclass(frozen=True)
class RiskProfile:
    """Immutable rule profile with identity, source and fingerprint."""

    id: str
    version: str
    kind: str
    status: str
    legal_status: str
    source: Mapping[str, Any]
    rules: tuple[Rule, ...]
    output: Mapping[str, Any]
    summary: Mapping[str, Any]
    open_decisions: tuple[str, ...]
    fingerprint: str
    assessment: Mapping[str, Any] | None = None

    @property
    def reference(self) -> dict[str, str]:
        """Identity recorded with every result that used this profile."""
        return {
            "id": self.id,
            "version": self.version,
            "fingerprint": self.fingerprint,
            "status": self.status,
        }

    def rule(self, code: str) -> Rule:
        """The rule with ``code``; unknown codes are an error, not ``None``."""
        for rule in self.rules:
            if rule.code == code:
                return rule
        raise ProfileError(f"Profil {self.id} enthält keine Regel {code!r}.")


def fingerprint(data: Mapping[str, Any]) -> str:
    """SHA-256 of the canonical JSON profile document."""
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


def _text(data: Mapping[str, Any], key: str, where: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ProfileError(f"{where}: {key!r} muss ein nicht leerer Text sein.")
    return value


def check_template(template: Any, where: str) -> None:
    """Message templates may only reference plain names (no attribute/index access)."""
    if not isinstance(template, str):
        raise ProfileError(f"{where}: Textvorlage muss Text sein.")
    try:
        parts = list(string.Formatter().parse(template))
    except ValueError as exc:
        raise ProfileError(f"{where}: ungültige Textvorlage: {exc}") from exc
    for _literal, name, spec, conversion in parts:
        if name is None:
            continue
        if not name.isidentifier() or conversion not in (None, "") or (spec and "{" in spec):
            raise ProfileError(f"{where}: unzulässiger Platzhalter {name!r}.")


def _messages(data: Any, where: str) -> Mapping[str, Mapping[str, str]] | None:
    if data is None:
        return None
    if not isinstance(data, dict) or not data:
        raise ProfileError(f"{where}: 'messages' muss ein Objekt je Variante sein.")
    for variant, parts in data.items():
        if not isinstance(parts, dict) or set(parts) != MESSAGE_PARTS:
            raise ProfileError(f"{where}: Variante {variant!r} braucht {sorted(MESSAGE_PARTS)}.")
        for template in parts.values():
            check_template(template, where)
    frozen: Mapping[str, Mapping[str, str]] = _freeze(data)
    return frozen


def _rule_from_dict(data: Any, index: int) -> Rule:
    where = f"Regel {index + 1}"
    if not isinstance(data, dict):
        raise ProfileError(f"{where} muss ein Objekt sein.")
    unknown = set(data) - _RULE_KEYS
    if unknown:
        raise ProfileError(f"{where}: unbekannte Felder {sorted(unknown)}.")
    kind = _text(data, "kind", where)
    if kind not in KINDS:
        raise ProfileError(f"{where}: unbekannte Regelart {kind!r}.")
    requires = data.get("requires", [])
    if not isinstance(requires, list) or not all(isinstance(c, str) for c in requires):
        raise ProfileError(f"{where}: 'requires' muss eine Liste von Spalten sein.")
    when = data.get("when_missing_columns", "error")
    if when not in WHEN_MISSING:
        raise ProfileError(f"{where}: 'when_missing_columns' muss eine von {WHEN_MISSING} sein.")
    interpretation = data.get("interpretation", "indicator")
    if interpretation not in INTERPRETATIONS:
        raise ProfileError(f"{where}: unbekannte Interpretation {interpretation!r}.")
    column = data.get("column")
    if column is not None and not isinstance(column, str):
        raise ProfileError(f"{where}: 'column' muss Text sein.")
    note = data.get("note")
    if note is not None and not isinstance(note, str):
        raise ProfileError(f"{where}: 'note' muss Text sein.")
    origin = data.get("origin")
    if not isinstance(origin, dict) or not origin.get("symbol"):
        raise ProfileError(f"{where}: 'origin' mit Quellsymbol ist Pflicht.")
    params = data.get("params")
    if not isinstance(params, dict):
        raise ProfileError(f"{where}: 'params' muss ein Objekt sein.")
    validate_params(kind, params, where)
    severity = data.get("severity")
    if severity is not None and severity not in SEVERITIES:
        raise ProfileError(f"{where}: unbekannte Schwere {severity!r}.")
    points = data.get("points")
    if points is not None and (isinstance(points, bool) or not isinstance(points, int | float)):
        raise ProfileError(f"{where}: 'points' muss eine Zahl sein.")
    echo = data.get("echo_fields")
    if echo is not None and (
        not isinstance(echo, dict)
        or not all(
            isinstance(k, str) and k.isidentifier() and isinstance(v, str) for k, v in echo.items()
        )
    ):
        raise ProfileError(f"{where}: 'echo_fields' muss Name → Feld zuordnen.")
    return Rule(
        code=_text(data, "code", where),
        label=_text(data, "label", where),
        kind=kind,
        params=_freeze(params),
        requires=tuple(requires),
        when_missing_columns=when,
        column=column,
        interpretation=interpretation,
        note=note,
        origin=_freeze(origin),
        severity=severity,
        messages=_messages(data.get("messages"), where),
        echo_fields=None if echo is None else _freeze(echo),
        points=points,
    )


def profile_from_dict(data: Mapping[str, Any]) -> RiskProfile:
    """Validate a profile document; nothing is defaulted silently."""
    if not isinstance(data, Mapping):
        raise ProfileError("Profil muss ein Objekt sein.")
    unknown = set(data) - _TOP_KEYS
    if unknown:
        raise ProfileError(f"Profil: unbekannte Felder {sorted(unknown)}.")
    if data.get("schema") != SCHEMA:
        raise ProfileError("Unbekanntes Profilschema.")
    status = _text(data, "status", "Profil")
    if status not in STATUSES:
        raise ProfileError(f"Unbekannter Profilstatus {status!r}.")
    source = data.get("source")
    if not isinstance(source, dict) or not source:
        raise ProfileError("Profil ohne Quellenangabe.")
    raw_rules = data.get("rules")
    if not isinstance(raw_rules, list) or not raw_rules:
        raise ProfileError("Profil ohne Regeln.")
    rules = tuple(_rule_from_dict(r, i) for i, r in enumerate(raw_rules))
    codes = [r.code for r in rules]
    if len(set(codes)) != len(codes):
        raise ProfileError("Regelcodes sind nicht eindeutig.")
    columns = [r.column for r in rules if r.column is not None]
    if len(set(columns)) != len(columns):
        raise ProfileError("Ausgabespalten sind nicht eindeutig.")
    output = data.get("output", {})
    summary = data.get("summary")
    if not isinstance(output, dict) or not isinstance(summary, dict):
        raise ProfileError("'output' und 'summary' müssen Objekte sein.")
    if summary.get("format") not in SUMMARY_FORMATS:
        raise ProfileError(f"Unbekanntes Zusammenfassungsformat {summary.get('format')!r}.")
    if summary["format"] == "riskanalysis.red_flag_summary" and not isinstance(
        summary.get("amount_field"), str
    ):
        raise ProfileError("Zusammenfassung verlangt 'amount_field'.")
    assessment = data.get("assessment")
    if assessment is not None:
        _check_assessment(assessment, rules)
    decisions = data.get("open_decisions", [])
    if not isinstance(decisions, list) or not all(isinstance(d, str) for d in decisions):
        raise ProfileError("'open_decisions' muss eine Liste von Texten sein.")
    return RiskProfile(
        id=_text(data, "id", "Profil"),
        version=_text(data, "version", "Profil"),
        kind=_text(data, "kind", "Profil"),
        status=status,
        legal_status=_text(data, "legal_status", "Profil"),
        source=_freeze(dict(source)),
        rules=rules,
        output=_freeze(dict(output)),
        summary=_freeze(dict(summary)),
        open_decisions=tuple(decisions),
        fingerprint=fingerprint(data),
        assessment=None if assessment is None else _freeze(dict(assessment)),
    )


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


def _check_points(data: dict[str, Any], rules: tuple[Rule, ...]) -> None:
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


def _check_assessment(data: Any, rules: tuple[Rule, ...]) -> None:
    """Profile-local legacy aggregation (weights/points); never across profiles."""
    where = "assessment"
    if isinstance(data, dict) and data.get("kind") == "points_stages":
        _check_points(data, rules)
        return
    if not isinstance(data, dict) or set(data) != _ASSESSMENT_KEYS:
        raise ProfileError(f"{where}: Felder {sorted(_ASSESSMENT_KEYS)} sind Pflicht.")
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
    summary = data["summary"]
    if not isinstance(summary, dict) or set(summary) != _SUMMARY_KEYS:
        raise ProfileError(f"{where}: summary braucht {sorted(_SUMMARY_KEYS)}.")
    for key in ("none", "one", "many"):
        check_template(summary[key], where)
    if not all(r.severity is not None or KINDS[r.kind].derives_severity for r in rules):
        raise ProfileError(f"{where}: jede Regel braucht eine Schwere.")


def _packaged() -> dict[tuple[str, str], Any]:
    found = {}
    for entry in resources.files("auditcore_risk.profile_data").iterdir():
        if entry.name.endswith(".json"):
            data = json.loads(entry.read_text(encoding="utf-8"))
            found[(str(data["id"]), str(data["version"]))] = entry
    return found


def available_profiles() -> tuple[tuple[str, str], ...]:
    """Packaged ``(id, version)`` pairs; none of them is an implicit default."""
    return tuple(sorted(_packaged()))


def load_profile(profile_id: str, version: str) -> RiskProfile:
    """Load an explicitly named packaged profile version."""
    if not isinstance(profile_id, str) or not isinstance(version, str):
        raise ProfileError("Profilkennung und Version sind als Text anzugeben.")
    entry = _packaged().get((profile_id, version))
    if entry is None:
        raise ProfileError(f"Profil {profile_id} in Version {version} ist nicht vorhanden.")
    return profile_from_dict(json.loads(entry.read_text(encoding="utf-8")))
