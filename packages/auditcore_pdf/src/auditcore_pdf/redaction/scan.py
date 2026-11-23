"""Plan erstellen: Seitentext, KI-Namen und versteckte Ablagen durchsuchen."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, TypeAlias

from auditcore_pdf.redaction.common import (
    _SOFT,
    NER_PATTERN_ID,
    RedactionError,
    _candidate_id,
    _norm,
)
from auditcore_pdf.redaction.criteria import Criteria, _matches, _Rule, _rules
from auditcore_pdf.redaction.hidden import _cleanup_info, _scan_hidden
from auditcore_pdf.redaction.layers import _expose_full_page, _reveal_layers, _ViewTransform
from auditcore_pdf.redaction.ner_document import _ner_document
from auditcore_pdf.redaction.ner_rules import NerFn
from auditcore_pdf.redaction.page_text import _dehyphenated, _page_text, _PageText, _span_rects
from auditcore_pdf.redaction.plan import Candidate, PageInfo, Plan, open_document

if TYPE_CHECKING:
    from pymupdf import Page, Rect

#: KI-Spanne auf dem Seitentext: (Anfang, Ende, Quelle)
NerSpan: TypeAlias = tuple[int, int, str]


def _resolve_overlaps(cands: list[Candidate]) -> list[Candidate]:
    """Überlappende Fundstellen einer Seite: Die längere gewinnt, bei gleicher
    Länge die mit höherer Priorität (Begriffe vor Mustern vor KI).

    Begriffe weichen nur anderen Begriffen. Ein eigener Begriff in einer
    E-Mail-Adresse oder einem KI-Namen bleibt als eigene Fundstelle stehen,
    damit er nicht unbemerkt lesbar bleibt, wenn die längere Fundstelle
    abgewählt wird.
    """
    ordered = sorted(cands, key=lambda c: (-(c.end - c.start), c.priority, c.start))
    kept: list[Candidate] = []
    taken_all: list[tuple[int, int]] = []
    taken_terms: list[tuple[int, int]] = []
    for c in ordered:
        is_term = c.source.startswith("begriff:")
        blockers = taken_terms if is_term else taken_all
        if any(c.start < e and c.end > s for s, e in blockers):
            continue
        kept.append(c)
        taken_all.append((c.start, c.end))
        if is_term:
            taken_terms.append((c.start, c.end))
    return sorted(kept, key=lambda c: c.start)


class _PageScanner:
    """Sammelt die Fundstellen einer Seite als Kandidaten mit Rechtecken."""

    def __init__(self, pno: int, pt: _PageText, transform: _ViewTransform):
        self.pno = pno
        self.pt = pt
        self.transform = transform
        self.found: list[Candidate] = []

    def add(
        self, source: str, start: int, end: int, priority: int, indices: list[int] | None = None
    ) -> None:
        pt = self.pt
        idx = indices if indices is not None else list(range(start, end))
        text = "".join(pt.text[i] for i in idx).replace(_SOFT, " ").strip()
        rects = _span_rects(pt, start, end, idx)
        if not rects or not text:
            return
        views = [self.transform.to_view(r) for r in rects]
        outside = all(o for _, o in views)
        self.found.append(
            Candidate(
                id=_candidate_id(self.pno, source, start, end, _norm(text)),
                kind="text",
                source=source,
                text=" ".join(text.split()),
                page=self.pno + 1,
                rects=[[round(v, 2) for v in r] for r in rects],
                view_rects=[v for v, _ in views],
                outside_view=outside,
                location="außerhalb des sichtbaren Bereichs" if outside else "Seitentext",
                start=start,
                end=end,
                priority=priority,
            )
        )

    def add_rule(self, prio: int, rule: _Rule, dehyph: tuple[str, list[int]] | None) -> None:
        for s, e in _matches(rule, self.pt.text):
            self.add(rule.source, s, e, prio)
        if not (rule.is_term and dehyph):
            return
        alt_text, mapping = dehyph
        for s, e in _matches(rule, alt_text):
            orig = mapping[s:e]
            # Nur Treffer, die tatsächlich über einen Trennstrich laufen
            if orig[-1] - orig[0] + 1 == len(orig):
                continue
            full = list(range(orig[0], orig[-1] + 1))
            self.add(rule.source, orig[0], orig[-1] + 1, prio, full)


def _scan_page_text(
    pno: int,
    pt: _PageText,
    rules: list[_Rule],
    transform: _ViewTransform,
    ner_spans: list[NerSpan] | None,
) -> list[Candidate]:
    scanner = _PageScanner(pno, pt, transform)
    dehyph = _dehyphenated(pt)
    for prio, rule in enumerate(rules):
        scanner.add_rule(prio, rule, dehyph)
    for s, e, source in ner_spans or []:
        scanner.add(source, s, e, len(rules) + (1 if source == NER_PATTERN_ID else 2))
    return _resolve_overlaps(scanner.found)


def _page_info(page: Page, rect: Rect, pt: _PageText) -> PageInfo:
    """Seitenangaben; ``rect`` ist die sichtbare Seite vor dem Aufdecken der CropBox."""
    info = PageInfo(page.number + 1, rect.width, rect.height, page.rotation, False, False)
    info.has_text = any(r is not None for r in pt.rects)
    if not info.has_text:
        info.image_only = bool(page.get_images(full=False)) or bool(page.get_drawings()[:1])
    return info


def build_plan(data: bytes, criteria: Criteria, ner: NerFn | None = None) -> Plan:
    """Alle Fundstellen ermitteln — Grundlage für Vorschau und Anwendung."""
    if NER_PATTERN_ID in criteria.patterns and ner is None:
        raise RedactionError("KI-Namenserkennung nicht verfügbar (spaCy-Modell fehlt)")
    rules = _rules(criteria)
    # Mit KI braucht die Erkennung alle Seiten zugleich (Nachsuche über das
    # ganze Dokument); ohne KI wird jede Seite sofort durchsucht.
    use_ner = ner if NER_PATTERN_ID in criteria.patterns else None
    doc = open_document(data)
    try:
        _reveal_layers(doc)  # Text ausgeblendeter Ebenen mitsuchen; doc wird verworfen
        pages: list[PageInfo] = []
        candidates: list[Candidate] = []
        texts: list[tuple[_PageText, _ViewTransform]] = []
        for page in doc:
            transform = _ViewTransform(page)
            visible = page.rect
            _expose_full_page(page)
            pt = _page_text(page)
            pages.append(_page_info(page, visible, pt))
            if use_ner is not None:
                texts.append((pt, transform))
            else:
                candidates.extend(_scan_page_text(page.number, pt, rules, transform, None))
        if use_ner is not None:
            ner_spans = _ner_document([pt for pt, _ in texts], use_ner)
            for pno, ((pt, transform), spans) in enumerate(zip(texts, ner_spans, strict=True)):
                candidates.extend(_scan_page_text(pno, pt, rules, transform, spans))
        candidates.extend(_scan_hidden(doc, rules))
        cleanup = _cleanup_info(doc)
    finally:
        doc.close()
    return Plan(hashlib.sha256(data).hexdigest(), criteria, pages, candidates, cleanup)
