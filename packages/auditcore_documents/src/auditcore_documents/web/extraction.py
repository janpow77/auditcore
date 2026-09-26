"""Belegerkennung als REST-Vertrag ``documents_extraction/1`` (nur Standardbibliothek).

Der Dienst nimmt ein hochgeladenes Dokument (PDF oder Bild), führt die
Dokumentpipeline (:func:`auditcore_documents.pipeline.build_pipeline`) mit
einem ausdrücklich gewählten Profil aus und liefert Extraktionsergebnis,
Konfidenzen und Validierungsbefunde. OCR und Donut kommen ausschließlich
über die Ports der Anwendung (:class:`ExtractionEngines`); die Bibliothek
kennt keinen Host und lädt kein Modell. Ohne angeschlossene Engine ist die
Belegerkennung abgeschaltet (404 ``extraction_disabled``).

Das Dokument wird nur für die Dauer des Laufs in einem temporären
Verzeichnis abgelegt und danach gelöscht; der Dienst speichert nichts.
Vertrag: ``docs/ui/extraction-rest.md`` im Repository.
"""

from __future__ import annotations

import asyncio
import hashlib
import re
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path, PurePath

from auditcore_documents import __version__
from auditcore_documents.pipeline import (
    PIPELINE_PROFILES,
    RECOMMENDED_PIPELINE,
    InMemoryAuditLog,
    OcrRouting,
    OcrStage,
    PipelineContext,
    PipelineProfile,
    RetentionPolicyConfig,
    build_pipeline,
)
from auditcore_documents.pipeline.donut import DonutPort
from auditcore_documents.pipeline.retention import CATEGORY_DAYS_FIELD
from auditcore_documents.pipeline.stages.ingestion import ALLOWED_MIME_TYPES
from auditcore_documents.pipeline.stages.ocr_results import (
    ChandraPort,
    Rasterizer,
    RouterOcr,
    TesseractPort,
    pdfium_rasterizer,
)
from auditcore_documents.web.extraction_result import Thresholds, run_result

CONTRACT = "documents_extraction/1"
LIBRARY = f"auditcore_documents {__version__}"
_SUFFIX = re.compile(r"\.[a-z0-9]{1,5}")

#: Deutsche Bezeichnungen der mitgelieferten Profile (unbekannte Profile zeigen ihre Kennung).
PROFILE_LABELS = {
    "auditcore.pipeline": "Empfohlen (korrigiertes Verhalten)",
    "flowinvoice.pipeline": "Originalverhalten flowinvoice",
    "auditcore.pipeline.donut": "Donut-Belegerkennung (erprobend)",
}


class ExtractionError(ValueError):
    """Anfrage erfüllt den Vertrag nicht (Status, Code, deutsche Meldung)."""

    def __init__(self, message: str, *, status: int = 422, code: str = "invalid_input") -> None:
        super().__init__(message)
        self.status = status
        self.code = code

    def to_dict(self) -> dict[str, object]:
        """JSON-Fehlerkörper ``{"error": {"code", "message"}}``."""
        return {"error": {"code": self.code, "message": str(self)}}


@dataclass(frozen=True)
class ExtractionEngines:
    """OCR-Ports der Anwendung; fehlt alles, ist die Belegerkennung abgeschaltet.

    ``router`` (OCR-Gateway, nur mit ``routing``), ``chandra`` und ``tesseract``
    tragen die Profile ohne Donut; ``donut`` (``HttpDonut``, ``flowagent_donut``
    oder ``LocalDonut``) schaltet das Donut-Profil frei. Adressen und Modelle
    legt die Anwendung in ihren Ports fest.
    """

    router: RouterOcr | None = None
    routing: OcrRouting | None = None
    chandra: ChandraPort | None = None
    tesseract: TesseractPort | None = None
    donut: DonutPort | None = None
    rasterizer: Rasterizer | None = pdfium_rasterizer

    @property
    def text_ocr(self) -> bool:
        """Mindestens eine Engine für die Profile ohne Donut."""
        return any(port is not None for port in (self.router, self.chandra, self.tesseract))

    def flags(self) -> dict[str, bool]:
        """Welche Ports angeschlossen sind (ohne Adressen)."""
        return {
            "router": self.router is not None,
            "chandra": self.chandra is not None,
            "tesseract": self.tesseract is not None,
            "donut": self.donut is not None,
        }


@dataclass(frozen=True)
class ExtractionSettings:
    """Grenzen, angebotene Profile und Aufbewahrungsfristen der Anwendung."""

    max_upload_bytes: int = 20 * 1024 * 1024
    profiles: tuple[str, ...] = tuple(PIPELINE_PROFILES)
    default_profile: str = RECOMMENDED_PIPELINE.profile_id
    retention: RetentionPolicyConfig = field(
        default_factory=lambda: RetentionPolicyConfig(name="standard", is_default=True)
    )
    thresholds: Thresholds = field(default_factory=Thresholds)


