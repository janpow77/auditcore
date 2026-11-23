"""Anwendung einer bestätigten Auswahl: schwärzen, bereinigen, nachprüfen."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from auditcore_pdf.redaction.common import RedactionError, RedactionStaleError
from auditcore_pdf.redaction.criteria import Criteria
from auditcore_pdf.redaction.expectation import _Expectation, _FullySelected
from auditcore_pdf.redaction.groups import _text_groups
from auditcore_pdf.redaction.layers import _restore_layers, _reveal_layers, _ViewTransform
from auditcore_pdf.redaction.ner_rules import NerFn
from auditcore_pdf.redaction.plan import Candidate, Plan, open_document
from auditcore_pdf.redaction.redact_pages import (
    _drop_xfa,
    _page_boxes,
    _redact_pages,
    _remove_hidden_candidates,
)
from auditcore_pdf.redaction.scan import build_plan
from auditcore_pdf.redaction.scrub import _sanitize, _scrub_strings
from auditcore_pdf.redaction.selection import ApplyReport, Selection
from auditcore_pdf.redaction.verify import _verify


def _chosen_candidates(plan: Plan, selection: Selection) -> list[Candidate]:
    """Die ausgewählten Fundstellen; fail-closed bei veralteter Auswahl."""
    by_id = {c.id: c for c in plan.candidates}
    unknown = selection.selected - by_id.keys()
    if unknown:
        raise RedactionStaleError(
            f"{len(unknown)} ausgewählte Fundstelle(n) passen nicht mehr zur Datei. "
            "Bitte neu suchen."
        )
    chosen = [by_id[i] for i in sorted(selection.selected)]
    if not chosen and not selection.areas and not selection.sanitize:
        raise RedactionError("Keine Fundstelle und kein Bereich ausgewählt")
    page_count = len(plan.pages)
    for area in selection.areas:
        if not 1 <= area.page <= page_count:
            raise RedactionError(f"Bereich auf Seite {area.page}: Seite gibt es nicht")
    return chosen


@dataclass
class _Prepared:
    """Was vor dem Schwärzen aus dem unveränderten Dokument feststeht."""

    transforms: list[_ViewTransform]
    before: dict[str, str]
    limits: dict[tuple[str, str], int]
    originals: dict[tuple[str, str], set[str]]
    all_keys: set[str]


def _prepare(data: bytes, chosen: list[Candidate], selection: Selection) -> _Prepared:
    """Erwartung für die Nachprüfung, je Seite und für versteckte Ablagen."""
    doc = open_document(data)
    try:
        transforms = [_ViewTransform(page) for page in doc]  # vor dem Aufdecken der CropBox
        before, pts = _text_groups(doc)
        expect = _Expectation(pts)
        expect.add_candidates(chosen)
        for area in selection.areas:
            expect.add_area(area.page, transforms[area.page - 1].from_view(list(area.box)))
    finally:
        doc.close()
    limits = expect.limits(before)
    return _Prepared(transforms, before, limits, expect.originals, expect.all_keys())


@dataclass
class _Redacted:
    out: bytes
    hidden_removed: int
    sanitized: list[str]


def _redact(
    data: bytes, chosen: list[Candidate], selection: Selection, prep: _Prepared
) -> _Redacted:
    doc = open_document(data)
    try:
        layers = _reveal_layers(doc)
        hidden = [c for c in chosen if c.kind == "hidden"]
        _remove_hidden_candidates(doc, hidden)
        page_boxes = _page_boxes(chosen, selection.areas, prep.transforms)
        removed_annots = _redact_pages(doc, page_boxes)
        fully_selected = _FullySelected(prep.before, prep.limits)
        replaced = _scrub_strings(doc, prep.all_keys, fully_selected)
        replaced += _drop_xfa(doc)
        sanitized = _sanitize(doc) if selection.sanitize else []
        _restore_layers(doc, layers)
        out = doc.tobytes(garbage=4, deflate=True)
    finally:
        doc.close()
    return _Redacted(out, len(hidden) + replaced + removed_annots, sanitized)


def _report(
    plan: Plan, chosen: list[Candidate], selection: Selection, result: _Redacted
) -> ApplyReport:
    by_source: dict[str, int] = {}
    for c in chosen:
        by_source[c.source] = by_source.get(c.source, 0) + 1
    deselected = [c for c in plan.candidates if c.id not in selection.selected]
    return ApplyReport(
        redactions=sum(1 for c in chosen if c.kind == "text"),
        areas=len(selection.areas),
        hidden_removed=result.hidden_removed,
        by_source=by_source,
        pages=sorted({c.page for c in chosen if c.page} | {a.page for a in selection.areas}),
        sanitized=result.sanitized,
        deselected=len(deselected),
    )


def apply_plan(
    data: bytes, selection: Selection, ner: NerFn | None = None
) -> tuple[bytes, ApplyReport]:
    """Genau die bestätigte Auswahl schwärzen und das Ergebnis nachprüfen."""
    digest = hashlib.sha256(data).hexdigest()
    if selection.sha256 != digest:
        raise RedactionStaleError(
            "Der Plan gehört zu einer anderen Datei. Bitte Fundstellen neu suchen."
        )
    plan = build_plan(data, selection.criteria, ner)
    chosen = _chosen_candidates(plan, selection)
    prep = _prepare(data, chosen, selection)
    result = _redact(data, chosen, selection, prep)
    _verify(result.out, selection, prep.limits, prep.originals)
    return result.out, _report(plan, chosen, selection, result)


def redact_all(
    data: bytes,
    criteria: Criteria,
    ner: NerFn | None = None,
    sanitize: bool = True,
) -> tuple[bytes, ApplyReport, Plan]:
    """Alle Fundstellen schwärzen (Programmschnittstelle ohne Vorschau)."""
    plan = build_plan(data, criteria, ner)
    selection = Selection(
        plan.sha256, criteria, frozenset(c.id for c in plan.candidates), (), sanitize
    )
    if not plan.candidates and not sanitize:
        return data, ApplyReport(0, 0, 0, {}, [], [], 0), plan
    out, report = apply_plan(data, selection, ner)
    return out, report, plan
