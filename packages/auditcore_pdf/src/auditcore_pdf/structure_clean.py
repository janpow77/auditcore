"""Bereinigung der Strukturbereiche: Lesezeichen, Formulare, Ziele, Skripte, Alt-Texte.

Jede Kategorie wird vollständig entfernt, wenn die Richtlinie es verlangt;
andernfalls werden nur Einträge mit Treffer entfernt oder ersetzt.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from auditcore_pdf.matching import PatternSpec, TextMatcher
from auditcore_pdf.models import SanitizationPolicy
from auditcore_pdf.pdfstrings import (
    blank_strings,
    find_key_references,
    find_key_strings,
    pdf_text_string,
)
from auditcore_pdf.structure import (
    ALT_KEYS,
    JS_KEY,
    object_source,
    stream_kind,
    widget_texts,
)

if TYPE_CHECKING:
    from pymupdf import Document, Page

#: Ersatztext für Lesezeichen- und Ebenennamen mit Treffer
REDACTED_PLACEHOLDER = "[geschwärzt]"


def _clean_outline(doc: Document, matcher: TextMatcher, strip: bool) -> list[str]:
    toc = doc.get_toc(simple=False)
    if strip and toc:
        doc.set_toc([])
        return [f"Lesezeichen: {len(toc)} entfernt"]
    hits = [entry for entry in toc if matcher.matches(str(entry[1]))]
    for entry in hits:
        entry[1] = REDACTED_PLACEHOLDER
    if hits:
        doc.set_toc(toc)
        return [f"Lesezeichen: {len(hits)} Titel ersetzt"]
    return []


def _clean_page(page: Page, matcher: TextMatcher, policy: SanitizationPolicy) -> list[str]:
    pno = int(page.number) + 1
    cleaned: list[str] = []
    for widget in list(page.widgets()):
        if policy.strip_form_fields or any(matcher.matches(t) for t in widget_texts(widget)):
            page.delete_widget(widget)
            cleaned.append(f"Formularfeld auf Seite {pno} entfernt")
    for link in page.get_links():
        if policy.strip_links or matcher.matches(str(link.get("uri") or "")):
            page.delete_link(link)
            cleaned.append(f"Verknüpfung auf Seite {pno} entfernt")
    return cleaned


def _remove_named_destinations(doc: Document) -> None:
    catalog = doc.pdf_catalog()
    kind, value = doc.xref_get_key(catalog, "Names")
    if kind == "xref":
        doc.xref_set_key(int(str(value).split()[0]), "Dests", "null")
    elif kind == "dict":
        doc.xref_set_key(catalog, "Names/Dests", "null")
    doc.xref_set_key(catalog, "Dests", "null")


def _clean_document_level(
    doc: Document, matcher: TextMatcher, policy: SanitizationPolicy
) -> list[str]:
    cleaned: list[str] = []
    names = [str(name) for name in (doc.resolve_names() or {})]
    if names and (policy.strip_named_destinations or any(map(matcher.matches, names))):
        _remove_named_destinations(doc)
        cleaned.append(f"Benannte Ziele: {len(names)} entfernt")
    labels = [str(label.get("prefix") or "") for label in doc.get_page_labels() or []]
    if labels and (policy.strip_page_labels or any(map(matcher.matches, labels))):
        doc.xref_set_key(doc.pdf_catalog(), "PageLabels", "null")
        cleaned.append("Seitenbeschriftungen entfernt")
    for xref, info in (doc.get_ocgs() or {}).items():
        if matcher.matches(str(info.get("name") or "")):
            doc.xref_set_key(int(xref), "Name", pdf_text_string(REDACTED_PLACEHOLDER))
            cleaned.append(f"Ebenenname (Objekt {xref}) ersetzt")
    return cleaned


def _blank_keys(doc: Document, xref: int, keys: tuple[str, ...], select: TextMatcher | None) -> int:
    """Leert Zeichenketten der Schlüssel in Objekt und Inhaltsstrom; ``None`` = alle."""
    count = 0
    source = object_source(doc, xref)
    hits = [s for s in find_key_strings(source, keys) if select is None or select.matches(s.text)]
    if hits:
        new_source = blank_strings(source, [(s.start, s.end) for s in hits])
        doc.update_object(xref, new_source.decode("latin-1"))
        count += len(hits)
    if stream_kind(doc, xref) == "content":
        data = bytes(doc.xref_stream(xref))
        found = find_key_strings(data, keys)
        hits = [s for s in found if select is None or select.matches(s.text)]
        if hits:
            doc.update_stream(xref, blank_strings(data, [(s.start, s.end) for s in hits]))
            count += len(hits)
    return count


def _javascript_present(doc: Document, matcher: TextMatcher) -> tuple[bool, bool]:
    """(Skript vorhanden, Skript mit Treffer)."""
    present = hit = False
    for xref in range(1, doc.xref_length()):
        source = object_source(doc, xref)
        texts = [s.text for s in find_key_strings(source, (JS_KEY,))]
        for ref in find_key_references(source, JS_KEY):
            texts.append(bytes(doc.xref_stream(ref) or b"").decode("utf-8", errors="replace"))
        present = present or bool(texts)
        hit = hit or any(map(matcher.matches, texts))
    return present, hit


def _remove_javascript(doc: Document) -> int:
    """Leert alle Skripte (direkt und als Strom); Aktionen bleiben ohne Code stehen."""
    count = 0
    for xref in range(1, doc.xref_length()):
        for ref in find_key_references(object_source(doc, xref), JS_KEY):
            if doc.xref_is_stream(ref):
                doc.update_stream(ref, b"")
                count += 1
        count += _blank_keys(doc, xref, (JS_KEY,), None)
    return count


def _clean_object_strings(
    doc: Document, matcher: TextMatcher, policy: SanitizationPolicy
) -> list[str]:
    cleaned: list[str] = []
    present, hit = _javascript_present(doc, matcher)
    if present and (policy.strip_javascript or hit):
        cleaned.append(f"JavaScript: {_remove_javascript(doc)} Skripte geleert")
    select = None if policy.strip_alt_texts else matcher
    alt_count = sum(_blank_keys(doc, x, ALT_KEYS, select) for x in range(1, doc.xref_length()))
    if alt_count:
        cleaned.append(f"Alternativtexte/ActualText: {alt_count} geleert")
    return cleaned


def sanitize_structure(
    doc: Document,
    terms: list[str],
    patterns: list[PatternSpec],
    policy: SanitizationPolicy,
) -> list[str]:
    """Bereinigt Lesezeichen, Formularfelder, Verknüpfungen, benannte Ziele,
    Seitenbeschriftungen, Ebenennamen, JavaScript und Alternativtexte.

    Liefert eine Beschreibung je bereinigtem Bereich.
    """
    matcher = TextMatcher(terms, patterns)
    cleaned = _clean_outline(doc, matcher, policy.strip_outline)
    for index in range(doc.page_count):
        cleaned.extend(_clean_page(doc[index], matcher, policy))
    cleaned.extend(_clean_document_level(doc, matcher, policy))
    cleaned.extend(_clean_object_strings(doc, matcher, policy))
    return cleaned
