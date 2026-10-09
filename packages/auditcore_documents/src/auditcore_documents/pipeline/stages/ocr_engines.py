"""Eingebaute OCR-Bausteine: parametrisierter Rasterer und Tesseract als Subprozess.

``pdfium_rasterizer_for`` liefert einen ``Rasterizer`` mit wählbarer Auflösung
und Seitengrenze (Vorgaben wie ``pdfium_rasterizer``: 200 dpi, 50 Seiten).

``TesseractCli`` erfüllt ``TesseractPort`` über das Programm ``tesseract``
(Tesseract ≥ 4, z. B. Debian-Paket ``tesseract-ocr`` mit ``tesseract-ocr-deu``).
Es braucht kein Python-Paket: Bilder gehen über die Standardeingabe an den
Prozess, PDF wird vorher gerastert (Extra ``ocr-raster``). Die Bibliothek
bleibt damit frei von OCR-Modellen; ein eigener ``TesseractPort`` (etwa ein
Dienst im Netz) ist weiterhin möglich.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from auditcore_documents.pipeline.stages.ocr_results import (
    MAX_OCR_PAGES,
    OCR_RENDER_DPI,
    ParsedDocument,
    ParsedPage,
    Rasterizer,
    looks_like_pdf,
    pdfium_rasterizer,
    render_pdf_pages,
)

#: Zulässige Rasterauflösung (wie ``OcrSettings.pdf_dpi``).
DPI_RANGE = (72, 600)
#: Zulässige Seitengrenze (wie ``OcrSettings.max_pages``).
MAX_PAGES_RANGE = (1, 500)

#: Fehlertext der OCR-Stufe ohne Tesseract-Port; nennt den eingebauten Anschluss.
TESSERACT_MISSING = (
    "No Tesseract engine configured – OcrStage(tesseract=TesseractCli()) nutzt das "
    "Programm tesseract (PDF mit Extra ocr-raster), alternativ ein eigener TesseractPort"
)

#: Führt ``tesseract`` aus: (Argumente, Eingabebytes, Zeitlimit) → Standardausgabe.
TesseractRunner = Callable[[list[str], bytes, float], str]


def _check_int(name: str, value: int, bounds: tuple[int, int]) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} muss eine ganze Zahl sein.")
    low, high = bounds
    if not low <= value <= high:
        raise ValueError(f"{name} muss zwischen {low} und {high} liegen.")


def pdfium_rasterizer_for(
    *, dpi: int = OCR_RENDER_DPI, max_pages: int = MAX_OCR_PAGES
) -> Rasterizer:
    """``Rasterizer`` mit eigener Auflösung (72–600 dpi) und Seitengrenze (1–500)."""
    _check_int("dpi", dpi, DPI_RANGE)
    _check_int("max_pages", max_pages, MAX_PAGES_RANGE)
    if dpi == OCR_RENDER_DPI and max_pages == MAX_OCR_PAGES:
        return pdfium_rasterizer

    def rasterize(data: bytes) -> list[tuple[int, bytes]] | None:
        return render_pdf_pages(data, dpi=dpi, max_pages=max_pages)

    return rasterize


def run_tesseract(args: list[str], data: bytes, timeout: float) -> str:
    """``tesseract`` als externer Prozess ohne Shell; Ausgabe als UTF-8."""
    completed = subprocess.run(  # noqa: S603 - festes Programm, keine Shell
        args, input=data, check=True, capture_output=True, timeout=timeout
    )
    return completed.stdout.decode("utf-8")


def _confidence(value: str) -> float | None:
    try:
        number = float(value)
    except ValueError:
        return None
    return number / 100.0 if number >= 0 else None


def page_from_tsv(tsv: str) -> ParsedPage:
    """Seite aus der TSV-Ausgabe: Wörter je Zeile, Konfidenz als Mittel der Wörter (0–1)."""
    lines: dict[tuple[str, ...], list[str]] = {}
    confidences: list[float] = []
    for row in tsv.splitlines()[1:]:
        cells = row.split("\t")
        if len(cells) < 12 or cells[0] != "5" or not cells[11].strip():
            continue
        lines.setdefault(tuple(cells[1:5]), []).append(cells[11].strip())
        confidence = _confidence(cells[10])
        if confidence is not None:
            confidences.append(confidence)
    text = "\n".join(" ".join(words) for words in lines.values())
    average = sum(confidences) / len(confidences) if confidences else None
    return ParsedPage(text=text, confidence=average)


@dataclass
class TesseractCli:
    """``TesseractPort`` über das Programm ``tesseract`` (Subprozess, keine Shell).

    ``languages``, ``psm`` und ``oem`` entsprechen ``OcrSettings``; ``rasterizer``
    bestimmt Auflösung und Seitengrenze für PDF. ``runner`` ist für Tests
    austauschbar. Fehlt das Programm, endet ``parse`` mit ``FileNotFoundError``
    (die OCR-Stufe meldet ``TESSERACT_OCR_FAILED``).
    """

    executable: str = "tesseract"
    languages: str = "deu+eng"
    psm: int = 3
    oem: int = 3
    timeout: float = 120.0
    rasterizer: Rasterizer | None = pdfium_rasterizer
    runner: TesseractRunner = run_tesseract

    def _arguments(self) -> list[str]:
        return [
            self.executable,
            "stdin",
            "stdout",
            "-l",
            self.languages,
            "--psm",
            str(self.psm),
            "--oem",
            str(self.oem),
            "tsv",
        ]

    def _images(self, data: bytes) -> list[bytes]:
        if not looks_like_pdf(data):
            return [data]
        pages = self.rasterizer(data) if self.rasterizer is not None else None
        if not pages:
            raise RuntimeError(
                "PDF konnte für Tesseract nicht gerastert werden "
                "(Extra ocr-raster installieren oder einen Rasterizer übergeben)."
            )
        return [image for _number, image in pages]

    def parse(self, path: Path) -> ParsedDocument:
        """Bild oder PDF erkennen; Text je Seite und Gesamttext mit Leerzeile dazwischen."""
        arguments = self._arguments()
        pages = [
            page_from_tsv(self.runner(arguments, image, self.timeout))
            for image in self._images(path.read_bytes())
        ]
        raw_text = "\n\n".join(page.text for page in pages)
        return ParsedDocument(raw_text=raw_text, pages=pages)


def resolve_rasterizer(
    rasterizer: Rasterizer | None, *, dpi: int, max_pages: int
) -> Rasterizer | None:
    """Rasterer der OCR-Stufe: ``dpi``/``max_pages`` gelten für den eingebauten pdfium-Rasterer.

    Ein eigener Rasterer bestimmt seine Parameter selbst; abweichende Werte
    wären dort wirkungslos und führen deshalb zu ``ValueError``.
    """
    if rasterizer is pdfium_rasterizer:
        return pdfium_rasterizer_for(dpi=dpi, max_pages=max_pages)
    if (dpi, max_pages) != (OCR_RENDER_DPI, MAX_OCR_PAGES):
        raise ValueError(
            "raster_dpi und raster_max_pages gelten nur für den eingebauten "
            "pdfium_rasterizer; ein eigener Rasterizer erhält sie selbst."
        )
    return rasterizer
