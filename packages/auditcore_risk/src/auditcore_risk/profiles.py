"""Versioned, source-bound rule profiles.

A profile is the complete, explicit statement of one rule set: codes, labels,
rule kinds with every threshold/weight/matching parameter, the output and
summary format and the source it was characterized from. Legacy profiles
reproduce one source exactly; nothing here merges, harmonises or re-weights
profiles, and no profile is an implicit default.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from auditcore_common.frozen import freeze
from auditcore_common.hashing import canonical_sha256
from auditcore_common.profiles import packaged_profile_entries

from .assessment_schema import SEVERITIES, check_assessment
from .base import MISSING_AMOUNT_FIELD, WHEN_MISSING, JsonObject
from .errors import ProfileError
from .rules import KINDS, validate_params
from .templates import check_template

SCHEMA = "auditcore_risk.profile/1"
STATUSES = frozenset({"LEGACY_CHARACTERIZED", "CANDIDATE_HUMAN_DECISION_REQUIRED", "APPROVED"})
INTERPRETATIONS = frozenset({"indicator", "descriptive_prior"})
SUMMARY_FORMATS = frozenset({"riskanalysis.red_flag_summary", "flowstat.counts", "none"})
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
    params: JsonObject
    requires: tuple[str, ...]
    when_missing_columns: str
    column: str | None
    interpretation: str
    note: str | None
    origin: JsonObject
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
    source: JsonObject
    rules: tuple[Rule, ...]
    output: JsonObject
    summary: JsonObject
    open_decisions: tuple[str, ...]
    fingerprint: str
    assessment: JsonObject | None = None

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


def fingerprint(data: JsonObject) -> str:
    """SHA-256 of the canonical JSON profile document."""
    return canonical_sha256(data)


def _freeze(value: object) -> Any:
    """:func:`auditcore_common.frozen.freeze`, typed ``Any`` for the dataclass fields."""
    return freeze(value)


def _text(data: JsonObject, key: str, where: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ProfileError(f"{where}: {key!r} muss ein nicht leerer Text sein.")
    return value


def _messages(data: object, where: str) -> Mapping[str, Mapping[str, str]] | None:
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


def _rule_kind(data: object, where: str) -> str:
    if not isinstance(data, dict):
        raise ProfileError(f"{where} muss ein Objekt sein.")
    unknown = set(data) - _RULE_KEYS
    if unknown:
        raise ProfileError(f"{where}: unbekannte Felder {sorted(unknown)}.")
    kind = _text(data, "kind", where)
    if kind not in KINDS:
        raise ProfileError(f"{where}: unbekannte Regelart {kind!r}.")
    return kind


def _rule_columns(data: JsonObject, where: str) -> tuple[list[str], str]:
    """Required columns and what happens when one of them is absent."""
    requires = data.get("requires", [])
    if not isinstance(requires, list) or not all(isinstance(c, str) for c in requires):
        raise ProfileError(f"{where}: 'requires' muss eine Liste von Spalten sein.")
    when = data.get("when_missing_columns", "error")
    if when not in WHEN_MISSING:
        raise ProfileError(f"{where}: 'when_missing_columns' muss eine von {WHEN_MISSING} sein.")
    return requires, when


def _rule_texts(data: JsonObject, where: str) -> tuple[str, str | None, str | None]:
    """Interpretation, output column and note of the rule."""
    interpretation = data.get("interpretation", "indicator")
    if interpretation not in INTERPRETATIONS:
        raise ProfileError(f"{where}: unbekannte Interpretation {interpretation!r}.")
    column = data.get("column")
    if column is not None and not isinstance(column, str):
        raise ProfileError(f"{where}: 'column' muss Text sein.")
    note = data.get("note")
    if note is not None and not isinstance(note, str):
        raise ProfileError(f"{where}: 'note' muss Text sein.")
    return interpretation, column, note


def _check_undetermined(kind: str, params: JsonObject, requires: list[str], where: str) -> None:
    """``undetermined`` only for amount rules whose only required column is the amount."""
    amount_key = MISSING_AMOUNT_FIELD.get(kind)
    if amount_key is None or params.get("missing_amount_reason") is None:
        raise ProfileError(
            f"{where}: 'when_missing_columns' undetermined gilt nur für Betragsregeln "
            f"({sorted(MISSING_AMOUNT_FIELD)}) mit 'missing_amount_reason'."
        )
    if set(requires) - {params[amount_key]}:
        raise ProfileError(
            f"{where}: bei undetermined darf nur die Betragsspalte "
            f"{params[amount_key]!r} Pflichtspalte sein."
        )


def _rule_params(
    data: JsonObject, kind: str, requires: list[str], when: str, where: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Source origin and validated parameters of the rule."""
    origin = data.get("origin")
    if not isinstance(origin, dict) or not origin.get("symbol"):
        raise ProfileError(f"{where}: 'origin' mit Quellsymbol ist Pflicht.")
    params = data.get("params")
    if not isinstance(params, dict):
        raise ProfileError(f"{where}: 'params' muss ein Objekt sein.")
    validate_params(kind, params, where)
    if when == "undetermined":
        _check_undetermined(kind, params, requires, where)
    return origin, params


