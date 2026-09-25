"""Datenmodell der Diagrammsammlung (ohne Datenbank, ohne Pydantic)."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from ..errors import CollectionError
from ..extensions import DiagramInfo

#: Arten stabiler fachlicher Schlüssel im Schlüsselindex.
KEY_KINDS = ("ka", "bk", "prueffeld", "feststellung_ref", "register", "rolle", "kennzeichen")
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


def check_id(value: str, what: str) -> str:
    """Prüft IDs (auch als Dateinamen verwendbar, kein Pfadwechsel möglich)."""
    if not isinstance(value, str) or not _ID.match(value):
        raise CollectionError(f"Ungültige {what}-ID „{value}“ (erlaubt: Buchstaben, Ziffern, _ . -).")
    return value


def sha256_xml(xml: str | bytes) -> str:
    """SHA-256 über die UTF-8-Bytes des XML genau so, wie es gespeichert wird."""
    return hashlib.sha256(xml.encode("utf-8") if isinstance(xml, str) else xml).hexdigest()


@dataclass
class Folder:
    """Ordner (Gruppe) der Sammlung, verschachtelbar."""

    id: str
    name: str
    parent_id: str | None = None
    position: int = 0
    description: str | None = None


@dataclass
class Tag:
    """Tag; ein Diagramm kann beliebig viele tragen."""

    id: str
    name: str
    color: str | None = None


@dataclass(frozen=True)
class Approval:
    """Unveränderlicher freigegebener Stand (neue Version statt Änderung)."""

    version: str
    sha256: str
    cutoff_date: str | None = None
    approved_on: str | None = None
    approved_by: str | None = None


@dataclass
class DiagramExcerpt:
    """Aus dem XML abgeleitete Angaben (nicht von Hand pflegen)."""

    process_ids: list[str] = field(default_factory=list)
    calls: list[tuple[str, str]] = field(default_factory=list)
    link_throws: list[tuple[str, str]] = field(default_factory=list)
    link_catches: list[tuple[str, str]] = field(default_factory=list)
    activities: int = 0
    activities_with_legal_basis: int = 0
    #: Art → Wert → Element-IDs (Arten siehe ``KEY_KINDS``).
    keys: dict[str, dict[str, list[str]]] = field(default_factory=dict)


@dataclass
class DiagramEntry:
    """Diagramm in der Sammlung: Ordner, Tags, Position, Infos, Auszug, Freigaben."""

    id: str
    name: str
    folder_id: str | None = None
    tags: list[str] = field(default_factory=list)
    position: int = 0
    info: DiagramInfo | None = None
    excerpt: DiagramExcerpt = field(default_factory=DiagramExcerpt)
    approvals: list[Approval] = field(default_factory=list)

    @property
    def status(self) -> str | None:
        """Status aus den Diagramm-Infos."""
        return self.info.status if self.info else None

    @property
    def title(self) -> str:
        """Titel aus den Diagramm-Infos, sonst Name."""
        return (self.info.title if self.info and self.info.title else None) or self.name


@dataclass(frozen=True)
class DiagramReference:
    """Verweis eines Elements auf ein anderes Diagramm (Aufruf oder Link)."""

    source_diagram: str
    source_element: str
    kind: str
    key: str
    target_diagram: str | None
    target_element: str | None = None

    @property
    def resolved(self) -> bool:
        """``True``, wenn das Ziel in der Sammlung gefunden wurde."""
        return self.target_diagram is not None


@dataclass(frozen=True)
class FolderNode:
    """Knoten des Ordnerbaums."""

    folder: Folder | None
    children: tuple[FolderNode, ...]
    diagrams: tuple[DiagramEntry, ...]


@dataclass(frozen=True)
class GroupOverview:
    """Kennzahlen einer Gruppe: Anzahl, Status, Rechtsgrundlagen, KA-Abdeckung, Ablauf."""

    count: int
    status_distribution: dict[str, int]
    activities: int
    activities_with_legal_basis: int
    expired: tuple[str, ...]
    #: KA-Nummer → Diagramm-IDs, in denen sie belegt ist.
    key_requirement_coverage: dict[int, tuple[str, ...]]
    diagrams: tuple[str, ...]

    @property
    def legal_basis_coverage(self) -> float | None:
        """Anteil der Aktivitäten mit Rechtsgrundlage (``None`` ohne Aktivitäten)."""
        return round(self.activities_with_legal_basis / self.activities, 4) if self.activities else None

    def to_dict(self) -> dict[str, object]:
        """JSON-fähige Darstellung."""
        return {
            "count": self.count,
            "status_distribution": dict(self.status_distribution),
            "activities": self.activities,
            "activities_with_legal_basis": self.activities_with_legal_basis,
            "legal_basis_coverage": self.legal_basis_coverage,
            "expired": list(self.expired),
            "key_requirement_coverage": {str(k): list(v) for k, v in sorted(self.key_requirement_coverage.items())},
            "diagrams": list(self.diagrams),
        }
