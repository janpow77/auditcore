"""Entfernen versteckter Fundstellen, Ersetzen von Zeichenketten, Bereinigung."""

from __future__ import annotations

import contextlib
import re
import unicodedata
from collections.abc import Callable, Iterable, Iterator
from typing import TYPE_CHECKING

from auditcore_pdf.engine import fitz
from auditcore_pdf.redaction.common import REDACTED_MARK, HiddenRef, _clean, _flat
from auditcore_pdf.redaction.hidden import _cleanup_info, _info_xref
from auditcore_pdf.redaction.pdf_strings import _literal, _pdf_strings
from auditcore_pdf.redaction.plan import Candidate, CleanupInfo
from auditcore_pdf.redaction.verify import _word_in

if TYPE_CHECKING:
    from pymupdf import Document

_HiddenRemover = Callable[["Document", HiddenRef, list[Candidate]], None]


def _remove_metadata(doc: Document, ref: HiddenRef, _cands: list[Candidate]) -> None:
    meta = dict(doc.metadata or {})
    meta[ref["key"]] = ""
    doc.set_metadata({k: v for k, v in meta.items() if k not in ("format", "encryption")})


def _remove_info_key(doc: Document, ref: HiddenRef, _cands: list[Candidate]) -> None:
    info = _info_xref(doc)
    if info:
        doc.xref_set_key(info, ref["key"], "null")


def _remove_xmp(doc: Document, _ref: HiddenRef, _cands: list[Candidate]) -> None:
    doc.del_xml_metadata()


def _redacted_title(title: str, cands: list[Candidate]) -> str:
    original = title
    # Nur die ausgewählten Treffer ersetzen, abgewählte bleiben stehen.
    for cand in cands:
        title = _literal(cand.text).sub(REDACTED_MARK, title)
    # Unsichtbare Zeichen (etwa „Kra\u200buse“) verhindern das Ersetzen im
    # Rohtext. Steht danach noch ein ausgewählter Text im bereinigten
    # Titel, wird der ganze Titel ersetzt.
    leftover = any(_flat(c.text) in _flat(_clean(title)) for c in cands)
    return REDACTED_MARK if title == original or leftover else title


def _remove_toc(doc: Document, ref: HiddenRef, cands: list[Candidate]) -> None:
    toc = doc.get_toc(simple=False)
    i = int(ref["index"])
    if i < len(toc):
        toc[i][1] = _redacted_title(toc[i][1], cands)
        doc.set_toc(toc)


def _remove_annot(doc: Document, ref: HiddenRef, _cands: list[Candidate]) -> None:
    page = doc[ref["page"]]
    for annot in page.annots() or []:
        if annot.xref == ref["xref"]:
            page.delete_annot(annot)
            break


def _remove_link(doc: Document, ref: HiddenRef, _cands: list[Candidate]) -> None:
    page = doc[ref["page"]]
    for link in page.get_links():
        uri = link.get("uri") or link.get("file") or ""
        if link.get("xref", 0) == ref["xref"] and uri == ref["uri"]:
            page.delete_link(link)
            break


def _remove_widget(doc: Document, ref: HiddenRef, _cands: list[Candidate]) -> None:
    page = doc[ref["page"]]
    for widget in page.widgets() or []:
        if widget.xref == ref["xref"]:
            page.delete_widget(widget)
            break


def _remove_attachment(doc: Document, ref: HiddenRef, _cands: list[Candidate]) -> None:
    with contextlib.suppress(Exception):
        doc.embfile_del(ref["name"])


_REMOVERS: dict[str | int, _HiddenRemover] = {
    "metadata": _remove_metadata,
    "infokey": _remove_info_key,
    "xmp": _remove_xmp,
    "toc": _remove_toc,
    "annot": _remove_annot,
    "link": _remove_link,
    "widget": _remove_widget,
    "attachment": _remove_attachment,
}


def _remove_hidden(doc: Document, cands: list[Candidate]) -> None:
    """Versteckte Fundstellen eines Fundorts entfernen oder leeren."""
    ref = cands[0].ref
    remover = _REMOVERS.get(ref.get("type", ""))
    if remover is not None:
        remover(doc, ref, cands)


