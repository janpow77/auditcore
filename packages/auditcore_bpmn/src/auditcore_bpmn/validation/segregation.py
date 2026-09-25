"""Funktionstrennung (``BPMN-FT…``): Regeln aus dem Profil, Meldungen aus dem Katalog."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..model import BpmnElement
from ..profiles import SegregationRule, Selection
from ..vocabulary import label
from .context import ValidationContext
from .issues import ValidationIssue
from .messages import MESSAGES, SEVERITIES
from .registry import rule

Issues = Iterator[ValidationIssue]


def _issue(
    ctx: ValidationContext, spec: SegregationRule, message_id: str, element: BpmnElement, **params: Any
) -> ValidationIssue:
    severity = spec.severity if spec.severity in SEVERITIES else MESSAGES[message_id].severity
    titles = {"titel": label(spec.title), "titel_de": label(spec.title, "de"), "titel_en": label(spec.title, "en")}
    return ValidationIssue(f"BPMN-{spec.id}", severity, {**titles, **params}, element.id, message_id=message_id)


def matches(element: BpmnElement, selection: Selection) -> bool:
    """Aktivität passt über ein Kennzeichen oder die Prüfart eines Prüfbezugs."""
    ext = element.extensions
    if set(selection.markers) & set(ext.marker_types()):
        return True
    return bool(selection.audit_types) and any(r.audit_type in selection.audit_types for r in ext.audit_references)


def _selected(ctx: ValidationContext, selection: Selection) -> list[BpmnElement]:
    return [e for e in ctx.document.flow_nodes if e.is_activity and matches(e, selection)]


def separate_bodies(ctx: ValidationContext, spec: SegregationRule) -> Issues:
    """Zwei Tätigkeitsarten dürfen nicht bei derselben Stelle liegen."""
    for first in _selected(ctx, spec.a):
        body = ctx.body_of(first)
        for second in _selected(ctx, spec.b):
            other = ctx.body_of(second)
            if first.id != second.id and body and other and body[0] == other[0]:
                yield _issue(ctx, spec, "BPMN-FT-STELLEN", first, a=first.label, b=second.label, stelle=body[1])


def excluded_role(ctx: ValidationContext, spec: SegregationRule) -> Issues:
    """Eine Tätigkeitsart darf nicht bei bestimmten Rollen liegen."""
    for element in _selected(ctx, spec.selection):
        _where, actor = ctx.document.actor_of(element)
        if actor is not None and actor.role in spec.roles:
            yield _issue(ctx, spec, "BPMN-FT-ROLLE", element, name=element.label, rolle=actor.role)


def _second_party(ctx: ValidationContext, element: BpmnElement) -> bool:
    own = ctx.body_of(element)
    for successor in ctx.successors(element):
        other = ctx.body_of(successor)
        if own and other and other[0] != own[0]:
            return True
    own_role = ctx.document.actor_of(element)[1]
    return any(
        c.responsible and (own_role is None or c.responsible != own_role.role) for c in element.extensions.controls
    )


def four_eyes(ctx: ValidationContext, spec: SegregationRule) -> Issues:
    """Vier-Augen-Kennzeichen braucht eine zweite Stelle oder Rolle."""
    for element in ctx.document.flow_nodes:
        if "vier_augen" in element.extensions.marker_types() and not _second_party(ctx, element):
            yield _issue(ctx, spec, "BPMN-FT-VIERAUGEN", element, name=element.label)


_KINDS = {"separate_bodies": separate_bodies, "excluded_role": excluded_role, "four_eyes": four_eyes}


@rule("segregation", "BPMN-FT…")
def check_segregation(ctx: ValidationContext) -> Issues:
    """Alle Funktionstrennungsregeln des Profils; unbekannte Arten werden übergangen."""
    for spec in ctx.profile.segregation_rules:
        handler = _KINDS.get(spec.kind)
        if handler is not None:
            yield from handler(ctx, spec)
