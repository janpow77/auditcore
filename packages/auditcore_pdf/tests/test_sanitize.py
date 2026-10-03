"""Tests für Metadaten-, Anhangs- und Anmerkungsbereinigung."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, cast

import pymupdf as fitz

from auditcore_pdf import (
    SanitizationPolicy,
    get_document_info,
    redact_document,
    sanitize_annotations,
    sanitize_attachments,
)
from auditcore_pdf.sanitize import PDF_ANNOT_REDACT

if TYPE_CHECKING:
    from pymupdf import Document


def test_sanitize_metadata(sensitive_pdf: bytes) -> None:
    redacted_pdf, report = redact_document(
        sensitive_pdf,
        terms=["STRENG_GEHEIM"],
        policy=SanitizationPolicy(scrub_metadata=True),
        verify=True,
    )
    info = get_document_info(redacted_pdf)
    # Titel enthielt "Bericht mit STRENG_GEHEIM im Titel" und muss bereinigt sein
    assert "STRENG_GEHEIM" not in info.metadata.get("title", "")
    assert "title" in report.metadata_fields_cleaned


def test_sanitize_attachments(sensitive_pdf: bytes) -> None:
    redacted_pdf, report = redact_document(
        sensitive_pdf,
        terms=["STRENG_GEHEIM"],
        policy=SanitizationPolicy(strip_attachments=True),
        verify=True,
    )
    info = get_document_info(redacted_pdf)
    assert len(info.attachments) == 0
    assert "geheimnis.txt" in report.attachments_removed


def test_sanitize_annotations(sensitive_pdf: bytes) -> None:
    redacted_pdf, report = redact_document(
        sensitive_pdf,
        terms=["STRENG_GEHEIM"],
        policy=SanitizationPolicy(strip_annotations=False),
        verify=True,
    )
    # Anmerkung enthielt STRENG_GEHEIM und wurde gelöscht
    doc = fitz.open(stream=redacted_pdf, filetype="pdf")
    p1 = doc[0]
    annots = list(p1.annots() or [])
    for a in annots:
        content = (a.info or {}).get("content", "")
        assert "STRENG_GEHEIM" not in content
    doc.close()
    assert report.annotations_removed >= 1


def _pdf_with_xmp_and_attachments() -> bytes:
    """Erzeugt ein PDF mit vertraulichem XMP-Strom und drei unterschiedlichen Anhängen."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text(fitz.Point(72, 100), "Neutraler Seitentext.")
    doc.set_metadata({"title": "Neutraler Titel", "author": "Prüferin"})
    doc.set_xml_metadata("<x:xmpmeta><dc>Bearbeiter STRENG_GEHEIM</dc></x:xmpmeta>")
    doc.embfile_add("STRENG_GEHEIM_liste.txt", b"neutral", filename="a.txt")
    doc.embfile_add("anlage.txt", b"Inhalt STRENG_GEHEIM", filename="b.txt")
    doc.embfile_add("leer.txt", b"", filename="c.txt")
    doc.embfile_add("harmlos.txt", b"nur oeffentliche Angaben", filename="d.txt")
    pdf_bytes = bytes(doc.tobytes())
    doc.close()
    return pdf_bytes


def test_sanitize_xmp_metadata_with_term() -> None:
    redacted_pdf, report = redact_document(
        _pdf_with_xmp_and_attachments(),
        terms=["STRENG_GEHEIM"],
        policy=SanitizationPolicy(scrub_metadata=True, clean_xmp=True),
    )
    assert "xmp_metadata" in report.metadata_fields_cleaned
    doc = fitz.open(stream=redacted_pdf, filetype="pdf")
    try:
        assert "STRENG_GEHEIM" not in (doc.get_xml_metadata() or "")
        # Unverdächtige Standardfelder bleiben erhalten
        assert doc.metadata is not None
        assert doc.metadata["title"] == "Neutraler Titel"
    finally:
        doc.close()


