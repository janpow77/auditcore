"""Versionierte, quellengebundene Vergleichsprofile.

Ein Profil hält alle Schalter fest, in denen sich charakterisiertes
Originalverhalten und bewusst korrigiertes Verhalten unterscheiden.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

from auditcore_common.hashing import canonical_sha256

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
    #: Nach „Nach … wird folgender Absatz n eingefügt“ folgende Absätze umnummerieren (D2).
    renumber_after_insert: bool
    status: str
    source: str

    @property
    def fingerprint(self) -> str:
        data = asdict(self)
        # Felder ab 2026.09.2 nur aufnehmen, wenn sie vom Originalverhalten
        # abweichen: so bleiben die Fingerabdrücke der Originalprofile stabil.
        if not data.get("renumber_after_insert"):
            data.pop("renumber_after_insert", None)
        return canonical_sha256(data, compact=False)

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
    renumber_after_insert=False,
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
    renumber_after_insert=False,
    status="SOURCE_CHARACTERIZED",
    source=_SOURCE,
)

#: Korrigiertes, empfohlenes Verhalten (Nutzerentscheidung D1/D2 vom 23.09.2026):
#: Änderungsbefehle, die mit „§“ beginnen, werden gelesen (DC-C04), nach einer
#: Einfügung wird umnummeriert (DC-L01), Ersetzungen treffen alle Vorkommen
#: (DC-L02), ohne rapidfuzz klarer Fehler (DC-C01); Profilidentität im Ergebnis.
CORRECTED = CompareProfile(
    profile_id="auditcore.document_compare",
    version="2026.09.2",
    result_version="1.1.0+auditcore.2026.09.2",
    scorer="rapidfuzz-token-set",
    amendment_reading="all-paragraphs",
    record_profile=True,
    renumber_after_insert=True,
    status="DECIDED_RECOMMENDED",
    source=_SOURCE,
)

#: Empfohlenes Profil für neue Anwendungen (D1).
RECOMMENDED = CORRECTED

PROFILES = {p.profile_id: p for p in (LEGACY, LEGACY_DIFFLIB, CORRECTED)}


def get_profile(profile_id: str) -> CompareProfile:
    try:
        return PROFILES[profile_id]
    except KeyError:
        raise ValueError(f"Unbekanntes Vergleichsprofil: {profile_id}") from None
