"""Immutable domain model: board, column, card, label, share and transition policy."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .errors import JsonObject

PRIORITIES: tuple[str, ...] = ("hoch", "mittel", "niedrig")
PERMISSIONS: tuple[str, ...] = ("read", "edit")
WIP_MODES: tuple[str, ...] = ("block", "warn")


@dataclass(frozen=True)
class Column:
    """A board column; ``status_aliases`` map external statuses onto it (cockpit)."""

    id: str
    label: str
    color: str = "#7c3aed"
    wip_limit: int | None = None
    done: bool = False
    status_aliases: tuple[str, ...] = ()


#: audit_designer DEFAULT_COLUMNS (workspace.py) – used when a board has no own columns.
DEFAULT_COLUMNS: tuple[Column, ...] = (
    Column("offen", "Offen", "#7c3aed"),
    Column("in_arbeit", "In Arbeit", "#f59e0b"),
    Column("erledigt", "Erledigt", "#10b981"),
)


@dataclass(frozen=True)
class ChecklistItem:
    text: str
    done: bool = False


@dataclass(frozen=True)
class CardLink:
    """Reference to something outside the board, e.g. kind ``notebook-page``."""

    kind: str
    target: str
    title: str = ""


@dataclass(frozen=True)
class Attachment:
    """Attachment metadata only; the bytes stay with the consumer."""

    id: str
    filename: str
    mime_type: str = "application/octet-stream"
    size: int = 0


@dataclass(frozen=True)
class Label:
    id: str
    name: str
    color: str = "#6b7280"


@dataclass(frozen=True)
class Share:
    user_id: str
    permission: str = "read"
    shared_by: str | None = None
    created_at: str | None = None


@dataclass(frozen=True)
class TransitionPolicy:
    """Movement rules.

    ``allowed`` None means every column change is allowed (audit_designer);
    otherwise only the listed (source, target) pairs. Cards never leave a
    ``locked_columns`` column (cockpit ``laeuft``); ``fixed_order_columns``
    forbid reordering inside the column.
    """

    allowed: frozenset[tuple[str, str]] | None = None
    locked_columns: frozenset[str] = frozenset()
    fixed_order_columns: frozenset[str] = frozenset()

    @property
    def mode(self) -> str:
        """``free`` (every change allowed) or ``restricted`` (only ``allowed`` pairs)."""
        return "free" if self.allowed is None else "restricted"


@dataclass(frozen=True)
class Card:
    id: str
    column_id: str
    rank: str
    title: str
    description: str = ""
    priority: str = "mittel"
    tags: tuple[str, ...] = ()
    assignees: tuple[str, ...] = ()
    due: str | None = None
    color: str | None = None
    image: str | None = None
    badge: str | None = None
    checklist: tuple[ChecklistItem, ...] = ()
    links: tuple[CardLink, ...] = ()
    attachments: tuple[Attachment, ...] = ()
    created_at: str = ""
    updated_at: str = ""
    extra: JsonObject = field(default_factory=dict)


def card_order_key(card: Card) -> tuple[str, str, str]:
    """Stable order inside a column: rank, then creation time, then id."""
    return (card.rank, card.created_at, card.id)


@dataclass(frozen=True)
class Board:
    id: str
    title: str
    owner_id: str
    columns: tuple[Column, ...] = DEFAULT_COLUMNS
    cards: tuple[Card, ...] = ()
    labels: tuple[Label, ...] = ()
    shares: tuple[Share, ...] = ()
    transitions: TransitionPolicy = TransitionPolicy()
    wip_mode: str = "block"
    icon: str = "📋"
    pinned: bool = False
    archived: bool = False
    version: int = 0
    created_at: str = ""
    updated_at: str = ""
    extra: JsonObject = field(default_factory=dict)

    def column(self, column_id: str) -> Column | None:
        return next((c for c in self.columns if c.id == column_id), None)

    def card(self, card_id: str) -> Card | None:
        return next((c for c in self.cards if c.id == card_id), None)

    def cards_in(self, column_id: str) -> tuple[Card, ...]:
        """Cards of one column in display order."""
        return tuple(
            sorted((c for c in self.cards if c.column_id == column_id), key=card_order_key)
        )

    def ordered_cards(self) -> tuple[Card, ...]:
        """All cards: column order first, then display order; unknown columns last."""
        result: list[Card] = []
        for column in self.columns:
            result.extend(self.cards_in(column.id))
        known = {c.id for c in self.columns}
        stray = [c for c in self.cards if c.column_id not in known]
        return tuple(result + sorted(stray, key=card_order_key))

    def share_for(self, user_id: str) -> Share | None:
        return next((s for s in self.shares if s.user_id == user_id), None)

    def with_cards(self, cards: tuple[Card, ...]) -> Board:
        return replace(self, cards=cards)


def first_column(board: Board) -> Column:
    """First column (target for removed columns and for re-opening cards)."""
    return board.columns[0]


def done_column(board: Board) -> Column:
    """First column flagged ``done``, otherwise the last column (audit_designer)."""
    flagged = next((c for c in board.columns if c.done), None)
    return flagged if flagged is not None else board.columns[-1]


def column_for_status(board: Board, status: str) -> Column | None:
    """Column whose id or alias equals an external status (cockpit ``spalteVon``)."""
    for column in board.columns:
        if column.id == status or status in column.status_aliases:
            return column
    return None
