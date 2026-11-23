"""Seitentext mit Zeichenpositionen: Zeilen, Umbrüche, Silbentrennung."""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypeAlias, TypedDict

from auditcore_pdf.engine import fitz
from auditcore_pdf.redaction.common import _CHAR_MAP, _HARD, _HYPHENS, _INVISIBLE, _SOFT

if TYPE_CHECKING:
    from pymupdf import Page, Rect

#: Zeichenrechteck ``(x0, y0, x1, y1)``
CharRect: TypeAlias = tuple[float, float, float, float]


class _RawChar(TypedDict):
    c: str
    bbox: CharRect


class _RawSpan(TypedDict, total=False):
    chars: list[_RawChar]


class _RawLine(TypedDict, total=False):
    bbox: CharRect
    spans: list[_RawSpan]


@dataclass
class _PageText:
    text: str
    rects: list[CharRect | None]  # Zeichenrechteck oder None
    lines: list[int]  # Zeilennummer je Zeichen, -1 für Trenner
    hyphen_breaks: list[int]  # Index des Trennstrichs vor einem weichen Umbruch
    # Sichtbare Zeile je Zeilennummer: Fragmente derselben Grundlinie (großer
    # Wortabstand im Blocksatz oder in Formularen) teilen sich eine.
    rows: list[int] = field(default_factory=list)


def _break_kind(prev: tuple[float, ...], nxt: tuple[float, ...]) -> str | None:
    """Wie schließt die Zeile ``nxt`` an ``prev`` an?

    ``"below"``: nächste Zeile desselben Absatzes. ``"same"``: Fortsetzung auf
    derselben Grundlinie; MuPDF trennt dort bei großem Wortabstand, etwa im
    Blocksatz, in Tabellen oder in erzeugten Formularen. ``None``: harter
    Wechsel (Spalte, Absatz).
    """
    height = max(1.0, prev[3] - prev[1])
    below = prev[1] + 0.5 * height <= nxt[1] <= prev[3] + 1.5 * height
    overlap = nxt[0] < prev[2] and nxt[2] > prev[0]
    if below and overlap:
        return "below"
    if abs(nxt[3] - prev[3]) <= 0.3 * height and -0.5 * height <= nxt[0] - prev[2] <= 3 * height:
        return "same"
    return None


def _text_flags() -> int:
    # Ohne MediaBox-Beschnitt: Text außerhalb der Seite steht trotzdem in der
    # Datei. Ohne Ligaturen: „ﬁ“ wird zu „f“ + „i“ und damit auffindbar.
    flags: int = (
        fitz.TEXTFLAGS_RAWDICT
        & ~fitz.TEXT_PRESERVE_IMAGES
        & ~fitz.TEXT_MEDIABOX_CLIP
        & ~fitz.TEXT_PRESERVE_LIGATURES
    )
    return flags


