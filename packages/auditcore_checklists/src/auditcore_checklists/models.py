"""Domänenmodelle für Checklisten, Baumstrukturen, Antworten und Pakete."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from .errors import JsonObject, JsonValue


class NodeType(StrEnum):
    """Arten von Knoten im Checklisten-Baum."""

    HEADING = "HEADING"
    QUESTION = "QUESTION"
    DECISION = "DECISION"
    HINT = "HINT"


class AnswerType(StrEnum):
    """Unterstützte Antworttypen für Fragen und Entscheidungen."""

    BOOLEAN = "BOOLEAN"
    BOOLEAN_JN = "BOOLEAN_JN"
    CURRENCY = "CURRENCY"
    DATE = "DATE"
    CUSTOM_ENUM = "CUSTOM_ENUM"
    TEXT = "TEXT"
    MULTI_CHOICE = "MULTI_CHOICE"


class FindingType(StrEnum):
    """Art des Prüfbefunds bei der Auswertung."""

    NONE = "keiner"
    FORMAL = "formell"
    FINANCIAL = "finanziell"


class FindingSeverity(StrEnum):
    """Schweregrad eines Prüfbefunds."""

    HINT = "hinweis"
    MODERATE = "moderat"
    SIGNIFICANT = "wesentlich"


class NodeStatus(StrEnum):
    """Bearbeitungsstatus eines Knotens."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class HistoryAction(StrEnum):
    """Arten von Änderungen in der Knotenhistorie."""

    STATUS_CHANGED = "status_changed"
    NOTE_ADDED = "note_added"
    NODE_CREATED = "node_created"
    NODE_UPDATED = "node_updated"


@dataclass(frozen=True)
class TeamNote:
    """Team-Notiz bzw. Diskussionsbeitrag zu einem Knoten."""

    id: str
    username: str
    message: str
    timestamp: str
    user_id: int | str | None = None
    parent_note_id: str | None = None


@dataclass(frozen=True)
class NodeContent:
    """Fachlicher Inhalt eines Baumknotens."""

    title: str
    answer_type: AnswerType | None = None
    answer_options: tuple[str, ...] = ()
    category_id: int | str | None = None
    hints: tuple[str, ...] = ()
    public_remark: str | None = None
    remark_snippets: Mapping[str, str] = field(default_factory=dict)
    qchess_eingabetyp: int | None = None
    qchess_antwortset_id: str | None = None
    qchess_ja_label: str | None = None
    qchess_nein_label: str | None = None


@dataclass(frozen=True)
class NodeInternal:
    """Interne Metadaten eines Knotens (nicht für Auswertungsberichte)."""

    team_notes: tuple[TeamNote, ...] = ()
    status: str = "pending"
    created_at: str | None = None
    updated_at: str | None = None
    created_by: int | str | None = None


@dataclass(frozen=True)
class ChecklistNode:
    """Ein Knoten in der Checklisten-Hierarchie."""

    id: str
    node_type: NodeType
    parent_id: str | None
    content: NodeContent
    branch: str | None = None
    sort_order: int = 0
    internal: NodeInternal = field(default_factory=NodeInternal)
    children: tuple[str, ...] = ()


@dataclass(frozen=True)
class CategoryItemDefinition:
    """Option eines Antwortsets (Kategorie)."""

    value: str
    sort_order: int = 0


@dataclass(frozen=True)
class CategoryDefinition:
    """Wiederverwendbare Antwortset-Definition."""

    name: str
    description: str = ""
    icon_name: str = "list"
    color: str = "#003478"
    items: tuple[CategoryItemDefinition, ...] = ()


@dataclass(frozen=True)
class ChecklistAnswer:
    """Erfasste Antwort zu einer Prüffrage oder Entscheidung."""

    node_id: str
    value: JsonValue = None
    is_na: bool = False
    remark_user: str | None = None
    doc_refs: tuple[str, ...] = ()
    befund_typ: FindingType = FindingType.NONE
    finding_severity: FindingSeverity | None = None
    finding_text: str | None = None
    answered_at: str | None = None
    answered_by: str | None = None


@dataclass(frozen=True)
class TreeValidationFinding:
    """Ergebnis einer Validierungsprüfung der Baumstruktur."""

    severity: str
    node_id: str | None
    code: str
    message: str


@dataclass(frozen=True)
class ProjectMetadata:
    """Metadaten des Checklisten-Projekts."""

    name: str
    description: str = ""
    tags: tuple[str, ...] = ()
    aktenzeichen: str | None = None
    geschaeftsjahr: str | None = None
    module: str = "standard"
    current_version: str = "1.0"


@dataclass(frozen=True)
class VersionSnapshot:
    """Schnappschuss einer Checklisten-Version."""

    version_number: str
    is_frozen: bool = False
    notes: str = ""
    created_at: str | None = None
    tree_data: JsonObject = field(default_factory=dict)
    history: tuple[JsonObject, ...] = ()
