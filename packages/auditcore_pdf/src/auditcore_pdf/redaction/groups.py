"""Prüfgruppen für die Nachprüfung: Text je Seite und versteckte Ablagen."""

from __future__ import annotations

from typing import TYPE_CHECKING

from auditcore_pdf.redaction.common import _HARD, _HYPHENS, HIDDEN_GROUP, _clean, _flat
from auditcore_pdf.redaction.hidden import _iter_hidden_strings
from auditcore_pdf.redaction.layers import _expose_full_page, _reveal_layers
from auditcore_pdf.redaction.page_text import _page_text, _PageText
from auditcore_pdf.redaction.plan import Candidate

if TYPE_CHECKING:
    from pymupdf import Document, Rect


def _page_group(page: int | None) -> str:
    return f"Seite {page}" if page else HIDDEN_GROUP


def _positions(hay: str, key: str) -> list[int]:
    if not key:
        return []
    found: list[int] = []
    i = hay.find(key)
    while i >= 0:
        found.append(i)
        i = hay.find(key, i + 1)
    return found


def _occurrences(hay: str, key: str) -> int:
    return len(_positions(hay, key))


def _flat_map(text: str) -> tuple[str, list[int]]:
    """Vergleichsform wie ``_flat`` und zu jedem Zeichen die Stelle im Seitentext."""
    out: list[str] = []
    origin: list[int] = []
    for i, ch in enumerate(text):
        if ch == _HARD:
            continue
        f = _flat(ch)
        out.append(f)
        origin.extend([i] * len(f))
    return "".join(out), origin


def _same_text(span: str, text: str) -> bool:
    """Passt der Ausschnitt des Seitentexts zur Fundstelle? Trennstriche am
    Zeilenende fallen bei Begriffen weg und zählen deshalb nicht."""
    a, b = _flat(span.replace(_HARD, "")), _flat(text)
    if a == b:
        return True
    strip = str.maketrans("", "", _HYPHENS)
    return a.translate(strip) == b.translate(strip)


def _text_groups(doc: Document) -> tuple[dict[str, str], list[_PageText]]:
    """Text je Prüfgruppe in Vergleichsform: eine Gruppe je Seite, eine für
    alle versteckten Ablagen. Ebenen und Bereiche außerhalb der CropBox
    zählen mit. Das Dokument wird dabei verändert und darf nicht gespeichert werden."""
    _reveal_layers(doc)
    groups: dict[str, str] = {}
    pts: list[_PageText] = []
    for page in doc:
        _expose_full_page(page)
        pt = _page_text(page)
        pts.append(pt)
        groups[_page_group(page.number + 1)] = _flat_map(pt.text)[0]
    groups[HIDDEN_GROUP] = "\x01".join(
        _flat(_clean(text)) for _l, text, _p, _r in _iter_hidden_strings(doc)
    )
    return groups, pts


def _area_indices(pt: _PageText, region: Rect) -> list[int]:
    """Stellen im Seitentext, deren Zeichenmitte im Bereich liegt."""
    x0, y0, x1, y1 = region.x0, region.y0, region.x1, region.y1
    return [
        i
        for i, r in enumerate(pt.rects)
        if r is not None and x0 <= (r[0] + r[2]) / 2 <= x1 and y0 <= (r[1] + r[3]) / 2 <= y1
    ]


def _inside_other(c: Candidate, others: list[Candidate]) -> bool:
    """Liegt eine versteckte Fundstelle ganz in einer längeren ausgewählten
    Fundstelle derselben Ablage? Dann zählt sie dort schon mit."""
    for o in others:
        if o is c or o.location != c.location or o.ref != c.ref or o.page != c.page:
            continue
        longer = (o.end - o.start) > (c.end - c.start)
        if o.start <= c.start and c.end <= o.end and longer and _flat(c.text) in _flat(o.text):
            return True
    return False


def _area_snippets(pt: _PageText, region: Rect) -> list[str]:
    """Text unter einem eigenen Bereich, je Zeile getrennt."""
    x0, y0, x1, y1 = region.x0, region.y0, region.x1, region.y1
    by_line: dict[int, list[str]] = {}
    for i, r in enumerate(pt.rects):
        if r is None:
            continue
        cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
        if x0 <= cx <= x1 and y0 <= cy <= y1:
            by_line.setdefault(pt.lines[i], []).append(pt.text[i])
    return [s for s in ("".join(v) for v in by_line.values()) if len(_flat(s)) >= 3]


def _limits(
    groups: dict[str, str],
    selected: dict[str, list[str]],
    covered: dict[str, tuple[list[int], set[int]] | None] | None = None,
) -> dict[tuple[str, str], int]:
    """Höchstens zulässige Vorkommen je (Gruppe, Text) nach dem Schwärzen.

    Zulässig ist, was vorher in der Gruppe stand, abzüglich der Vorkommen in
    ausgewählten Stellen. So zählen Schreibvarianten („Krüger“, „KRÜGER“)
    und verschachtelte Begriffe („Max Mustermann“ und „Mustermann“) richtig,
    und abgewählte gleiche Texte bleiben erlaubt.

    Für Seiten liegt in ``covered`` die Lage: die Herkunft jedes Zeichens der
    Vergleichsform und die Menge der ausgewählten Stellen im Seitentext. Ein
    Vorkommen wird dann nur abgezogen, wenn es ganz in ausgewählten Stellen
    liegt, und nur einmal, auch wenn sich ausgewählte Fundstellen überlappen
    (Begriff in einer E-Mail-Adresse, Fundstelle unter einem eigenen Bereich).
    Ohne Lage (versteckte Ablagen, unsichere Lage) wird über die Texte gezählt.
    """
    covered = covered or {}
    limits: dict[tuple[str, str], int] = {}
    for group, keys in selected.items():
        hay = groups.get(group, "")
        where = covered.get(group)
        if where is not None:
            for k in set(keys):
                limits[(group, k)] = _limit_by_position(hay, k, *where)
        else:
            for k, n in _limits_by_text(hay, keys).items():
                limits[(group, k)] = n
    return limits


def _limit_by_position(hay: str, key: str, origin: list[int], mask: set[int]) -> int:
    spots = _positions(hay, key)
    end = len(origin)
    inside = sum(
        1 for i in spots if all(origin[j] in mask for j in range(i, min(i + len(key), end)))
    )
    return len(spots) - inside


def _limits_by_text(hay: str, keys: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for k in keys:
        counts[k] = counts.get(k, 0) + 1
    limits: dict[str, int] = {}
    for k in counts:
        inside = sum(n * _occurrences(t, k) for t, n in counts.items() if k in t)
        limits[k] = max(0, _occurrences(hay, k) - inside)
    return limits
