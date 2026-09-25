"""Bridge to the audit_designer workspace format (``vpai_pages`` + ``vpai_workspace_tasks``).

Import turns 1-based positions into rank keys (``spread_ranks``) in the order
the original shows cards (position, then ``created_at``); export produces
positions 1..N per column again, so a consumer can migrate in both directions.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace

from .errors import JsonObject, JsonValue
from .model import DEFAULT_COLUMNS, Board, Card, ChecklistItem, Column, Share
from .rank import spread_ranks

#: Old share dialog value "write" means "edit" (the backend only knew read/edit).
LEGACY_PERMISSIONS: Mapping[str, str] = {"read": "read", "edit": "edit", "write": "edit"}
LEGACY_EXTRA_FIELDS = ("generated_prompt", "prompt_generated_at", "file_count")


def _text(row: Mapping[str, object], key: str, default: str = "") -> str:
    value = row.get(key)
    return default if value is None else str(value)


def _optional(row: Mapping[str, object], key: str) -> str | None:
    value = row.get(key)
    return None if value in (None, "") else str(value)


def _texts(row: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = row.get(key)
    return tuple(str(v) for v in value) if isinstance(value, list) else ()


def _position(row: Mapping[str, object]) -> int:
    value = row.get("position")
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _columns(page: Mapping[str, object]) -> tuple[Column, ...]:
    raw = page.get("board_columns")
    if not isinstance(raw, list) or not raw:
        return DEFAULT_COLUMNS
    return tuple(
        Column(_text(c, "id"), _text(c, "label"), _text(c, "color", "#7c3aed"))
        for c in raw
        if isinstance(c, dict)
    )


def _checklist(row: Mapping[str, object]) -> tuple[ChecklistItem, ...]:
    raw = row.get("checklist")
    if not isinstance(raw, list):
        return ()
    return tuple(
        ChecklistItem(_text(i, "text"), i.get("done") is True) for i in raw if isinstance(i, dict)
    )


def _extra(row: Mapping[str, object], column_known: bool) -> JsonObject:
    extra: JsonObject = {"legacy_position": _position(row)}
    for key in LEGACY_EXTRA_FIELDS:
        value = row.get(key)
        if isinstance(value, str | int) and not isinstance(value, bool):
            extra[key] = value
    if not column_known:
        extra["legacy_status"] = _text(row, "status")
    return extra


def task_to_card(row: Mapping[str, object], column_id: str, rank: str, known: bool) -> Card:
    """One legacy task dict (``VpaiWorkspaceTask.to_dict``) as a card."""
    return Card(
        id=_text(row, "id"),
        column_id=column_id,
        rank=rank,
        title=_text(row, "title"),
        description=_text(row, "description"),
        priority=_text(row, "priority", "mittel"),
        tags=_texts(row, "tags"),
        due=_optional(row, "deadline"),
        color=_optional(row, "card_color"),
        image=_optional(row, "card_image"),
        badge=_optional(row, "badge"),
        checklist=_checklist(row),
        created_at=_text(row, "created_at"),
        updated_at=_text(row, "updated_at"),
        extra=_extra(row, known),
    )


def _cards(tasks: Sequence[Mapping[str, object]], columns: tuple[Column, ...]) -> tuple[Card, ...]:
    ids = [c.id for c in columns]
    cards: list[Card] = []
    groups: dict[str, list[Mapping[str, object]]] = {}
    for row in tasks:
        status = _text(row, "status")
        groups.setdefault(status if status in ids else ids[0], []).append(row)
    for column_id, rows in groups.items():
        rows.sort(key=lambda r: (_text(r, "status") not in ids, _position(r),
                                _text(r, "created_at")))
        for row, rank in zip(rows, spread_ranks(len(rows)), strict=True):
            cards.append(task_to_card(row, column_id, rank, _text(row, "status") in ids))
    return tuple(cards)


def _shares(shares: Sequence[Mapping[str, object]]) -> tuple[Share, ...]:
    return tuple(
        Share(
            user_id=_text(s, "shared_with_user_id"),
            permission=LEGACY_PERMISSIONS.get(_text(s, "permission"), "read"),
            shared_by=_optional(s, "shared_by_user_id"),
            created_at=_optional(s, "created_at"),
        )
        for s in shares
    )


def import_workspace(
    page: Mapping[str, object],
    tasks: Sequence[Mapping[str, object]],
    shares: Sequence[Mapping[str, object]] = (),
) -> Board:
    """Board from ``VpaiPage.to_dict()``, task dicts and share rows.

    Tasks with a status that is no column of the page land in the first column
    and keep their old status in ``extra.legacy_status`` (the original UI did
    not show them at all).
    """
    columns = _columns(page)
    board = Board(
        id=_text(page, "id"),
        title=_text(page, "title", "Workspace"),
        owner_id=_text(page, "owner_user_id"),
        icon=_text(page, "icon", "📋"),
        pinned=page.get("is_pinned") is True,
        archived=page.get("is_archived") is True,
        columns=columns,
        version=1,
        created_at=_text(page, "created_at"),
        updated_at=_text(page, "updated_at"),
        extra={"legacy_notebook_id": _text(page, "notebook_id")},
    )
    return replace(board, cards=_cards(tasks, columns), shares=_shares(shares))


def export_board_columns(board: Board) -> list[JsonObject]:
    """``board_columns`` value of the page (id, label, color)."""
    return [{"id": c.id, "label": c.label, "color": c.color} for c in board.columns]


def export_workspace_tasks(board: Board) -> list[JsonObject]:
    """Task dicts with ``status`` = column and ``position`` 1..N per column."""
    rows: list[JsonObject] = []
    for column in board.columns:
        for position, card in enumerate(board.cards_in(column.id), start=1):
            checklist: list[JsonValue] = [{"text": i.text, "done": i.done} for i in card.checklist]
            row: JsonObject = {
                "id": card.id, "title": card.title, "description": card.description,
                "status": column.id, "priority": card.priority, "position": position,
                "tags": list(card.tags), "deadline": card.due, "card_color": card.color,
                "card_image": card.image, "badge": card.badge, "checklist": checklist,
                "created_at": card.created_at, "updated_at": card.updated_at,
            }
            for key in LEGACY_EXTRA_FIELDS:
                if key in card.extra:
                    row[key] = card.extra[key]
            rows.append(row)
    return rows
