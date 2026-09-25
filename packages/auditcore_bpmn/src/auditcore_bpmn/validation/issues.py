"""Ergebnisse der Prüfregeln: :class:`ValidationIssue` und :class:`ValidationReport`.

Bewusst nicht „Feststellung“ genannt: Prüffeststellungen im fachlichen Sinn
sind :class:`auditcore_bpmn.extensions.AuditFinding` (``flowaudit:feststellung``).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ..vocabulary import label
from .messages import ERROR, MESSAGES, NOTE, SEVERITY_LABELS, WARNING

RULESET_VERSION = "2026.09.1"
REPORT_SCHEMA = "auditcore_bpmn.validation-report/1"


@dataclass(frozen=True)
class ValidationIssue:
    """Treffer einer Prüfregel an einem Element, am Diagramm oder an der Sammlung."""

    rule_id: str
    severity: str
    params: Mapping[str, object] = field(default_factory=dict)
    element_id: str | None = None
    diagram_id: str | None = None
    #: Meldungsvorlage, falls sie von der Regel-ID abweicht (Funktionstrennung aus dem Profil).
    message_id: str | None = None

    def message(self, language: str = "de") -> str:
        """Meldungstext in ``language`` (``de`` oder ``en``)."""
        return MESSAGES[self.message_id or self.rule_id].render(language, self.params)

    def to_dict(self, language: str = "de") -> dict[str, object]:
        """JSON-fähige Darstellung."""
        data: dict[str, object] = {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "severity_label": label(SEVERITY_LABELS[self.severity], language),
            "message": self.message(language),
            "params": dict(self.params),
        }
        if self.element_id:
            data["element_id"] = self.element_id
        if self.diagram_id:
            data["diagram_id"] = self.diagram_id
        return data


def issue(rule_id: str, element_id: str | None = None, **params: object) -> ValidationIssue:
    """Treffer mit dem Schweregrad aus dem Meldungskatalog."""
    return ValidationIssue(rule_id, MESSAGES[rule_id].severity, params, element_id)


@dataclass(frozen=True)
class ValidationReport:
    """Ergebnis einer Prüfung mit Profil, Stichtag und Regelwerksversion."""

    issues: tuple[ValidationIssue, ...]
    profile: str
    profile_origin: str
    reference_date: str | None
    ruleset_version: str = RULESET_VERSION

    def _by(self, severity: str) -> tuple[ValidationIssue, ...]:
        return tuple(i for i in self.issues if i.severity == severity)

    @property
    def errors(self) -> tuple[ValidationIssue, ...]:
        """Treffer der Schwere Fehler."""
        return self._by(ERROR)

    @property
    def warnings(self) -> tuple[ValidationIssue, ...]:
        """Treffer der Schwere Warnung."""
        return self._by(WARNING)

    @property
    def notes(self) -> tuple[ValidationIssue, ...]:
        """Treffer der Schwere Hinweis."""
        return self._by(NOTE)

    @property
    def is_valid(self) -> bool:
        """``True``, wenn keine Regel der Schwere Fehler anschlägt."""
        return not self.errors

    def rule_ids(self) -> list[str]:
        """Regel-IDs aller Treffer."""
        return [i.rule_id for i in self.issues]

    def to_dict(self, language: str = "de") -> dict[str, object]:
        """JSON nach ``validation-report-1.schema.json``."""
        return {
            "schema": REPORT_SCHEMA,
            "ruleset_version": self.ruleset_version,
            "profile": self.profile,
            "profile_origin": self.profile_origin,
            "reference_date": self.reference_date,
            "valid": self.is_valid,
            "counts": {ERROR: len(self.errors), WARNING: len(self.warnings), NOTE: len(self.notes)},
            "issues": [i.to_dict(language) for i in self.issues],
        }
