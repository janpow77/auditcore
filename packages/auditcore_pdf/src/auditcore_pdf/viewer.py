"""Anzeige-, Lese- und Analysefunktionen für PDF-Dokumente."""

from __future__ import annotations

from auditcore_pdf.engine import make_matrix, open_pdf
from auditcore_pdf.models import DocumentInfo, PageInfo


def get_document_info(pdf_bytes: bytes) -> DocumentInfo:
    """Ermittelt Struktur- und Metadaten eines PDF-Dokuments."""
    doc = open_pdf(pdf_bytes)
    try:
        page_count = int(doc.page_count)
        metadata = {str(k): str(v) for k, v in (doc.metadata or {}).items() if v}
        is_encrypted = bool(doc.is_encrypted)
        attachments = list(doc.embfile_names())
        has_signatures = False

        pages: list[PageInfo] = []
        scanned_page_numbers: list[int] = []

        for idx in range(page_count):
            pno = idx + 1
            page = doc[idx]
            rect = page.rect
            text = page.get_text("text").strip()
            images = page.get_images()
            image_count = len(images)
            has_text = len(text) > 0
            is_scanned = (not has_text) and (image_count > 0)
            if is_scanned:
                scanned_page_numbers.append(pno)

            pages.append(
                PageInfo(
                    page_number=pno,
                    width=float(rect.width),
                    height=float(rect.height),
                    rotation=int(page.rotation),
                    has_text=has_text,
                    image_count=image_count,
                    is_scanned=is_scanned,
                )
            )

        return DocumentInfo(
            page_count=page_count,
            metadata=metadata,
            is_encrypted=is_encrypted,
            pages=pages,
            attachments=attachments,
            has_signatures=has_signatures,
            scanned_page_numbers=scanned_page_numbers,
        )
    finally:
        doc.close()


def render_page(
    pdf_bytes: bytes,
    page_number: int = 1,
    dpi: int = 150,
    image_format: str = "png",
) -> bytes:
    """Rendert eine einzelne PDF-Seite als Rasterbild."""
    doc = open_pdf(pdf_bytes)
    try:
        if page_number < 1 or page_number > doc.page_count:
            raise IndexError(
                f"Ungültige Seitennummer {page_number}. Dokument hat {doc.page_count} Seiten."
            )
        page = doc[page_number - 1]
        zoom = dpi / 72.0
        mat = make_matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        return bytes(pix.tobytes(image_format))
    finally:
        doc.close()


def extract_page_text(pdf_bytes: bytes, page_number: int = 1) -> str:
    """Extrahiert den Klartext einer einzelnen Seite."""
    doc = open_pdf(pdf_bytes)
    try:
        if page_number < 1 or page_number > doc.page_count:
            raise IndexError(
                f"Ungültige Seitennummer {page_number}. Dokument hat {doc.page_count} Seiten."
            )
        page = doc[page_number - 1]
        text: str = str(page.get_text("text"))
        return text
    finally:
        doc.close()


def extract_all_text(pdf_bytes: bytes) -> str:
    """Extrahiert den gesamten Text aller Seiten eines Dokuments."""
    doc = open_pdf(pdf_bytes)
    try:
        parts: list[str] = []
        for idx in range(doc.page_count):
            parts.append(str(doc[idx].get_text("text")))
        return "\n".join(parts)
    finally:
        doc.close()


def get_toc(pdf_bytes: bytes) -> list[tuple[int, str, int]]:
    """Liest das Inhaltsverzeichnis (Lesezeichen) des Dokuments aus."""
    doc = open_pdf(pdf_bytes)
    try:
        raw_toc = doc.get_toc()
        return [(int(lvl), str(title), int(pno)) for lvl, title, pno in raw_toc]
    finally:
        doc.close()
