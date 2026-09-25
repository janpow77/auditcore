"""Versioned, source-bound profiles: keywords, endpoints, queries and core documents.

Profiles are data recorded from the executed source applications. Profiles of
different applications stay separate; nothing here merges them.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import resources
from types import MappingProxyType
from typing import Any

from .errors import ProfileError

PROFILE_SCHEMA = "auditcore_legal_sources.profile/1"


@dataclass(frozen=True)
class CoreDocument:
    """A CELEX document the profile always includes."""

    celex: str
    title: str
    period: str


@dataclass(frozen=True)
class FeedSource:
    """Feed or publication-page source of a profile (BaFin, CURIA, ECA)."""

    key: str
    feeds: Mapping[str, str]
    alternative_feeds: Mapping[str, str]
    document_types: Mapping[str, str]
    case_patterns: tuple[str, ...]
    publication_urls: tuple[str, ...]
    base_url: str
    link_markers: tuple[str, ...]
    min_title_length: int


def _feed_source(key: str, data: Mapping[str, Any]) -> FeedSource:
    return FeedSource(
        key=key,
        feeds=MappingProxyType(dict(data.get("feeds", {}))),
        alternative_feeds=MappingProxyType(dict(data.get("alternative_feeds", {}))),
        document_types=MappingProxyType(dict(data.get("document_types", {}))),
        case_patterns=tuple(data.get("case_patterns", ())),
        publication_urls=tuple(data.get("publication_urls", ())),
        base_url=str(data.get("base_url", "")),
        link_markers=tuple(data.get("link_markers", ())),
        min_title_length=int(data.get("min_title_length", 1)),
    )


@dataclass(frozen=True)
class SourceProfile:
    """Immutable, explicitly selected source profile."""

    id: str
    version: str
    status: str
    source: Mapping[str, Any]
    keywords_de: tuple[str, ...]
    keywords_en: tuple[str, ...]
    dip_api_url: str
    dip_portal_url: str
    dip_keywords: tuple[str, ...]
    dip_page_size: int
    dip_classification: str
    eurlex_endpoint: str
    eurlex_document_url: str
    eurlex_queries: Mapping[str, str]
    eurlex_core_documents: tuple[CoreDocument, ...]
    eurlex_update_query_template: str | None
    eurlex_funding_period_rule: str
    feeds: Mapping[str, FeedSource]
    fingerprint: str

    @property
    def reference(self) -> dict[str, str]:
        """Identity recorded in the provenance of every document."""
        return {"id": self.id, "version": self.version, "fingerprint": self.fingerprint}


def fingerprint(data: Mapping[str, object]) -> str:
    """SHA-256 of the canonical JSON profile document."""
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def profile_from_dict(data: Mapping[str, Any]) -> SourceProfile:
    """Validate a profile document.

    Raises:
        ProfileError: schema violation or missing field; nothing is defaulted.
    """
    try:
        if data["schema"] != PROFILE_SCHEMA:
            raise ProfileError("Unbekanntes Profilschema.")
        dip, eurlex = data["dip"], data["eurlex"]
        queries = dict(eurlex["queries"])
        if not queries or not all(isinstance(q, str) and q.strip() for q in queries.values()):
            raise ProfileError("SPARQL-Abfragen des Profils fehlen oder sind leer.")
        if dip["classification"] not in ("auditdatabase.dip", "none"):
            raise ProfileError("Unbekannte DIP-Klassifikationsregel.")
        if eurlex["funding_period_rule"] not in ("auditdatabase", "designer"):
            raise ProfileError("Unbekannte Förderperiodenregel.")
        template = eurlex["update_query_template"]
        if template is not None and template.count("{since}") != 1:
            raise ProfileError("Aktualisierungsabfrage braucht genau einen Platzhalter {since}.")
        page_size = int(dip["page_size"])
        if not 1 <= page_size <= 100:
            raise ProfileError("DIP-Seitengröße muss zwischen 1 und 100 liegen.")
        return SourceProfile(
            id=str(data["id"]),
            version=str(data["version"]),
            status=str(data["status"]),
            source=MappingProxyType(dict(data["source"])),
            keywords_de=tuple(data["keywords"]["de"]),
            keywords_en=tuple(data["keywords"]["en"]),
            dip_api_url=str(dip["api_url"]),
            dip_portal_url=str(dip["portal_url"]),
            dip_keywords=tuple(dip["keywords"]),
            dip_page_size=page_size,
            dip_classification=str(dip["classification"]),
            eurlex_endpoint=str(eurlex["endpoint"]),
            eurlex_document_url=str(eurlex["document_url"]),
            eurlex_queries=MappingProxyType(queries),
            eurlex_core_documents=tuple(
                CoreDocument(str(d["celex"]), str(d["title"]), str(d["period"]))
                for d in eurlex["core_documents"]
            ),
            eurlex_update_query_template=eurlex["update_query_template"],
            eurlex_funding_period_rule=str(eurlex["funding_period_rule"]),
            feeds=MappingProxyType(
                {key: _feed_source(key, value) for key, value in dict(data["feeds"]).items()}
            ),
            fingerprint=fingerprint(data),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ProfileError(f"Profil ist unvollständig oder fehlerhaft: {exc!r}") from exc


def available_profiles() -> tuple[tuple[str, str], ...]:
    """Packaged ``(id, version)`` pairs; there is no implicit default profile."""
    found = []
    for entry in resources.files("auditcore_legal_sources.profiles").iterdir():
        if entry.name.endswith(".json"):
            data = json.loads(entry.read_text(encoding="utf-8"))
            found.append((str(data["id"]), str(data["version"])))
    return tuple(sorted(found))


def load_profile(profile_id: str, version: str) -> SourceProfile:
    """Load an explicitly named packaged profile version."""
    name = f"{profile_id}-{version}.json"
    if "/" in name or "\\" in name or name.startswith("."):
        raise ProfileError("Ungültige Profilkennung.")
    entry = resources.files("auditcore_legal_sources.profiles").joinpath(name)
    if not entry.is_file():
        raise ProfileError(f"Profil {profile_id} in Version {version} ist nicht vorhanden.")
    profile = profile_from_dict(json.loads(entry.read_text(encoding="utf-8")))
    if (profile.id, profile.version) != (profile_id, version):
        raise ProfileError("Profildatei und Profilkennung stimmen nicht überein.")
    return profile