def test_sanitize_selective_attachments_by_name_and_content() -> None:
    """Ohne Pauschalentfernung gehen nur Anhänge mit Treffer in Name oder Inhalt."""
    redacted_pdf, report = redact_document(
        _pdf_with_xmp_and_attachments(),
        terms=["STRENG_GEHEIM"],
        policy=SanitizationPolicy(strip_attachments=False),
    )
    assert sorted(report.attachments_removed) == ["STRENG_GEHEIM_liste.txt", "anlage.txt"]
    info = get_document_info(redacted_pdf)
    assert sorted(info.attachments) == ["harmlos.txt", "leer.txt"]
    assert report.verified is True


def test_sanitize_remove_all_metadata() -> None:
    redacted_pdf, report = redact_document(
        _pdf_with_xmp_and_attachments(),
        terms=["NICHT_VORHANDEN"],
        policy=SanitizationPolicy(remove_all_metadata=True, clean_xmp=True),
    )
    assert {"title", "author"} <= set(report.metadata_fields_cleaned)
    doc = fitz.open(stream=redacted_pdf, filetype="pdf")
    try:
        assert doc.metadata is not None
        assert doc.metadata["title"] == ""
        assert doc.metadata["author"] == ""
        assert "STRENG_GEHEIM" not in (doc.get_xml_metadata() or "")
    finally:
        doc.close()


def test_sanitize_annotations_keeps_redact_annotations() -> None:
    """Bestehende Schwärzungsanmerkungen bleiben für apply_redactions erhalten."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.add_redact_annot(fitz.Rect(70, 85, 200, 110), fill=(0, 0, 0))
    note = page.add_text_annot(fitz.Point(72, 300), "Notiz")
    note.set_info(content="Allgemeine Notiz", title="Prüfer")
    try:
        removed = sanitize_annotations(doc, [], [], SanitizationPolicy(strip_annotations=True))
        assert removed == 1
        remaining = [a.type[0] for a in doc[0].annots() or []]
        assert remaining == [PDF_ANNOT_REDACT]
    finally:
        doc.close()


class _BrokenAttachmentDoc:
    """Dokument-Attrappe, deren Anhangsverzeichnis nicht lesbar ist."""

    def embfile_names(self) -> list[str]:
        raise RuntimeError("Anhangsverzeichnis beschädigt")


def test_sanitize_attachments_tolerates_unreadable_directory() -> None:
    doc = cast("Document", _BrokenAttachmentDoc())
    removed = sanitize_attachments(doc, ["STRENG_GEHEIM"], [], SanitizationPolicy())
    assert removed == []


class _UntypedAnnot:
    """Anmerkung ohne auswertbaren Typ, aber mit vertraulichem Inhalt."""

    type: tuple[int, ...] = ()
    info: ClassVar[dict[str, str]] = {"content": "Hinweis STRENG_GEHEIM", "title": "Prüfer"}


class _Page:
    def __init__(self, annots: list[_UntypedAnnot]) -> None:
        self._annots = annots
        self.deleted: list[_UntypedAnnot] = []

    def annots(self) -> list[_UntypedAnnot]:
        return list(self._annots)

    def delete_annot(self, annot: _UntypedAnnot) -> None:
        self.deleted.append(annot)


class _SinglePageDoc:
    page_count = 1

    def __init__(self, page: _Page) -> None:
        self._page = page

    def __getitem__(self, idx: int) -> _Page:
        return self._page


def test_sanitize_annotations_handles_missing_annotation_type() -> None:
    """Auch Anmerkungen ohne lesbaren Typ werden inhaltlich geprüft und entfernt."""
    annot = _UntypedAnnot()
    page = _Page([annot])
    doc = cast("Document", _SinglePageDoc(page))
    removed = sanitize_annotations(doc, ["streng_geheim"], [], SanitizationPolicy())
    assert removed == 1
    assert page.deleted == [annot]
