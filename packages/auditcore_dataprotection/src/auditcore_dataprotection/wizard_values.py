"""Typed wizard answers: numbers and tables (e.g. transfers with legal basis).

The REST contract transports every answer as text. A number is a non-negative
integer in text form; a table is a JSON list of rows whose keys are the
columns of the question. Both are validated before they reach the register.
"""

from __future__ import annotations

import json
from collections.abc import Mapping

from .errors import ValidationError
from .wizard_catalog import KIND_NUMBER, KIND_TABLE, QuestionDef

MAX_ROWS = 200


def _rows(question: QuestionDef, value: str) -> list[dict[str, str]]:
    try:
        raw = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"{question.id}: die Tabelle ist nicht lesbar.") from exc
    if not isinstance(raw, list) or len(raw) > MAX_ROWS:
        raise ValidationError(
            f"{question.id}: erwartet wird eine Liste mit höchstens {MAX_ROWS} Zeilen."
        )
    keys = {key for key, _, _ in question.columns}
    rows: list[dict[str, str]] = []
    for index, row in enumerate(raw, start=1):
        if not isinstance(row, Mapping) or set(row) - keys:
            raise ValidationError(f"{question.id}: Zeile {index} enthält unbekannte Spalten.")
        clean = {k: str(row.get(k) or "").strip() for k in keys}
        missing = [
            title for key, title, required in question.columns if required and not clean[key]
        ]
        if missing:
            raise ValidationError(f"{question.id}: in Zeile {index} fehlt {', '.join(missing)}.")
        rows.append(clean)
    if not rows:
        raise ValidationError(f"{question.id}: mindestens eine Zeile angeben oder „unklar“ wählen.")
    return rows


def check_typed(question: QuestionDef, value: str) -> None:
    """Reject numbers and tables that are not well-formed."""
    if question.kind == KIND_NUMBER and not value.strip().isdigit():
        raise ValidationError(f"{question.id}: erwartet wird eine ganze Zahl ab 0.")
    if question.kind == KIND_TABLE:
        _rows(question, value)


def to_register(question: QuestionDef, value: str) -> object:
    """Register representation of a confirmed, typed answer."""
    if question.kind == KIND_NUMBER:
        return int(value.strip())
    if question.kind == KIND_TABLE:
        return _rows(question, value)
    return value


def from_register(question: QuestionDef, value: object) -> str | None:
    """Wizard text form of a register value of a typed question."""
    if question.kind == KIND_NUMBER and isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if question.kind == KIND_TABLE and isinstance(value, list) and value:
        return json.dumps(value, ensure_ascii=False)
    return None
