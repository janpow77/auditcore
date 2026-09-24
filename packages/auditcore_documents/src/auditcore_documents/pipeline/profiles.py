"""Versionierte Pipeline-Profile: Originalverhalten und korrigiertes Verhalten.

``LEGACY_PIPELINE`` (flowinvoice fb2d185) bildet das charakterisierte
Original ab. ``CORRECTED_PIPELINE`` behebt zwei belegte Defekte:

* PL-C01: Ein REVIEW_NEEDED einer Stufe bleibt bis zum Ende erhalten (im
  Original setzt die nächste Stufe RUNNING, am Ende steht OK).
* PL-C02: Die IBAN-Erkennung endet am Zeilenende (im Original läuft das
  Muster über Zeilenumbrüche hinweg und macht gültige IBAN ungültig).

Entschieden am 2026-09-23 (Nutzerzitat „alle empfehlungen“):

* D4: ``CORRECTED_PIPELINE`` ist das empfohlene Profil (``RECOMMENDED_PIPELINE``).
* D5: Beträge werden gebietsschemabewusst gelesen (``18251.04`` bleibt
  ``18251.04``); mehrdeutige Beträge führen über ``VAL_AMOUNT_FORMAT`` zu
  REVIEW_NEEDED statt zu einem geratenen Wert. Feldmuster überspringen keine
  Zeilenumbrüche und beginnen nicht mitten im Wort.
* D6: Ein Ausfall des OCR-Gateways ist ein wiederholbarer Fehler
  (``OCR_GATEWAY_UNAVAILABLE``, drei Wiederholungen) statt REJECTED.
* D7: Der Löschlauf setzt alle fünf Aufbewahrungsfristen durch.

``LEGACY_PIPELINE`` bleibt unverändert und bitgenau.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field

from auditcore_documents.pipeline.retention import ALL_CATEGORIES, LEGACY_CATEGORIES
from auditcore_documents.pipeline.stages.postprocess import FIELD_PATTERNS, corrected_patterns

_SOURCE = "janpow77/flowinvoice@fb2d18568d2eaf64574d131ceae51a936b9aac02 backend/app/pipeline"
CORRECTED_IBAN_PATTERN = r"IBAN[ \t]*:?[ \t]*([A-Z]{2}\d{2}(?:[ \t]?[A-Z0-9]){11,30})"

_LEGACY_DEFAULTS: dict[str, object] = {
    "amount_mode": "legacy-de",
    "gateway_outage_is_error": False,
    "retry_gateway": False,
    "retention_categories": LEGACY_CATEGORIES,
    # ab 2026.09.24 (Donut): Vorgaben entsprechen dem bisherigen Verhalten.
    "ocr_backend": None,
    "donut_min_field_confidence": None,
}


@dataclass(frozen=True)
class PipelineProfile:
    profile_id: str
    version: str
    preserve_review: bool
    field_patterns: dict[str, list[str]] = field(default_factory=dict)
    amount_mode: str = "legacy-de"
    gateway_outage_is_error: bool = False
    retry_gateway: bool = False
    retention_categories: tuple[str, ...] = LEGACY_CATEGORIES
    status: str = "SOURCE_CHARACTERIZED"
    source: str = _SOURCE
    #: Ausdrücklich gewähltes OCR-Backend des Profils (``None`` = wie bisher per Stufe).
    ocr_backend: str | None = None
    #: Schwellwert der Feldkonfidenz für die Donut-Zusammenführung.
    donut_min_field_confidence: float | None = None

    @property
    def fingerprint(self) -> str:
        data = asdict(self)
        # Felder ab 2026.09.2 nur aufnehmen, wenn sie vom Originalverhalten
        # abweichen: so bleiben die Fingerabdrücke der Originalprofile stabil.
        for key, legacy_value in _LEGACY_DEFAULTS.items():
            if data.get(key) == legacy_value:
                data.pop(key, None)
        payload = json.dumps(data, sort_keys=True, ensure_ascii=False)
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
    version="2026.09.2",
    preserve_review=True,
    field_patterns={
        **corrected_patterns(FIELD_PATTERNS),
        "iban": [CORRECTED_IBAN_PATTERN],
    },
    amount_mode="locale-aware",
    gateway_outage_is_error=True,
    retry_gateway=True,
    retention_categories=ALL_CATEGORIES,
    status="DECIDED_RECOMMENDED",
)

#: Empfohlenes Profil (Entscheidung D4 vom 2026-09-23).
RECOMMENDED_PIPELINE = CORRECTED_PIPELINE

#: Donut-Belegerkennung (Plan DONUT_OCR_PLAN.md 2a, Entscheidungen E1–E9 vom 24.09.2026):
#: abgeleitet von ``CORRECTED_PIPELINE``; OCR-Backend ``donut`` mit Tesseract-Abgleich,
#: ``DonutFieldMergeStage`` und Pflicht-Plausibilität. Nur ausdrücklich wählbar.
DONUT_PIPELINE = PipelineProfile(
    profile_id="auditcore.pipeline.donut",
    version="2026.09.24",
    preserve_review=True,
    field_patterns=dict(CORRECTED_PIPELINE.field_patterns),
    amount_mode="locale-aware",
    gateway_outage_is_error=True,
    retry_gateway=True,
    retention_categories=ALL_CATEGORIES,
    status="EXPERIMENTAL",
    source="auditcore docs/architecture/DONUT_OCR_PLAN.md 2a (abgeleitet von auditcore.pipeline "
    "2026.09.2)",
    ocr_backend="donut",
    donut_min_field_confidence=0.90,
)

PIPELINE_PROFILES = {
    p.profile_id: p for p in (LEGACY_PIPELINE, CORRECTED_PIPELINE, DONUT_PIPELINE)
}
