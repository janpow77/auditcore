"""Ablage gespeicherter Vergleiche als Port mit einer Referenz im Arbeitsspeicher.

Die Bibliothek persistiert nichts. Anwendungen binden ihre Datenbank über
:class:`ComparisonStore` an; :class:`InMemoryComparisonStore` genügt für
Einzelprozess-Werkzeuge, Demos und Tests.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import Protocol

from auditcore_documents.model import ComparisonResult


@dataclass
class StoredComparison:
    """Ein Vergleich mit Kennung, Eigentümer und Titel."""

    comparison_id: str
    owner: str
    title: str
    created_at: str
    result: ComparisonResult

    def envelope(self) -> dict[str, object]:
        """JSON-Form ``Comparison`` des REST-Vertrags (docs/ui/synopsis-rest.md)."""
        return {
            "id": self.comparison_id,
            "title": self.title,
            "created_at": self.created_at,
            "result": self.result.to_dict(),
        }

    def summary(self) -> dict[str, object]:
        """JSON-Form ``ComparisonSummary`` für Verlaufslisten."""
        result = self.result
        return {
            "id": self.comparison_id,
            "title": self.title,
            "created_at": self.created_at,
            "old_filename": result.old_filename,
            "new_filename": result.new_filename,
            "comparison_type": str(result.metadata.get("comparison_type", "standard")),
            "counts": {
                "changed": result.changed_count,
                "removed": result.removed_count,
                "added": result.added_count,
                "moved": result.moved_count,
            },
        }


class ComparisonStore(Protocol):
    """Persistenzport; Mandanten- und Rechteprüfung liegt beim Aufrufer (``owner``)."""

    def add(self, item: StoredComparison) -> None: ...

    def get(self, owner: str, comparison_id: str) -> StoredComparison | None: ...

    def list(self, owner: str) -> list[StoredComparison]: ...

    def replace(self, item: StoredComparison) -> None: ...

    def delete(self, owner: str, comparison_id: str) -> bool: ...


class InMemoryComparisonStore:
    """Begrenzte Ablage im Arbeitsspeicher; älteste Einträge fallen zuerst heraus.

    Nicht für mehrere Prozesse gedacht. Zugriffe erfolgen im Ereignis-Thread
    der ASGI-Anwendung; der Vergleich selbst läuft außerhalb der Ablage.
    """

    def __init__(self, max_items: int = 100) -> None:
        if type(max_items) is not int or max_items < 1:
            raise ValueError("max_items muss eine positive ganze Zahl sein")
        self._max_items = max_items
        self._items: OrderedDict[tuple[str, str], StoredComparison] = OrderedDict()

    def add(self, item: StoredComparison) -> None:
        self._items[(item.owner, item.comparison_id)] = item
        while len(self._items) > self._max_items:
            self._items.popitem(last=False)

    def get(self, owner: str, comparison_id: str) -> StoredComparison | None:
        return self._items.get((owner, comparison_id))

    def list(self, owner: str) -> list[StoredComparison]:
        """Neueste zuerst."""
        return [
            item for (key_owner, _), item in reversed(self._items.items()) if key_owner == owner
        ]

    def replace(self, item: StoredComparison) -> None:
        key = (item.owner, item.comparison_id)
        if key not in self._items:
            raise KeyError(item.comparison_id)
        self._items[key] = item

    def delete(self, owner: str, comparison_id: str) -> bool:
        return self._items.pop((owner, comparison_id), None) is not None
