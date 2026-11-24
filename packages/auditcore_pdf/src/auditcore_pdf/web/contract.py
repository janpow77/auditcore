"""REST contract ``pdf_redaction/1``: catalogue, plan, page preview, apply (framework-free).

The service holds no state: every request carries the PDF again, the plan is
never stored and never logged (it contains plaintext of the findings). The
host sets authentication, CORS and rate limits; :class:`Limits` bounds upload
size, page count, selection size and preview resolution.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import PurePath
from urllib.parse import quote

from auditcore_common import rest

from .. import __version__
from ..engine import fitz
from ..redaction import (
    MAX_AREAS,
    MAX_AREAS_PER_PAGE,
    MAX_TERM_LENGTH,
    MAX_TERMS,
    NER_PATTERN_ID,
    PATTERNS,
    Criteria,
    NerFn,
    RedactionError,
    RedactionNerError,
    RedactionStaleError,
    RedactionVerificationError,
    Selection,
    apply_plan,
    build_plan,
)
from ..redaction.plan import open_document

CONTRACT = "pdf_redaction/1"
LIBRARY = f"auditcore_pdf {__version__}"
Json = dict[str, object]
MIB = 1024 * 1024
#: Seitennummer im Formularfeld ``page`` (nur ASCII-Ziffern, keine Riesenzahlen).
PAGE_NUMBER = re.compile(r"[0-9]{1,6}")


@dataclass(frozen=True)
class Limits:
    """Request limits of the contract (reported in the catalogue)."""

    max_upload_bytes: int = 50 * MIB
    max_pages: int = 500
    max_selection_bytes: int = 8 * MIB
    max_criteria_bytes: int = 256 * 1024
    preview_dpi: int = 110
    preview_max_edge: int = 1800

    def __post_init__(self) -> None:
        for name, value in vars(self).items():
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"Limits.{name} muss eine positive ganze Zahl sein")


class ContractError(rest.ContractError):
    """Request does not satisfy the ``pdf_redaction/1`` contract (status, code, ``to_dict``)."""


@dataclass(frozen=True)
class Applied:
    """Redacted PDF with the counts of the verified report (no plaintext)."""

    content: bytes
    filename: str
    headers: Mapping[str, str]


def _reject_constant(value: str) -> object:
    raise ValueError(f"{value} ist nicht erlaubt")


def _finite(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Zahl außerhalb des Wertebereichs")
    return number


def decode_json(raw: bytes | str, limit: int, name: str) -> object:
    """JSON field ``name`` within ``limit`` bytes; NaN and Infinity are rejected."""
    data = raw.encode("utf-8") if isinstance(raw, str) else raw
    if len(data) > limit:
        raise ContractError(f"„{name}“ ist zu groß.", status=413, code="too_large")
    try:
        return json.loads(data, parse_constant=_reject_constant, parse_float=_finite)
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise ContractError(
            f"„{name}“ ist kein gültiges JSON.", status=400, code="invalid_json"
        ) from exc


def attachment(filename: str) -> str:
    """``Content-Disposition`` with an ASCII fallback and the UTF-8 name (RFC 5987)."""
    ascii_name = filename.encode("ascii", "replace").decode("ascii").replace("?", "_")
    ascii_name = ascii_name.replace('"', "_").replace("\\", "_")
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename)}"


def redacted_name(filename: str) -> str:
    """``<stem>_geschwärzt.pdf`` from the upload name (path parts dropped)."""
    stem = PurePath(filename.replace("\\", "/")).stem.strip() or "dokument"
    stem = "".join(ch for ch in stem if ch.isprintable() and ch not in '"/\\')[:120]
    return f"{stem or 'dokument'}_geschwärzt.pdf"


def _bool(value: object, name: str, default: bool) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ContractError(f"„{name}“ muss wahr oder falsch sein.", code="invalid_criteria")
    return value


def _strings(value: object, name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise ContractError(f"„{name}“ muss eine Liste von Texten sein.", code="invalid_criteria")
    return list(value)


class RedactionService:
    """Endpoints of ``pdf_redaction/1``; ``ner`` enables the AI name pattern."""

    def __init__(self, ner: NerFn | None = None, limits: Limits | None = None) -> None:
        self.ner = ner
        self.limits = limits or Limits()

    # -- GET /catalogue ---------------------------------------------------
    def catalogue(self) -> Json:
        """Patterns with availability, limits and the contract version."""
        limits = self.limits
        return {
            "contract": CONTRACT,
            "library": LIBRARY,
            "ner_available": self.ner is not None,
            "patterns": [
                {
                    "id": key,
                    "label": spec.label,
                    "hint": spec.hint,
                    "ai": spec.ai,
                    "available": key != NER_PATTERN_ID or self.ner is not None,
                }
                for key, spec in PATTERNS.items()
            ],
            "limits": {
                "max_upload_bytes": limits.max_upload_bytes,
                "max_pages": limits.max_pages,
                "max_selection_bytes": limits.max_selection_bytes,
                "max_terms": MAX_TERMS,
                "max_term_length": MAX_TERM_LENGTH,
                "max_areas": MAX_AREAS,
                "max_areas_per_page": MAX_AREAS_PER_PAGE,
            },
        }

    # -- shared checks ----------------------------------------------------
    def check_size(self, size: int) -> None:
        """413 ``too_large`` above ``max_upload_bytes``."""
        if size > self.limits.max_upload_bytes:
            raise ContractError("Die Datei ist zu groß.", status=413, code="too_large")

    def _page_count(self, data: bytes) -> int:
        self.check_size(len(data))
        if not data:
            raise ContractError("Feld „file“ fehlt oder ist leer.", status=400, code="missing_file")
        try:
            doc = open_document(data)
        except RedactionError as exc:
            raise ContractError(str(exc), code="invalid_pdf") from exc
        try:
            count = int(doc.page_count)
        finally:
            doc.close()
        if count > self.limits.max_pages:
            raise ContractError(
                f"Die PDF hat {count} Seiten; zulässig sind höchstens {self.limits.max_pages}.",
                status=413,
                code="too_many_pages",
            )
        return count

    def _require_ner(self, criteria: Criteria) -> None:
        if NER_PATTERN_ID in criteria.patterns and self.ner is None:
            raise ContractError(
                "KI-Namenserkennung ist nicht eingerichtet.", status=503, code="ner_unavailable"
            )

    def criteria(self, payload: object) -> Criteria:
        """Strictly typed criteria; 422 ``invalid_criteria`` or ``empty_criteria``."""
        if not isinstance(payload, dict):
            raise ContractError("„criteria“ muss ein JSON-Objekt sein.", code="invalid_criteria")
        try:
            criteria = Criteria.from_input(
                _strings(payload.get("patterns"), "patterns"),
                _strings(payload.get("terms"), "terms"),
                _bool(payload.get("case_sensitive"), "case_sensitive", False),
                _bool(payload.get("whole_word"), "whole_word", True),
            )
        except RedactionError as exc:
            raise ContractError(str(exc), code="invalid_criteria") from exc
        if not criteria.patterns and not criteria.terms:
            raise ContractError(
                "Mindestens ein Muster oder Begriff ist nötig.", code="empty_criteria"
            )
        self._require_ner(criteria)
        return criteria

    # -- POST /plan -------------------------------------------------------
    def plan(self, data: bytes, criteria_payload: object) -> Json:
        """Findings with ids, display rectangles, text and location; changes nothing."""
        criteria = self.criteria(criteria_payload)
        self._page_count(data)
        try:
            plan = build_plan(data, criteria, self.ner)
        except RedactionNerError as exc:
            raise ContractError(str(exc), status=502, code="ner_failed") from exc
        except RedactionError as exc:
            raise ContractError(str(exc), code="invalid_pdf") from exc
        return {"contract": CONTRACT, **plan.to_dict()}

    # -- POST /preview ----------------------------------------------------
    def preview(self, data: bytes, page: object) -> bytes:
        """PNG of one page (1-based), longest edge at most ``preview_max_edge`` pixels."""
        count = self._page_count(data)
        number = page if isinstance(page, int) and not isinstance(page, bool) else None
        if isinstance(page, str) and PAGE_NUMBER.fullmatch(page.strip()):
            number = int(page.strip())
        if number is None or not 1 <= number <= count:
            raise ContractError(f"Seite muss zwischen 1 und {count} liegen.", code="invalid_page")
        doc = open_document(data)
        try:
            target = doc[number - 1]
            edge = max(float(target.rect.width), float(target.rect.height), 1.0)
            zoom = min(self.limits.preview_dpi / 72.0, self.limits.preview_max_edge / edge)
            pix = target.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            return bytes(pix.tobytes("png"))
        finally:
            doc.close()

    # -- POST /apply ------------------------------------------------------
    def apply(self, data: bytes, filename: str, selection_payload: object) -> Applied:
        """Redact exactly the confirmed selection; 422 when a selected finding stays legible."""
        self._page_count(data)
        try:
            selection = Selection.from_dict(selection_payload)
        except RedactionError as exc:
            raise ContractError(str(exc), code="invalid_selection") from exc
        self._require_ner(selection.criteria)
        try:
            out, report = apply_plan(data, selection, self.ner)
        except RedactionStaleError as exc:
            raise ContractError(str(exc), status=409, code="stale_plan") from exc
        except RedactionVerificationError as exc:
            raise ContractError(str(exc), code="verification_failed") from exc
        except RedactionNerError as exc:
            raise ContractError(str(exc), status=502, code="ner_failed") from exc
        except RedactionError as exc:
            raise ContractError(str(exc), code="invalid_selection") from exc
        name = redacted_name(filename)
        return Applied(
            out,
            name,
            {
                "Content-Disposition": attachment(name),
                "Cache-Control": "no-store",
                "X-Redactions": str(report.redactions),
                "X-Redaction-Areas": str(report.areas),
                "X-Redaction-Hidden": str(report.hidden_removed),
                "X-Redaction-Deselected": str(report.deselected),
                "X-Redaction-Pages": str(len(report.pages)),
                "X-Redaction-Sanitized": "true" if selection.sanitize else "false",
                "X-Redaction-Verified": "true",
            },
        )
