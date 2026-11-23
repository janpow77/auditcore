"""Nachprüfung im Rohinhalt: Bytefolgen in allen entpackten PDF-Objekten."""

from __future__ import annotations

import contextlib
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pymupdf import Document

_ESCAPED = [re.escape(bytes([b])) for b in range(256)]
_NO_START = frozenset(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/")
_NO_END = frozenset(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")


@dataclass
class _TrieNode:
    children: dict[int, _TrieNode] = field(default_factory=dict)
    terminal: bool = False

    def pattern(self) -> bytes:
        branches = [_ESCAPED[b] + child.pattern() for b, child in sorted(self.children.items())]
        if not branches:
            return b""
        body = branches[0] if len(branches) == 1 else b"(?:" + b"|".join(branches) + b")"
        return b"(?:" + body + b")?" if self.terminal else body


def _trie_pattern(forms: Iterable[bytes]) -> bytes:
    """Alternative vieler Bytefolgen als Präfixbaum. Eine flache Liste
    „a|b|c…“ mit Tausenden Einträgen kompiliert und sucht in Python sehr
    langsam; der Baum teilt gemeinsame Anfänge."""
    trie = _TrieNode()
    for form in forms:
        node = trie
        for byte in form:
            node = node.children.setdefault(byte, _TrieNode())
        node.terminal = True
    return trie.pattern()


class _RawScanner:
    """Sucht viele Bytefolgen (ohne Groß-/Kleinschreibung für ASCII).

    Ein kleiner Ausdruck aus den Anfängen der Formen findet in C-Geschwindigkeit
    die möglichen Fundorte; erst dort wird jede Form mit diesem Anfang
    verglichen. Die Formen werden nach Länge gruppiert (Anfang bis 16 Byte),
    damit eine kurze Form wie „Anna“ nicht alle langen Formen in wenige
    Gruppen zwingt. Mit ``bounded`` zählt ein Treffer nur mit Wortgrenze und
    nicht als PDF-Name („/Name“)."""

    def __init__(self, table: dict[bytes, str], bounded: bool):
        self.table, self.bounded = table, bounded
        groups: dict[int, dict[bytes, list[bytes]]] = {}
        for form in sorted(table, key=len, reverse=True):
            k = min(16, len(form))
            groups.setdefault(k, {}).setdefault(form[:k], []).append(form)
        self.parts = [
            (re.compile(b"(?=(" + _trie_pattern(by_prefix) + b"))"), by_prefix)
            for _k, by_prefix in sorted(groups.items())
        ]

    def scan(self, low: bytes, hits: set[str]) -> None:
        """``low``: bereits mit ``bytes.lower()`` umgewandelt."""
        size = len(low)
        for rx, by_prefix in self.parts:
            for m in rx.finditer(low):
                i = m.start()
                if self.bounded and i > 0 and low[i - 1] in _NO_START:
                    continue
                for form in by_prefix[m.group(1)]:
                    end = i + len(form)
                    if not low.startswith(form, i):
                        continue
                    if self.bounded and end < size and low[end] in _NO_END:
                        continue
                    hits.add(self.table[form])


def _byte_forms(text: str) -> tuple[set[bytes], set[bytes]]:
    """Mögliche Ablageformen eines Texts in PDF-Objekten: (Klartext, Hex).

    Bytevergleiche ignorieren Groß- und Kleinschreibung nur für ASCII, deshalb
    werden die üblichen Schreibweisen („Krüger“, „KRÜGER“) einzeln erzeugt.
    """
    plain: set[bytes] = set()
    utf16: set[bytes] = set()
    for variant in {text, text.upper(), text.lower(), text.capitalize(), text.title()}:
        for enc in ("utf-8", "latin-1", "cp1252"):
            with contextlib.suppress(UnicodeEncodeError):
                plain.add(variant.encode(enc))
        utf16.add(variant.encode("utf-16-be"))
    escaped = set()
    for form in plain:
        if any(b > 127 for b in form):
            escaped.add(b"".join(b"\\%03o" % b if b > 127 else bytes([b]) for b in form))
    hexes = {f.hex().encode() for f in plain | utf16}
    return plain | escaped | utf16, hexes


def _font_file_xrefs(doc: Document) -> set[int]:
    """Eingebettete Schriftdateien. Ihre Namenstabellen (Schriftname,
    Gestalter, Copyright) sind kein Dokumentinhalt und lösten sonst
    Fehlalarme aus, etwa „Vera“ in „Bitstream Vera“."""
    found: set[int] = set()
    for xref in range(1, doc.xref_length()):
        try:
            if doc.xref_get_key(xref, "Type")[1] != "/FontDescriptor":
                continue
            for key in ("FontFile", "FontFile2", "FontFile3"):
                kind, value = doc.xref_get_key(xref, key)
                if kind == "xref":
                    found.add(int(value.split()[0]))
        except Exception:
            continue
    return found


_Blobs = tuple[tuple[bytes, set[str]], ...]


def _needle_scanners(needles: list[str]) -> list[_RawScanner]:
    plain: dict[bytes, str] = {}
    hexes: dict[bytes, str] = {}
    for n in needles:
        p, h = _byte_forms(n)
        for form in p:
            plain.setdefault(form.lower(), n)
        for form in h:
            hexes.setdefault(form.lower(), n)
    return [_RawScanner(plain, True), _RawScanner(hexes, False)]


class _RawContents:
    """Treffer je Ablage: außerhalb und innerhalb von Inhaltsströmen."""

    def __init__(self, doc: Document):
        self.doc = doc
        self.fonts = _font_file_xrefs(doc)
        self.content = {x for page in doc for x in page.get_contents()}
        self.strict: set[str] = set()
        self.in_content: set[str] = set()

    def blobs(self, xref: int) -> _Blobs:
        doc = self.doc
        try:
            if xref in self.fonts or doc.xref_get_key(xref, "Subtype")[1] == "/Image":
                return ()
            head = doc.xref_object(xref, compressed=False).encode("latin-1", errors="ignore")
            body: bytes = (doc.xref_stream(xref) or b"") if doc.xref_is_stream(xref) else b""
            is_content = xref in self.content or doc.xref_get_key(xref, "Subtype")[1] == "/Form"
        except Exception:
            return ()
        if is_content:
            return ((head, self.strict), (body, self.in_content))
        return ((head + b"\n" + body, self.strict),)


def _raw_contains(doc: Document, needles: list[str]) -> tuple[set[str], set[str]]:
    """Texte, die nach dem Entpacken aller Objekte noch in der Datei stehen.

    Rückgabe: (Treffer außerhalb von Inhaltsströmen, Treffer in Inhaltsströmen
    von Seiten und Form-XObjects). Im Inhaltsstrom steht Text oft in Stücken
    („(Krause) Tj (straße) Tj“); ein Stück ist dort kein eigenes Wort.

    Klartext zählt nur mit Wortgrenze und nicht als PDF-Name („/Name“), damit
    zufällige Wortbestandteile und Schlüsselnamen keinen Fehlalarm auslösen.
    Bilddaten und Schriftdateien werden übersprungen.
    """
    scanners = _needle_scanners(needles)
    raw = _RawContents(doc)
    for xref in range(1, doc.xref_length()):
        for blob, hits in raw.blobs(xref):
            if blob:
                low = blob.lower()
                for scanner in scanners:
                    scanner.scan(low, hits)
        if len(raw.strict) == len(needles):
            break
    return raw.strict, raw.in_content - raw.strict
