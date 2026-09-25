"""Parse JSON-like card fields (REST bodies, Python callers) into validated values."""

from __future__ import annotations

import copy
from collections.abc import Callable, Mapping
from typing import TypeVar

from .errors import JsonObject, JsonValue, KanbanError
from .model import Attachment, CardLink, ChecklistItem
from .validation import (
    Limits,
    normalize_due,
    validate_badge,
    validate_description,
    validate_priority,
    validate_tags,
    validate_title,
)

T = TypeVar("T")
Parser = Callable[[str, object, Limits], object]


def invalid(name: str) -> KanbanError:
    return KanbanError("INVALID_REQUEST", f"Feld '{name}' hat einen ungültigen Typ")


def as_str(name: str, value: object) -> str:
    if not isinstance(value, str):
        raise invalid(name)
    return value


def as_optional_str(name: str, value: object) -> str | None:
    return None if value is None else as_str(name, value)


def as_bool(name: str, value: object) -> bool:
    if not isinstance(value, bool):
        raise invalid(name)
    return value


def as_str_tuple(name: str, value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise invalid(name)
    return tuple(as_str(name, item) for item in value)


def as_objects(name: str, value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list) or not all(isinstance(i, dict) for i in value):
        raise invalid(name)
    return list(value)


def is_json(value: object) -> bool:
    """True for values made of JSON types only."""
    if value is None or isinstance(value, str | bool | int | float):
        return True
    if isinstance(value, list):
        return all(is_json(v) for v in value)
    if isinstance(value, dict):
        return all(isinstance(k, str) and is_json(v) for k, v in value.items())
    return False


def as_json_object(name: str, value: object) -> JsonObject:
    if not isinstance(value, dict) or not is_json(value):
        raise invalid(name)
    result: JsonObject = {}
    for key, item in value.items():
        result[str(key)] = _json(item)
    return result


def _json(value: object) -> JsonValue:
    if isinstance(value, dict):
        return {str(k): _json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json(v) for v in value]
    if value is None or isinstance(value, str | bool | int | float):
        return value
    raise ValueError("not a JSON value")


def _checklist(name: str, value: object, limits: Limits) -> tuple[ChecklistItem, ...]:
    items = as_objects(name, value)
    if len(items) > limits.checklist_max:
        raise KanbanError("VALIDATION_ERROR", "Zu viele Checklisten-Einträge")
    return tuple(
        ChecklistItem(as_str(name, i.get("text")), as_bool(name, i.get("done", False)))
        for i in items
    )


def _links(name: str, value: object, _limits: Limits) -> tuple[CardLink, ...]:
    return tuple(
        CardLink(as_str(name, i.get("kind")), as_str(name, i.get("target")),
                 as_str(name, i.get("title", "")))
        for i in as_objects(name, value)
    )


def _size(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise invalid(name)
    return value


def _attachments(name: str, value: object, _limits: Limits) -> tuple[Attachment, ...]:
    return tuple(
        Attachment(
            as_str(name, i.get("id")),
            as_str(name, i.get("filename")),
            as_str(name, i.get("mime_type", "application/octet-stream")),
            _size(name, i.get("size", 0)),
        )
        for i in as_objects(name, value)
    )


def _cleared(name: str, value: object, _limits: Limits) -> str | None:
    """Nullable text where ``""`` also clears (original card_color / card_image)."""
    return as_optional_str(name, value) or None


#: Declarative field table: JSON name -> parser. ``column_id`` is handled by move logic.
CARD_FIELDS: Mapping[str, Parser] = {
    "title": lambda n, v, lim: validate_title(as_str(n, v), lim),
    "description": lambda n, v, lim: validate_description(as_str(n, v), lim),
    "priority": lambda n, v, _lim: validate_priority(as_str(n, v)),
    "tags": lambda n, v, lim: validate_tags(as_str_tuple(n, v), lim),
    "assignees": lambda n, v, _lim: as_str_tuple(n, v),
    "due": lambda n, v, _lim: normalize_due(as_optional_str(n, v)),
    "color": _cleared,
    "image": _cleared,
    "badge": lambda n, v, lim: validate_badge(as_optional_str(n, v), lim),
    "checklist": _checklist,
    "links": _links,
    "attachments": _attachments,
    "extra": lambda n, v, _lim: as_json_object(n, v),
}


def parse_card_fields(fields: Mapping[str, object], limits: Limits) -> dict[str, object]:
    """Validated values for the known card fields present in ``fields``."""
    return {
        name: parser(name, fields[name], limits)
        for name, parser in CARD_FIELDS.items()
        if name in fields
    }


def with_fields(obj: T, values: Mapping[str, object]) -> T:
    """Copy of a frozen dataclass with already validated attribute values."""
    new = copy.copy(obj)
    for name, value in values.items():
        object.__setattr__(new, name, value)
    return new
