"""Vergleich zweier Fassungen: Standardvergleich und Gesetzessynopse.

Frameworkunabhängig: keine Web-, Datenbank-, Celery- oder KI-Importe.
Dateisystemzugriffe beschränken sich auf das Lesen der beiden übergebenen
Dateien; Uhr, PDF-Seitenquelle und OCR sind injizierbar.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from auditcore_common.clock import utc_now
from auditcore_common.hashing import sha256_file

from auditcore_documents.article_law import (
    apply_commands,
    article_law_result,
    base_paragraphs,
)
from auditcore_documents.errors import CompareError
from auditcore_documents.limits import DEFAULT_LIMITS, ReadLimits
from auditcore_documents.matching import (
    build_rows,
    checklist_matches,
    detect_moves,
    text_matches,
)
from auditcore_documents.model import CompareItem, ComparisonResult
from auditcore_documents.pdftext import OcrCallback, PageSource, text_items_from_paragraphs
from auditcore_documents.profiles import CompareProfile
from auditcore_documents.reading import read_document, read_text_paragraphs
from auditcore_documents.scoring import get_scorer

DEFAULT_SECTIONS = ("changed", "removed", "added", "moved")
PDF_NOTICE = (
    "PDF-Dateien werden stets als Fließtext behandelt. "
    "Nachverfolgte Änderungen, ausgeblendete Texte und Tabellenstrukturen "
    "können aus PDF nicht rekonstruiert werden."
)


@dataclass(frozen=True)
class CompareOptions:
    """Fachliche Optionen eines Laufs (Vorgaben wie im Original)."""

    mode: str = "auto"
    threshold: int = 85
    include_answers: bool = True
    include_notes: bool = True
    include_editorial: bool = False
    highlight_words: bool = True
    output_sections: tuple[str, ...] | list[str] | None = None
    comparison_type: str = "standard"

    def sections(self) -> list[str]:
        return list(self.output_sections or DEFAULT_SECTIONS)


@dataclass(frozen=True)
class ReadContext:
    """Umgebungsabhängige Lesebausteine; alle optional und austauschbar."""

    ocr_callback: OcrCallback | None = None
    page_source: PageSource | None = None
    limits: ReadLimits = DEFAULT_LIMITS
    now: Callable[[], datetime] = field(default=utc_now)


def compare_items(
    old_items: list[CompareItem],
    new_items: list[CompareItem],
    *,
    mode: str,
    profile: CompareProfile,
    threshold: int = 85,
    include_answers: bool = True,
    include_notes: bool = True,
    include_editorial: bool = False,
) -> tuple[list[Any], dict[str, int]]:
    """Reiner Kern ohne Dateizugriff: Zuordnung, Umstellungen, Zeilen, Zählwerte."""
    scorer = get_scorer(profile.scorer)
    if mode == "text":
        pairs, removed, added = text_matches(old_items, new_items, threshold, scorer)
    else:
        pairs, removed, added = checklist_matches(old_items, new_items, threshold, scorer)
    moved, removed, added = detect_moves(removed, added)
    rows = build_rows(
        mode,
        pairs,
        removed,
        added,
        include_answers=include_answers,
        include_notes=include_notes,
        include_editorial=include_editorial,
        moved=moved,
    )
    counts = {
        "old_count": len(old_items),
        "new_count": len(new_items),
        "matched_count": len(pairs),
        "changed_count": sum(row.status == "changed" for row in rows),
        "removed_count": sum(row.status == "removed" for row in rows),
        "added_count": sum(row.status == "added" for row in rows),
        "moved_count": sum(row.status == "moved" for row in rows),
    }
    return rows, counts


def _validate(options: CompareOptions) -> None:
    if not 70 <= options.threshold <= 100:
        raise CompareError("Die Ähnlichkeitsschwelle muss zwischen 70 und 100 liegen.")


def _amendment_commands(path: Path, profile: CompareProfile, context: ReadContext) -> list[str]:
    paragraphs = read_text_paragraphs(
        path,
        ocr_callback=context.ocr_callback,
        page_source=context.page_source,
        limits=context.limits,
    )
    if profile.amendment_reading == "all-paragraphs":
        # DC-C04: auch Absätze, die mit „§“ beginnen, sind mögliche Befehle.
        commands = [text for text, _heading in paragraphs if text]
    else:
        commands = [item.text for item in text_items_from_paragraphs(paragraphs)]
    if not commands:
        raise CompareError(f"In {path.name} wurden keine vergleichbaren Textstellen gefunden.")
    return commands


def compare_article_law_files(
    base: Path,
    amendment: Path,
    *,
    profile: CompareProfile,
    context: ReadContext | None = None,
) -> ComparisonResult:
    """Stammgesetz und Änderungsbefehle zur Synopse zusammenführen."""
    context = context or ReadContext()
    _mode, items = read_document(
        base,
        "text",
        ocr_callback=context.ocr_callback,
        page_source=context.page_source,
        limits=context.limits,
    )
    try:
        paragraphs = base_paragraphs(items)
    except ValueError as exc:
        raise CompareError(str(exc)) from exc
    commands = _amendment_commands(amendment, profile, context)
    paragraphs, open_commands, recognised = apply_commands(
        paragraphs, commands, renumber_after_insert=profile.renumber_after_insert
    )
    result = article_law_result(
        paragraphs,
        open_commands,
        recognised,
        old_filename=base.name,
        new_filename=amendment.name,
        old_sha256=sha256_file(base),
        new_sha256=sha256_file(amendment),
        version=profile.result_version,
        now=context.now,
    )
    if profile.record_profile:
        result.metadata["profile"] = profile.identity()
    return result


def _compare_article_law(
    old: Path, new: Path, profile: CompareProfile, options: CompareOptions, context: ReadContext
) -> ComparisonResult:
    result = compare_article_law_files(old, new, profile=profile, context=context)
    result.metadata.update(
        {
            "old_modified_at": old.stat().st_mtime,
            "new_modified_at": new.stat().st_mtime,
            "output_sections": options.sections(),
            "highlight_words": options.highlight_words,
            "include_answers": False,
            "include_notes": False,
        }
    )
    return result


def _read_pair(
    old: Path, new: Path, mode: str, context: ReadContext
) -> tuple[str, list[CompareItem], list[CompareItem]]:
    """Beide Fassungen im selben Modus lesen; abweichende Dokumentarten sind ein Fehler."""

    def read(path: Path) -> tuple[str, list[CompareItem]]:
        return read_document(
            path,
            mode,
            ocr_callback=context.ocr_callback,
            page_source=context.page_source,
            limits=context.limits,
        )

    old_mode, old_items = read(old)
    new_mode, new_items = read(new)
    if old_mode != new_mode:
        raise CompareError(
            "Die Dokumentarten unterscheiden sich; bitte den Modus ausdrücklich wählen."
        )
    return old_mode, old_items, new_items


def _standard_metadata(
    old: Path, new: Path, detected_mode: str, has_pdf: bool, options: CompareOptions
) -> dict[str, Any]:
    return {
        "comparison_type": "standard",
        "detected_mode": detected_mode,
        "threshold": options.threshold,
        "include_answers": options.include_answers,
        "include_notes": options.include_notes,
        "include_editorial": options.include_editorial,
        "highlight_words": options.highlight_words,
        "output_sections": options.sections(),
        "old_modified_at": old.stat().st_mtime,
        "new_modified_at": new.stat().st_mtime,
        "pdf_notice": PDF_NOTICE if has_pdf else "",
    }


def compare_files(
    old: Path,
    new: Path,
    *,
    profile: CompareProfile,
    options: CompareOptions | None = None,
    context: ReadContext | None = None,
) -> ComparisonResult:
    """Zwei Fassungen vergleichen (Vertrag von ``DocumentCompareService.compare``)."""
    options = options or CompareOptions()
    context = context or ReadContext()
    _validate(options)
    if options.comparison_type == "article_law":
        return _compare_article_law(old, new, profile, options, context)
    if options.comparison_type != "standard":
        raise CompareError("Unbekannter Vergleichstyp.")
    has_pdf = old.suffix.casefold() == ".pdf" or new.suffix.casefold() == ".pdf"
    effective_mode = "text" if options.mode == "auto" and has_pdf else options.mode
    mode, old_items, new_items = _read_pair(old, new, effective_mode, context)
    rows, counts = compare_items(
        old_items,
        new_items,
        mode=mode,
        profile=profile,
        threshold=options.threshold,
        include_answers=options.include_answers,
        include_notes=options.include_notes,
        include_editorial=options.include_editorial,
    )
    metadata = _standard_metadata(old, new, mode, has_pdf, options)
    if profile.record_profile:
        metadata["profile"] = profile.identity()
    return ComparisonResult(
        version=profile.result_version,
        mode=mode,
        old_filename=old.name,
        new_filename=new.name,
        old_sha256=sha256_file(old),
        new_sha256=sha256_file(new),
        rows=rows,
        created_at=context.now().isoformat(),
        metadata=metadata,
        **counts,
    )
