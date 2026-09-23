"""PDF-Text: austauschbare Seitenquelle und reine Absatzbildung.

Die Absatzbildung (Seitenränder, Silbentrennung, Überschriften) ist reine
Textverarbeitung und entspricht unverändert dem Original. Die Seitenquelle
ist injizierbar: ``legacy_pdf_pages`` bildet die Originalreihenfolge ab
(``pdftotext -layout``, sonst ``pypdf``). Welche Quelle Text liefert, hängt
von der installierten Umgebung ab; Anwendungen können deshalb eine feste
Quelle wählen. OCR bleibt ein ausdrücklich übergebener Rückruf.
"""

from __future__ import annotations

import re
import subprocess
from collections import Counter
from collections.abc import Callable
from pathlib import Path

from auditcore_documents.errors import DependencyError, LimitExceededError, ParseError
from auditcore_documents.limits import DEFAULT_LIMITS, ReadLimits
from auditcore_documents.model import CompareItem
from auditcore_documents.ooxml import HEADING_RE

PAGE_NUMBER_RE = re.compile(r"^(?:Seite\s+)?\d+(?:\s+von\s+\d+)?$", re.IGNORECASE)

#: Liefert die Textseiten eines PDF.
PageSource = Callable[[Path], list[str]]
#: OCR-Rückruf der Anwendung (z. B. KI-Router); liefert den Text des Dokuments.
OcrCallback = Callable[[Path], str]


def _argument(path: Path) -> str:
    """Pfad als Programmargument; ein führendes „-“ wird nicht als Option gelesen."""
    text = str(path)
    return f"./{text}" if text.startswith("-") else text


def pdftotext_pages(
    path: Path, *, executable: str = "pdftotext", timeout: float = 120.0
) -> list[str]:
    """``pdftotext -layout`` (poppler-utils) als externer Prozess.

    Löst ``FileNotFoundError``, ``CalledProcessError`` oder
    ``TimeoutExpired`` aus, wenn das Programm fehlt, scheitert oder zu lange
    läuft. Die Ausgabe wird ausdrücklich als UTF-8 gelesen (DC-C05).
    """
    completed = subprocess.run(  # noqa: S603 - festes Programm, keine Shell
        [executable, "-layout", _argument(path), "-"],
        check=True,
        capture_output=True,
        timeout=timeout,
    )
    try:
        stdout = completed.stdout.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ParseError(f"{path.name}: pdftotext lieferte kein gültiges UTF-8.") from exc
    return [page for page in stdout.split("\f") if page.strip()]


def pypdf_pages(path: Path) -> list[str]:
    """Textextraktion mit ``pypdf`` (Extra ``pdf-text``); Fehlertexte wie im Original."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise DependencyError("PDF-Vergleich benötigt pdftotext oder pypdf.") from exc
    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception as exc:  # noqa: BLE001 - pypdf wirft uneinheitlich
                raise ParseError(f"{path.name} ist passwortgeschützt.") from exc
        return [page.extract_text() or "" for page in reader.pages]
    except ParseError:
        raise
    except Exception as exc:  # noqa: BLE001 - Originalvertrag: jeder Lesefehler
        raise ParseError(f"PDF konnte nicht gelesen werden: {exc}") from exc


def legacy_pdf_pages(path: Path, *, timeout: float = 120.0) -> list[str]:
    """Originalreihenfolge: zuerst ``pdftotext``, bei Fehlen/Fehler ``pypdf``."""
    try:
        return pdftotext_pages(path, timeout=timeout)
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return pypdf_pages(path)


def remove_repeating_margins(pages: list[str]) -> list[list[str]]:
    """Seitenzahlen und wiederkehrende Kopf-/Fußzeilen entfernen."""
    page_lines: list[list[str]] = []
    edge_counts: Counter[str] = Counter()
    for page in pages:
        lines = [re.sub(r"\s+", " ", line).strip() for line in page.splitlines()]
        nonempty = [line for line in lines if line]
        page_lines.append(lines)
        for line in {line.casefold() for line in [*nonempty[:3], *nonempty[-3:]]}:
            if line and not PAGE_NUMBER_RE.fullmatch(line):
                edge_counts[line.casefold()] += 1
    repeated = {
        value
        for value, count in edge_counts.items()
        if len(page_lines) >= 2 and count >= max(2, (len(page_lines) + 1) // 2)
    }
    return [
        [
            line
            for line in lines
            if not PAGE_NUMBER_RE.fullmatch(line) and line.casefold() not in repeated
        ]
        for lines in page_lines
    ]


def paragraphs_from_pdf_pages(pages: list[str]) -> list[tuple[str, bool]]:
    """Absätze aus Seiten; Satzende oder Leerzeile beendet einen Absatz."""
    cleaned_pages = remove_repeating_margins(pages)
    raw = "\n\f\n".join("\n".join(lines) for lines in cleaned_pages)
    raw = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", raw)
    paragraphs: list[tuple[str, bool]] = []
    buffer: list[str] = []

    def flush() -> None:
        if not buffer:
            return
        text = re.sub(r"\s+", " ", " ".join(buffer)).strip()
        if text:
            paragraphs.append((text, bool(HEADING_RE.match(text) and len(text) < 160)))
        buffer.clear()

    for raw_line in raw.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line or line == "\f":
            flush()
            continue
        heading = bool(HEADING_RE.match(line) and len(line) < 160)
        if heading:
            flush()
            paragraphs.append((line, True))
            continue
        buffer.append(line)
        if re.search(r"[.!?;:»”\"]$", line):
            flush()
    flush()
    return paragraphs


def text_items_from_paragraphs(paragraphs: list[tuple[str, bool]]) -> list[CompareItem]:
    """Fließtext-Einheiten; Überschriften gliedern und werden nicht verglichen."""
    items: list[CompareItem] = []
    heading = "Ohne Gliederung"
    paragraph_number = 0
    for source_index, (text, is_heading) in enumerate(paragraphs):
        if not text:
            continue
        if is_heading:
            heading = text[:240]
            paragraph_number = 0
            continue
        paragraph_number += 1
        items.append(
            CompareItem(
                source_id=str(source_index),
                section=heading,
                text=text,
                location=f"{heading}, Absatz {paragraph_number}",
                kind="text",
                order=len(items),
            )
        )
    return items


def pdf_paragraphs(
    path: Path,
    *,
    page_source: PageSource | None = None,
    ocr_callback: OcrCallback | None = None,
    limits: ReadLimits = DEFAULT_LIMITS,
) -> list[tuple[str, bool]]:
    """Absätze eines PDF; ohne Textebene nur mit ausdrücklichem OCR-Rückruf."""
    if path.stat().st_size > limits.max_file_bytes:
        raise LimitExceededError(
            f"{path.name} ist größer als die zulässigen {limits.max_file_bytes} Bytes."
        )
    source = page_source or (lambda p: legacy_pdf_pages(p, timeout=limits.pdftotext_timeout))
    pages = source(path)
    if len(pages) > limits.max_pdf_pages:
        raise LimitExceededError(f"{path.name} hat mehr als {limits.max_pdf_pages} Seiten.")
    text_length = sum(len(page.strip()) for page in pages)
    if text_length < 20:
        if ocr_callback is None:
            raise ParseError(
                f"{path.name} enthält keine nutzbare Textebene. Bitte OCR vorschalten."
            )
        ocr_text = ocr_callback(path)
        if len((ocr_text or "").strip()) < 20:
            raise ParseError(
                f"Die OCR von {path.name} hat keinen ausreichend lesbaren Text geliefert."
            )
        pages = [ocr_text]
    return paragraphs_from_pdf_pages(pages)
