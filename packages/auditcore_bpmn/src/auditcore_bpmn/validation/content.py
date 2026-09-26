"""Fachliche Regeln (``BPMN-F…``): Diagramm-Infos, Rechtsgrundlagen, Akteure, Prüfbezüge."""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from datetime import date

from ..extensions import AuditReference, DiagramInfo, LegalBasis
from ..vocabulary import (
    AUDIT_TYPES,
    CONFIDENTIALITY,
    CROSS_REFERENCE_KINDS,
    DIAGRAM_STATUS,
    MARKERS,
    VARIANTS,
    label,
)
from .context import ValidationContext
from .issues import ValidationIssue, issue
from .registry import rule

Issues = Iterator[ValidationIssue]
_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _allowed(vocabulary: Iterable[str]) -> str:
    return ", ".join(vocabulary)


def _holders(ctx: ValidationContext) -> Iterator[tuple[str | None, str, object]]:
    """``(element_id, name, extensions_or_info)`` für Elemente und Diagramm-Infos."""
    for element in ctx.document:
        yield element.id, element.label, element.extensions
    if ctx.document.diagram_info is not None:
        yield ctx.info_owner, ctx.info_title, ctx.document.diagram_info


@rule("content", "BPMN-F001")
def check_legal_basis_present(ctx: ValidationContext) -> Issues:
    """BPMN-F001: Rechtsgrundlage an Aktivitäten."""
    for element in ctx.document:
        if element.type in ctx.config.legal_basis_types and not element.extensions.legal_bases:
            yield issue("BPMN-F001", element.id, name=element.label)


def _unstructured_act(items: Iterable[LegalBasis]) -> bool:
    return any(item.is_structured and not item.act for item in items)


@rule("content", "BPMN-F010")
def check_legal_basis_structure(ctx: ValidationContext) -> Issues:
    """BPMN-F010: strukturierte Rechtsgrundlage nennt eine Norm."""
    for element_id, name, holder in _holders(ctx):
        if _unstructured_act(getattr(holder, "legal_bases", ())):
            yield issue("BPMN-F010", element_id, name=name)


@rule("content", "BPMN-F011", "BPMN-F012")
def check_markers(ctx: ValidationContext) -> Issues:
    """BPMN-F011/F012: bekannte Kennzeichen, Kennzeichen Rechtsgrundlage belegt."""
    for element in ctx.document:
        extensions = element.extensions
        for marker in extensions.markers:
            if marker.type not in MARKERS:
                yield issue("BPMN-F011", element.id, typ=marker.type, name=element.label)
        if "rechtsgrundlage" in extensions.marker_types() and not extensions.legal_bases:
            yield issue("BPMN-F012", element.id, name=element.label)


@rule("content", "BPMN-F027")
def check_cross_references(ctx: ValidationContext) -> Issues:
    """BPMN-F027: Verweise mit bekannter Art und Schlüssel."""
    for element_id, name, holder in _holders(ctx):
        for reference in getattr(holder, "cross_references", ()):
            if reference.kind not in CROSS_REFERENCE_KINDS or not reference.key:
                yield issue("BPMN-F027", element_id, name=name, wert=reference.kind or "")


@rule("content", "BPMN-F020", "BPMN-F021", "BPMN-F022")
def check_actors(ctx: ValidationContext) -> Issues:
    """BPMN-F020/F021/F022: Akteur-Rolle an Pools und Lanes, im Profil und in der Periode."""
    for element in (*ctx.document.participants, *ctx.document.lanes):
        kind = "Pool" if element.type == "participant" else "Lane"
        actor = element.extensions.actor
        if actor is None or not actor.role:
            yield issue("BPMN-F020", element.id, art=kind, name=element.label)
            continue
        role = ctx.profile.role(actor.role)
        if role is None:
            yield issue("BPMN-F021", element.id, rolle=actor.role, name=element.label, profil=ctx.profile.id)
        elif not ctx.profile.role_provided(actor.role) or not role.applies_to(ctx.period):
            yield issue(
                "BPMN-F022",
                element.id,
                rolle=actor.role,
                bezeichnung=label(role.labels),
                bezeichnung_en=label(role.labels, "en"),
                name=element.label,
                periode=ctx.period or "?",
            )


def _reference_issues(ctx: ValidationContext, element_id: str | None, name: str, item: AuditReference) -> Issues:
    number = item.key_requirement_number
    profile = ctx.profile
    if number is None or profile.key_requirement(number) is None:
        numbers = profile.key_requirement_numbers
        available = f"{min(numbers)}–{max(numbers)}" if numbers else "keine"
        yield issue(
            "BPMN-F023", element_id, ka=item.key_requirement or "", name=name, profil=profile.id, vorhanden=available
        )
    elif item.assessment_criterion:
        criterion = item.assessment_criterion.strip()
        if not criterion.startswith(f"{number}."):
            yield issue("BPMN-F024", element_id, bk=criterion, ka=number, name=name)
        elif profile.criterion_known(number, criterion) is False:
            yield issue("BPMN-F025", element_id, bk=criterion, name=name)
    if item.audit_type and item.audit_type not in AUDIT_TYPES:
        yield issue("BPMN-F026", element_id, wert=item.audit_type, name=name)


