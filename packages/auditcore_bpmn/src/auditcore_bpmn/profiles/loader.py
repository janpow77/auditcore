"""Profile laden: mitgelieferte JSON-Dateien und eigene Profile der Anwendung."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from importlib import resources

from ..errors import CatalogError
from ..extensions import DiagramInfo
from .model import Profile
from .parsing import profile_from_dict

STANDARD_PROFILE = "foerderperiode-2021-2027"
_FILE = re.compile(r"^(?P<id>[a-z0-9-]+?)-(?P<version>\d{4}\.\d{2}\.\d+)\.json$")


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
