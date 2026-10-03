"""Tests für den Engine-Zugriffspunkt: Rückfälle beim Import, Pflichtprüfung und Grenzwerte."""

from __future__ import annotations

import importlib
import sys
from collections.abc import Iterator
from contextlib import contextmanager

import pymupdf
import pytest

from auditcore_pdf import engine, merge_documents
from auditcore_pdf.engine import (
    MAX_PAGES,
    is_pymupdf_available,
    make_matrix,
    make_rect,
    new_pdf,
    open_pdf,
)


@contextmanager
def _engine_reloaded(pymupdf_mod: object, fitz_mod: object) -> Iterator[None]:
    """Lädt ``engine`` mit präparierten Modulen neu und stellt danach den Ursprung wieder her.

    ``None`` in ``sys.modules`` lässt den jeweiligen Import mit ``ImportError`` scheitern.
    Die übrigen Module des Pakets greifen über die Modulglobalen von ``engine`` zu und
    sehen deshalb während des Blocks den neu geladenen Zustand.
    """
    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "pymupdf", pymupdf_mod)
        mp.setitem(sys.modules, "fitz", fitz_mod)
        try:
            importlib.reload(engine)
            yield
        finally:
            mp.undo()
            importlib.reload(engine)


def test_engine_available_with_pymupdf() -> None:
    assert is_pymupdf_available() is True
    assert engine.fitz is pymupdf


def test_engine_falls_back_to_fitz_module() -> None:
    """Ohne Modul ``pymupdf`` wird der ältere Importname ``fitz`` verwendet."""
    with _engine_reloaded(None, pymupdf):
        assert engine.is_pymupdf_available() is True
        assert engine.fitz is pymupdf
        doc = engine.new_pdf()
        try:
            assert doc.page_count == 0
        finally:
            doc.close()
    # Nach dem Block ist wieder die maßgebliche Engine aktiv
    assert engine.fitz is pymupdf
    assert engine.is_pymupdf_available() is True


def test_engine_without_pymupdf_reports_missing_extra() -> None:
    """Fehlt PyMuPDF ganz, bleibt der Import möglich, jede PDF-Funktion meldet das Extra."""
    with _engine_reloaded(None, None):
        assert engine.is_pymupdf_available() is False
        # Platzhaltermodul statt Importfehler
        assert engine.fitz.__name__ == "fitz"
        assert not hasattr(engine.fitz, "open")

        calls = (
            engine.new_pdf,
            lambda: engine.make_rect(0, 0, 10, 10),
            lambda: engine.make_matrix(1, 1),
            lambda: engine.open_pdf(b"%PDF-1.7"),
            # Höhere Operationen nutzen dieselbe Pflichtprüfung
            lambda: merge_documents([b"%PDF-1.7"]),
        )
        for call in calls:
            with pytest.raises(RuntimeError, match=r"auditcore_pdf\[pymupdf\]"):
                call()
    assert engine.is_pymupdf_available() is True


def test_new_pdf_is_empty() -> None:
    doc = new_pdf()
    try:
        assert doc.page_count == 0
    finally:
        doc.close()


def test_make_rect_and_matrix() -> None:
    rect = make_rect(10, 20, 110, 70)
    assert (rect.width, rect.height) == (100, 50)
    matrix = make_matrix(2, 3)
    assert (matrix.a, matrix.d) == (2, 3)


def test_open_pdf_rejects_empty_content() -> None:
    with pytest.raises(ValueError, match="darf nicht leer sein"):
        open_pdf(b"")


def test_open_pdf_returns_document(sample_pdf: bytes) -> None:
    doc = open_pdf(sample_pdf)
    try:
        assert doc.page_count == 3
    finally:
        doc.close()


def test_open_pdf_enforces_page_limit(sample_pdf: bytes, monkeypatch: pytest.MonkeyPatch) -> None:
    """Dokumente oberhalb von MAX_PAGES werden abgewiesen, die Meldung nennt beide Zahlen."""
    assert MAX_PAGES == 5000
    monkeypatch.setattr(engine, "MAX_PAGES", 2)
    with pytest.raises(ValueError, match="3 Seiten – zulässig sind höchstens 2 Seiten"):
        open_pdf(sample_pdf)
    # An der Grenze selbst wird noch geöffnet
    monkeypatch.setattr(engine, "MAX_PAGES", 3)
    doc = open_pdf(sample_pdf)
    doc.close()
