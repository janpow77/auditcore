"""Textabschnitte, Zusammenhang und Namensbestandteile für die KI-Namenserkennung."""

from __future__ import annotations

import re

from auditcore_pdf.redaction.common import _HARD
from auditcore_pdf.redaction.ner_rules import (
    _ARTICLE_BEFORE,
    _CONTACT_WORDS,
    _DAY_BEFORE,
    _MONTH_ABBREVIATIONS,
    _NAME_EDGE,
    _NAME_PREFIX_BEFORE,
    _NO_CONTEXT,
    _NOT_NAMES,
    _SHORT_SEGMENT_WORDS,
    _SPAN_PART,
    _TABLE_WORDS,
    _TITLE_IN_SPAN,
    _TITLES,
    _YEAR_AFTER,
)
from auditcore_pdf.redaction.page_text import _PageText


def _hard_parts(text: str, start: int, end: int) -> list[tuple[int, int]]:
    """Eine KI-Fundstelle an harten Grenzen (Zelle, Spalte, Absatz) teilen.

    spaCy fasst in Tabellen Namen aus benachbarten Zellen zu einem zusammen
    („Jan Reiter Stahl“). Über einen gewöhnlichen Zeilenumbruch im Fließtext
    darf ein Name dagegen laufen.
    """
    parts: list[tuple[int, int]] = []
    pos, end = max(0, start), min(end, len(text))
    while pos < end:
        stop = text.find(_HARD, pos, end)
        stop = end if stop < 0 else stop
        a, b = pos, stop
        while a < b and text[a] in _NAME_EDGE:
            a += 1
        while b > a and text[b - 1] in _NAME_EDGE:
            b -= 1
        if sum(ch.isalpha() for ch in text[a:b]) >= 2:
            parts.append((a, b))
        pos = stop + 1
    return parts


def _short_segments(text: str) -> list[tuple[int, int]]:
    """Kurze Abschnitte zwischen harten Grenzen, ohne Leerraum und Titel am Anfang."""
    segments: list[tuple[int, int]] = []
    pos = 0
    while pos <= len(text):
        stop = text.find(_HARD, pos)
        stop = len(text) if stop < 0 else stop
        a, b = pos, stop
        while a < b and text[a].isspace():
            a += 1
        while b > a and text[b - 1].isspace():
            b -= 1
        title = _TITLES.match(text, a, b)
        if title:
            a = title.end()
        if b > a and len(text[a:b].split()) <= _SHORT_SEGMENT_WORDS:
            segments.append((a, b))
        pos = stop + 1
    return segments


def _line_segments(pt: _PageText) -> list[tuple[int, int]]:
    """Zeichenbereiche der einzelnen Textzeilen, ohne Leerraum am Rand."""
    segments: list[tuple[int, int]] = []
    i, n = 0, len(pt.lines)
    while i < n:
        line = pt.lines[i]
        j = i
        while j < n and pt.lines[j] == line:
            j += 1
        if line >= 0:
            a, b = i, j
            while a < b and pt.text[a].isspace():
                a += 1
            while b > a and pt.text[b - 1].isspace():
                b -= 1
            if b > a:
                segments.append((a, b))
        i = j
    return segments


def _name_tokens(text: str) -> list[str]:
    """Wörter eines Namens, die im Dokument nachgesucht werden dürfen."""
    return [
        t
        for t in re.findall(r"[^\W\d_]+(?:-[^\W\d_]+)*", text)
        if len(t) >= 3
        and all(p[:1].isupper() and p[1:].islower() for p in t.split("-"))
        and t not in _NOT_NAMES
        and not any(p in _CONTACT_WORDS for p in t.split("-"))
    ]


def _free_tokens(text: str) -> list[str] | None:
    """Wörter eines Satz- oder Listenbelegs, die ohne Grenze nachgesucht
    werden. Besteht der Beleg nur aus Spaltenköpfen („Summe Netto nach
    Skonto“, „Netto, Brutto“), ist er kein Name: ``None``, er gilt dann wie
    ein Zellbeleg. Neben einem anderen Wort („Petra Preis“) oder nach Anrede
    oder Titel („Dr. Menge“) ist der Spaltenkopf ein Nachname."""
    tokens = _name_tokens(text)
    if any(t not in _TABLE_WORDS for t in tokens) or (tokens and _TITLE_IN_SPAN.search(text)):
        return tokens
    return None


def _is_name_noun(text: str, start: int, end: int) -> bool:
    """Steht das nachgesuchte Wort hier als Substantiv oder Datum statt als Name?"""
    before = text[max(0, start - 30) : start]
    if _ARTICLE_BEFORE.search(before) and not _NAME_PREFIX_BEFORE.search(before):
        return True
    if text[start:end] in _MONTH_ABBREVIATIONS and text[end : end + 1] == ".":
        return bool(
            _DAY_BEFORE.search(text[max(0, start - 6) : start]) or _YEAR_AFTER.match(text, end)
        )
    return False


def _has_context(pt: _PageText, start: int, end: int) -> bool:
    """Steht der Treffer in einem Satz? Verlangt wird ein kleingeschriebenes
    Wort in derselben Zelle, in der Zeile des Treffers oder einer Zeile direkt
    davor oder danach („Projektleiter ist Thomas Berger“, auch umbrochen).
    Weiter entfernte Zeilen desselben Blocks zählen nicht: Ein Formular, das
    MuPDF als einen Block liest, macht sonst aus einem Etikett oben
    („Kundennummer Belegart Auftraggeber“) einen Satz.
    Eine Kopfzeile aus Großwörtern („Ort Telefon Begünstigter Betrag“) liest
    MuPDF bei engen Spalten als eine Zeile; sie ist kein Satz. Wörter aus
    ``_NO_CONTEXT`` („in EUR“, „je Stück“, „inkl. USt“) stehen auch in
    Kopfzeilen und zählen nicht."""
    text = pt.text
    left = text.rfind(_HARD, 0, start) + 1
    right = text.find(_HARD, end)
    right = len(text) if right < 0 else right
    row = (lambda n: pt.rows[n]) if pt.rows else (lambda n: n)
    hit_lines = [row(n) for n in pt.lines[start:end] if n >= 0]
    first, last = (min(hit_lines) - 1, max(hit_lines) + 1) if hit_lines else (-1, -1)
    return any(
        m.group()[0].islower()
        and m.group() not in _NO_CONTEXT
        and (
            not hit_lines
            or (pt.lines[m.start()] >= 0 and first <= row(pt.lines[m.start()]) <= last)
        )
        for lo, hi in ((left, start), (end, right))
        for m in _SPAN_PART.finditer(text, lo, hi)
    )


def _merge_spans(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for a, b in sorted(spans):
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    return merged
