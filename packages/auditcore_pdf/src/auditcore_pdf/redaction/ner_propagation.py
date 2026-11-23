"""Nachsuche belegter Namen im ganzen Dokument, mit Grenze und Mustersatz.

Nachgesucht werden die Bestandteile belegter Namen (Quelle
``NER_PROPAGATED_ID``), etwa ein allein stehender Nachname. Belegt ist
ein Name, den die KI aus mindestens zwei Bestandteilen erkennt oder den
die Listenform bestätigt. Nicht nachgesucht wird, wo das Wort als
Substantiv oder Datum steht (``_is_name_noun``). Steht der Beleg nicht
in einem Satz (``_has_context``), sondern in einer Zelle oder Kopfzeile,
muss die KI ihn im Mustersatz ``_CONFIRM_FRAME`` als Person bestätigen;
sonst gilt die Obergrenze ``_PROPAGATION_FLOOR``/``_PROPAGATION_FACTOR``.
Belege über Zellgrenzen hinweg bekommen auch mit Bestätigung nur die
höhere Untergrenze ``_PROPAGATION_FLOOR_CONFIRMED``, ebenso Zellbelege,
deren Name der Mustersatz nur zum Teil bestätigt. Spaltenköpfe aus
``_TABLE_WORDS`` werden aus Zellbelegen nie ohne Anrede nachgesucht. Über
der Grenze bleiben nur Fundstellen mit Anrede oder Titel davor. Der
Mustersatz läuft nur für Wörter, die sonst an der Grenze scheitern.
"""

from __future__ import annotations

import bisect
import re
from dataclasses import dataclass, field

from auditcore_pdf.redaction.common import _HARD, NER_PROPAGATED_ID
from auditcore_pdf.redaction.ner_calls import _ner_results
from auditcore_pdf.redaction.ner_rules import (
    _CONFIRM_FRAME,
    _CONFIRM_START,
    _CONTACT_WORDS,
    _PROPAGATION_FACTOR,
    _PROPAGATION_FLOOR,
    _PROPAGATION_FLOOR_CONFIRMED,
    _SALUTATION_BEFORE,
    _SPAN_PART,
    _TABLE_WORDS,
    _WORD_RUN,
    NerFn,
)
from auditcore_pdf.redaction.ner_text import _is_name_noun, _merge_spans, _name_tokens
from auditcore_pdf.redaction.page_text import _PageText

#: Fundstelle eines nachgesuchten Worts: (Seite, Anfang, Ende, mit Anrede)
Hit = tuple[int, int, int, bool]


def _multi_part(text: str) -> bool:
    return len(_SPAN_PART.findall(text)) >= 2


@dataclass
class _Evidence:
    """Belegte Namenswörter, aus denen die Nachsuche schöpft."""

    sure: set[str] = field(default_factory=set)  # ohne Grenze nachgesucht
    loose: set[str] = field(default_factory=set)  # Grenze _PROPAGATION_FLOOR_CONFIRMED
    cell_spans: dict[str, set[str]] = field(default_factory=dict)  # Zellbeleg → Wörter
    cross_spans: dict[str, set[str]] = field(default_factory=dict)  # Beleg über Zellgrenzen

    def from_cell(self, text: str, into: dict[str, set[str]]) -> None:
        tokens = _name_tokens(text)
        if tokens:
            words = [
                w
                for w in text.replace(_HARD, " ").split()
                if not any(p.strip(".,;:") in _CONTACT_WORDS for p in re.split(r"[/-]", w))
            ]
            into.setdefault(" ".join(words), set()).update(tokens)

    def strong(self) -> set[str]:
        spans = (self.cell_spans, self.cross_spans)
        return self.sure | {t for group in spans for tokens in group.values() for t in tokens}


