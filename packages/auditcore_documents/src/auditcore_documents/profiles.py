"""Versionierte, quellengebundene Vergleichsprofile.

Ein Profil hält alle Schalter fest, in denen sich charakterisiertes
Originalverhalten und bewusst korrigiertes Verhalten unterscheiden.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Literal

from auditcore_documents.scoring import ScorerName

AmendmentReading = Literal["legacy-skip-headings", "all-paragraphs"]


@dataclass(frozen=True)
class CompareProfile:
    """Fachliche Schalter eines Vergleichs."""

    profile_id: str
    version: str
    #: Wert für ``ComparisonResult.version`` (im Bericht „Vergleichsmodul …“).
    result_version: str
    scorer: ScorerName
    #: Wie Änderungsbefehle im Artikelgesetz gelesen werden, siehe DC-C04.
    amendment_reading: AmendmentReading
    #: Profilkennung in ``metadata["profile"]`` aufnehmen (Legacy: nein).
    record_profile: bool
    status: str
    source: str

    @property
    def fingerprint(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def identity(self) -> dict[str, str]:
        return {"id": self.profile_id, "version": self.version, "fingerprint": self.fingerprint}


_SOURCE = (
    "janpow77/audit_designer@030a71e083ef0feddc14545b095a4945bc0bbd7a "
    "backend/app/modules/document_compare"
)

#: Originalverhalten in der Produktionsumgebung (rapidfuzz installiert).
LEGACY = CompareProfile(
    profile_id="audit_designer.document_compare",
    version="1.1.0",
    result_version="1.1.0",
    scorer="rapidfuzz-token-set",
    amendment_reading="legacy-skip-headings",
    record_profile=False,
    status="SOURCE_CHARACTERIZED",
    source=_SOURCE,
)

#: Originalverhalten ohne rapidfuzz (Rückfall auf difflib im Original).
LEGACY_DIFFLIB = CompareProfile(
    profile_id="audit_designer.document_compare.difflib",
    version="1.1.0",
    result_version="1.1.0",
    scorer="difflib-ratio",
    amendment_reading="legacy-skip-headings",
    record_profile=False,
    status="SOURCE_CHARACTERIZED",
    source=_SOURCE,
)

#: Korrigiertes Verhalten: Änderungsbefehle, die mit „§“ beginnen, werden
#: gelesen (DC-C04); Profilidentität im Ergebnis.
CORRECTED = CompareProfile(
    profile_id="auditcore.document_compare",
    version="2026.09.1",
    result_version="1.1.0+auditcore.2026.09.1",
    scorer="rapidfuzz-token-set",
    amendment_reading="all-paragraphs",
    record_profile=True,
    status="CORRECTED_REQUIRES_HUMAN_DECISION_FOR_ADOPTION",
    source=_SOURCE,
)

PROFILES = {p.profile_id: p for p in (LEGACY, LEGACY_DIFFLIB, CORRECTED)}


def get_profile(profile_id: str) -> CompareProfile:
    try:
        return PROFILES[profile_id]
    except KeyError:
        raise ValueError(f"Unbekanntes Vergleichsprofil: {profile_id}") from None
