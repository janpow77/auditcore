"""JSON (de)serialization of boards; format ``auditcore_kanban.board/1``.

The shape is described by ``schemas/board.schema.json`` (JSON Schema 2020-12)
and mirrored by ``@flowaudit/kanban-core``.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from importlib.resources import files

from .card_fields import as_json_object
from .errors import JsonObject, JsonValue, KanbanError
from .model import (
    WIP_MODES,
    Attachment,
    Board,
    Card,
    CardLink,
    ChecklistItem,
    Column,
    Label,
    Share,
    TransitionPolicy,
)

SCHEMA_VERSION = "auditcore_kanban.board/1"


def board_schema() -> JsonObject:
    """The packaged JSON Schema of the board document."""
    text = files("auditcore_kanban").joinpath("schemas/board.schema.json").read_text("utf-8")
    loaded = json.loads(text)
    return as_json_object("schema", loaded)


# -- to JSON -----------------------------------------------------------------


def column_to_json(column: Column) -> JsonObject:
    return {
        "id": column.id,
        "label": column.label,
        "color": column.color,
        "wip_limit": column.wip_limit,
        "done": column.done,
        "status_aliases": list(column.status_aliases),
    }


def card_to_json(card: Card) -> JsonObject:
    return {
        "id": card.id,
        "column_id": card.column_id,
        "rank": card.rank,
        "title": card.title,
        "description": card.description,
        "priority": card.priority,
        "tags": list(card.tags),
        "assignees": list(card.assignees),
        "due": card.due,
        "color": card.color,
        "image": card.image,
        "badge": card.badge,
        "checklist": [{"text": i.text, "done": i.done} for i in card.checklist],
        "links": [{"kind": x.kind, "target": x.target, "title": x.title} for x in card.links],
        "attachments": [
            {"id": a.id, "filename": a.filename, "mime_type": a.mime_type, "size": a.size}
            for a in card.attachments
        ],
        "created_at": card.created_at,
        "updated_at": card.updated_at,
        "extra": card.extra,
    }


def policy_to_json(policy: TransitionPolicy) -> JsonObject:
    allowed: list[JsonValue] = [[a, b] for a, b in sorted(policy.allowed or ())]
    return {
        "mode": policy.mode,
        "allowed": allowed,
        "locked_columns": [c for c in sorted(policy.locked_columns)],
        "fixed_order_columns": [c for c in sorted(policy.fixed_order_columns)],
    }


def share_to_json(share: Share) -> JsonObject:
    return {
        "user_id": share.user_id,
        "permission": share.permission,
        "shared_by": share.shared_by,
        "created_at": share.created_at,
    }


def board_to_json(board: Board) -> JsonObject:
    """Complete board document; cards in board order for stable output."""
    return {
        "schema_version": SCHEMA_VERSION,
        "id": board.id,
        "title": board.title,
        "icon": board.icon,
        "owner_id": board.owner_id,
        "pinned": board.pinned,
        "archived": board.archived,
        "version": board.version,
        "created_at": board.created_at,
        "updated_at": board.updated_at,
        "columns": [column_to_json(c) for c in board.columns],
        "cards": [card_to_json(c) for c in board.ordered_cards()],
        "labels": [{"id": x.id, "name": x.name, "color": x.color} for x in board.labels],
        "shares": [share_to_json(s) for s in board.shares],
        "transitions": policy_to_json(board.transitions),
        "wip_mode": board.wip_mode,
        "extra": board.extra,
    }


def dumps(board: Board) -> str:
    return json.dumps(board_to_json(board), ensure_ascii=False, indent=2, sort_keys=False)


# -- from JSON ---------------------------------------------------------------


class _Reader:
    """Typed access to one JSON object; errors name the path."""

    def __init__(self, raw: object, path: str) -> None:
        if not isinstance(raw, dict):
            raise KanbanError("INVALID_DOCUMENT", f"{path}: Objekt erwartet")
        self.raw: Mapping[str, object] = raw
        self.path = path

    def _fail(self, key: str) -> KanbanError:
        return KanbanError("INVALID_DOCUMENT", f"{self.path}.{key}: ungültiger Wert")

    def text(self, key: str, default: str | None = None) -> str:
        value = self.raw.get(key, default)
        if not isinstance(value, str):
            raise self._fail(key)
        return value

    def optional_text(self, key: str) -> str | None:
        value = self.raw.get(key)
        return None if value is None else self.text(key)

    def integer(self, key: str, default: int | None = None) -> int | None:
        value = self.raw.get(key, default)
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int):
            raise self._fail(key)
        return value

    def flag(self, key: str, default: bool = False) -> bool:
        value = self.raw.get(key, default)
        if not isinstance(value, bool):
            raise self._fail(key)
        return value

    def texts(self, key: str) -> tuple[str, ...]:
        value = self.raw.get(key, [])
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise self._fail(key)
        return tuple(value)

    def objects(self, key: str) -> list[_Reader]:
        value = self.raw.get(key, [])
        if not isinstance(value, list):
            raise self._fail(key)
        return [_Reader(item, f"{self.path}.{key}[{i}]") for i, item in enumerate(value)]

    def extra(self, key: str = "extra") -> JsonObject:
        value = self.raw.get(key, {})
        try:
            return as_json_object(key, value)
        except KanbanError:
            raise self._fail(key) from None


def column_from_json(r: _Reader) -> Column:
    return Column(
        id=r.text("id"),
        label=r.text("label"),
        color=r.text("color", "#7c3aed"),
        wip_limit=r.integer("wip_limit"),
        done=r.flag("done"),
        status_aliases=r.texts("status_aliases"),
    )


def card_from_json(r: _Reader) -> Card:
    return Card(
        id=r.text("id"), column_id=r.text("column_id"), rank=r.text("rank"),
        title=r.text("title"), description=r.text("description", ""),
        priority=r.text("priority", "mittel"), tags=r.texts("tags"),
        assignees=r.texts("assignees"), due=r.optional_text("due"),
        color=r.optional_text("color"), image=r.optional_text("image"),
        badge=r.optional_text("badge"),
        checklist=tuple(ChecklistItem(i.text("text"), i.flag("done"))
                        for i in r.objects("checklist")),
        links=tuple(CardLink(i.text("kind"), i.text("target"), i.text("title", ""))
                    for i in r.objects("links")),
        attachments=tuple(
            Attachment(i.text("id"), i.text("filename"),
                       i.text("mime_type", "application/octet-stream"), i.integer("size", 0) or 0)
            for i in r.objects("attachments")
        ),
        created_at=r.text("created_at", ""), updated_at=r.text("updated_at", ""),
        extra=r.extra(),
    )


def _pairs(raw: object, path: str) -> frozenset[tuple[str, str]]:
    if not isinstance(raw, list) or not all(
        isinstance(p, list) and len(p) == 2 and all(isinstance(x, str) for x in p) for p in raw
    ):
        raise KanbanError("INVALID_DOCUMENT", f"{path}.allowed: ungültiger Wert")
    return frozenset((str(p[0]), str(p[1])) for p in raw)


def policy_from_json(raw: object, path: str = "transitions") -> TransitionPolicy:
    """``mode`` free ignores ``allowed``; restricted allows only the listed pairs."""
    if raw is None:
        return TransitionPolicy()
    r = _Reader(raw, path)
    mode = r.text("mode", "free")
    if mode not in ("free", "restricted"):
        raise KanbanError("INVALID_DOCUMENT", f"{path}.mode: ungültiger Wert")
    allowed = _pairs(r.raw.get("allowed", []), path) if mode == "restricted" else None
    return TransitionPolicy(
        allowed=allowed,
        locked_columns=frozenset(r.texts("locked_columns")),
        fixed_order_columns=frozenset(r.texts("fixed_order_columns")),
    )


def _wip_mode(r: _Reader) -> str:
    mode = r.text("wip_mode", "block")
    if mode not in WIP_MODES:
        raise KanbanError("INVALID_DOCUMENT", "board.wip_mode: ungültiger Wert")
    return mode


def board_from_json(raw: object) -> Board:
    """Parse and structurally check a board document."""
    r = _Reader(raw, "board")
    version = r.text("schema_version", SCHEMA_VERSION)
    if version != SCHEMA_VERSION:
        raise KanbanError("INVALID_DOCUMENT", f"Unbekannte Formatversion '{version}'")
    columns = tuple(column_from_json(c) for c in r.objects("columns"))
    if not columns:
        raise KanbanError("INVALID_DOCUMENT", "board.columns: mindestens eine Spalte erforderlich")
    return Board(
        id=r.text("id"), title=r.text("title"), owner_id=r.text("owner_id"),
        icon=r.text("icon", "📋"), pinned=r.flag("pinned"), archived=r.flag("archived"),
        version=r.integer("version", 0) or 0,
        created_at=r.text("created_at", ""), updated_at=r.text("updated_at", ""),
        columns=columns,
        cards=tuple(card_from_json(c) for c in r.objects("cards")),
        labels=tuple(Label(x.text("id"), x.text("name"), x.text("color", "#6b7280"))
                     for x in r.objects("labels")),
        shares=tuple(Share(s.text("user_id"), s.text("permission", "read"),
                           s.optional_text("shared_by"), s.optional_text("created_at"))
                     for s in r.objects("shares")),
        transitions=policy_from_json(r.raw.get("transitions")),
        wip_mode=_wip_mode(r),
        extra=r.extra(),
    )


def loads(text: str) -> Board:
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as error:
        raise KanbanError("INVALID_DOCUMENT", f"Kein gültiges JSON: {error.msg}") from None
    return board_from_json(raw)


def columns_from_json(raw: object) -> list[Column]:
    """Column list of a request body."""
    return [column_from_json(c) for c in _Reader({"columns": raw}, "body").objects("columns")]