class _Propagation:
    """Wo stehen die belegten Wörter außerhalb der direkten Treffer?"""

    def __init__(
        self, pts: list[_PageText], direct_pages: list[list[tuple[int, int]]], ev: _Evidence
    ):
        self.ev = ev
        self.strong = ev.strong()
        self.direct_texts: dict[str, set[str]] = {}
        self.found: dict[str, list[Hit]] = {}
        for pno, (pt, direct) in enumerate(zip(pts, direct_pages, strict=True)):
            self._collect_direct(pt, direct)
            self._collect_hits(pno, pt, direct)

    def _collect_direct(self, pt: _PageText, direct: list[tuple[int, int]]) -> None:
        for x, y in direct:
            for word in _WORD_RUN.findall(pt.text, x, y):
                if word in self.strong:
                    self.direct_texts.setdefault(word, set()).add(pt.text[x:y])

    def _collect_hits(self, pno: int, pt: _PageText, direct: list[tuple[int, int]]) -> None:
        merged = _merge_spans(direct)
        starts = [a for a, _ in merged]
        for m in _WORD_RUN.finditer(pt.text):
            word = m.group()
            if word not in self.strong:
                continue
            a, b = m.span()
            i = bisect.bisect_right(starts, a) - 1
            if (i >= 0 and merged[i][1] > a) or (i + 1 < len(merged) and merged[i + 1][0] < b):
                continue
            if not _is_name_noun(pt.text, a, b):
                addressed = bool(_SALUTATION_BEFORE.search(pt.text[max(0, a - 30) : a]))
                self.found.setdefault(word, []).append((pno, a, b, addressed))

    def _limit(self, word: str, floor: int) -> int:
        return max(floor, _PROPAGATION_FACTOR * len(self.direct_texts.get(word, ())))

    def capped(self, word: str) -> bool:
        if word in self.ev.sure:
            return False
        if word in _TABLE_WORDS:
            return True
        floor = _PROPAGATION_FLOOR_CONFIRMED if word in self.ev.loose else _PROPAGATION_FLOOR
        return len(self.found[word]) > self._limit(word, floor)

    def probes(self) -> list[tuple[str, int]]:
        """Zellbelege für den Mustersatz: (Text, 0 = Zelle | 1 = über Zellgrenzen)."""
        # Den Mustersatz braucht nur, wer sonst an der Grenze scheitert;
        # Spaltenköpfe hebt er nicht über die Grenze.
        found = self.found
        over = {
            w
            for w in found
            if w not in _TABLE_WORDS and self.capped(w) and not all(h[3] for h in found[w])
        }
        # Über Zellgrenzen hilft die Bestätigung nur bis _PROPAGATION_FLOOR_CONFIRMED.
        loose_limit = {w: self._limit(w, _PROPAGATION_FLOOR_CONFIRMED) for w in over}
        groups = (self.ev.cell_spans, self.ev.cross_spans)
        return sorted(
            (t, k)
            for k, spans in enumerate(groups)
            for t, tokens in spans.items()
            if _multi_part(t)
            and any(w in over and (not k or len(found[w]) <= loose_limit[w]) for w in tokens)
        )

    def confirm(self, ner: NerFn) -> None:
        probes = self.probes()
        frames = [_CONFIRM_FRAME.format(t) for t, _k in probes]
        for (text, k), spans in zip(probes, _ner_results(ner, frames), strict=True):
            tokens = (self.ev.cross_spans if k else self.ev.cell_spans)[text]
            confirmed = _confirmed_tokens(text, tokens, spans)
            # Bestätigt die KI nur einen Teil („Auftragnehmer Thomas Berger“ →
            # „Thomas Berger“), gelten dessen Wörter mit der höheren
            # Untergrenze; ohne Grenze nur, wenn die bestätigten Teile alle
            # Wörter des Zellbelegs decken.
            target = self.ev.sure if not k and confirmed == tokens else self.ev.loose
            target.update(confirmed - _TABLE_WORDS)


def _confirmed_tokens(text: str, tokens: set[str], spans: list[tuple[int, int]]) -> set[str]:
    """Wörter des Belegs, die die KI im Mustersatz in Namen aus zwei Teilen meldet."""
    end = _CONFIRM_START + len(text)
    confirmed: set[str] = set()
    for a, b in spans:
        a, b = max(a, _CONFIRM_START), min(b, end)
        piece = text[a - _CONFIRM_START : b - _CONFIRM_START]
        if b > a and _multi_part(piece):
            confirmed.update(set(_name_tokens(piece)) & tokens)
    return confirmed


def _propagate(
    pts: list[_PageText],
    direct_pages: list[list[tuple[int, int]]],
    ev: _Evidence,
    ner: NerFn,
    out: list[list[tuple[int, int, str]]],
) -> list[list[tuple[int, int, str]]]:
    """Ergänzt ``out`` um die nachgesuchten Fundstellen; Rückgabe je Seite sortiert."""
    prop = _Propagation(pts, direct_pages, ev)
    prop.confirm(ner)
    for word, hits in prop.found.items():
        limited = prop.capped(word)
        for pno, a, b, addressed in hits:
            if addressed or not limited:
                out[pno].append((a, b, NER_PROPAGATED_ID))
    return [sorted(spans) for spans in out]
