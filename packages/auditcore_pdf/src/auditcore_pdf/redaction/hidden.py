"""Versteckte Textablagen: Metadaten, XMP, Lesezeichen, Kommentare, Links, Felder, Anhänge."""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from typing import TYPE_CHECKING, TypeAlias

from auditcore_pdf.redaction.common import HiddenRef, _candidate_id, _clean, _norm
from auditcore_pdf.redaction.criteria import _matches, _Rule
from auditcore_pdf.redaction.plan import Candidate, CleanupInfo

if TYPE_CHECKING:
    from pymupdf import Document, Page

#: (Fundort, Text, Seite 1-basiert oder ``None``, Referenz)
HiddenString: TypeAlias = tuple[str, str, int | None, HiddenRef]

_STANDARD_INFO = frozenset(
    (
        "Title",
        "Author",
        "Subject",
        "Keywords",
        "Creator",
        "Producer",
        "CreationDate",
        "ModDate",
        "Trapped",
    )
)
_MAX_ATTACHMENT_TEXT = 5 * 1024 * 1024
_MAX_JS_XREFS = 20000


def _info_xref(doc: Document) -> int:
    """Objektnummer des Info-Wörterbuchs, 0 wenn es keines gibt."""
    try:
        kind, value = doc.xref_get_key(-1, "Info")
        return int(value.split()[0]) if kind == "xref" else 0
    except Exception:
        return 0


def _custom_info(doc: Document) -> list[tuple[str, str]]:
    """Eigene Schlüssel im Info-Wörterbuch, die ``doc.metadata`` nicht zeigt."""
    xref = _info_xref(doc)
    if not xref:
        return []
    found: list[tuple[str, str]] = []
    for key in doc.xref_get_keys(xref):
        if key in _STANDARD_INFO:
            continue
        kind, value = doc.xref_get_key(xref, key)
        if kind == "string" and value:
            found.append((key, value))
    return found


def _metadata_strings(doc: Document) -> Iterator[HiddenString]:
    for key, value in (doc.metadata or {}).items():
        if value and key not in ("format", "encryption"):
            yield f"Metadaten ({key})", str(value), None, {"type": "metadata", "key": key}
    for key, value in _custom_info(doc):
        yield f"Metadaten ({key})", value, None, {"type": "infokey", "key": key}
    xmp = doc.get_xml_metadata() or ""
    if xmp:
        yield "XMP-Metadaten", xmp, None, {"type": "xmp"}
    for i, entry in enumerate(doc.get_toc(simple=True)):
        page = entry[2] if entry[2] > 0 else None
        yield "Lesezeichen", str(entry[1]), page, {"type": "toc", "index": i}


def _annotation_strings(page: Page) -> Iterator[HiddenString]:
    for annot in page.annots() or []:
        info = annot.info or {}
        keys = ("content", "title", "subject")
        text = " ".join(str(info.get(k) or "") for k in keys).strip()
        if text:
            ref: HiddenRef = {"type": "annot", "page": page.number, "xref": annot.xref}
            yield "Kommentar", text, page.number + 1, ref


def _link_strings(page: Page) -> Iterator[HiddenString]:
    for link in page.get_links():
        uri = link.get("uri") or link.get("file") or ""
        if uri:
            ref: HiddenRef = {
                "type": "link",
                "page": page.number,
                "xref": link.get("xref", 0),
                "uri": uri,
            }
            yield "Link", str(uri), page.number + 1, ref


def _widget_strings(page: Page) -> Iterator[HiddenString]:
    for widget in page.widgets() or []:
        value = widget.field_value
        if value not in (None, "", False, "Off"):
            ref: HiddenRef = {"type": "widget", "page": page.number, "xref": widget.xref}
            yield f"Formularfeld „{widget.field_name}“", str(value), page.number + 1, ref


def _attachment_strings(doc: Document) -> Iterator[HiddenString]:
    for name in doc.embfile_names():
        try:
            data = doc.embfile_get(name)
        except Exception:
            continue
        text = name
        if len(data) <= _MAX_ATTACHMENT_TEXT:
            text += "\n" + data.decode("utf-8", errors="ignore")
        yield f"Dateianhang „{name}“", text, None, {"type": "attachment", "name": name}


def _iter_hidden_strings(doc: Document) -> Iterator[HiddenString]:
    """(Fundort, Text, Seite, Referenz) für alle versteckten Textablagen."""
    yield from _metadata_strings(doc)
    for page in doc:
        yield from _annotation_strings(page)
        yield from _link_strings(page)
        yield from _widget_strings(page)
    yield from _attachment_strings(doc)


def _scan_hidden(doc: Document, rules: list[_Rule]) -> list[Candidate]:
    found: list[Candidate] = []
    for location, text, page, ref in _iter_hidden_strings(doc):
        flat = " ".join(_clean(text).split())
        for prio, rule in enumerate(rules):
            for s, e in _matches(rule, flat):
                hit = flat[s:e]
                key = ("hidden", location, sorted(ref.items()), rule.source, s, _norm(hit))
                found.append(
                    Candidate(
                        id=_candidate_id(*key),
                        kind="hidden",
                        source=rule.source,
                        text=hit,
                        page=page,
                        location=location,
                        ref=ref,
                        priority=prio,
                        start=s,
                        end=e,
                    )
                )
    return found


def _has_javascript(doc: Document) -> bool:
    with contextlib.suppress(Exception):
        for x in range(1, min(doc.xref_length(), _MAX_JS_XREFS)):
            obj = doc.xref_object(x, compressed=True)
            if "/JavaScript" in obj or "/JS" in obj:
                return True
    return False


def _cleanup_info(doc: Document) -> CleanupInfo:
    skip = ("format", "encryption")
    meta = {k: v for k, v in (doc.metadata or {}).items() if v and k not in skip}
    meta.update(_custom_info(doc))
    return {
        "metadata_fields": sorted(meta),
        "xmp": bool(doc.get_xml_metadata()),
        "attachments": len(doc.embfile_names()),
        "javascript": _has_javascript(doc),
    }
