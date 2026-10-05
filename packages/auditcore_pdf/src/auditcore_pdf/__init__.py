"""auditcore_pdf – Vollständige PDF-Verarbeitung,
Seitenoperationen, Anzeige und nachprüfbare Schwärzung.
"""

from __future__ import annotations

from auditcore_pdf.engine import MAX_PAGES, is_pymupdf_available, open_pdf
from auditcore_pdf.imagecheck import find_unverifiable_pages
from auditcore_pdf.models import (
    DEFAULT_IMAGE_COVERAGE_THRESHOLD,
    DEFAULT_PATTERNS,
    STANDARD_PATTERNS,
    DocumentInfo,
    PageInfo,
    RedactionBox,
    RedactionFinding,
    RedactionPattern,
    RedactionReport,
    SanitizationPolicy,
    VerificationResult,
)
from auditcore_pdf.operations import (
    delete_pages,
    extract_pages,
    merge_documents,
    reorder_pages,
    rotate_pages,
    split_document,
)
from auditcore_pdf.redact import find_redaction_targets, redact_document
from auditcore_pdf.sanitize import (
    find_unverifiable_attachments,
    sanitize_annotations,
    sanitize_attachments,
    sanitize_metadata,
)
from auditcore_pdf.structure_clean import sanitize_structure
from auditcore_pdf.verification import verify_redaction
from auditcore_pdf.viewer import (
    extract_all_text,
    extract_page_text,
    get_document_info,
    get_toc,
    render_page,
)

__all__ = [
    "DEFAULT_IMAGE_COVERAGE_THRESHOLD",
    "DEFAULT_PATTERNS",
    "MAX_PAGES",
    "STANDARD_PATTERNS",
    "DocumentInfo",
    "PageInfo",
    "RedactionBox",
    "RedactionFinding",
    "RedactionPattern",
    "RedactionReport",
    "SanitizationPolicy",
    "VerificationResult",
    "delete_pages",
    "extract_all_text",
    "extract_page_text",
    "extract_pages",
    "find_redaction_targets",
    "find_unverifiable_attachments",
    "find_unverifiable_pages",
    "get_document_info",
    "get_toc",
    "is_pymupdf_available",
    "merge_documents",
    "open_pdf",
    "redact_document",
    "render_page",
    "reorder_pages",
    "rotate_pages",
    "sanitize_annotations",
    "sanitize_attachments",
    "sanitize_metadata",
    "sanitize_structure",
    "split_document",
    "verify_redaction",
]

__version__ = "0.2.0"
