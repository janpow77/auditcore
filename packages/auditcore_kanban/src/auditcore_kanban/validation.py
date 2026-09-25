"""Input validation with the limits and German messages of audit_designer (workspace.py)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import datetime

from .errors import KanbanError
from .model import PRIORITIES, Column

COLUMN_ID_PATTERN = r"^[a-z0-9][a-z0-9_-]{0,49}$"
_COLUMN_ID_RE = re.compile(COLUMN_ID_PATTERN)


@dataclass(frozen=True)
class Limits:
    """Defaults are the constants of the original backend."""

    title_max: int = 300
    description_max: int = 10000
    tags_max: int = 20
    tag_length_max: int = 80
    columns_min: int = 1
    columns_max: int = 10
    column_label_max: int = 80
    board_title_max: int = 500
    badge_max: int = 20
    checklist_max: int = 200


DEFAULT_LIMITS = Limits()


def _fail(message: str) -> KanbanError:
    return KanbanError("VALIDATION_ERROR", message)


def validate_title(title: str, limits: Limits = DEFAULT_LIMITS) -> str:
    """Trimmed card title; empty or too long is rejected."""
    stripped = title.strip()
    if not stripped:
        raise _fail("Titel darf nicht leer sein")
    if len(stripped) > limits.title_max:
        raise _fail("Titel ist zu lang")
    return stripped


def validate_description(description: str, limits: Limits = DEFAULT_LIMITS) -> str:
    if len(description) > limits.description_max:
        raise _fail("Beschreibung ist zu lang")
    return description


def validate_tags(tags: Sequence[str], limits: Limits = DEFAULT_LIMITS) -> tuple[str, ...]:
    if len(tags) > limits.tags_max:
        raise _fail("Zu viele Tags")
    if any(len(tag) > limits.tag_length_max for tag in tags):
        raise _fail("Tag ist zu lang")
    return tuple(tags)


def validate_priority(priority: str) -> str:
    if priority not in PRIORITIES:
        raise _fail(f"Ungültige Priorität '{priority}'. Erlaubt: {sorted(PRIORITIES)}")
    return priority


def validate_badge(badge: str | None, limits: Limits = DEFAULT_LIMITS) -> str | None:
    """Empty clears the badge (original); longer than the DB column is rejected."""
    if not badge:
        return None
    if len(badge) > limits.badge_max:
        raise _fail("Badge ist zu lang")
    return badge


def validate_board_title(title: str, limits: Limits = DEFAULT_LIMITS) -> str:
    stripped = title.strip()
    if not stripped:
        raise _fail("Titel darf nicht leer sein")
    if len(stripped) > limits.board_title_max:
        raise _fail("Titel ist zu lang")
    return stripped


def normalize_due(value: str | None) -> str | None:
    """ISO date or date-time (``Z`` allowed); empty/None clears. Invalid is rejected."""
    if value is None or value == "":
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise _fail("Ungültiges Deadline-Format") from None
    if len(value) == 10:
        return parsed.date().isoformat()
    return parsed.isoformat()


def _check_column(column: Column, limits: Limits) -> Column:
    if not _COLUMN_ID_RE.match(column.id):
        raise _fail("Spalten-ID darf nur Kleinbuchstaben, Zahlen, _ und - enthalten")
    if not column.label or len(column.label) > limits.column_label_max:
        raise _fail("Spaltenlabel ist ungültig")
    if column.wip_limit is not None and column.wip_limit < 1:
        raise _fail("WIP-Limit muss mindestens 1 sein")
    return column


def validate_columns(
    columns: Sequence[Column], limits: Limits = DEFAULT_LIMITS
) -> tuple[Column, ...]:
    """Column set in the original check order: count, unique ids, then each column."""
    if len(columns) < limits.columns_min:
        raise _fail("Mindestens eine Spalte erforderlich")
    if len(columns) > limits.columns_max:
        raise _fail(f"Maximal {limits.columns_max} Spalten erlaubt")
    stripped = [replace(c, id=c.id.strip(), label=c.label.strip()) for c in columns]
    ids = [c.id for c in stripped]
    if len(ids) != len(set(ids)):
        raise _fail("Spalten-IDs müssen eindeutig sein")
    return tuple(_check_column(c, limits) for c in stripped)
