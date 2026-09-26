"""Speicher-Port für Sammlung, Diagramme und freigegebene Stände; Dateisystem-Umsetzung."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Protocol

from ..errors import CollectionError
from .collection import DiagramCollection
from .model import check_id
from .serialization import collection_from_json, collection_to_json


class Storage(Protocol):
    """Port für Laden und Speichern; die Anwendung liefert eine Umsetzung (Datei, Datenbank, REST)."""

    def load_collection(self) -> DiagramCollection | None:
        """Gespeicherte Sammlung oder ``None``."""

    def save_collection(self, collection: DiagramCollection) -> None:
        """Speichert die Sammlung."""

    def load_diagram(self, diagram_id: str) -> str:
        """XML eines Diagramms."""

    def save_diagram(self, diagram_id: str, xml: str) -> None:
        """Speichert das XML eines Diagramms."""

    def delete_diagram(self, diagram_id: str) -> None:
        """Löscht das XML eines Diagramms."""

    def diagram_ids(self) -> list[str]:
        """IDs aller gespeicherten Diagramme."""

    def save_approved(self, diagram_id: str, version: str, xml: str) -> None:
        """Speichert einen freigegebenen Stand unveränderlich."""

    def load_approved(self, diagram_id: str, version: str) -> str:
        """XML eines freigegebenen Stands."""


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=".tmp-", suffix=path.suffix)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="") as stream:
            stream.write(text)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


class FileStorage:
    """Ablage: ``sammlung.json``, ``diagramme/<id>.bpmn``, ``freigaben/<id>/<version>.bpmn``.

    Schreiben ist atomar (temporäre Datei + Umbenennen); freigegebene Stände
    werden nie überschrieben; IDs sind gegen Pfadwechsel geprüft.
    """

    def __init__(self, directory: str | os.PathLike[str]) -> None:
        self.root = Path(directory)
        (self.root / "diagramme").mkdir(parents=True, exist_ok=True)
        (self.root / "freigaben").mkdir(parents=True, exist_ok=True)

    def _diagram(self, diagram_id: str) -> Path:
        return self.root / "diagramme" / f"{check_id(diagram_id, 'Diagramm')}.bpmn"

    def _approved(self, diagram_id: str, version: str) -> Path:
        return self.root / "freigaben" / check_id(diagram_id, "Diagramm") / f"{check_id(version, 'Versions')}.bpmn"

    def load_collection(self) -> DiagramCollection | None:
        """Liest ``sammlung.json`` oder liefert ``None``."""
        path = self.root / "sammlung.json"
        return collection_from_json(path.read_text(encoding="utf-8")) if path.is_file() else None

    def save_collection(self, collection: DiagramCollection) -> None:
        """Schreibt ``sammlung.json`` atomar."""
        _atomic_write(self.root / "sammlung.json", collection_to_json(collection))

    def load_diagram(self, diagram_id: str) -> str:
        """Liest ``diagramme/<id>.bpmn``."""
        path = self._diagram(diagram_id)
        if not path.is_file():
            raise CollectionError(f"Diagramm „{diagram_id}“ ist nicht gespeichert.")
        return path.read_text(encoding="utf-8")

    def save_diagram(self, diagram_id: str, xml: str) -> None:
        """Schreibt ``diagramme/<id>.bpmn`` atomar."""
        _atomic_write(self._diagram(diagram_id), xml)

    def delete_diagram(self, diagram_id: str) -> None:
        """Löscht ``diagramme/<id>.bpmn``, falls vorhanden."""
        self._diagram(diagram_id).unlink(missing_ok=True)

    def diagram_ids(self) -> list[str]:
        """IDs aller Dateien unter ``diagramme/``."""
        return sorted(path.stem for path in (self.root / "diagramme").glob("*.bpmn"))

    def save_approved(self, diagram_id: str, version: str, xml: str) -> None:
        """Schreibt ``freigaben/<id>/<version>.bpmn``; vorhandene Stände bleiben unverändert."""
        path = self._approved(diagram_id, version)
        if path.exists():
            if path.read_text(encoding="utf-8") == xml:
                return
            raise CollectionError(f"Freigegebener Stand {version} von „{diagram_id}“ ist unveränderlich.")
        _atomic_write(path, xml)

    def load_approved(self, diagram_id: str, version: str) -> str:
        """Liest ``freigaben/<id>/<version>.bpmn``."""
        path = self._approved(diagram_id, version)
        if not path.is_file():
            raise CollectionError(f"Freigegebener Stand {version} von „{diagram_id}“ ist nicht vorhanden.")
        return path.read_text(encoding="utf-8")
