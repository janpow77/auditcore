"""Text außerhalb der Seiteninhalte: Lesezeichen, Formulare, Ziele, Skripte, Alt-Texte.

Diese Bereiche erscheinen nicht oder nur teilweise in der Textextraktion einer Seite,
werden aber von Betrachtern angezeigt oder lassen sich auslesen. Die Sammlung
liefert jeden Text mit Kategorie und Ortsangabe; Nachprüfung und Bereinigung
verwenden dieselbe Sammlung.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from auditcore_pdf.pdfstrings import find_key_references, find_key_strings

if TYPE_CHECKING:
    from pymupdf import Document, Page

#: Schlüssel für Ersatztexte in Struktur- und Inhaltsdaten
ALT_KEYS: tuple[str, ...] = ("Alt", "ActualText", "E")
JS_KEY = "JS"

_KEY_LABELS = {
    "Alt": "Alternativtext",
    "ActualText": "ActualText",
    "E": "Abkürzungsauflösung",
    "JS": "JavaScript",
}

OUTLINE = "outline"
FORM_FIELD = "form_field"
LINK = "link"
NAMED_DESTINATION = "named_destination"
PAGE_LABEL = "page_label"
OPTIONAL_CONTENT = "optional_content"
ALT_TEXT = "alt_text"
JAVASCRIPT = "javascript"
XMP = "xmp"


@dataclass(frozen=True)
class TextItem:
    """Ein Text aus einem Strukturbereich des Dokuments."""

    category: str
    location: str
    text: str


def _outline_items(doc: Document) -> list[TextItem]:
    return [
        TextItem(OUTLINE, f"Lesezeichen {number}", str(entry[1]))
        for number, entry in enumerate(doc.get_toc(simple=True), start=1)
    ]


def widget_texts(widget: object) -> list[str]:
    """Name, Wert, Beschriftung (Tooltip) und Auswahlwerte eines Formularfelds."""
    texts = [getattr(widget, name, None) for name in ("field_name", "field_value", "field_label")]
    for choice in getattr(widget, "choice_values", None) or []:
        texts.extend(choice if isinstance(choice, list | tuple) else [choice])
    return [text for text in texts if isinstance(text, str) and text]


def _page_items(page: Page) -> list[TextItem]:
    pno = int(page.number) + 1
    items = [
        TextItem(FORM_FIELD, f"Formularfeld {number} (Seite {pno})", text)
        for number, widget in enumerate(page.widgets(), start=1)
        for text in widget_texts(widget)
    ]
    items.extend(
        TextItem(LINK, f"Verknüpfung {number} (Seite {pno})", str(link.get("uri") or ""))
        for number, link in enumerate(page.get_links(), start=1)
    )
    return items


def _document_items(doc: Document) -> list[TextItem]:
    items = [
        TextItem(NAMED_DESTINATION, "Benanntes Ziel", str(name))
        for name in (doc.resolve_names() or {})
    ]
    items.extend(
        TextItem(PAGE_LABEL, f"Seitenbeschriftung {number}", str(label.get("prefix") or ""))
        for number, label in enumerate(doc.get_page_labels() or [], start=1)
    )
    items.extend(
        TextItem(OPTIONAL_CONTENT, f"Ebenenname (Objekt {xref})", str(info.get("name") or ""))
        for xref, info in (doc.get_ocgs() or {}).items()
    )
    return items


def catalog_metadata_xref(doc: Document) -> int:
    """Objektnummer des Dokument-XMP-Stroms (0, wenn keiner verknüpft ist)."""
    kind, value = doc.xref_get_key(doc.pdf_catalog(), "Metadata")
    return int(str(value).split()[0]) if kind == "xref" else 0


def object_source(doc: Document, xref: int) -> bytes:
    """Quelltext des Objekts (ohne Strom) als Bytes."""
    return str(doc.xref_object(xref, compressed=False)).encode("latin-1", errors="replace")


def stream_kind(doc: Document, xref: int) -> str:
    """``xmp``, ``content`` (Seiteninhalt, Formular-XObject), ``other`` oder ``""`` (kein Strom).

    Als Inhaltsstrom gelten Form-XObjects und Ströme ohne Typ-, Untertyp- und
    Schriftlängenangabe (Seiteninhalte). Bilder, Schriften, Farbprofile und
    Anhänge sind Binärdaten und werden nicht nach Zeichenketten durchsucht.
    """
    if not doc.xref_is_stream(xref):
        return ""
    subtype = doc.xref_get_key(xref, "Subtype")[1]
    kind = doc.xref_get_key(xref, "Type")[1]
    if kind == "/Metadata":
        return "xmp"
    if subtype == "/Form":
        return "content"
    untyped = (subtype, kind) == ("null", "null")
    binary_keys = ("Length1", "N")
    if untyped and all(doc.xref_get_key(xref, key)[0] == "null" for key in binary_keys):
        return "content"
    return "other"


def _key_items(data: bytes, keys: tuple[str, ...], where: str) -> list[TextItem]:
    return [
        TextItem(
            JAVASCRIPT if found.key == JS_KEY else ALT_TEXT,
            f"{_KEY_LABELS[found.key]} ({where})",
            found.text,
        )
        for found in find_key_strings(data, keys)
    ]


def _object_items(doc: Document, xref: int, skip_xmp: int) -> list[TextItem]:
    source = object_source(doc, xref)
    items = _key_items(source, (*ALT_KEYS, JS_KEY), f"Objekt {xref}")
    items.extend(
        TextItem(JAVASCRIPT, f"JavaScript (Objekt {ref})", decode_stream(doc, ref))
        for ref in find_key_references(source, JS_KEY)
    )
    kind = stream_kind(doc, xref)
    if kind == "xmp" and xref != skip_xmp:
        items.append(TextItem(XMP, f"XMP-Metadatenstrom (Objekt {xref})", decode_stream(doc, xref)))
    elif kind == "content":
        data = bytes(doc.xref_stream(xref))
        items.extend(_key_items(data, ALT_KEYS, f"Inhaltsstrom Objekt {xref}"))
    return items


def decode_stream(doc: Document, xref: int) -> str:
    """Entpackter Strominhalt als Text (UTF-8, ersatzweise mit Ersatzzeichen)."""
    return bytes(doc.xref_stream(xref) or b"").decode("utf-8", errors="replace")


def collect_structure_texts(doc: Document) -> list[TextItem]:
    """Sammelt alle Texte aus Strukturbereichen des Dokuments."""
    items = _outline_items(doc)
    for index in range(doc.page_count):
        items.extend(_page_items(doc[index]))
    items.extend(_document_items(doc))
    skip_xmp = catalog_metadata_xref(doc)
    for xref in range(1, doc.xref_length()):
        items.extend(_object_items(doc, xref, skip_xmp))
    return [item for item in items if item.text]
