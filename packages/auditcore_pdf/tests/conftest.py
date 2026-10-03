"""Test-Fixtures zur Erzeugung synthetischer PDF-Dokumente im Arbeitsspeicher."""

from __future__ import annotations

import pymupdf as fitz
import pytest


@pytest.fixture
def sample_pdf() -> bytes:
    """Erzeugt ein einfaches dreiseitiges PDF-Dokument mit Text und Lesezeichen."""
    doc = fitz.open()
    for i in range(1, 4):
        page = doc.new_page(width=595, height=842)
        page.insert_text(fitz.Point(72, 100), f"Seite {i} Inhalt.\nDies ist ein Prüfbericht.")
    doc.set_toc(
        [
            [1, "Abschnitt 1", 1],
            [1, "Abschnitt 2", 2],
            [1, "Abschnitt 3", 3],
        ]
    )
    doc.set_metadata(
        {
            "title": "Prüfbericht 2026",
            "author": "Prüfbehörde Hessen",
            "subject": "Systemprüfung",
        }
    )
    pdf_bytes = doc.tobytes()
    doc.close()
    return bytes(pdf_bytes)


@pytest.fixture
def sensitive_pdf() -> bytes:
    """Erzeugt ein PDF mit vertraulichen Daten in Text, Metadaten, Anmerkungen und Anhängen."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text(fitz.Point(72, 100), "Öffentlicher Kontext vor dem Geheimnis.")
    page.insert_text(fitz.Point(72, 130), "STRENG_GEHEIM ist das vertrauliche Kennwort.")
    page.insert_text(fitz.Point(72, 160), "Kontakt: pruefer@flowaudit.de")
    page.insert_text(fitz.Point(72, 175), "IBAN DE02120300000123456789.")
    page.insert_text(fitz.Point(72, 190), "Öffentlicher Kontext nach dem Geheimnis.")

    # Mehrzeilige Phrase
    page.insert_text(fitz.Point(72, 240), "Dies ist ein vertraulicher")
    page.insert_text(fitz.Point(72, 260), "Aktenvorgang zur Prüfung.")

    # Fallunterscheidung Groß/Klein
    page.insert_text(fitz.Point(72, 300), "WORT_GROSS und wort_klein stehen hier.")

    # Anmerkung (Kommentar)
    annot = page.add_text_annot(fitz.Point(72, 350), "Kommentar mit STRENG_GEHEIM Notiz.")
    annot.set_info(content="Kommentar mit STRENG_GEHEIM Notiz.", title="Prüfer")

    # Metadaten mit Geheimnis
    doc.set_metadata(
        {
            "title": "Bericht mit STRENG_GEHEIM im Titel",
            "author": "Max Mustermann",
        }
    )

    # Anhang mit Geheimnis
    doc.embfile_add(
        "geheimnis.txt",
        b"Inhalt enthaelt STRENG_GEHEIM Daten",
        filename="geheimnis.txt",
    )

    pdf_bytes = doc.tobytes()
    doc.close()
    return bytes(pdf_bytes)


@pytest.fixture
def scanned_pdf() -> bytes:
    """Erzeugt ein PDF ohne Textebene (simulierter Scan mit Rasterbild)."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    # Erzeuge ein winziges 10x10 Bild
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 10, 10), 0)
    pix.clear_with(200)
    page.insert_image(fitz.Rect(50, 50, 200, 200), pixmap=pix)
    pdf_bytes = doc.tobytes()
    doc.close()
    return bytes(pdf_bytes)