def _is_echo_map(echo: object) -> bool:
    return isinstance(echo, dict) and all(
        isinstance(k, str) and k.isidentifier() and isinstance(v, str) for k, v in echo.items()
    )


def _rule_scoring(
    data: JsonObject, where: str
) -> tuple[str | None, float | None, dict[str, str] | None]:
    """Severity, criterion points and echoed fields of the rule."""
    severity = data.get("severity")
    if severity is not None and severity not in SEVERITIES:
        raise ProfileError(f"{where}: unbekannte Schwere {severity!r}.")
    points = data.get("points")
    if points is not None and (isinstance(points, bool) or not isinstance(points, int | float)):
        raise ProfileError(f"{where}: 'points' muss eine Zahl sein.")
    echo = data.get("echo_fields")
    if echo is not None and not _is_echo_map(echo):
        raise ProfileError(f"{where}: 'echo_fields' muss Name → Feld zuordnen.")
    return severity, points, echo


def _rule_from_dict(data: Any, index: int) -> Rule:
    where = f"Regel {index + 1}"
    kind = _rule_kind(data, where)
    requires, when = _rule_columns(data, where)
    interpretation, column, note = _rule_texts(data, where)
    origin, params = _rule_params(data, kind, requires, when, where)
    severity, points, echo = _rule_scoring(data, where)
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


def _profile_status(data: object) -> str:
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
    return status


def _profile_rules(data: JsonObject) -> tuple[Rule, ...]:
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
    return rules


def _output_and_summary(data: JsonObject) -> tuple[dict[str, Any], dict[str, Any]]:
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
    return output, summary


def profile_from_dict(data: JsonObject) -> RiskProfile:
    """Validate a profile document; nothing is defaulted silently."""
    status = _profile_status(data)
    source = data.get("source")
    if not isinstance(source, dict) or not source:
        raise ProfileError("Profil ohne Quellenangabe.")
    rules = _profile_rules(data)
    output, summary = _output_and_summary(data)
    assessment = data.get("assessment")
    if assessment is not None:
        check_assessment(assessment, rules)
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


_RESOURCES = "auditcore_risk.profile_data"


def available_profiles() -> tuple[tuple[str, str], ...]:
    """Packaged ``(id, version)`` pairs; none of them is an implicit default."""
    return tuple(sorted(packaged_profile_entries(_RESOURCES)))


def load_profile(profile_id: str, version: str) -> RiskProfile:
    """Load an explicitly named packaged profile version."""
    if not isinstance(profile_id, str) or not isinstance(version, str):
        raise ProfileError("Profilkennung und Version sind als Text anzugeben.")
    entry = packaged_profile_entries(_RESOURCES).get((profile_id, version))
    if entry is None:
        raise ProfileError(f"Profil {profile_id} in Version {version} ist nicht vorhanden.")
    return profile_from_dict(json.loads(entry.read_text(encoding="utf-8")))
