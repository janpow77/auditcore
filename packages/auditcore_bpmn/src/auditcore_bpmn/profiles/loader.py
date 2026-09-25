"""Profile laden: mitgelieferte JSON-Dateien und eigene Profile der Anwendung."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from importlib import resources
from types import MappingProxyType
from typing import Any

from ..errors import CatalogError
from ..extensions import DiagramInfo
from ..vocabulary import ROLES, Role
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
STANDARD_PROFILE = "foerderperiode-2021-2027"
_FILE = re.compile(r"^(?P<id>[a-z0-9-]+?)-(?P<version>\d{4}\.\d{2}\.\d+)\.json$")


def _optional_labels(value: Any) -> Any:
    return labels(value) if value else None


def _key_requirement(entry: Mapping[str, Any]) -> KeyRequirement:
    requirement = KeyRequirement(
        number=int(entry["number"]),
        title=labels(entry["title"]),
        bodies=labels(entry["bodies"]) if entry.get("bodies") else MappingProxyType({}),
        scope=_optional_labels(entry.get("scope")),
        footnote=_optional_labels(entry.get("footnote")),
        assessment_criteria=tuple(
            AssessmentCriterion(str(c["code"]), labels(c.get("title") or {"de": ""}))
            for c in entry.get("assessment_criteria", ())
        ),
    )
    check_criteria(requirement)
    return requirement


def _selection(data: Mapping[str, Any] | None) -> Selection:
    data = data or {}
    return Selection(markers=tuple(data.get("markers", ())), audit_types=tuple(data.get("audit_types", ())))


def _segregation_rule(rule: Mapping[str, Any]) -> SegregationRule:
    return SegregationRule(
        id=str(rule["id"]),
        kind=str(rule["kind"]),
        severity=str(rule.get("severity", "warnung")),
        title=labels(rule["title"]),
        a=_selection(rule.get("a")),
        b=_selection(rule.get("b")),
        selection=_selection(rule.get("selection")),
        roles=tuple(rule.get("roles", ())),
    )


def _legal_basis_template(entry: Mapping[str, Any]) -> LegalBasisTemplate:
    return LegalBasisTemplate(
        act=str(entry["act"]),
        short_title=labels(entry["short_title"]),
        article=entry.get("article"),
        annex=entry.get("annex"),
        celex=entry.get("celex"),
        eli=entry.get("eli"),
    )


def _custom_roles(data: Mapping[str, Any]) -> dict[str, Role]:
    return {
        str(code): Role(str(code), labels(entry["labels"]), entry.get("from_year"), entry.get("until_year"))
        for code, entry in (data.get("custom_roles") or {}).items()
    }


def _check_roles(roles: tuple[str, ...], custom: Mapping[str, Role]) -> None:
    unknown = [code for code in roles if code not in ROLES and code not in custom]
    if unknown:
        raise CatalogError(f"Unbekannte Rollen ohne Bezeichnung: {unknown}")


def _build(data: Mapping[str, Any]) -> Profile:
    requirements = data.get("key_requirements") or {}
    legal = data.get("legal_bases") or {}
    custom = _custom_roles(data)
    roles = tuple(str(code) for code in data.get("roles", ()))
    _check_roles(roles, custom)
    entries = tuple(_key_requirement(entry) for entry in requirements.get("entries", ()))
    if len({e.number for e in entries}) != len(entries):
        raise CatalogError("Kernanforderungen sind doppelt nummeriert.")
    return Profile(
        id=str(data["id"]),
        version=str(data["version"]),
        title=labels(data["title"]),
        programming_period=data.get("programming_period"),
        roles=roles,
        funds=tuple(str(code) for code in data.get("funds", ())),
        key_requirements=entries,
        key_requirement_source=MappingProxyType(dict(requirements.get("source") or {})),
        assessment_criteria_note=_optional_labels(requirements.get("assessment_criteria_note")),
        legal_bases=tuple(_legal_basis_template(entry) for entry in legal.get("entries", ())),
        legal_bases_source=MappingProxyType(dict(legal.get("source") or {})),
        segregation_rules=tuple(_segregation_rule(rule) for rule in data.get("segregation_rules", ())),
        role_aliases=tuple((str(a["pattern"]), str(a["role"])) for a in data.get("role_aliases", ())),
        templates=tuple(
            Template(str(t["id"]), labels(t["title"]), str(t["file"]), str(t.get("origin", "")))
            for t in data.get("templates", ())
        ),
        custom_roles=MappingProxyType(custom),
    )


def profile_from_dict(data: Mapping[str, Any]) -> Profile:
    """Profil aus JSON-Daten (Schema ``auditcore_bpmn.profile/1``)."""
    if data.get("schema") != PROFILE_SCHEMA:
        raise CatalogError(f"Profilschema {data.get('schema')!r} wird nicht unterstützt.")
    try:
        return _build(data)
    except CatalogError:
        raise
    except (KeyError, TypeError, ValueError) as error:
        raise CatalogError(f"Profil ist unvollständig oder fehlerhaft: {error!r}") from error


def available_profiles() -> tuple[tuple[str, str], ...]:
    """Mitgelieferte ``(id, version)``-Paare."""
    found = []
    for entry in resources.files("auditcore_bpmn.profiles.data").iterdir():
        match = _FILE.match(entry.name)
        if match:
            found.append((match["id"], match["version"]))
    return tuple(sorted(found))


def _version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def load_profile(profile_id: str = STANDARD_PROFILE, version: str | None = None) -> Profile:
    """Mitgeliefertes Profil; ohne ``version`` die neueste Fassung."""
    versions = [v for i, v in available_profiles() if i == profile_id]
    if not versions:
        raise CatalogError(f"Profil {profile_id} ist nicht vorhanden.")
    chosen = version or max(versions, key=_version_key)
    if chosen not in versions:
        raise CatalogError(f"Profil {profile_id} in Version {chosen} ist nicht vorhanden.")
    entry = resources.files("auditcore_bpmn.profiles.data").joinpath(f"{profile_id}-{chosen}.json")
    profile = profile_from_dict(json.loads(entry.read_text(encoding="utf-8")))
    if (profile.id, profile.version) != (profile_id, chosen):
        raise CatalogError("Profildatei und Profilkennung stimmen nicht überein.")
    return profile


class ProfileRegistry:
    """Mitgelieferte und von der Anwendung registrierte Profile."""

    def __init__(self, profiles: Iterable[Profile] = (), *, standard: str = STANDARD_PROFILE) -> None:
        self._profiles: dict[str, Profile] = {}
        for profile_id, _version in available_profiles():
            self._profiles.setdefault(profile_id, load_profile(profile_id))
        for profile in profiles:
            self.register(profile)
        if standard not in self._profiles:
            raise CatalogError(f"Standardprofil {standard} ist nicht registriert.")
        self.standard = standard

    def register(self, profile: Profile) -> None:
        """Registriert oder ersetzt ein Profil."""
        self._profiles[profile.id] = profile

    def get(self, profile_id: str) -> Profile | None:
        """Profil zu einer ID oder ``None``."""
        return self._profiles.get(profile_id)

    @property
    def ids(self) -> tuple[str, ...]:
        """IDs aller registrierten Profile."""
        return tuple(sorted(self._profiles))

    def for_diagram(self, info: DiagramInfo | None) -> tuple[Profile, str]:
        """Profil eines Diagramms und die Herkunft der Wahl.

        Herkunft: ``"profile"`` (Feld ``profil``), ``"period"`` (erstes Profil
        der Förderperiode), ``"standard"`` oder ``"standard-unknown"``
        (angegebenes Profil unbekannt).
        """
        if info and info.profile:
            found = self._profiles.get(info.profile)
            return (found, "profile") if found else (self._profiles[self.standard], "standard-unknown")
        if info and info.programming_period:
            for profile_id in sorted(self._profiles):
                if self._profiles[profile_id].programming_period == info.programming_period:
                    return self._profiles[profile_id], "period"
        return self._profiles[self.standard], "standard"


def load_template(profile: Profile, template_id: str) -> str:
    """BPMN-XML einer Vorlage des Profils (mitgelieferte Vorlagen liegen in ``auditcore_bpmn.templates``)."""
    template = next((t for t in profile.templates if t.id == template_id), None)
    if template is None:
        raise CatalogError(f"Vorlage „{template_id}“ ist im Profil {profile.id} nicht vorhanden.")
    entry = resources.files("auditcore_bpmn.templates").joinpath(template.file)
    if not entry.is_file():
        raise CatalogError(f"Vorlagendatei {template.file} fehlt.")
    return entry.read_text(encoding="utf-8")
