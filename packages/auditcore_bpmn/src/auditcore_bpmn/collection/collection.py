"""Diagrammsammlung: Ordner, Tags, Reihenfolge und Diagrammeinträge.

Jedes Diagramm liegt in genau einem Ordner (``folder_id``; ``None`` = oberste
Ebene) und trägt beliebig viele Tags. Aus dem XML hält die Sammlung nur einen
Auszug (:class:`DiagramExcerpt`). Abfragen, Übersichten, Verweise, Regeln und
Freigaben stehen in eigenen Modulen und sind hier als Methoden erreichbar.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from typing import TYPE_CHECKING

from ..errors import CollectionError
from ..model import BpmnDocument, as_document
from .excerpt import excerpt_from_document
from .model import Approval, DiagramEntry, DiagramReference, Folder, FolderNode, GroupOverview, Tag, check_id

if TYPE_CHECKING:
    from ..validation import ValidationIssue


def _next_position(positions: Iterable[int]) -> int:
    return 1 + max(positions, default=-1)


class DiagramCollection:
    """Veränderliche Sammlung; jede Änderung prüft die Integrität sofort."""

    def __init__(self, id: str = "sammlung", name: str = "Diagrammsammlung") -> None:  # noqa: A002
        self.id = id
        self.name = name
        self.folders: dict[str, Folder] = {}
        self.tags: dict[str, Tag] = {}
        self.diagrams: dict[str, DiagramEntry] = {}

    # -- Ordner ------------------------------------------------------------------
    def add_folder(
        self,
        id: str,
        name: str,
        parent_id: str | None = None,
        *,  # noqa: A002
        position: int | None = None,
        description: str | None = None,
    ) -> Folder:
        """Legt einen Ordner an (Position am Ende, falls nicht angegeben)."""
        check_id(id, "Ordner")
        if id in self.folders:
            raise CollectionError(f"Ordner „{id}“ existiert bereits.")
        if parent_id is not None and parent_id not in self.folders:
            raise CollectionError(f"Übergeordneter Ordner „{parent_id}“ ist unbekannt.")
        if position is None:
            position = _next_position(f.position for f in self.folders.values() if f.parent_id == parent_id)
        folder = Folder(id, name, parent_id, position, description)
        self.folders[id] = folder
        return folder

    def ancestors(self, folder_id: str | None) -> list[str]:
        """Kette bis zur obersten Ebene; wirft bei Zyklus oder unbekanntem Ordner."""
        chain: list[str] = []
        current = folder_id
        while current is not None:
            if current in chain:
                raise CollectionError(f"Ordner „{current}“ bildet einen Zyklus.")
            folder = self.folders.get(current)
            if folder is None:
                raise CollectionError(f"Ordner „{current}“ ist unbekannt.")
            chain.append(current)
            current = folder.parent_id
        return chain

    def move_folder(self, folder_id: str, parent_id: str | None) -> None:
        """Hängt einen Ordner um; Zyklen werden abgewiesen."""
        if folder_id not in self.folders:
            raise CollectionError(f"Ordner „{folder_id}“ ist unbekannt.")
        if parent_id is not None and folder_id in self.ancestors(parent_id):
            raise CollectionError("Ein Ordner kann nicht in sich selbst oder einen Unterordner verschoben werden.")
        self.folders[folder_id].parent_id = parent_id

    def remove_folder(self, folder_id: str) -> None:
        """Entfernt einen leeren Ordner."""
        occupied = any(f.parent_id == folder_id for f in self.folders.values()) or any(
            d.folder_id == folder_id for d in self.diagrams.values()
        )
        if occupied:
            raise CollectionError(f"Ordner „{folder_id}“ ist nicht leer.")
        self.folders.pop(folder_id, None)

    def add_tag(self, id: str, name: str, color: str | None = None) -> Tag:  # noqa: A002
        """Legt einen Tag an oder ersetzt ihn."""
        check_id(id, "Tag")
        tag = Tag(id, name, color)
        self.tags[id] = tag
        return tag

    # -- Diagramme ------------------------------------------------------------------
    def _check_tags(self, tags: Iterable[str]) -> list[str]:
        tag_ids = list(dict.fromkeys(tags))
        unknown = [t for t in tag_ids if t not in self.tags]
        if unknown:
            raise CollectionError(f"Unbekannte Tags: {unknown}")
        return tag_ids

    def add_diagram(
        self,
        id: str,
        xml: str | bytes | BpmnDocument | None = None,
        *,  # noqa: A002
        name: str | None = None,
        folder_id: str | None = None,
        tags: Iterable[str] = (),
        position: int | None = None,
    ) -> DiagramEntry:
        """Nimmt ein Diagramm auf; mit XML werden Infos und Auszug übernommen."""
        check_id(id, "Diagramm")
        if id in self.diagrams:
            raise CollectionError(f"Diagramm „{id}“ existiert bereits.")
        if folder_id is not None and folder_id not in self.folders:
            raise CollectionError(f"Ordner „{folder_id}“ ist unbekannt.")
        tag_ids = self._check_tags(tags)
        if position is None:
            position = _next_position(d.position for d in self.diagrams.values() if d.folder_id == folder_id)
        entry = DiagramEntry(id, name or id, folder_id, tag_ids, position)
        self.diagrams[id] = entry
        if xml is not None:
            self.refresh(id, xml)
        return entry

    def entry(self, diagram_id: str) -> DiagramEntry:
        """Eintrag eines Diagramms oder :class:`CollectionError`."""
        try:
            return self.diagrams[diagram_id]
        except KeyError as error:
            raise CollectionError(f"Diagramm „{diagram_id}“ ist unbekannt.") from error

    def refresh(self, diagram_id: str, xml: str | bytes | BpmnDocument) -> DiagramEntry:
        """Übernimmt Diagramm-Infos und Auszug aus dem XML."""
        entry = self.entry(diagram_id)
        document = as_document(xml)
        entry.info = document.diagram_info
        entry.excerpt = excerpt_from_document(document)
        if entry.name == entry.id and entry.info and entry.info.title:
            entry.name = entry.info.title
        return entry

    def remove_diagram(self, diagram_id: str) -> None:
        """Entfernt ein Diagramm aus der Sammlung."""
        self.entry(diagram_id)
        del self.diagrams[diagram_id]

    def move_diagram(self, diagram_id: str, folder_id: str | None, *, position: int | None = None) -> None:
        """Verschiebt ein Diagramm in einen Ordner (optional an eine Position) und nummeriert neu."""
        entry = self.entry(diagram_id)
        if folder_id is not None and folder_id not in self.folders:
            raise CollectionError(f"Ordner „{folder_id}“ ist unbekannt.")
        entry.folder_id = folder_id
        siblings = [d for d in self.in_folder(folder_id) if d.id != diagram_id]
        index = len(siblings) if position is None else max(0, min(position, len(siblings)))
        siblings.insert(index, entry)
        for number, item in enumerate(siblings):
            item.position = number

    def set_order(self, folder_id: str | None, diagram_ids: list[str]) -> None:
        """Setzt die Reihenfolge aller Diagramme eines Ordners."""
        current = {d.id for d in self.in_folder(folder_id)}
        if set(diagram_ids) != current or len(diagram_ids) != len(current):
            raise CollectionError("Die Reihenfolge muss genau die Diagramme des Ordners enthalten.")
        for number, diagram_id in enumerate(diagram_ids):
            self.diagrams[diagram_id].position = number

    def set_tags(self, diagram_id: str, tags: Iterable[str]) -> None:
        """Ersetzt die Tags eines Diagramms (nur bekannte Tags)."""
        self.entry(diagram_id).tags = self._check_tags(tags)

    # -- Einfache Abfragen ------------------------------------------------------------
    def in_folder(self, folder_id: str | None) -> list[DiagramEntry]:
        """Diagramme direkt in einem Ordner, sortiert nach Position und Name."""
        items = (d for d in self.diagrams.values() if d.folder_id == folder_id)
        return sorted(items, key=lambda d: (d.position, d.name.casefold(), d.id))

    def subfolders(self, folder_id: str | None) -> list[Folder]:
        """Unterordner eines Ordners, sortiert nach Position und Name."""
        items = (f for f in self.folders.values() if f.parent_id == folder_id)
        return sorted(items, key=lambda f: (f.position, f.name.casefold(), f.id))

    def diagrams_in(self, folder_id: str | None, *, recursive: bool = True) -> list[DiagramEntry]:
        """Diagramme eines Ordners, auf Wunsch einschließlich Unterordnern."""
        result = list(self.in_folder(folder_id))
        if recursive:
            for folder in self.subfolders(folder_id):
                result.extend(self.diagrams_in(folder.id))
        return result

    def with_tag(self, tag_id: str) -> list[DiagramEntry]:
        """Diagramme mit einem Tag."""
        return [d for d in self.diagrams.values() if tag_id in d.tags]

    def tree(self, folder_id: str | None = None) -> FolderNode:
        """Ordnerbaum ab ``folder_id`` (``None`` = oberste Ebene)."""
        return FolderNode(
            self.folders.get(folder_id) if folder_id else None,
            tuple(self.tree(f.id) for f in self.subfolders(folder_id)),
            tuple(self.in_folder(folder_id)),
        )

    # -- Delegationen ------------------------------------------------------------
    def search(self, term: str = "", *, status: str | None = None, tag: str | None = None) -> list[DiagramEntry]:
        """Volltextsuche, siehe :func:`auditcore_bpmn.collection.queries.search`."""
        from .queries import search

        return search(self, term, status=status, tag=tag)

    def elements_by_key(self, kind: str, value: str) -> list[tuple[str, str]]:
        """Elemente zu einem fachlichen Schlüssel, siehe :func:`queries.elements_by_key`."""
        from .queries import elements_by_key

        return elements_by_key(self, kind, value)

    def overview(
        self,
        folder_id: str | None = None,
        *,
        recursive: bool = True,
        tag_id: str | None = None,
        reference_date: date | None = None,
    ) -> GroupOverview:
        """Übersicht einer Gruppe, siehe :func:`queries.overview`."""
        from .queries import overview

        return overview(self, folder_id, recursive=recursive, tag_id=tag_id, reference_date=reference_date)

    def references(self) -> list[DiagramReference]:
        """Verweise zwischen Diagrammen, siehe :func:`queries.references`."""
        from .queries import references

        return references(self)

    def target_actual_pairs(self) -> list[tuple[str, str]]:
        """Paare aus Ist- und Soll-Diagramm."""
        from .queries import target_actual_pairs

        return target_actual_pairs(self)

    def validate(self) -> list[ValidationIssue]:
        """Regeln der Sammlung (``BPMN-K…``)."""
        from .checks import validate_collection

        return validate_collection(self)

    def approve(self, diagram_id: str, xml: str | bytes, version: str, **details: str | None) -> Approval:
        """Hält einen freigegebenen Stand fest, siehe :func:`approvals.approve`."""
        from .approvals import approve

        return approve(self, diagram_id, xml, version, **details)

    def check_approval(self, diagram_id: str, xml: str | bytes, version: str | None = None) -> ValidationIssue | None:
        """Prüft XML gegen einen freigegebenen Stand, siehe :func:`approvals.check_approval`."""
        from .approvals import check_approval

        return check_approval(self, diagram_id, xml, version)

    def to_dict(self) -> dict[str, object]:
        """JSON-Daten nach ``diagram-collection-1.schema.json``."""
        from .serialization import collection_to_dict

        return collection_to_dict(self)

    def to_json(self) -> str:
        """JSON-Text (UTF-8, eingerückt)."""
        from .serialization import collection_to_json

        return collection_to_json(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> DiagramCollection:
        """Sammlung aus JSON-Daten; prüft Schema, IDs und Ordnerzyklen."""
        from .serialization import collection_from_dict

        return collection_from_dict(data)

    @classmethod
    def from_json(cls, text: str) -> DiagramCollection:
        """Sammlung aus JSON-Text."""
        from .serialization import collection_from_json

        return collection_from_json(text)
