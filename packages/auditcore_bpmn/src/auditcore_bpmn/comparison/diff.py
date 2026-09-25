"""Versionsvergleich zweier Stände desselben Diagramms mit Synopse und Differenzfarben."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..model import BpmnDocument, as_document
from .matching import comparable, features, match_elements

DIFF_COLORS = {
    "hinzugefuegt": ("#e6f4ea", "#1e8e3e"),
    "entfallen": ("#fce8e6", "#b3261e"),
    "geaendert": ("#fef7e0", "#e37400"),
}
_LABELS = {"hinzugefuegt": "hinzugefügt", "entfallen": "entfallen", "geaendert": "geändert"}


@dataclass(frozen=True)
class Change:
    """Änderung eines Elements; ``kind``: ``hinzugefuegt``, ``entfallen``, ``geaendert`` oder ``unveraendert``."""

    kind: str
    element_type: str
    name: str
    old_id: str | None = None
    new_id: str | None = None
    fields: tuple[tuple[str, Any, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """JSON-fähige Darstellung."""
        return {
            "kind": self.kind,
            "element_type": self.element_type,
            "name": self.name,
            "old_id": self.old_id,
            "new_id": self.new_id,
            "fields": [{"field": f, "old": a, "new": n} for f, a, n in self.fields],
        }


def _text(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    if isinstance(value, dict):
        return "; ".join(f"{k}: {v}" for k, v in value.items())
    return "" if value is None else str(value)


@dataclass(frozen=True)
class Comparison:
    """Ergebnis des Versionsvergleichs."""

    changes: tuple[Change, ...]

    def of_kind(self, kind: str) -> list[Change]:
        """Änderungen einer Art."""
        return [c for c in self.changes if c.kind == kind]

    @property
    def unchanged(self) -> bool:
        """``True``, wenn sich kein Element geändert hat."""
        return all(c.kind == "unveraendert" for c in self.changes)

    def synopsis(self) -> list[dict[str, str]]:
        """Zeilen „Element | Feld | alter Stand | neuer Stand | Änderung“ für Berichte."""
        rows = []
        for change in self.changes:
            if change.kind == "geaendert":
                rows += [
                    {
                        "element": change.name,
                        "feld": f,
                        "alt": _text(a),
                        "neu": _text(n),
                        "aenderung": _LABELS[change.kind],
                    }
                    for f, a, n in change.fields
                ]
            elif change.kind in ("hinzugefuegt", "entfallen"):
                old = change.name if change.kind == "entfallen" else ""
                new = change.name if change.kind == "hinzugefuegt" else ""
                rows.append(
                    {"element": change.name, "feld": "", "alt": old, "neu": new, "aenderung": _LABELS[change.kind]}
                )
        return rows

    def colors(self) -> tuple[dict[str, tuple[str, str]], dict[str, tuple[str, str]]]:
        """Farben der grafischen Differenz: (alter Stand, neuer Stand)."""
        old: dict[str, tuple[str, str]] = {}
        new: dict[str, tuple[str, str]] = {}
        for change in self.changes:
            color = DIFF_COLORS.get(change.kind)
            if color is None:
                continue
            if change.old_id and change.kind != "hinzugefuegt":
                old[change.old_id] = color
            if change.new_id and change.kind != "entfallen":
                new[change.new_id] = color
        return old, new

    def to_dict(self) -> dict[str, Any]:
        """JSON-fähige Darstellung."""
        return {"changes": [c.to_dict() for c in self.changes]}


def compare(old: str | bytes | BpmnDocument, new: str | bytes | BpmnDocument) -> Comparison:
    """Elementweiser Vergleich: hinzugefügt, entfallen, geändert (mit Feldern), unverändert."""
    old_doc, new_doc = as_document(old), as_document(new)
    mapping = match_elements(old_doc, new_doc)
    changes: list[Change] = []
    for element in comparable(old_doc):
        partner_id = mapping.get(element.id)
        if partner_id is None:
            changes.append(Change("entfallen", element.type, element.label, old_id=element.id))
            continue
        partner = new_doc.elements[partner_id]
        before, after = features(old_doc, element), features(new_doc, partner)
        fields = tuple((key, before[key], after[key]) for key in before if before[key] != after[key])
        kind = "geaendert" if fields else "unveraendert"
        changes.append(Change(kind, partner.type, partner.label, element.id, partner.id, fields))
    matched = set(mapping.values())
    changes += [
        Change("hinzugefuegt", e.type, e.label, new_id=e.id) for e in comparable(new_doc) if e.id not in matched
    ]
    return Comparison(tuple(changes))