@rule("content", "BPMN-F023", "BPMN-F024", "BPMN-F025", "BPMN-F026")
def check_audit_references(ctx: ValidationContext) -> Issues:
    """BPMN-F023–F026: KA im Katalog, BK passend, Prüfart bekannt."""
    for element_id, name, holder in _holders(ctx):
        references = list(getattr(holder, "audit_references", ()))
        references += [
            AuditReference(key_requirement=f.key_requirement, assessment_criterion=f.assessment_criterion)
            for f in getattr(holder, "findings", ())
            if f.key_requirement
        ]
        for item in references:
            yield from _reference_issues(ctx, element_id, name, item)


@rule("content", "BPMN-F002", "BPMN-F016")
def check_diagram_info_present(ctx: ValidationContext) -> Issues:
    """BPMN-F002/F016: Diagramm-Infos vorhanden, Profil bekannt."""
    info = ctx.document.diagram_info
    if info is None:
        yield issue("BPMN-F002")
    elif ctx.profile_origin == "standard-unknown":
        yield issue("BPMN-F016", ctx.info_owner, wert=info.profile, profil=ctx.profile.id)


def _info(ctx: ValidationContext) -> DiagramInfo | None:
    return ctx.document.diagram_info


@rule("content", "BPMN-F003", "BPMN-F004")
def check_status(ctx: ValidationContext) -> Issues:
    """BPMN-F003/F004: Status gesetzt und bekannt."""
    info = _info(ctx)
    if info is None:
        return
    if not info.status:
        yield issue("BPMN-F003", ctx.info_owner)
    elif info.status not in DIAGRAM_STATUS:
        yield issue("BPMN-F004", ctx.info_owner, wert=info.status, zulaessig=_allowed(DIAGRAM_STATUS))


def parse_date(value: str | None) -> date | None:
    """ISO-Datum oder ``None``."""
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None


@rule("content", "BPMN-F009")
def check_date_formats(ctx: ValidationContext) -> Issues:
    """BPMN-F009: Datumsfelder im Format JJJJ-MM-TT."""
    info = _info(ctx)
    if info is None:
        return
    for name, value in (
        ("gueltig_ab", info.valid_from),
        ("gueltig_bis", info.valid_until),
        ("freigegeben_am", info.approved_on),
        ("vks_stichtag", info.system_cutoff_date),
    ):
        if value and parse_date(value) is None:
            yield issue("BPMN-F009", ctx.info_owner, feld=name, wert=value)


@rule("content", "BPMN-F005", "BPMN-F006", "BPMN-F007")
def check_validity(ctx: ValidationContext) -> Issues:
    """BPMN-F005/F006/F007: Gültigkeitszeitraum zum Stichtag."""
    info = _info(ctx)
    if info is None:
        return
    start, end, today = parse_date(info.valid_from), parse_date(info.valid_until), ctx.reference_date
    if start and end and start > end:
        yield issue("BPMN-F007", ctx.info_owner, ab=info.valid_from, bis=info.valid_until)
    if end and end < today:
        yield issue("BPMN-F005", ctx.info_owner, datum=info.valid_until, stichtag=today.isoformat())
    if start and start > today:
        yield issue("BPMN-F006", ctx.info_owner, datum=info.valid_from, stichtag=today.isoformat())


@rule("content", "BPMN-F008")
def check_approval(ctx: ValidationContext) -> Issues:
    """BPMN-F008: Freigabe mit Person und Datum."""
    info = _info(ctx)
    if info is not None and info.status == "freigegeben" and not (info.approved_by and info.approved_on):
        yield issue("BPMN-F008", ctx.info_owner)


@rule("content", "BPMN-F013")
def check_header_colors(ctx: ValidationContext) -> Issues:
    """BPMN-F013: Kopfzeilenfarben als #RRGGBB."""
    info = _info(ctx)
    if info is None:
        return
    for name, value in (("kopfzeilenfarbe", info.header_color), ("kopfzeilen_textfarbe", info.header_text_color)):
        if value and not _COLOR.match(value):
            yield issue("BPMN-F013", ctx.info_owner, wert=value, feld=name)


@rule("content", "BPMN-F014", "BPMN-F015")
def check_funds_and_period(ctx: ValidationContext) -> Issues:
    """BPMN-F014/F015: Fonds und Förderperiode passend zum Profil."""
    info, profile = _info(ctx), ctx.profile
    if info is None:
        return
    for fund in info.funds:
        if fund not in profile.funds:
            yield issue("BPMN-F014", ctx.info_owner, wert=fund, profil=profile.id)
    period, expected = info.programming_period, profile.programming_period
    if period and expected and period != expected:
        yield issue("BPMN-F015", ctx.info_owner, wert=period, profil=profile.id, periode=expected)


@rule("content", "BPMN-F017", "BPMN-F018")
def check_confidentiality_and_variant(ctx: ValidationContext) -> Issues:
    """BPMN-F017/F018: Vertraulichkeit, Variante und Soll-Bezug."""
    info = _info(ctx)
    if info is None:
        return
    for name, value, vocabulary in (
        ("vertraulichkeit", info.confidentiality, CONFIDENTIALITY),
        ("variante", info.variant, VARIANTS),
    ):
        if value and value not in vocabulary:
            yield issue("BPMN-F017", ctx.info_owner, wert=value, feld=name, zulaessig=_allowed(vocabulary))
    if info.variant == "ist" and not info.reference_diagram:
        yield issue("BPMN-F018", ctx.info_owner)
