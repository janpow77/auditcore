"""Lesen, Dekodieren und Ersetzen von PDF-Zeichenketten in Objekt- und Inhaltsdaten.

Grundlage für die Prüfung von Alternativtexten, ActualText und JavaScript, die
PyMuPDF nicht als eigene Struktur bereitstellt. Gearbeitet wird auf Bytes, damit
Objektquelltexte und (entpackte) Inhaltsströme gleich behandelt werden.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_SIMPLE_ESCAPES = {
    ord("n"): b"\n",
    ord("r"): b"\r",
    ord("t"): b"\t",
    ord("b"): b"\b",
    ord("f"): b"\f",
}
_OCTAL = re.compile(rb"[0-7]{1,3}")
_HEX_STRING = re.compile(rb"<([0-9A-Fa-f\s]*)>")
_BACKSLASH, _OPEN, _CLOSE, _CR, _LF = 0x5C, 0x28, 0x29, 0x0D, 0x0A


@dataclass(frozen=True)
class KeyString:
    """Zeichenkettenwert eines Schlüssels mit Lage im untersuchten Datenblock."""

    key: str
    text: str
    start: int
    end: int


def decode_text(raw: bytes) -> str:
    """Dekodiert einen PDF-Textstring (UTF-16BE oder UTF-8 mit BOM, sonst Latin-1)."""
    if raw.startswith(b"\xfe\xff"):
        return raw[2:].decode("utf-16-be", errors="replace")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw[3:].decode("utf-8", errors="replace")
    # Näherung für PDFDocEncoding: deckt ASCII und die westeuropäischen Zeichen ab.
    return raw.decode("latin-1")


def _escape(data: bytes, index: int) -> tuple[bytes, int]:
    """Wertet eine Escape-Folge ab ``index`` (Zeichen nach dem Backslash) aus."""
    if index >= len(data):
        return b"", index
    char = data[index]
    if char in _SIMPLE_ESCAPES:
        return _SIMPLE_ESCAPES[char], index + 1
    octal = _OCTAL.match(data, index)
    if octal:
        return bytes([int(octal.group(), 8) & 0xFF]), octal.end()
    if char == _CR:
        # Zeilenfortsetzung: Backslash vor CR, LF oder CRLF fällt weg.
        return b"", index + (2 if data[index + 1 : index + 2] == b"\n" else 1)
    if char == _LF:
        return b"", index + 1
    return bytes([char]), index + 1


def _literal(data: bytes, start: int) -> tuple[bytes, int]:
    """Liest einen Literal-String ab der öffnenden Klammer; liefert Inhalt und Ende."""
    out = bytearray()
    depth = 0
    index = start
    while index < len(data):
        char = data[index]
        if char == _BACKSLASH:
            raw, index = _escape(data, index + 1)
            out += raw
            continue
        depth += (char == _OPEN) - (char == _CLOSE)
        if depth == 0:
            return bytes(out), index + 1
        if index > start:
            out.append(char)
        index += 1
    return bytes(out), len(data)


def parse_string_at(data: bytes, pos: int) -> tuple[bytes, int] | None:
    """Liest einen Literal- oder Hex-String an ``pos``; sonst ``None``."""
    head = data[pos : pos + 2]
    if head[:1] == b"(":
        return _literal(data, pos)
    if head[:1] == b"<" and head != b"<<":
        match = _HEX_STRING.match(data, pos)
        if match:
            digits = re.sub(rb"\s", b"", match.group(1))
            if len(digits) % 2:
                digits += b"0"
            return bytes.fromhex(digits.decode("ascii")), match.end()
    return None


def _key_regex(keys: tuple[str, ...]) -> re.Pattern[bytes]:
    names = b"|".join(re.escape(key.encode("ascii")) for key in keys)
    return re.compile(rb"/(" + names + rb")(?![A-Za-z0-9#_.\-])\s*")


def find_key_strings(data: bytes, keys: tuple[str, ...]) -> list[KeyString]:
    """Alle Zeichenkettenwerte der angegebenen Schlüssel in einem Datenblock."""
    found: list[KeyString] = []
    for match in _key_regex(keys).finditer(data):
        parsed = parse_string_at(data, match.end())
        if parsed is None:
            continue
        raw, end = parsed
        key = match.group(1).decode("ascii")
        found.append(KeyString(key, decode_text(raw), match.end(), end))
    return found


def find_key_references(data: bytes, key: str) -> list[int]:
    """Objektnummern indirekter Werte eines Schlüssels (z. B. ``/JS 12 0 R``)."""
    regex = re.compile(rb"/" + re.escape(key.encode("ascii")) + rb"\s+(\d+)\s+\d+\s+R\b")
    return [int(match.group(1)) for match in regex.finditer(data)]


def blank_strings(data: bytes, spans: list[tuple[int, int]]) -> bytes:
    """Ersetzt die angegebenen String-Bereiche durch einen leeren String ``()``."""
    result = data
    for start, end in sorted(spans, reverse=True):
        result = result[:start] + b"()" + result[end:]
    return result


def pdf_text_string(text: str) -> str:
    """Kodiert einen Text als PDF-Hex-String in UTF-16BE mit BOM."""
    return "<FEFF" + text.encode("utf-16-be").hex().upper() + ">"