# Einträge in Inhaltsströmen, die Text unabhängig von den Glyphen tragen.
_STREAM_TEXT_KEYS = re.compile(r"/(?:ActualText|Alt|E)\s*(?=[(<])")


class _KeyIndex:
    """Schnelle Suche vieler Schlüssel (Vergleichsform) in vielen Texten:
    Index über die ersten drei Zeichen statt Schlüssel × Texte."""

    def __init__(self, keys: Iterable[str]):
        self.by_prefix: dict[str, list[str]] = {}
        self.short: list[str] = []
        for k in sorted(set(keys), key=len, reverse=True):
            if len(k) >= 3:
                self.by_prefix.setdefault(k[:3], []).append(k)
            elif k:
                self.short.append(k)

    def __bool__(self) -> bool:
        return bool(self.by_prefix or self.short)

    def found(self, text: str) -> Iterator[str]:
        """Schlüssel in ``text`` (bereinigt). Kurze Schlüssel zählen nur als
        ganzes Wort, sonst träfe „AB“ jede „Abbildung“."""
        if self.short:
            words = unicodedata.normalize("NFKC", text).casefold()
            yield from (k for k in self.short if _word_in(words, k))
        flat = _flat(text)
        for i in range(len(flat) - 2):
            for k in self.by_prefix.get(flat[i : i + 3], ()):
                if flat.startswith(k, i):
                    yield k


# Zeichenketten, die nur eine andere Darstellung sichtbarer Inhalte sind
# (Alternativtext, Ersatztext, Abkürzung, Feld-Tooltip). Sie werden ersetzt,
# sobald sie einen geschwärzten Text enthalten, auch wenn derselbe Text an
# anderer Stelle bewusst lesbar bleibt.
_ALT_KEYS = frozenset({"Alt", "ActualText", "E", "TU"})
_KEY_BEFORE = re.compile(r"/([A-Za-z]+)\s*$")


def _key_before(src: str, pos: int) -> str:
    m = _KEY_BEFORE.search(src, max(0, pos - 40), pos)
    return m.group(1) if m else ""


class _StringScrubber:
    """Ersetzt Zeichenketten mit geschwärztem Text in allen Objekten und Strömen."""

    def __init__(self, doc: Document, index: _KeyIndex, fully_selected: Callable[[str], bool]):
        self.doc = doc
        self.index = index
        self.fully_selected = fully_selected
        self.mark = fitz.get_pdf_str(REDACTED_MARK)
        self.alt_targets = self._alt_targets()
        self.replaced = 0

    def hit(self, text: str, alt: bool) -> bool:
        return any(alt or self.fully_selected(k) for k in self.index.found(_clean(text)))

    def _alt_targets(self) -> set[int]:
        """Alternativtexte, die als eigenes Objekt abgelegt sind: /Alt 12 0 R"""
        targets: set[int] = set()
        ref_rx = re.compile(r"/(?:" + "|".join(sorted(_ALT_KEYS)) + r")\s+(\d+)\s+0\s+R")
        for xref in range(1, self.doc.xref_length()):
            try:
                src = self.doc.xref_object(xref, compressed=True)
                targets.update(int(m.group(1)) for m in ref_rx.finditer(src))
            except Exception:
                continue
        return targets

    def run(self) -> int:
        for xref in range(1, self.doc.xref_length()):
            try:
                src = self.doc.xref_object(xref, compressed=False)
            except Exception:
                continue
            if "(" in src or "<" in src:
                self._scrub_object(xref, src)
            self._scrub_stream(xref)
        return self.replaced

    def _scrub_object(self, xref: int, src: str) -> None:
        parts: list[str] = []
        last = 0
        for s, e, text in _pdf_strings(src):
            if self.hit(text, xref in self.alt_targets or _key_before(src, s) in _ALT_KEYS):
                parts.append(src[last:s] + self.mark)
                last = e
                self.replaced += 1
        if parts:
            self.doc.update_object(xref, "".join(parts) + src[last:])

    def _scrub_stream(self, xref: int) -> None:
        doc = self.doc
        try:
            if not doc.xref_is_stream(xref) or doc.xref_get_key(xref, "Subtype")[1] == "/Image":
                return
            raw: bytes = doc.xref_stream(xref) or b""
            is_xmp = doc.xref_get_key(xref, "Type")[1] == "/Metadata"
        except Exception:
            return
        if is_xmp:
            # XMP-Paket (auch auf Seiten- oder Objektebene, die die Suche nicht
            # einzeln ausweist): enthält es einen geschwärzten Text, wird es geleert.
            if self.hit(raw.decode("utf-8", "replace"), True):
                doc.update_stream(xref, b"")
                self.replaced += 1
            return
        if b"/ActualText" in raw or b"/Alt" in raw or b"/E" in raw:
            self._scrub_stream_text(xref, raw.decode("latin-1"))

    def _scrub_stream_text(self, xref: int, stream: str) -> None:
        out: list[str] = []
        last = 0
        for m in _STREAM_TEXT_KEYS.finditer(stream):
            if m.start() < last:
                continue
            for _s, e, text in _pdf_strings(stream, m.end(), only_at=m.end()):
                if self.hit(text, True):
                    # Eintrag entfernen: Die Textextraktion fällt dann auf die
                    # (geschwärzten) Glyphen zurück.
                    out.append(stream[last : m.start()])
                    last = e
                    self.replaced += 1
        if out:
            self.doc.update_stream(xref, ("".join(out) + stream[last:]).encode("latin-1"))


