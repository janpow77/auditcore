"""Tests für Seiten- und Dokumentenoperationen."""

from __future__ import annotations

import pytest

from auditcore_pdf import (
    delete_pages,
    extract_page_text,
    extract_pages,
    get_document_info,
    merge_documents,
    reorder_pages,
    rotate_pages,
    split_document,
)


def test_reorder_pages(sample_pdf: bytes) -> None:
    reordered = reorder_pages(sample_pdf, [3, 1, 2])
    info = get_document_info(reordered)
    assert info.page_count == 3
    assert "Seite 3 Inhalt" in extract_page_text(reordered, 1)
    assert "Seite 1 Inhalt" in extract_page_text(reordered, 2)
    assert "Seite 2 Inhalt" in extract_page_text(reordered, 3)


def test_rotate_pages(sample_pdf: bytes) -> None:
    rotated = rotate_pages(sample_pdf, {1: 90, 2: 180})
    info = get_document_info(rotated)
    assert info.pages[0].rotation == 90
    assert info.pages[1].rotation == 180
    assert info.pages[2].rotation == 0


def test_delete_pages(sample_pdf: bytes) -> None:
    reduced = delete_pages(sample_pdf, [2])
    info = get_document_info(reduced)
    assert info.page_count == 2
    assert "Seite 1 Inhalt" in extract_page_text(reduced, 1)
    assert "Seite 3 Inhalt" in extract_page_text(reduced, 2)

    with pytest.raises(ValueError):
        delete_pages(sample_pdf, [1, 2, 3])


def test_extract_pages(sample_pdf: bytes) -> None:
    extracted = extract_pages(sample_pdf, [2])
    info = get_document_info(extracted)
    assert info.page_count == 1
    assert "Seite 2 Inhalt" in extract_page_text(extracted, 1)


def test_merge_documents(sample_pdf: bytes) -> None:
    merged = merge_documents([sample_pdf, sample_pdf])
    info = get_document_info(merged)
    assert info.page_count == 6


def test_split_document(sample_pdf: bytes) -> None:
    chunks = split_document(sample_pdf, chunk_size=2)
    assert len(chunks) == 2
    assert get_document_info(chunks[0]).page_count == 2
    assert get_document_info(chunks[1]).page_count == 1
