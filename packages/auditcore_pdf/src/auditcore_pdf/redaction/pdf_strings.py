"""Zeichenketten in PDF-Objekten finden und dekodieren."""

from __future__ import annotations

import re
from collections.abc import Iterator


def _literal(text: str) -> re.Pattern[str]:
    return re.compile(r"\s+".join(re.escape(p) for p in text.split()), re.IGNORECASE)


_ESCAPES = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f"}


def _decode_pdf_bytes(raw: bytes) -> str:
    if raw[:2] == b"\xfe\xff":
        return raw[2:].decode("utf-16-be", errors="ignore")
    if raw[:3] == b"\xef\xbb\xbf":
        return raw[3:].decode("utf-8", errors="ignore")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="ignore")


def _decode_literal(body: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(body):
        c = body[i]
        if c != "\\":
            out.append(c)
            i += 1
            continue
        i += 1
        if i >= len(body):
            break
        e = body[i]
        if e in _ESCAPES:
            out.append(_ESCAPES[e])
        elif e in "01234567":
            j = i
            while j < len(body) and j < i + 3 and body[j] in "01234567":
                j += 1
            out.append(chr(int(body[i:j], 8) & 0xFF))
            i = j
            continue
        elif e in "\r\n":
            if e == "\r" and body[i + 1 : i + 2] == "\n":
                i += 1
        else:
            out.append(e)
        i += 1
    return _decode_pdf_bytes("".join(out).encode("latin-1", errors="replace"))


def _literal_end(src: str, i: int) -> int:
    """Ende der Literal-Zeichenkette, die bei ``i`` mit „(“ beginnt."""
    n = len(src)
    depth, j = 1, i + 1
    while j < n and depth:
        if src[j] == "\\":
            j += 2
            continue
        if src[j] == "(":
            depth += 1
        elif src[j] == ")":
            depth -= 1
        j += 1
    return j


def _hex_text(src: str, i: int, j: int) -> str | None:
    digits = "".join(src[i + 1 : j].split())
    if len(digits) % 2:
        digits += "0"
    try:
        return _decode_pdf_bytes(bytes.fromhex(digits))
    except ValueError:
        return None


def _pdf_strings(
    src: str, start: int = 0, only_at: int | None = None
) -> Iterator[tuple[int, int, str]]:
    """Zeichenketten im Quelltext eines PDF-Objekts: (Anfang, Ende, Text).

    ``src`` ist latin-1-dekodiert, ein Zeichen je Byte. Mit ``only_at`` wird
    nur die Zeichenkette gelesen, die genau dort beginnt."""
    i = start
    n = len(src)
    while i < n:
        c = src[i]
        if c == "(":
            j = _literal_end(src, i)
            yield i, j, _decode_literal(src[i + 1 : j - 1])
            i = j
        elif c == "<" and src[i + 1 : i + 2] != "<":
            j = src.find(">", i)
            if j < 0:
                return
            text = _hex_text(src, i, j)
            if text is not None:
                yield i, j + 1, text
            i = j + 1
        else:
            i += 2 if c == "<" else 1
        if only_at is not None:
            return
