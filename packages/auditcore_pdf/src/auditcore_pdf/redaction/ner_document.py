"""KI-Namenserkennung über das ganze Dokument: Aufträge, direkte Treffer, Belege."""

from __future__ import annotations

from dataclasses import dataclass, field

from auditcore_pdf.redaction.common import _HARD, NER_PATTERN_ID
from auditcore_pdf.redaction.ner_calls import _ner_results
from auditcore_pdf.redaction.ner_propagation import _Evidence, _multi_part, _propagate
from auditcore_pdf.redaction.ner_rules import (
    _LIST_NAME,
    _NOT_NAMES,
    NerFn,
)
from auditcore_pdf.redaction.ner_text import (
    _free_tokens,
    _hard_parts,
    _has_context,
    _line_segments,
    _short_segments,
)
from auditcore_pdf.redaction.page_text import _PageText

Span = tuple[int, int]


@dataclass
class _PageJobs:
    """Aufträge einer Seite an die KI (Indizes in die gemeinsame Auftragsliste)."""

    full: int
    segments: list[tuple[int, int]] = field(default_factory=list)  # (Versatz, Auftrag)
    listed: list[tuple[int, int, int]] = field(default_factory=list)  # (Anfang, Ende, Auftrag)


class _JobList:
    """Alle Texte für einen einzigen KI-Aufruf; gleiche Abschnitte nur einmal."""

    def __init__(self) -> None:
        self.texts: list[str] = []
        self._segment_job: dict[str, int] = {}

    def add(self, text: str) -> int:
        self.texts.append(text)
        return len(self.texts) - 1

    def segment(self, text: str) -> int:
        if text not in self._segment_job:
            self._segment_job[text] = self.add(text)
        return self._segment_job[text]

    def page(self, pt: _PageText) -> _PageJobs:
        page = _PageJobs(self.add(pt.text.replace(_HARD, "\n")))
        for a, b in _short_segments(pt.text):
            page.segments.append((a, self.segment(pt.text[a:b])))
        for a, b in _line_segments(pt):
            m = _LIST_NAME.match(pt.text, a, b)
            if m and m.group("last") not in _NOT_NAMES and m.group("first") not in _NOT_NAMES:
                job = self.add(f"{m.group('first')} {m.group('last')}")
                page.listed.append((m.start("last"), m.end("first"), job))
        return page


class _DirectHits:
    """Direkte KI-Treffer einer Seite und die daraus folgenden Belege."""

    def __init__(self, pt: _PageText, evidence: _Evidence):
        self.pt = pt
        self.evidence = evidence
        self.direct: set[Span] = set()

    def full_text(self, spans: list[Span]) -> None:
        text, ev = self.pt.text, self.evidence
        for s, e in spans:
            s, e = max(0, s), min(e, len(text))
            if e <= s:
                continue
            parts = _hard_parts(text, s, e)
            self.direct.update(parts)
            for a, b in parts:
                if not _multi_part(text[a:b]):
                    continue
                free = _free_tokens(text[a:b]) if _has_context(self.pt, a, b) else None
                if free is not None:
                    ev.sure.update(free)
                else:
                    ev.from_cell(text[a:b], ev.cell_spans)
            # Über Zellgrenzen erkannt („Klaus / Wagner“ in getrennten
            # Spalten, „Jan / Reiter / Stahl“).
            if len(parts) > 1 and _multi_part(text[s:e]):
                ev.from_cell(text[s:e], ev.cross_spans)

    def segment(self, offset: int, length: int, spans: list[Span]) -> None:
        text, ev = self.pt.text, self.evidence
        for s, e in spans:
            s, e = max(0, s), min(e, length)
            for a, b in _hard_parts(text, offset + s, offset + e):
                self.direct.add((a, b))
                if _multi_part(text[a:b]):
                    ev.from_cell(text[a:b], ev.cell_spans)

    def listed(self, start: int, end: int, length: int, spans: list[Span]) -> None:
        if not any(a == 0 and b == length for a, b in spans):
            return
        self.direct.add((start, end))
        free = _free_tokens(self.pt.text[start:end])
        if free is None:
            self.evidence.from_cell(self.pt.text[start:end], self.evidence.cell_spans)
        else:
            self.evidence.sure.update(free)


def _direct_page(
    pt: _PageText, page: _PageJobs, jobs: list[str], results: list[list[Span]], ev: _Evidence
) -> list[Span]:
    hits = _DirectHits(pt, ev)
    hits.full_text(results[page.full])
    for offset, k in page.segments:
        hits.segment(offset, len(jobs[k]), results[k])
    for s, e, k in page.listed:
        hits.listed(s, e, len(jobs[k]), results[k])
    return sorted(hits.direct)


def _ner_document(pts: list[_PageText], ner: NerFn) -> list[list[tuple[int, int, str]]]:
    """KI-Namenserkennung über das ganze Dokument.

    Je Seite werden drei Quellen zusammengeführt:
    - der Seitentext im Zusammenhang (Namen über Zeilenumbrüche hinweg),
      geteilt an harten Grenzen;
    - jeder kurze Abschnitt für sich (Tabellenzellen, Listeneinträge),
      ohne Titel am Anfang; gleiche Abschnitte prüft die KI nur einmal;
    - die Listenform „Nachname, Vorname“, wenn die KI „Vorname Nachname“
      als Person erkennt.

    Alles, was die KI meldet, wird direkt übernommen: Ein übersehener Name
    wiegt schwerer als ein Fehltreffer, den die Vorschau abwählen kann.
    Die Nachsuche belegter Namen beschreibt :func:`_propagate`.

    Rückgabe: je Seite (start, ende, quelle).
    """
    jobs = _JobList()
    pages = [jobs.page(pt) for pt in pts]
    results = _ner_results(ner, jobs.texts)
    evidence = _Evidence()
    direct_pages = [
        _direct_page(pt, page, jobs.texts, results, evidence)
        for pt, page in zip(pts, pages, strict=True)
    ]
    out = [[(a, b, NER_PATTERN_ID) for a, b in direct] for direct in direct_pages]
    if not evidence.strong():
        return out
    return _propagate(pts, direct_pages, evidence, ner, out)
