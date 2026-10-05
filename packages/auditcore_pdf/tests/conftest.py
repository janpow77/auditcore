"""Test-Fixtures zur Erzeugung synthetischer PDF-Dokumente im Arbeitsspeicher."""

from __future__ import annotations

from collections.abc import Callable

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


def _add_structure_leaks(doc: fitz.Document, page: fitz.Page) -> None:
    """Hinterlegt LECK-Begriffe in Formular, Verknüpfung, Zielen, Skripten und Alt-Texten."""
    widget = fitz.Widget()
    widget.field_type = fitz.PDF_WIDGET_TYPE_TEXT
    widget.field_name = "feld_LECK_NAME"
    widget.field_value = "LECK_FORM"
    widget.rect = fitz.Rect(72, 400, 300, 420)
    page.add_widget(widget)
    page.insert_link(
        {"kind": fitz.LINK_URI, "from": fitz.Rect(72, 450, 200, 470), "uri": "mailto:LECK@x.de"}
    )
    doc.set_page_labels([{"startpage": 0, "prefix": "LECK_LABEL-", "style": "D"}])
    catalog = doc.pdf_catalog()
    dests, scripts = doc.get_new_xref(), doc.get_new_xref()
    doc.update_object(dests, f"<< /Names [(LECK_DEST) [{page.xref} 0 R /Fit]] >>")
    doc.update_object(scripts, "<< /Names [(s) << /S /JavaScript /JS (LECK_JS_NAME) >>] >>")
    doc.xref_set_key(catalog, "Names", f"<< /Dests {dests} 0 R /JavaScript {scripts} 0 R >>")
    doc.xref_set_key(catalog, "OpenAction", "<< /S /JavaScript /JS (app.alert\\('LECK_JS'\\)) >>")
    figure, root = doc.get_new_xref(), doc.get_new_xref()
    alt_hex = "<FEFF" + "LECK_ALT".encode("utf-16-be").hex() + ">"
    doc.update_object(figure, f"<< /Type /StructElem /S /Figure /P {root} 0 R /Alt {alt_hex} >>")
    doc.update_object(root, f"<< /Type /StructTreeRoot /K [{figure} 0 R] >>")
    doc.xref_set_key(catalog, "StructTreeRoot", f"{root} 0 R")
    doc.add_ocg("Ebene LECK_OCG", on=True)
    content = page.get_contents()[0]
    marked = b"/Span <</ActualText (Neutral)>> BDC\n" + doc.xref_stream(content) + b"\nEMC\n"
    doc.update_stream(content, marked)


@pytest.fixture
def structure_pdf() -> bytes:
    """PDF mit dem Begriff LECK ausschließlich außerhalb des sichtbaren Seitentexts.

    Der Seitentext „LECK_GLYPHE“ ist durch ActualText „Neutral“ überdeckt.
    """
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text(fitz.Point(72, 100), "LECK_GLYPHE")
    doc.set_toc([[1, "Kapitel LECK_TOC", 1], [2, "Unterkapitel neutral", 1]])
    _add_structure_leaks(doc, page)
    pdf_bytes = bytes(doc.tobytes())
    doc.close()
    return pdf_bytes


@pytest.fixture
def layered_pdf() -> bytes:
    """PDF mit Text auf einer ausgeblendeten und einer sichtbaren Ebene."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    hidden = doc.add_ocg("Ausgeblendet", on=False)
    visible = doc.add_ocg("Sichtbar", on=True)
    page.insert_text(fitz.Point(72, 100), "Sichtbarer Grundtext.")
    page.insert_text(fitz.Point(72, 140), "Versteckt GEHEIM_EBENE hier", oc=hidden)
    page.insert_text(fitz.Point(72, 180), "Zweite Ebene neutral", oc=visible)
    pdf_bytes = bytes(doc.tobytes())
    doc.close()
    return pdf_bytes


def _make_image_page_pdf(image_rect: tuple[float, float, float, float], text: bool = True) -> bytes:
    """Seite mit Text oben links und einem Bild an der angegebenen Stelle."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    if text:
        page.insert_text(fitz.Point(72, 100), "Neutraler Begleittext.")
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 10, 10), 0)
    pix.clear_with(200)
    page.insert_image(fitz.Rect(*image_rect), pixmap=pix)
    pdf_bytes = bytes(doc.tobytes())
    doc.close()
    return pdf_bytes


@pytest.fixture
def image_page_pdf() -> Callable[..., bytes]:
    """Fabrik für Seiten mit Bild an frei wählbarer Stelle (optional ohne Text)."""
    return _make_image_page_pdf