class _PageTextBuilder:
    """Setzt den Suchtext einer Seite Zeile für Zeile aus den Glyphen zusammen."""

    def __init__(self) -> None:
        self.chars: list[str] = []
        self.rects: list[CharRect | None] = []
        self.lines: list[int] = []
        self.hyphen_breaks: list[int] = []
        self.rows: list[int] = []
        self.prev_bbox: CharRect | None = None
        self.line_no = 0

    def push(self, char: str, rect: CharRect | None, line: int) -> None:
        self.chars.append(char)
        self.rects.append(rect)
        self.lines.append(line)

    def add_line(self, line: _RawLine) -> None:
        glyphs = _visible_glyphs(line)
        if not glyphs:
            return
        x0, y0, x1, y1 = line["bbox"]
        bbox = (x0, y0, x1, y1)
        kind = self._separate(self.prev_bbox, bbox) if self.prev_bbox is not None else None
        for g in glyphs:
            self._add_glyph(g)
        if not self.rows:
            self.rows.append(0)
        else:
            self.rows.append(self.rows[-1] if kind == "same" else self.rows[-1] + 1)
        self.line_no += 1
        self.prev_bbox = bbox

    def _separate(self, prev: CharRect, bbox: CharRect) -> str | None:
        kind = _break_kind(prev, bbox)
        last = self.chars[-1] if self.chars else ""
        if kind == "below" and last in _HYPHENS:
            self.hyphen_breaks.append(len(self.chars) - 1)
        if kind is None:
            self.push(_HARD, None, -1)
        elif not last.isspace():
            self.push(_SOFT, None, -1)
        return kind

    def _add_glyph(self, glyph: _RawChar) -> None:
        c = _CHAR_MAP.get(glyph["c"], glyph["c"])
        x0, y0, x1, y1 = glyph["bbox"]
        box = (x0, y0, x1, y1)
        if c.isspace():
            self.push(" ", None, self.line_no)
        elif unicodedata.combining(c):
            self._combine(c, box)
        else:
            norm = unicodedata.normalize("NFKC", c) or c
            if len(norm) == 1:
                self.push(norm, box, self.line_no)
            else:
                self._split(norm, box)

    def _combine(self, mark: str, box: CharRect) -> None:
        """Zerlegter Umlaut (NFD): mit dem Grundbuchstaben vereinen."""
        prev_rect = self.rects[-1] if self.rects else None
        if prev_rect is None or self.lines[-1] != self.line_no:
            return
        composed = unicodedata.normalize("NFC", self.chars[-1] + mark)
        if len(composed) == 1:
            self.chars[-1] = composed
            self.rects[-1] = (
                min(prev_rect[0], box[0]),
                min(prev_rect[1], box[1]),
                max(prev_rect[2], box[2]),
                max(prev_rect[3], box[3]),
            )

    def _split(self, norm: str, box: CharRect) -> None:
        """Kompatibilitätszeichen wie „ﬁ“ oder „½“: Breite aufteilen."""
        step = (box[2] - box[0]) / len(norm)
        for k, part in enumerate(norm):
            if part.isspace():
                self.push(" ", None, self.line_no)
            else:
                rect = (box[0] + k * step, box[1], box[0] + (k + 1) * step, box[3])
                self.push(part, rect, self.line_no)

    def result(self) -> _PageText:
        text = "".join(self.chars)
        return _PageText(text, self.rects, self.lines, self.hyphen_breaks, self.rows)


def _visible_glyphs(line: _RawLine) -> list[_RawChar]:
    """Unsichtbare Zeichen entfallen; ein weiches Trennzeichen zählt nur am Zeilenende."""
    glyphs = [c for span in line.get("spans", []) for c in span.get("chars", [])]
    last_index = len(glyphs) - 1
    return [
        g
        for k, g in enumerate(glyphs)
        if g["c"] not in _INVISIBLE and (g["c"] != "\u00ad" or k == last_index)
    ]


def _page_text(page: Page) -> _PageText:
    builder = _PageTextBuilder()
    raw = page.get_text("rawdict", flags=_text_flags(), clip=fitz.INFINITE_RECT())
    for block in raw.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            builder.add_line(line)
    return builder.result()


def _dehyphenated(pt: _PageText) -> tuple[str, list[int]] | None:
    """Suchtext ohne Trennstrich + Umbruch; Abbildung auf die Originalindizes."""
    if not pt.hyphen_breaks:
        return None
    drop: set[int] = set()
    for h in pt.hyphen_breaks:
        drop.add(h)
        if h + 1 < len(pt.text) and pt.text[h + 1] == _SOFT:
            drop.add(h + 1)
    keep = [i for i in range(len(pt.text)) if i not in drop]
    return "".join(pt.text[i] for i in keep), keep


def _span_rects(
    pt: _PageText, start: int, end: int, indices: Iterable[int] | None = None
) -> list[Rect]:
    """Je Zeile ein Rechteck über die getroffenen Zeichen."""
    by_line: dict[int, list[float]] = {}
    for i in indices if indices is not None else range(start, end):
        rect = pt.rects[i]
        if rect is None:
            continue
        line = pt.lines[i]
        box = by_line.get(line)
        if box is None:
            by_line[line] = list(rect)
        else:
            box[0] = min(box[0], rect[0])
            box[1] = min(box[1], rect[1])
            box[2] = max(box[2], rect[2])
            box[3] = max(box[3], rect[3])
    return [fitz.Rect(by_line[k]) for k in sorted(by_line)]
