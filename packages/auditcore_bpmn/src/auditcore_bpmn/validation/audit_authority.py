"""Regeln der Prüfbehörden-Funktionen (``BPMN-P…``): Kontrollen, Risiken, Prüfpfad, Tests, Feststellungen."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Iterator, Mapping

from ..extensions import AuditFinding, Risk
from ..model import BpmnElement
from ..vocabulary import (
    CONTROL_TYPES,
    DEADLINE_UNITS,
    EXECUTION_MODES,
    FINDING_SEVERITIES,
    FINDING_STATUS,
    FINDING_TYPES,
    RISK_CATEGORIES,
    RISK_LEVELS,
    SOURCE_TYPES,
    TEST_RESULTS,
)
from .context import ValidationContext
from .issues import ValidationIssue, issue
from .registry import rule

Issues = Iterator[ValidationIssue]
_DATA_TYPES = ("dataObjectReference", "dataStoreReference", "dataObject", "dataStore")


def _unknown_values(
    element_id: str | None, name: str, checks: Iterable[tuple[str, str | None, Mapping[str, object]]]
) -> Issues:
    for field_name, value, vocabulary in checks:
        if value and value not in vocabulary:
            yield issue(
                "BPMN-P007", element_id, wert=value, feld=field_name, name=name, zulaessig=", ".join(vocabulary)
            )


def control_ids(ctx: ValidationContext) -> set[str]:
    """IDs aller Kontrollen im Dokument."""
    return {c.id for e in ctx.document for c in e.extensions.controls if c.id}


@rule("audit_authority", "BPMN-P008")
def check_unique_ids(ctx: ValidationContext) -> Issues:
    """BPMN-P008: IDs von Kontrollen, Risiken, Prüfschritten und Feststellungen eindeutig."""
    counts: Counter[str] = Counter()
    for element in ctx.document:
        ext = element.extensions
        ids = [c.id for c in ext.controls] + [r.id for r in ext.risks]
        ids += [s.id for s in ext.audit_steps] + [f.id for f in ext.findings]
        counts.update(i for i in ids if i)
    info = ctx.document.diagram_info
    if info is not None:
        counts.update(i for i in [r.id for r in info.risks] + [f.id for f in info.findings] if i)
    for identifier, count in counts.items():
        if count > 1:
            yield issue("BPMN-P008", None, id=identifier)


def _has_data_association(ctx: ValidationContext, element: BpmnElement) -> bool:
    return any(a.parent_id == element.id for a in ctx.document.by_type("dataOutputAssociation", "dataInputAssociation"))


@rule("audit_authority", "BPMN-P001", "BPMN-P007")
def check_controls(ctx: ValidationContext) -> Issues:
    """BPMN-P001/P007: Kontrolle mit Nachweis und bekannten Werten."""
    for element in ctx.document:
        for control in element.extensions.controls:
            label = control.label or control.id or "Kontrolle"
            if not control.evidence and not _has_data_association(ctx, element):
                yield issue("BPMN-P001", element.id, kontrolle=label, name=element.label)
            yield from _unknown_values(
                element.id,
                element.label,
                (("art", control.control_type, CONTROL_TYPES), ("durchfuehrung", control.execution, EXECUTION_MODES)),
            )


def _tested(ctx: ValidationContext, element: BpmnElement, control_id: str | None) -> bool:
    local = any(step.control in (None, control_id) for step in element.extensions.audit_steps)
    remote = control_id is not None and any(
        step.control == control_id for other in ctx.document for step in other.extensions.audit_steps
    )
    return local or remote


@rule("audit_authority", "BPMN-P004")
def check_key_controls_tested(ctx: ValidationContext) -> Issues:
    """BPMN-P004: Schlüsselkontrolle hat einen Prüfschritt."""
    for element in ctx.document:
        for control in element.extensions.controls:
            if control.key_control and not _tested(ctx, element, control.id):
                yield issue(
                    "BPMN-P004", element.id, kontrolle=control.label or control.id or "Kontrolle", name=element.label
                )


@rule("audit_authority", "BPMN-P011")
def check_key_control_marker(ctx: ValidationContext) -> Issues:
    """BPMN-P011: Kennzeichen Schlüsselkontrolle nur mit Schlüsselkontrolle."""
    for element in ctx.document:
        ext = element.extensions
        if "schluesselkontrolle" in ext.marker_types() and not any(c.key_control for c in ext.controls):
            yield issue("BPMN-P011", element.id, name=element.label)


def _risk_issues(element_id: str | None, name: str, risk: Risk, known: set[str]) -> Issues:
    label = risk.label or risk.id or "Risiko"
    if not risk.controls:
        yield issue("BPMN-P005", element_id, risiko=label, name=name)
    for control_id in risk.controls:
        if control_id not in known:
            yield issue("BPMN-P006", element_id, risiko=label, kontrolle=control_id)
    yield from _unknown_values(
        element_id,
        name,
        (
            ("kategorie", risk.category, RISK_CATEGORIES),
            ("inhaerent", risk.inherent, RISK_LEVELS),
            ("kontrollrisiko", risk.control_risk, RISK_LEVELS),
            ("restrisiko", risk.residual, RISK_LEVELS),
        ),
    )


@rule("audit_authority", "BPMN-P005", "BPMN-P006", "BPMN-P007")
def check_risks(ctx: ValidationContext) -> Issues:
    """BPMN-P005/P006/P007: Risiken mit bekannten Kontrollen und Stufen."""
    known = control_ids(ctx)
    for element in ctx.document:
        for risk in element.extensions.risks:
            yield from _risk_issues(element.id, element.label, risk, known)
    info = ctx.document.diagram_info
    for risk in info.risks if info else ():
        yield from _risk_issues(ctx.info_owner, ctx.info_title, risk, known)


@rule("audit_authority", "BPMN-P010", "BPMN-P012", "BPMN-P007")
def check_audit_steps(ctx: ValidationContext) -> Issues:
    """BPMN-P010/P012/P007: Ergebnisse und Kontrollbezug der Prüfschritte."""
    known = control_ids(ctx)
    for element in ctx.document:
        for step in element.extensions.audit_steps:
            label = step.id or step.case or "Prüfschritt"
            yield from _unknown_values(element.id, element.label, (("ergebnis", step.result, TEST_RESULTS),))
            if step.result == "nicht_erfuellt":
                yield issue("BPMN-P010", element.id, schritt=label, name=element.label)
            if step.control and step.control not in known:
                yield issue("BPMN-P012", element.id, schritt=label, kontrolle=step.control)


def _finding_issues(element_id: str | None, name: str, finding: AuditFinding) -> Issues:
    if not finding.finding_type or not finding.description:
        yield issue("BPMN-P009", element_id, name=name)
    yield from _unknown_values(
        element_id,
        name,
        (
            ("art", finding.finding_type, FINDING_TYPES),
            ("einstufung", finding.severity, FINDING_SEVERITIES),
            ("status", finding.status, FINDING_STATUS),
        ),
    )


@rule("audit_authority", "BPMN-P009", "BPMN-P007")
def check_findings(ctx: ValidationContext) -> Issues:
    """BPMN-P009/P007: Feststellungen mit Art, Beschreibung und bekannten Werten."""
    for element in ctx.document:
        for finding in element.extensions.findings:
            yield from _finding_issues(element.id, element.label, finding)
    info = ctx.document.diagram_info
    for finding in info.findings if info else ():
        yield from _finding_issues(ctx.info_owner, ctx.info_title, finding)


@rule("audit_authority", "BPMN-P003", "BPMN-P007")
def check_deadlines(ctx: ValidationContext) -> Issues:
    """BPMN-P003/P007: Fristen mit Rechtsgrundlage und bekannter Einheit."""
    for element in ctx.document:
        ext = element.extensions
        for deadline in ext.deadlines:
            if not deadline.legal_bases and not ext.legal_bases:
                yield issue("BPMN-P003", element.id, frist=deadline.display or "Frist", name=element.label)
            yield from _unknown_values(element.id, element.label, (("einheit", deadline.unit, DEADLINE_UNITS),))


@rule("audit_authority", "BPMN-P007")
def check_sources(ctx: ValidationContext) -> Issues:
    """BPMN-P007: bekannte Quellenart."""
    for element in ctx.document:
        for source in element.extensions.sources:
            yield from _unknown_values(element.id, element.label, (("art", source.source_type, SOURCE_TYPES),))


def _referenced(ctx: ValidationContext, element: BpmnElement) -> bool:
    attribute = "dataObjectRef" if element.type == "dataObject" else "dataStoreRef"
    return any(other.attributes.get(attribute) == element.id for other in ctx.document)


@rule("audit_authority", "BPMN-P002")
def check_data_storage(ctx: ValidationContext) -> Issues:
    """BPMN-P002: Datenobjekte und -speicher mit Aufbewahrungsort."""
    for element in ctx.document.by_type(*_DATA_TYPES):
        if element.type in ("dataObject", "dataStore") and _referenced(ctx, element):
            continue
        if not any(item.storage_location for item in element.extensions.evidence):
            yield issue("BPMN-P002", element.id, name=element.label)