def _scrub_strings(doc: Document, keys: set[str], fully_selected: Callable[[str], bool]) -> int:
    """Zeichenketten in PDF-Objekten ersetzen, die einen geschwärzten Text
    enthalten: Alternativtext und ActualText im Strukturbaum und im
    Inhaltsstrom, Feldbeschriftungen, eigene Metadaten-Schlüssel und
    Ähnliches.

    Alternativtexte (``_ALT_KEYS``) werden immer ersetzt. Andere
    Zeichenketten nur, wenn ``fully_selected`` gilt, damit ein abgewählter
    Text an anderer Stelle (Lesezeichen, Feldwert) lesbar bleibt."""
    index = _KeyIndex(keys)
    if not index:
        return 0
    return _StringScrubber(doc, index, fully_selected).run()


_EXTRA_SANITIZE_KEYS = ("PieceInfo", "Metadata")


def _sanitize_notes(info: CleanupInfo) -> list[str]:
    notes = (
        (info["metadata_fields"], "Metadaten"),
        (info["xmp"], "XMP-Metadaten"),
        (info["attachments"], "Dateianhänge"),
        (info["javascript"], "JavaScript"),
    )
    return [label for present, label in notes if present]


def _clear_info_dict(doc: Document) -> None:
    doc.set_metadata({})
    doc.del_xml_metadata()
    info_xref = _info_xref(doc)
    if info_xref:
        for key in doc.xref_get_keys(info_xref):
            doc.xref_set_key(info_xref, key, "null")


def _drop_extra_keys(doc: Document) -> bool:
    """Private Anwendungsdaten, XMP an Seiten und Bildern, XFA-Formulardaten."""
    cat = doc.pdf_catalog()
    extra = False
    for xref in range(1, doc.xref_length()):
        try:
            names = doc.xref_get_keys(xref)
        except Exception:
            continue
        for key in _EXTRA_SANITIZE_KEYS:
            if key in names and not (key == "Metadata" and xref == cat):
                doc.xref_set_key(xref, key, "null")
                extra = True
    return extra


def _sanitize(doc: Document) -> list[str]:
    done = _sanitize_notes(_cleanup_info(doc))
    doc.scrub(
        attached_files=True,
        clean_pages=False,
        embedded_files=True,
        hidden_text=False,  # unsichtbare OCR-Textebenen bleiben erhalten
        javascript=True,
        metadata=True,
        redactions=False,
        remove_links=False,
        reset_fields=False,
        reset_responses=True,
        thumbnails=True,
        xml_metadata=True,
    )
    _clear_info_dict(doc)
    if _drop_extra_keys(doc):
        done.append("Anwendungsdaten")
    return done
