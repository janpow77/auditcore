"""Tests für Anzeige-, Extraktions- und Dokumentanalyse-Funktionen."""

from __future__ import annotations

import pytest

from auditcore_pdf import (
    extract_all_text,
    extract_page_text,
    get_document_info,
    get_toc,
    render_page,
)


def test_get_document_info(sample_pdf: bytes) -> None:
    info = get_document_info(sample_pdf)
    assert info.page_count == 3
    assert not info.is_encrypted
    assert info.metadata.get("title") == "Prüfbericht 2026"
    assert len(info.pages) == 3
    assert info.pages[0].has_text is True
    assert info.pages[0].width == pytest.approx(595, rel=1e-2)
    assert info.pages[0].height == pytest.approx(842, rel=1e-2)
    assert len(info.scanned_page_numbers) == 0


def test_extract_page_text(sample_pdf: bytes) -> None:
    text_p1 = extract_page_text(sample_pdf, 1)
    assert "Seite 1 Inhalt" in text_p1
    assert "Prüfbericht" in text_p1

    text_p2 = extract_page_text(sample_pdf, 2)
    assert "Seite 2 Inhalt" in text_p2

    with pytest.raises(IndexError):
        extract_page_text(sample_pdf, 99)


def test_extract_all_text(sample_pdf: bytes) -> None:
    full_text = extract_all_text(sample_pdf)
    assert "Seite 1 Inhalt" in full_text
    assert "Seite 2 Inhalt" in full_text
    assert "Seite 3 Inhalt" in full_text


def test_render_page_returns_png_bytes(sample_pdf: bytes) -> None:
    img_bytes = render_page(sample_pdf, 1, dpi=72, image_format="png")
    assert isinstance(img_bytes, bytes)
    assert len(img_bytes) > 100
    # PNG-Magic Bytes
    assert img_bytes.startswith(b"\x89PNG")


def test_get_toc(sample_pdf: bytes) -> None:
    toc = get_toc(sample_pdf)
    assert len(toc) == 3
    assert toc[0] == (1, "Abschnitt 1", 1)
    assert toc[1] == (1, "Abschnitt 2", 2)
    assert toc[2] == (1, "Abschnitt 3", 3)


def test_scanned_pdf_detection(scanned_pdf: bytes) -> None:
    info = get_document_info(scanned_pdf)
    assert info.page_count == 1
    assert info.pages[0].is_scanned is True
    assert info.pages[0].has_text is False
    assert info.pages[0].image_count >= 1
    assert 1 in info.scanned_page_numbers
