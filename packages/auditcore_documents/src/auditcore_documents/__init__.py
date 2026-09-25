"""auditcore_documents – Dokumentvergleich und Gesetzessynopse.

Reiner Kern (nur Standardbibliothek): Datenmodell, Normalisierung, Zuordnung,
Änderungsbefehle, Einstellungen, Begründungsport, Synopse-Datensätze.
Extras: ``docx`` (lxml, DOCX/DOCM lesen), ``pdf-text`` (pypdf),
``fuzzy`` (rapidfuzz, Produktionsmaß), ``docx-render`` (python-docx).
"""

from __future__ import annotations

from auditcore_documents.article_law import (
    COMMAND_PATTERNS,
    LawParagraph,
    apply_commands,
    base_paragraphs,
)
from auditcore_documents.compare import (
    CompareOptions,
    ReadContext,
    compare_article_law_files,
    compare_files,
    compare_items,
)
from auditcore_documents.errors import (
    CompareError,
    DependencyError,
    LimitExceededError,
    ParseError,
)
from auditcore_documents.limits import DEFAULT_LIMITS, ReadLimits
from auditcore_documents.model import CompareItem, CompareRow, ComparisonResult
from auditcore_documents.normalize import (
    normalise_for_match,
    normalise_semantic,
    normalise_verbatim,
    word_diff,
)
from auditcore_documents.pdftext import (
    legacy_pdf_pages,
    paragraphs_from_pdf_pages,
    pdftotext_pages,
    pypdf_pages,
    remove_repeating_margins,
    text_items_from_paragraphs,
)
from auditcore_documents.profiles import (
    CORRECTED,
    LEGACY,
    LEGACY_DIFFLIB,
    PROFILES,
    RECOMMENDED,
    CompareProfile,
    get_profile,
)
from auditcore_documents.reading import (
    ALLOWED_EXTENSIONS,
    detect_mode,
    read_document,
    read_text_paragraphs,
)
from auditcore_documents.reasons import (
    ReasonProvider,
    apply_reasons_cli,
    apply_reasons_worker,
    generate_reason,
    mcp_tool_provider,
    verify_legal_references,
)
from auditcore_documents.scoring import difflib_ratio, get_scorer, rapidfuzz_token_set
from auditcore_documents.settings import (
    DEFAULT_SETTINGS,
    load_settings,
    merge_settings,
    sanitise_settings,
    save_settings,
)
from auditcore_documents.synopsis import synopsis_extra, synopsis_records

__version__ = "0.2.1"

__all__ = [
    "ALLOWED_EXTENSIONS",
    "COMMAND_PATTERNS",
    "CORRECTED",
    "DEFAULT_LIMITS",
    "DEFAULT_SETTINGS",
    "LEGACY",
    "LEGACY_DIFFLIB",
    "PROFILES",
    "RECOMMENDED",
    "CompareError",
    "CompareItem",
    "CompareOptions",
    "CompareProfile",
    "CompareRow",
    "ComparisonResult",
    "DependencyError",
    "LawParagraph",
    "LimitExceededError",
    "ParseError",
    "ReadContext",
    "ReadLimits",
    "ReasonProvider",
    "__version__",
    "apply_commands",
    "apply_reasons_cli",
    "apply_reasons_worker",
    "base_paragraphs",
    "compare_article_law_files",
    "compare_files",
    "compare_items",
    "detect_mode",
    "difflib_ratio",
    "generate_reason",
    "get_profile",
    "get_scorer",
    "legacy_pdf_pages",
    "load_settings",
    "mcp_tool_provider",
    "merge_settings",
    "normalise_for_match",
    "normalise_semantic",
    "normalise_verbatim",
    "paragraphs_from_pdf_pages",
    "pdftotext_pages",
    "pypdf_pages",
    "rapidfuzz_token_set",
    "read_document",
    "read_text_paragraphs",
    "remove_repeating_margins",
    "sanitise_settings",
    "save_settings",
    "synopsis_extra",
    "synopsis_records",
    "text_items_from_paragraphs",
    "verify_legal_references",
    "word_diff",
]
