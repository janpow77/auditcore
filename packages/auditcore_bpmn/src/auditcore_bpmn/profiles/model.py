"""Datenmodell der Profile (gebündelte, versionierte Kataloge je Förderperiode)."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from types import MappingProxyType

from ..errors import CatalogError
from ..vocabulary import ROLES, Labels, Role


def labels(value: object) -> Labels:
    """Bezeichnung aus Text oder ``{de, en}``."""
    if isinstance(value, str):
        return MappingProxyType({"de": value})
    if isinstance(value, Mapping) and value:
        return MappingProxyType({str(k): str(v) for k, v in value.items()})
    raise CatalogError("Bezeichnung muss Text oder {de, en} sein.")


def _empty() -> Labels:
    return MappingProxyType({})


@dataclass(frozen=True)
class AssessmentCriterion:
    """Bewertungskriterium einer KA."""

    code: str
    title: Labels = field(default_factory=_empty)


@dataclass(frozen=True)
class KeyRequirement:
    """Kernanforderung mit Titel, betroffenen Stellen und optionalen BK."""

    number: int
    title: Labels
    bodies: Labels = field(default_factory=_empty)
    scope: Labels | None = None
    footnote: Labels | None = None
    assessment_criteria: tuple[AssessmentCriterion, ...] = ()


@dataclass(frozen=True)
class LegalBasisTemplate:
    """Häufige Rechtsgrundlage mit Kurztitel aus dem Rechtstext."""

    act: str
    short_title: Labels
    article: str | None = None
    annex: str | None = None
    celex: str | None = None
    eli: str | None = None


@dataclass(frozen=True)
class Selection:
    """Auswahl von Aktivitäten über Kennzeichen oder die Prüfart ihrer Prüfbezüge."""

    markers: tuple[str, ...] = ()
    audit_types: tuple[str, ...] = ()


@dataclass(frozen=True)
class SegregationRule:
    """Regel zur Funktionstrennung: ``separate_bodies``, ``excluded_role`` oder ``four_eyes``."""

    id: str
    kind: str
    severity: str
    title: Labels
    a: Selection = Selection()
    b: Selection = Selection()
    selection: Selection = Selection()
    roles: tuple[str, ...] = ()


@dataclass(frozen=True)
class Template:
    """Vorlage (BPMN-Datei im Paket)."""

    id: str
    title: Labels
    file: str
    origin: str = ""


@dataclass(frozen=True)
class Profile:
    """Profil: Kataloge und Regeln einer Förderperiode."""

    id: str
    version: str
    title: Labels
    programming_period: str | None
    roles: tuple[str, ...]
    funds: tuple[str, ...]
    key_requirements: tuple[KeyRequirement, ...]
    key_requirement_source: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))
    assessment_criteria_note: Labels | None = None
    legal_bases: tuple[LegalBasisTemplate, ...] = ()
    legal_bases_source: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))
    segregation_rules: tuple[SegregationRule, ...] = ()
    role_aliases: tuple[tuple[str, str], ...] = ()
    templates: tuple[Template, ...] = ()
    #: Zusätzliche Rollen eines eigenen Profils.
    custom_roles: Mapping[str, Role] = field(default_factory=lambda: MappingProxyType({}))

    @property
    def reference(self) -> str:
        """``id@version``."""
        return f"{self.id}@{self.version}"

    def key_requirement(self, number: int | str | None) -> KeyRequirement | None:
        """KA zu einer Nummer oder ``None``."""
        try:
            wanted = int(str(number).strip())
        except (TypeError, ValueError):
            return None
        return next((k for k in self.key_requirements if k.number == wanted), None)

    @property
    def key_requirement_numbers(self) -> tuple[int, ...]:
        """Nummern aller KA."""
        return tuple(k.number for k in self.key_requirements)

    def criterion_known(self, key_requirement: int | str | None, criterion: str) -> bool | None:
        """``True``/``False`` gegen den BK-Katalog der KA; ``None``, wenn keiner vorliegt."""
        entry = self.key_requirement(key_requirement)
        if entry is None or not entry.assessment_criteria:
            return None
        return any(item.code == criterion.strip() for item in entry.assessment_criteria)

    def role(self, code: str | None) -> Role | None:
        """Rolle aus eigenen Rollen oder dem Standardkatalog."""
        if not code:
            return None
        return self.custom_roles.get(code) or ROLES.get(code)

    def role_provided(self, code: str | None) -> bool:
        """``True``, wenn die Rolle im Profil vorgesehen ist."""
        return bool(code) and (code in self.roles or code in self.custom_roles)

    def role_from_text(self, text: str | None) -> str | None:
        """Rolle aus Lane-Namen oder Aufgabenpräfix über die Aliasliste (erster Treffer)."""
        lowered = (text or "").casefold()
        if not lowered:
            return None
        return next((code for pattern, code in self.role_aliases if pattern.casefold() in lowered), None)

    def with_assessment_criteria(self, criteria: Mapping[int, Iterable[tuple[str, Labels | str]]]) -> Profile:
        """Neues Profil mit eingespeisten Bewertungskriterien je KA (z. B. aus Leitlinien der Kommission)."""
        unknown = set(criteria) - set(self.key_requirement_numbers)
        if unknown:
            raise CatalogError(f"Unbekannte Kernanforderungen: {sorted(unknown)}")
        updated = []
        for entry in self.key_requirements:
            items = criteria.get(entry.number)
            if items is not None:
                entry = replace(
                    entry, assessment_criteria=tuple(AssessmentCriterion(str(c), labels(t)) for c, t in items)
                )
                check_criteria(entry)
            updated.append(entry)
        return replace(self, key_requirements=tuple(updated))


def check_criteria(entry: KeyRequirement) -> None:
    """Prüft, dass jedes BK mit ``{KA}.`` beginnt."""
    for criterion in entry.assessment_criteria:
        if not criterion.code.startswith(f"{entry.number}."):
            raise CatalogError(f"Bewertungskriterium {criterion.code} passt nicht zur KA {entry.number}.")
