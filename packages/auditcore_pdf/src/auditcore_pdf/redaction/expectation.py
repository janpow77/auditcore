"""Erwartung für die Nachprüfung: ausgewählte Texte, Lage und Grenzen je Gruppe."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from auditcore_pdf.redaction.common import HIDDEN_GROUP, _flat
from auditcore_pdf.redaction.groups import (
    _area_indices,
    _area_snippets,
    _flat_map,
    _inside_other,
    _limits,
    _occurrences,
    _page_group,
    _same_text,
)
from auditcore_pdf.redaction.page_text import _PageText
from auditcore_pdf.redaction.plan import Candidate

if TYPE_CHECKING:
    from pymupdf import Rect


class _Expectation:
    """Sammelt, was nach dem Schwärzen nicht mehr lesbar sein darf."""

    def __init__(self, pts: list[_PageText]):
        self.pts = pts
        self.selected_keys: dict[str, list[str]] = {}
        self.originals: dict[tuple[str, str], set[str]] = {}
        # Lage der ausgewählten Stellen je Seite. None heißt: Lage unsicher,
        # für diese Seite wird über die Texte gezählt (strenger, nie lockerer).
        self.masks: dict[int, set[int] | None] = {}

    def note(self, group: str, text: str) -> None:
        key = _flat(text)
        if key:
            self.selected_keys.setdefault(group, []).append(key)
            self.originals.setdefault((group, key), set()).add(text)

    def cover(self, pno: int, indices: Iterable[int], ok: bool = True) -> None:
        mask = self.masks.get(pno, set())
        if mask is None or not ok:
            self.masks[pno] = None
            return
        mask.update(indices)
        self.masks[pno] = mask

    def add_candidates(self, chosen: list[Candidate]) -> None:
        chosen_hidden = [c for c in chosen if c.kind != "text"]
        for c in chosen:
            if c.kind == "text":
                self._add_text(c)
            elif not _inside_other(c, chosen_hidden):
                self.note(HIDDEN_GROUP, c.text)

    def _add_text(self, c: Candidate) -> None:
        pts = self.pts
        self.note(_page_group(c.page), c.text)
        pno = (c.page or 1) - 1
        ok = 0 <= pno < len(pts) and _same_text(pts[pno].text[c.start : c.end], c.text)
        self.cover(pno, range(c.start, c.end), ok)
        if not ok:
            return
        # Mehrzeilige Fundstelle: jede Zeile einzeln prüfen, damit
        # ein Teilausfall („Max“ weg, „Mustermann“ stehen) auffällt.
        by_line: dict[int, list[str]] = {}
        for i in range(c.start, c.end):
            if pts[pno].lines[i] >= 0:
                by_line.setdefault(pts[pno].lines[i], []).append(pts[pno].text[i])
        if len(by_line) > 1:
            for chars in by_line.values():
                part = "".join(chars)
                if len(_flat(part)) >= 3:
                    self.note(_page_group(c.page), part)

    def add_area(self, page: int, region: Rect) -> None:
        pt = self.pts[page - 1]
        for snippet in _area_snippets(pt, region):
            self.note(_page_group(page), snippet)
        self.cover(page - 1, _area_indices(pt, region))

    def limits(self, before: dict[str, str]) -> dict[tuple[str, str], int]:
        covered: dict[str, tuple[list[int], set[int]] | None] = {
            _page_group(pno + 1): None if mask is None else (_flat_map(self.pts[pno].text)[1], mask)
            for pno, mask in self.masks.items()
        }
        return _limits(before, self.selected_keys, covered)

    def all_keys(self) -> set[str]:
        return {k for keys in self.selected_keys.values() for k in keys}


class _FullySelected:
    """Kommt der Text nur innerhalb ausgewählter Stellen vor? Je Gruppe
    nach denselben (lagerichtigen) Grenzen wie die Nachprüfung, damit
    überlappende Auswahl nicht doppelt zählt."""

    def __init__(self, before: dict[str, str], limits: dict[tuple[str, str], int]):
        self.before = before
        self.limits = limits
        self.cache: dict[str, bool] = {}

    def __call__(self, key: str) -> bool:
        if key not in self.cache:
            limits = self.limits
            self.cache[key] = all(
                limits[(g, key)] == 0 if (g, key) in limits else _occurrences(hay, key) == 0
                for g, hay in self.before.items()
            )
        return self.cache[key]
