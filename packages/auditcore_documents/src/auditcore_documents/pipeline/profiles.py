"""Versionierte Pipeline-Profile: Originalverhalten und korrigiertes Verhalten.

``LEGACY_PIPELINE`` (flowinvoice fb2d185) bildet das charakterisierte
Original ab. ``CORRECTED_PIPELINE`` behebt zwei belegte Defekte:

* PL-C01: Ein REVIEW_NEEDED einer Stufe bleibt bis zum Ende erhalten (im
  Original setzt die nächste Stufe RUNNING, am Ende steht OK).
* PL-C02: Die IBAN-Erkennung endet am Zeilenende (im Original läuft das
  Muster über Zeilenumbrüche hinweg und macht gültige IBAN ungültig).

Die Übernahme des korrigierten Profils ändert Ergebnisse und ist deshalb
eine fachliche Entscheidung der Anwendung (HUMAN_DECISION_REQUIRED).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field

from auditcore_documents.pipeline.stages.postprocess import FIELD_PATTERNS

_SOURCE = "janpow77/flowinvoice@fb2d18568d2eaf64574d131ceae51a936b9aac02 backend/app/pipeline"
CORRECTED_IBAN_PATTERN = r"IBAN[ \t]*:?[ \t]*([A-Z]{2}\d{2}(?:[ \t]?[A-Z0-9]){11,30})"


@dataclass(frozen=True)
class PipelineProfile:
    profile_id: str
    version: str
    preserve_review: bool
    field_patterns: dict[str, list[str]] = field(default_factory=dict)
    status: str = "SOURCE_CHARACTERIZED"
    source: str = _SOURCE

    @property
    def fingerprint(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def identity(self) -> dict[str, str]:
        return {"id": self.profile_id, "version": self.version, "fingerprint": self.fingerprint}


LEGACY_PIPELINE = PipelineProfile(
    profile_id="flowinvoice.pipeline",
    version="1.0.0",
    preserve_review=False,
    field_patterns={k: list(v) for k, v in FIELD_PATTERNS.items()},
)

CORRECTED_PIPELINE = PipelineProfile(
    profile_id="auditcore.pipeline",
    version="2026.09.1",
    preserve_review=True,
    field_patterns={
        **{k: list(v) for k, v in FIELD_PATTERNS.items()},
        "iban": [CORRECTED_IBAN_PATTERN],
    },
    status="CORRECTED_REQUIRES_HUMAN_DECISION_FOR_ADOPTION",
)

PIPELINE_PROFILES = {p.profile_id: p for p in (LEGACY_PIPELINE, CORRECTED_PIPELINE)}
