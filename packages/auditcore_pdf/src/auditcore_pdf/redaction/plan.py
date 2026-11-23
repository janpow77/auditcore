"""Plan der Schwärzung: Fundstellen, Seitenangaben und Bereinigungshinweise."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypedDict

from auditcore_common.json_values import JsonObject

from auditcore_pdf.engine import fitz, require_engine
from auditcore_pdf.redaction.common import PLAN_VERSION, Box, HiddenRef, RedactionError
from auditcore_pdf.redaction.criteria import Criteria
from auditcore_pdf.redaction.patterns import source_label

if TYPE_CHECKING:
    from pymupdf import Document


class CleanupInfo(TypedDict):
    """Was die Bereinigung entfernen würde (Metadaten, XMP, Anhänge, JavaScript)."""

    metadata_fields: list[str]
    xmp: bool
    attachments: int
    javascript: bool


@dataclass
class Candidate:
    """Eine Fundstelle im Seitentext (``kind="text"``) oder in einer versteckten Ablage."""

    id: str
    kind: str  # "text" | "hidden"
    source: str
    text: str
    page: int | None = None  # 1-basiert
    rects: list[Box] = field(default_factory=list)  # PDF-Koordinaten (ungedreht)
    view_rects: list[Box] = field(default_factory=list)  # 0…1, Anzeige (gedreht)
    location: str = "Seitentext"
    ref: HiddenRef = field(default_factory=dict)  # Fundort versteckter Inhalte
    outside_view: bool = False
    start: int = 0
    end: int = 0
    priority: int = 0

    def union_rect(self) -> Box | None:
        if not self.rects:
            return None
        box = fitz.Rect(self.rects[0])
        for r in self.rects[1:]:
            box |= fitz.Rect(r)
        return [round(float(v), 2) for v in box]

    def to_dict(self) -> JsonObject:
        return {
            "id": self.id,
            "kind": self.kind,
            "source": self.source,
            "label": source_label(self.source),
            "text": self.text,
            "page": self.page,
            "rects": self.view_rects,
            "pdf_rect": self.union_rect(),
            "location": self.location,
            "outside_view": self.outside_view,
            "selected": True,
        }


@dataclass
class PageInfo:
    """Maße und Textlage einer Seite im Plan."""

    page: int
    width: float
    height: float
    rotation: int
    has_text: bool
    image_only: bool

    def to_dict(self) -> JsonObject:
        return {
            "page": self.page,
            "width": round(self.width, 2),
            "height": round(self.height, 2),
            "rotation": self.rotation,
            "has_text": self.has_text,
        }


@dataclass
class Plan:
    """Ergebnis von :func:`build_plan`; enthält Klartext, nie protokollieren."""

    sha256: str
    criteria: Criteria
    pages: list[PageInfo]
    candidates: list[Candidate]
    cleanup: CleanupInfo

    @property
    def text_candidates(self) -> list[Candidate]:
        return [c for c in self.candidates if c.kind == "text"]

    def by_source(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for c in self.candidates:
            counts[c.source] = counts.get(c.source, 0) + 1
        return counts

    def to_dict(self) -> JsonObject:
        cleanup = self.cleanup
        return {
            "version": PLAN_VERSION,
            "sha256": self.sha256,
            "criteria": self.criteria.to_dict(),
            "page_count": len(self.pages),
            "pages": [p.to_dict() for p in self.pages],
            "pages_without_text": [p.page for p in self.pages if p.image_only],
            "total": len(self.candidates),
            "by_source": self.by_source(),
            "candidates": [c.to_dict() for c in self.candidates],
            "cleanup": {
                "metadata_fields": cleanup["metadata_fields"],
                "xmp": cleanup["xmp"],
                "attachments": cleanup["attachments"],
                "javascript": cleanup["javascript"],
            },
        }


def open_document(data: bytes) -> Document:
    """Öffnet eine ungeschützte PDF mit mindestens einer Seite."""
    require_engine()
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise RedactionError("Die Datei ist keine lesbare PDF-Datei") from exc
    if doc.needs_pass or doc.is_encrypted:
        doc.close()
        raise RedactionError("Die PDF ist passwortgeschützt. Bitte zuerst entsperren.")
    if doc.page_count == 0:
        doc.close()
        raise RedactionError("Die PDF enthält keine Seiten")
    return doc
