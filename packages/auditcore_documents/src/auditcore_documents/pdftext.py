"""PDF-Text: austauschbare Seitenquelle und reine Absatzbildung.

Die Absatzbildung (Seitenränder, Silbentrennung, Überschriften) ist reine
Textverarbeitung. Silbentrennung und Überschriften entsprechen dem Original;
Seitenränder werden ab 0.6.0 nur noch im Randbereich und ohne Verlust des
ersten Vorkommens entfernt (``MarginRules``; Original: ``LEGACY_MARGINS``). Die Seitenquelle
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
from dataclasses import dataclass
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


@dataclass(frozen=True)
class MarginRules:
    """Regeln für das Entfernen von Seitenzahlen und Kopf-/Fußzeilen.

    ``edge_lines`` ist die Zahl der ersten und letzten nichtleeren Zeilen je
    Seite, die als Rand gelten. ``edge_only`` beschränkt das Entfernen auf
    diesen Rand; Zeilen außerhalb bleiben stets erhalten (eine reine Zahl
    mitten in einer Tabelle ist Inhalt). ``keep_first_occurrence`` behält das
    erste Vorkommen einer wiederkehrenden Randzeile im Dokument (etwa einen
    Stichtag im Seitenkopf). Seitenzahlen am Rand fallen immer weg.
    """

    edge_lines: int = 3
    edge_only: bool = True
    keep_first_occurrence: bool = True

    def __post_init__(self) -> None:
        if isinstance(self.edge_lines, bool) or not isinstance(self.edge_lines, int):
            raise TypeError("edge_lines muss eine ganze Zahl sein.")
        if self.edge_lines < 0:
            raise ValueError("edge_lines darf nicht negativ sein.")


#: Standard ab 0.6.0: nur der Rand, erstes Vorkommen bleibt; kein Inhaltsverlust.
DEFAULT_MARGINS = MarginRules()
#: Originalverhalten (Profile ``LEGACY``/``LEGACY_DIFFLIB``): Seitenzahlen und
#: wiederkehrende Randzeilen werden auf der ganzen Seite und bei jedem
#: Vorkommen entfernt.
LEGACY_MARGINS = MarginRules(edge_only=False, keep_first_occurrence=False)


def _edge_indexes(lines: list[str], count: int) -> list[int]:
    """Indizes der ersten und letzten ``count`` nichtleeren Zeilen (Reihenfolge der Seite)."""
    nonempty = [index for index, line in enumerate(lines) if line]
    if count == 0:
        return []
    return sorted({*nonempty[:count], *nonempty[-count:]})


def _repeated_edge_lines(page_lines: list[list[str]], count: int) -> set[str]:
    """Randzeilen (casefold), die auf mindestens der Hälfte der Seiten wiederkehren."""
    if len(page_lines) < 2:
        return set()
    edge_counts: Counter[str] = Counter()
    for lines in page_lines:
        edge = {lines[index].casefold() for index in _edge_indexes(lines, count)}
        edge_counts.update(line for line in edge if not PAGE_NUMBER_RE.fullmatch(line))
    threshold = max(2, (len(page_lines) + 1) // 2)
    return {value for value, seen in edge_counts.items() if seen >= threshold}


def _clean_page(
    lines: list[str], repeated: set[str], kept: set[str], rules: MarginRules
) -> list[str]:
    """Eine Seite bereinigen; ``kept`` merkt sich bereits behaltene Randzeilen."""
    candidates = (
        set(_edge_indexes(lines, rules.edge_lines)) if rules.edge_only else set(range(len(lines)))
    )
    result: list[str] = []
    for index, line in enumerate(lines):
        if index in candidates and _drop(line, repeated, kept, rules):
            continue
        result.append(line)
    return result


def _drop(line: str, repeated: set[str], kept: set[str], rules: MarginRules) -> bool:
    if PAGE_NUMBER_RE.fullmatch(line):
        return True
    key = line.casefold()
    if key not in repeated:
        return False
    if rules.keep_first_occurrence and key not in kept:
        kept.add(key)
        return False
    return True


def remove_repeating_margins(
    pages: list[str], rules: MarginRules = DEFAULT_MARGINS
) -> list[list[str]]:
    """Seitenzahlen und wiederkehrende Kopf-/Fußzeilen am Seitenrand entfernen.

    Wiederkehrend ist eine Randzeile, die auf mindestens der Hälfte der Seiten
    (mindestens zwei) im Rand steht. Mit :data:`DEFAULT_MARGINS` bleiben
    Zeilen außerhalb des Randes und das erste Vorkommen einer wiederkehrenden
    Randzeile erhalten; :data:`LEGACY_MARGINS` bildet das Original ab.
    """
    page_lines = [
        [re.sub(r"\s+", " ", line).strip() for line in page.splitlines()] for page in pages
    ]
    repeated = _repeated_edge_lines(page_lines, rules.edge_lines)
    kept: set[str] = set()
    return [_clean_page(lines, repeated, kept, rules) for lines in page_lines]


def paragraphs_from_pdf_pages(
    pages: list[str], *, margins: MarginRules = DEFAULT_MARGINS
) -> list[tuple[str, bool]]:
    """Absätze aus Seiten; Satzende oder Leerzeile beendet einen Absatz.

    ``margins`` steuert das Entfernen der Seitenränder (:func:`remove_repeating_margins`).
    """
    cleaned_pages = remove_repeating_margins(pages, margins)
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
    margins: MarginRules = DEFAULT_MARGINS,
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
    return paragraphs_from_pdf_pages(pages, margins=margins)
