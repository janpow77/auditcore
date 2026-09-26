"""Profil aus JSON-Daten (Schema ``auditcore_bpmn.profile/1``) mit geprüften Typen."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from ..errors import CatalogError
from ..jsondata import integer, items, mapping, optional_integer, optional_mapping, optional_text, strings, text
from ..vocabulary import ROLES, Labels, Role
from .model import (
    AssessmentCriterion,
    KeyRequirement,
    LegalBasisTemplate,
    Profile,
    SegregationRule,
    Selection,
    Template,
    check_criteria,
    labels,
)

PROFILE_SCHEMA = "auditcore_bpmn.profile/1"


def _optional_labels(value: object) -> Labels | None:
    return labels(value) if value else None


def _key_requirement(entry: Mapping[str, object]) -> KeyRequirement:
    requirement = KeyRequirement(
        number=integer(entry.get("number"), "KA-Nummer"),
        title=labels(entry.get("title")),
        bodies=labels(entry["bodies"]) if entry.get("bodies") else MappingProxyType({}),
        scope=_optional_labels(entry.get("scope")),
        footnote=_optional_labels(entry.get("footnote")),
        assessment_criteria=tuple(
            AssessmentCriterion(text(c.get("code"), "BK"), labels(c.get("title") or {"de": ""}))
            for c in items(entry.get("assessment_criteria"), "Bewertungskriterien")
        ),
    )
    check_criteria(requirement)
    return requirement


def _selection(data: object) -> Selection:
    values = optional_mapping(data, "Auswahl")
    return Selection(markers=strings(values.get("markers")), audit_types=strings(values.get("audit_types")))


def _segregation_rule(rule: Mapping[str, object]) -> SegregationRule:
    return SegregationRule(
        id=text(rule.get("id"), "Regel-ID"),
        kind=text(rule.get("kind"), "Regelart"),
        severity=str(rule.get("severity", "warnung")),
        title=labels(rule.get("title")),
        a=_selection(rule.get("a")),
        b=_selection(rule.get("b")),
        selection=_selection(rule.get("selection")),
        roles=strings(rule.get("roles")),
    )


def _legal_basis_template(entry: Mapping[str, object]) -> LegalBasisTemplate:
    return LegalBasisTemplate(
        act=text(entry.get("act"), "Norm"),
        short_title=labels(entry.get("short_title")),
        article=optional_text(entry.get("article")),
        annex=optional_text(entry.get("annex")),
        celex=optional_text(entry.get("celex")),
        eli=optional_text(entry.get("eli")),
    )


def _custom_roles(data: Mapping[str, object]) -> dict[str, Role]:
    roles = {}
    for code, raw in optional_mapping(data.get("custom_roles"), "Eigene Rollen").items():
        entry = mapping(raw, f"Rolle {code}")
        roles[code] = Role(
            code,
            labels(entry.get("labels")),
            optional_integer(entry.get("from_year")),
            optional_integer(entry.get("until_year")),
        )
    return roles


def _check_roles(roles: tuple[str, ...], custom: Mapping[str, Role]) -> None:
    unknown = [code for code in roles if code not in ROLES and code not in custom]
    if unknown:
        raise CatalogError(f"Unbekannte Rollen ohne Bezeichnung: {unknown}")


def _requirements(data: Mapping[str, object]) -> tuple[KeyRequirement, ...]:
    block = optional_mapping(data.get("key_requirements"), "Kernanforderungen")
    entries = tuple(_key_requirement(entry) for entry in items(block.get("entries"), "Kernanforderungen"))
    if len({e.number for e in entries}) != len(entries):
        raise CatalogError("Kernanforderungen sind doppelt nummeriert.")
    return entries


def _templates(data: Mapping[str, object]) -> tuple[Template, ...]:
    return tuple(
        Template(
            text(t.get("id"), "Vorlage"), labels(t.get("title")), text(t.get("file"), "Datei"), str(t.get("origin", ""))
        )
        for t in items(data.get("templates"), "Vorlagen")
    )


def _build(data: Mapping[str, object]) -> Profile:
    requirements = optional_mapping(data.get("key_requirements"), "Kernanforderungen")
    legal = optional_mapping(data.get("legal_bases"), "Rechtsgrundlagen")
    custom = _custom_roles(data)
    roles = strings(data.get("roles"), "Rollen")
    _check_roles(roles, custom)
    return Profile(
        id=text(data.get("id"), "Profil-ID"),
        version=text(data.get("version"), "Version"),
        title=labels(data.get("title")),
        programming_period=optional_text(data.get("programming_period")),
        roles=roles,
        funds=strings(data.get("funds"), "Fonds"),
        key_requirements=_requirements(data),
        key_requirement_source=MappingProxyType(dict(optional_mapping(requirements.get("source")))),
        assessment_criteria_note=_optional_labels(requirements.get("assessment_criteria_note")),
        legal_bases=tuple(_legal_basis_template(e) for e in items(legal.get("entries"), "Rechtsgrundlagen")),
        legal_bases_source=MappingProxyType(dict(optional_mapping(legal.get("source")))),
        segregation_rules=tuple(_segregation_rule(rule) for rule in items(data.get("segregation_rules"), "Regeln")),
        role_aliases=tuple(
            (text(a.get("pattern"), "Muster"), text(a.get("role"), "Rolle")) for a in items(data.get("role_aliases"))
        ),
        templates=_templates(data),
        custom_roles=MappingProxyType(custom),
    )


def profile_from_dict(data: Mapping[str, object]) -> Profile:
    """Profil aus JSON-Daten (Schema ``auditcore_bpmn.profile/1``)."""
    if data.get("schema") != PROFILE_SCHEMA:
        raise CatalogError(f"Profilschema {data.get('schema')!r} wird nicht unterstützt.")
    try:
        return _build(data)
    except CatalogError:
        raise
    except (KeyError, TypeError, ValueError) as error:
        raise CatalogError(f"Profil ist unvollständig oder fehlerhaft: {error!r}") from error
