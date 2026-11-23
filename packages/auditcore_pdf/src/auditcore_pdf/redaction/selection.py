"""Bestätigte Auswahl aus der Vorschau und Bericht über die Anwendung."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from auditcore_common.json_values import JsonObject

from auditcore_pdf.redaction.common import MAX_AREAS, MAX_AREAS_PER_PAGE, RedactionError
from auditcore_pdf.redaction.criteria import Criteria

_AREA_HINT = "Bereich braucht „page“ (ganze Zahl) und „rect“ [x0, y0, x1, y1]"


@dataclass(frozen=True)
class Area:
    """Eigener Schwärzungsbereich auf einer Seite."""

    page: int  # 1-basiert
    box: tuple[float, float, float, float]  # 0…1 in Anzeigekoordinaten


@dataclass(frozen=True)
class Selection:
    """Was geschwärzt werden soll: Kennungen aus dem Plan und eigene Bereiche."""

    sha256: str
    criteria: Criteria
    selected: frozenset[str]
    areas: tuple[Area, ...] = ()
    sanitize: bool = True

    @classmethod
    def from_dict(cls, payload: object) -> Selection:
        """Liest die Auswahl aus ungeprüftem JSON; Fehler als :class:`RedactionError`."""
        if not isinstance(payload, dict):
            raise RedactionError("Plan muss ein JSON-Objekt sein")
        selected = payload.get("selected")
        criteria = _parse_criteria(payload.get("criteria") or {})
        if not isinstance(selected, list) or not all(isinstance(s, str) for s in selected):
            raise RedactionError("„selected“ muss eine Liste von Kennungen sein")
        return cls(
            sha256=str(payload.get("sha256") or ""),
            criteria=criteria,
            selected=frozenset(selected),
            areas=_parse_areas(payload.get("areas") or []),
            sanitize=bool(payload.get("sanitize", True)),
        )


def _text_list(crit: Mapping[str, object], name: str) -> list[str]:
    values = crit.get(name) or []
    if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
        raise RedactionError(f"„criteria.{name}“ muss eine Liste von Texten sein")
    return [str(v) for v in values]


def _parse_criteria(crit: object) -> Criteria:
    if not isinstance(crit, dict):
        raise RedactionError("„criteria“ muss ein JSON-Objekt sein")
    patterns, terms = _text_list(crit, "patterns"), _text_list(crit, "terms")
    return Criteria.from_input(
        patterns,
        terms,
        bool(crit.get("case_sensitive", False)),
        bool(crit.get("whole_word", True)),
    )


def _area_values(item: Mapping[str, object]) -> tuple[int, tuple[float, float, float, float]]:
    raw_page, raw_rect = item["page"], item["rect"]
    if isinstance(raw_page, bool) or not isinstance(raw_page, int):
        raise TypeError("page")
    if not isinstance(raw_rect, Iterable):
        raise TypeError("rect")
    x0, y0, x1, y1 = (float(v) for v in raw_rect)
    if not all(math.isfinite(v) for v in (x0, y0, x1, y1)):
        raise ValueError("rect")
    return raw_page, (x0, y0, x1, y1)


def _parse_area(item: object) -> Area | None:
    if not isinstance(item, dict):
        raise RedactionError("Bereich braucht „page“ und „rect“ [x0, y0, x1, y1]")
    try:
        page, (x0, y0, x1, y1) = _area_values(item)
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise RedactionError(_AREA_HINT) from exc
    box = (
        max(0.0, min(x0, x1)),
        max(0.0, min(y0, y1)),
        min(1.0, max(x0, x1)),
        min(1.0, max(y0, y1)),
    )
    if box[2] - box[0] <= 0 or box[3] - box[1] <= 0:
        return None
    return Area(page, box)


def _parse_areas(raw: object) -> tuple[Area, ...]:
    if not isinstance(raw, list) or len(raw) > MAX_AREAS:
        raise RedactionError(f"Höchstens {MAX_AREAS} Bereiche")
    areas = [area for area in map(_parse_area, raw) if area is not None]
    per_page: dict[int, int] = {}
    for area in areas:
        per_page[area.page] = per_page.get(area.page, 0) + 1
    crowded = [p for p, n in per_page.items() if n > MAX_AREAS_PER_PAGE]
    if crowded:
        limit = MAX_AREAS_PER_PAGE
        raise RedactionError(f"Höchstens {limit} Bereiche je Seite (Seite {crowded[0]})")
    return tuple(areas)


@dataclass
class ApplyReport:
    """Ergebnis der Anwendung; ``verified`` steht nur in erfolgreich geprüften Berichten."""

    redactions: int
    areas: int
    hidden_removed: int
    by_source: dict[str, int]
    pages: list[int]
    sanitized: list[str]
    deselected: int

    def to_dict(self) -> JsonObject:
        return {
            "redactions": self.redactions,
            "areas": self.areas,
            "hidden_removed": self.hidden_removed,
            "by_source": self.by_source,
            "pages": self.pages,
            "sanitized": self.sanitized,
            "deselected": self.deselected,
            "verified": True,
        }
