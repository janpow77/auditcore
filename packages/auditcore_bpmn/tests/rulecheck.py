"""Hilfe für Regeltests: Treffer einer Regel in einem Dokument."""

from __future__ import annotations

from helpers import STICHTAG

from auditcore_bpmn.model import parse_bpmn
from auditcore_bpmn.validation import ValidationConfig, ValidationIssue, validate


def hits(xml: str, rule_id: str, **config: object) -> list[ValidationIssue]:
    report = validate(parse_bpmn(xml), ValidationConfig(reference_date=STICHTAG, **config))  # type: ignore[arg-type]
    return [i for i in report.issues if i.rule_id == rule_id]


def elements(xml: str, rule_id: str) -> list[str | None]:
    return [i.element_id for i in hits(xml, rule_id)]
