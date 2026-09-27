"""Normauflösung mit ``auditcore_legal_sources`` (Extra ``legal``).

:class:`LegalSourcesNormResolver` ergänzt die syntaktische Auflösung
(:class:`auditcore_bpmn.citations.EuActResolver`) um Titel, Förderperiode und
Dokumenttyp aus den Kerndokumenten eines Quellprofils von
``auditcore_legal_sources`` sowie um Artikelüberschriften eines
Förderperioden-Profils dieses Pakets. Kein Netzwerkzugriff.

Ohne installiertes Extra wirft der Import dieses Moduls
:class:`auditcore_bpmn.errors.OptionalDependencyError`; alles andere
funktioniert unabhängig davon.
"""

from __future__ import annotations

from dataclasses import replace

from .citations import EuActResolver, NormResolution
from .errors import OptionalDependencyError
from .profiles import Profile

try:
    from auditcore_legal_sources import load_profile as _load_source_profile
    from auditcore_legal_sources.eurlex import celex_document_type
except ImportError as error:
    raise OptionalDependencyError(
        "Für die Normauflösung mit auditcore_legal_sources ist das Extra 'legal' nötig: "
        "pip install 'auditcore_bpmn[legal]'"
    ) from error

DEFAULT_SOURCE_PROFILE = ("auditdatabase.esi", "2026.09.2")


class LegalSourcesNormResolver:
    """Auflösung gegen die Kerndokumente eines ``auditcore_legal_sources``-Profils."""

    def __init__(
        self,
        profile_id: str = DEFAULT_SOURCE_PROFILE[0],
        version: str = DEFAULT_SOURCE_PROFILE[1],
        *,
        period_profile: Profile | None = None,
    ) -> None:
        source_profile = _load_source_profile(profile_id, version)
        self.source = f"auditcore_legal_sources:{profile_id}@{version}"
        self._core = {document.celex: document for document in source_profile.eurlex_core_documents}
        self._period_profile = period_profile
        self._syntactic = EuActResolver()

    def resolve(self, act: str) -> NormResolution | None:
        """Syntaktische Auflösung, ergänzt um Titel und Periode aus dem Quellprofil."""
        result = self._syntactic.resolve(act)
        if result is None:
            return None
        result = replace(result, document_type=celex_document_type(result.celex or ""), source=self.source)
        document = self._core.get(result.celex or "")
        if document is None:
            return result
        return replace(result, short_title=document.title, programming_period=document.period, catalogued=True)

    def article_title(self, act: str, article: str, language: str = "de") -> str | None:
        """Artikelüberschrift aus dem Förderperioden-Profil (falls hinterlegt)."""
        resolved = self._syntactic.resolve(act)
        if self._period_profile is None or resolved is None:
            return None
        for entry in self._period_profile.legal_bases:
            if entry.celex == resolved.celex and entry.article == article:
                return entry.short_title.get(language) or entry.short_title.get("de")
        return None
