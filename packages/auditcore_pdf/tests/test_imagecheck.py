"""Gemischte Seiten, binäre Anhänge und XMP: nicht prüfbare Bereiche werden gemeldet."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, cast

import pymupdf as fitz
import pytest

from auditcore_pdf import (
    SanitizationPolicy,
    find_unverifiable_attachments,
    find_unverifiable_pages,
    open_pdf,
    redact_document,
    verify_redaction,
)
from auditcore_pdf import engine as engine_module
from auditcore_pdf.sanitize import is_binary_attachment, remove_xmp

if TYPE_CHECKING:
    from pymupdf import Document

ImageFactory = Callable[..., bytes]


@pytest.mark.parametrize(
    ("rect", "with_text", "reason"),
    [
        ((50, 300, 545, 800), True, "Bildanteil"),
        ((60, 80, 120, 110), True, "Bild überdeckt Textbereich"),
        ((50, 50, 200, 200), False, "keine Textebene"),
        ((400, 700, 450, 750), True, None),
    ],
    ids=["grossflaechig", "ueber-text", "scan", "kleines-logo"],
)
def test_unverifiable_page_reasons(
    image_page_pdf: ImageFactory,
    rect: tuple[float, float, float, float],
    with_text: bool,
    reason: str | None,
) -> None:
    doc = open_pdf(image_page_pdf(rect, text=with_text))
    try:
        found = find_unverifiable_pages(doc, 0.25)
    finally:
        doc.close()
    if reason is None:
        assert found == {}
    else:
        assert reason in found[1]


def test_threshold_must_be_a_share(image_page_pdf: ImageFactory) -> None:
    doc = open_pdf(image_page_pdf((400, 700, 450, 750)))
    try:
        for invalid in (0.0, 1.5):
            with pytest.raises(ValueError, match="Bildanteil"):
                find_unverifiable_pages(doc, invalid)
    finally:
        doc.close()


def test_mixed_page_is_not_reported_as_verified(image_page_pdf: ImageFactory) -> None:
    pdf = image_page_pdf((50, 300, 545, 800))
    res = verify_redaction(pdf, forbidden_terms=["GEHEIM"])
    assert res.clean is True
    assert res.fully_verified is False
    assert res.unverifiable_pages == [1]
    assert res.unverifiable[0].startswith("Seite 1: Bildanteil")

    _, report = redact_document(pdf, terms=["GEHEIM"])
    assert report.unverifiable_pages == [1]
    assert report.scanned_pages_without_ocr == []
    assert report.verified is False
    assert report.verification_error is not None
    assert report.verification_error.startswith("nicht prüfbar: Seite 1: Bildanteil")


def test_threshold_is_configurable(image_page_pdf: ImageFactory) -> None:
    pdf = image_page_pdf((50, 300, 545, 800))
    assert verify_redaction(pdf, ["GEHEIM"], image_coverage_threshold=0.9).fully_verified
    policy = SanitizationPolicy(image_coverage_threshold=0.9)
    _, report = redact_document(pdf, terms=["GEHEIM"], policy=policy)
    assert report.unverifiable_pages == []
    assert report.verified is True


def _pdf_with_attachments() -> bytes:
    doc = fitz.open()
    doc.new_page()
    doc.embfile_add("text.txt", b"nur Text", filename="text.txt")
    doc.embfile_add("archiv.zip", b"PK\x03\x04\x00\x00binaer", filename="archiv.zip")
    doc.embfile_add("latin.bin", b"\xc4\xd6\xdc", filename="latin.bin")
    pdf_bytes = bytes(doc.tobytes())
    doc.close()
    return pdf_bytes


def test_binary_attachments_are_unverifiable_when_kept() -> None:
    pdf = _pdf_with_attachments()
    _, report = redact_document(
        pdf, terms=["GEHEIM"], policy=SanitizationPolicy(strip_attachments=False)
    )
    assert report.attachments_removed == []
    assert report.unverifiable_items == [
        "Anhang 'archiv.zip': binär oder komprimiert, Inhalt nicht prüfbar",
        "Anhang 'latin.bin': binär oder komprimiert, Inhalt nicht prüfbar",
    ]
    assert report.verified is False
    res = verify_redaction(pdf, forbidden_terms=["GEHEIM"])
    assert res.clean is True
    assert len(res.unverifiable) == 2

    _, stripped = redact_document(pdf, terms=["GEHEIM"])
    assert stripped.unverifiable_items == []
    assert stripped.verified is True


def test_is_binary_attachment() -> None:
    assert is_binary_attachment(b"a\x00b") is True
    assert is_binary_attachment(b"\xff") is True
    assert is_binary_attachment("Prüfung".encode()) is False


class _BrokenDoc:
    def embfile_names(self) -> list[str]:
        raise RuntimeError("beschädigt")


def test_find_unverifiable_attachments_tolerates_broken_directory() -> None:
    assert find_unverifiable_attachments(cast("Document", _BrokenDoc())) == []


def _pdf_with_neutral_xmp() -> bytes:
    doc = fitz.open()
    doc.new_page()
    doc.set_xml_metadata("<x:xmpmeta><dc>neutral</dc></x:xmpmeta>")
    pdf_bytes = bytes(doc.tobytes())
    doc.close()
    return pdf_bytes


def test_xmp_removed_whenever_metadata_is_scrubbed() -> None:
    out, report = redact_document(_pdf_with_neutral_xmp(), terms=["GEHEIM"])
    assert report.metadata_fields_cleaned == ["xmp_metadata"]
    doc = open_pdf(out)
    try:
        assert not doc.get_xml_metadata()
        assert remove_xmp(doc) == []
    finally:
        doc.close()


def test_xmp_kept_without_match_when_removal_disabled() -> None:
    policy = SanitizationPolicy(remove_xmp=False)
    out, report = redact_document(_pdf_with_neutral_xmp(), terms=["GEHEIM"], policy=policy)
    assert report.metadata_fields_cleaned == []
    doc = open_pdf(out)
    try:
        assert "neutral" in doc.get_xml_metadata()
    finally:
        doc.close()


def test_xmp_removed_on_match_when_removal_disabled() -> None:
    policy = SanitizationPolicy(remove_xmp=False)
    _, report = redact_document(_pdf_with_neutral_xmp(), terms=["neutral"], policy=policy)
    assert report.metadata_fields_cleaned == ["xmp_metadata"]


def test_metadata_untouched_when_scrubbing_disabled() -> None:
    policy = SanitizationPolicy(scrub_metadata=False)
    _, report = redact_document(_pdf_with_neutral_xmp(), terms=["neutral"], policy=policy)
    assert report.metadata_fields_cleaned == []
    assert report.verified is False


def test_without_actualtext_flag_only_visible_text_is_used(
    monkeypatch: pytest.MonkeyPatch, structure_pdf: bytes
) -> None:
    """Ältere PyMuPDF-Versionen ohne TEXT_IGNORE_ACTUALTEXT: Prüfung meldet das im Detail."""
    monkeypatch.delattr(fitz, "TEXT_IGNORE_ACTUALTEXT")
    assert engine_module.glyph_text_flags("TEXTFLAGS_TEXT") is None
    res = verify_redaction(structure_pdf, forbidden_terms=["LECK_GLYPHE"])
    assert res.clean is True
    assert res.details["glyphs_under_actualtext_checked"] is False
    _, report = redact_document(structure_pdf, terms=["LECK_GLYPHE"], verify=False)
    assert report.findings_count == 0
