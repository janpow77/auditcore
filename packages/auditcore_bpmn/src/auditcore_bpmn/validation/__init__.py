"""Prüfregeln mit stabilen IDs und zweisprachigen Meldungen.

Gruppen: ``structure`` (``BPMN-S…``), ``content`` (``BPMN-F…``),
``audit_authority`` (``BPMN-P…``) und ``segregation`` (``BPMN-FT…`` aus dem
Profil). Sammlungsregeln (``BPMN-K…``) prüft
:meth:`auditcore_bpmn.collection.DiagramCollection.validate`.
"""

from .context import ValidationConfig, ValidationContext
from .engine import validate
from .issues import RULESET_VERSION, ValidationIssue, ValidationReport, issue
from .messages import ERROR, MESSAGES, NOTE, SEVERITIES, WARNING, RuleMessage
from .registry import RULES, RegisteredRule, rule, rules_for

__all__ = [
    "ERROR",
    "MESSAGES",
    "NOTE",
    "RULES",
    "RULESET_VERSION",
    "SEVERITIES",
    "WARNING",
    "RegisteredRule",
    "RuleMessage",
    "ValidationConfig",
    "ValidationContext",
    "ValidationIssue",
    "ValidationReport",
    "issue",
    "rule",
    "rules_for",
    "validate",
]
