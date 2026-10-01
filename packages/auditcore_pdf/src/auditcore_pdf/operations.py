"""Seiten- und Dokumentenoperationen für PDF-Dateien."""

from __future__ import annotations

import pymupdf as fitz

from auditcore_pdf.engine import open_pdf


def reorder_pages(pdf_bytes: bytes, page_order: list[int]) -> bytes:
    """Sortiert die Seiten eines Dokuments nach einer 1-basierten Reihenfolge um."""
    if not page_order:
        raise ValueError("Seitenreihenfolge darf nicht leer sein.")
    doc = open_pdf(pdf_bytes)
    try:
        count = doc.page_count
        zero_based: list[int] = []
        for p in page_order:
            if p < 1 or p > count:
                raise IndexError(
                    f"Ungültige Seitennummer {p}. Dokument hat {count} Seiten."
                )
            zero_based.append(p - 1)
        doc.select(zero_based)
        out: bytes = doc.tobytes(garbage=3, deflate=True)
        return out
    finally:
        doc.close()


def rotate_pages(pdf_bytes: bytes, rotations: dict[int, int]) -> bytes:
    """Dreht ausgewählte Seiten (1-basierte Seitennummern auf Gradzahl, z. B. 90, 180, 270)."""
    doc = open_pdf(pdf_bytes)
    try:
        count = doc.page_count
        for page_num, angle in rotations.items():
            if page_num < 1 or page_num > count:
                raise IndexError(
                    f"Ungültige Seitennummer {page_num}. Dokument hat {count} Seiten."
                )
            page = doc[page_num - 1]
            page.set_rotation((page.rotation + angle) % 360)
        out: bytes = doc.tobytes(garbage=3, deflate=True)
        return out
    finally:
        doc.close()


def delete_pages(pdf_bytes: bytes, pages_to_delete: list[int] | set[int]) -> bytes:
    """Löscht die angegebenen 1-basierten Seitennummern aus dem Dokument."""
    doc = open_pdf(pdf_bytes)
    try:
        count = doc.page_count
        del_set = set(pages_to_delete)
        if len(del_set) >= count:
            raise ValueError("Es können nicht alle Seiten eines Dokuments gelöscht werden.")
        keep_zero_based: list[int] = []
        for idx in range(count):
            pno = idx + 1
            if pno not in del_set:
                keep_zero_based.append(idx)
        doc.select(keep_zero_based)
        out: bytes = doc.tobytes(garbage=3, deflate=True)
        return out
    finally:
        doc.close()


def extract_pages(pdf_bytes: bytes, pages_to_extract: list[int]) -> bytes:
    """Extrahiert ausgewählte 1-basierte Seiten in ein neues PDF-Dokument."""
    if not pages_to_extract:
        raise ValueError("Liste der zu extrahierenden Seiten darf nicht leer sein.")
    doc = open_pdf(pdf_bytes)
    try:
        count = doc.page_count
        zero_based: list[int] = []
        for p in pages_to_extract:
            if p < 1 or p > count:
                raise IndexError(
                    f"Ungültige Seitennummer {p}. Dokument hat {count} Seiten."
                )
            zero_based.append(p - 1)
        doc.select(zero_based)
        out: bytes = doc.tobytes(garbage=3, deflate=True)
        return out
    finally:
        doc.close()


def merge_documents(documents: list[bytes]) -> bytes:
    """Führt mehrere PDF-Dokumente nahtlos zu einer gemeinsamen PDF zusammen."""
    if not documents:
        raise ValueError("Dokumentenliste darf nicht leer sein.")
    merged = fitz.open()
    try:
        for doc_bytes in documents:
            sub_doc = open_pdf(doc_bytes)
            try:
                merged.insert_pdf(sub_doc)
            finally:
                sub_doc.close()
        out: bytes = merged.tobytes(garbage=3, deflate=True)
        return out
    finally:
        merged.close()


def split_document(pdf_bytes: bytes, chunk_size: int = 1) -> list[bytes]:
    """Teilt ein Dokument in Abschnitte von jeweils höchstens chunk_size Seiten auf."""
    if chunk_size < 1:
        raise ValueError(f"chunk_size muss mindestens 1 sein, erhalten: {chunk_size}")
    doc = open_pdf(pdf_bytes)
    try:
        count = doc.page_count
        chunks: list[bytes] = []
        for start in range(0, count, chunk_size):
            end = min(start + chunk_size, count)
            chunk_doc = fitz.open()
            try:
                chunk_doc.insert_pdf(doc, from_page=start, to_page=end - 1)
                chunks.append(bytes(chunk_doc.tobytes(garbage=3, deflate=True)))
            finally:
                chunk_doc.close()
        return chunks
    finally:
        doc.close()