class ExtractionService:
    """Anwendungsfälle der Belegerkennung (Katalog, Lauf)."""

    def __init__(
        self,
        engines: ExtractionEngines | None = None,
        settings: ExtractionSettings | None = None,
    ) -> None:
        self.engines = engines or ExtractionEngines()
        self.settings = settings or ExtractionSettings()
        unknown = [p for p in self.settings.profiles if p not in PIPELINE_PROFILES]
        if unknown:
            raise ValueError(f"Unbekannte Pipeline-Profile: {', '.join(unknown)}")

    def available(self, profile: PipelineProfile) -> bool:
        """Ob die angeschlossenen Engines das Profil tragen."""
        if profile.ocr_backend == "donut":
            return self.engines.donut is not None
        return self.engines.text_ocr

    @property
    def enabled(self) -> bool:
        """Mindestens ein angebotenes Profil ist ausführbar."""
        return any(self.available(PIPELINE_PROFILES[p]) for p in self.settings.profiles)

    def _default_profile(self) -> str | None:
        usable = [p for p in self.settings.profiles if self.available(PIPELINE_PROFILES[p])]
        if self.settings.default_profile in usable:
            return self.settings.default_profile
        return usable[0] if usable else None

    def _profile_entry(self, profile_id: str) -> dict[str, object]:
        profile = PIPELINE_PROFILES[profile_id]
        return {
            **profile.identity(),
            "label": PROFILE_LABELS.get(profile_id, profile_id),
            "status": profile.status,
            "ocr_backend": profile.ocr_backend,
            "recommended": profile is RECOMMENDED_PIPELINE,
            "min_field_confidence": profile.donut_min_field_confidence,
            "available": self.available(profile),
            "retention_categories": list(profile.retention_categories),
        }

    def catalogue(self) -> dict[str, object]:
        """``GET /profile``: Profile, Engines, Grenzen, Schwellen und Aufbewahrung."""
        retention = self.settings.retention
        return {
            "contract": CONTRACT,
            "library": LIBRARY,
            "enabled": self.enabled,
            "engines": self.engines.flags(),
            "profiles": [self._profile_entry(p) for p in self.settings.profiles],
            "default_profile": self._default_profile(),
            "accepted_types": sorted(ALLOWED_MIME_TYPES),
            "limits": {"max_upload_bytes": self.settings.max_upload_bytes},
            "thresholds": self.settings.thresholds.to_dict(),
            "retention": {
                "stored": False,
                "days": {c: getattr(retention, f) for c, f in CATEGORY_DAYS_FIELD.items()},
            },
        }

    def ensure_enabled(self) -> None:
        """404 ``extraction_disabled``, wenn keine Engine angeschlossen ist."""
        if not self.enabled:
            raise ExtractionError(
                "Belegerkennung ist abgeschaltet (keine OCR-Engine angeschlossen).",
                status=404,
                code="extraction_disabled",
            )

    def _resolve(self, profile_id: str | None) -> PipelineProfile:
        self.ensure_enabled()
        chosen = profile_id or self._default_profile() or ""
        if chosen not in self.settings.profiles:
            raise ExtractionError(f"Unbekanntes Profil: {chosen!r}.", code="unknown_profile")
        profile = PIPELINE_PROFILES[chosen]
        if not self.available(profile):
            raise ExtractionError(
                f"Profil {chosen!r} braucht eine Engine, die nicht angeschlossen ist.",
                code="profile_unavailable",
            )
        return profile

    def _ocr_stage(self, audit: InMemoryAuditLog) -> OcrStage:
        engines = self.engines
        return OcrStage(
            audit_service=audit,
            routing=engines.routing,
            router=engines.router,
            rasterizer=engines.rasterizer,
            chandra=engines.chandra,
            tesseract=engines.tesseract,
            donut=engines.donut,
            min_confidence_ok=self.settings.thresholds.ok,
            min_confidence_review=self.settings.thresholds.review,
        )

    def run(self, filename: str, content: bytes, profile_id: str | None) -> dict[str, object]:
        """``POST /runs``: ein Dokument mit dem gewählten Profil verarbeiten."""
        profile = self._resolve(profile_id)
        if not content:
            raise ExtractionError("Die Datei ist leer.", code="empty_file")
        if len(content) > self.settings.max_upload_bytes:
            raise ExtractionError("Die Datei ist zu groß.", status=413, code="too_large")
        digest = hashlib.sha256(content).hexdigest()
        suffix = PurePath(filename).suffix.casefold()
        with tempfile.TemporaryDirectory(prefix="auditcore-extraction-") as folder:
            path = Path(folder) / ("dokument" + (suffix if _SUFFIX.fullmatch(suffix) else ""))
            path.write_bytes(content)
            audit = InMemoryAuditLog()
            pipeline = build_pipeline(profile=profile, audit=audit, ocr=self._ocr_stage(audit))
            context = PipelineContext(
                document_id=str(uuid.uuid4()), input_uri=str(path), hash_original=digest
            )
            context = asyncio.run(pipeline.run(context))
        document = {"filename": PurePath(filename.replace("\\", "/")).name[:200], "sha256": digest}
        return {
            "contract": CONTRACT,
            "library": LIBRARY,
            "profile": {**profile.identity(), "status": profile.status},
            **run_result(context, document, self.settings.thresholds),
        }
