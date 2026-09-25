"""Endpoint handlers of the REST contract (docs/kanban/rest-api.md)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

from ..card_fields import as_optional_str, as_str
from ..errors import JsonObject, JsonValue, KanbanError
from ..filtering import DUE_STATES, CardFilter
from ..model import Board
from ..permissions import Action, authorize
from ..serialization import (
    board_to_json,
    card_to_json,
    columns_from_json,
    policy_from_json,
    share_to_json,
)
from ..service import BoardService, Outcome
from ..stats import board_stats
from ..templates import TEMPLATES


@dataclass(frozen=True)
class ApiRequest:
    user_id: str
    params: Mapping[str, str]
    query: Mapping[str, str]
    body: object
    if_match: str | None = None


@dataclass(frozen=True)
class Result:
    status: int
    body: JsonValue
    version: int | None = None


def _body(request: ApiRequest) -> Mapping[str, object]:
    if request.body is None:
        return {}
    if not isinstance(request.body, dict):
        raise KanbanError("INVALID_REQUEST", "JSON-Objekt als Anfragekörper erwartet")
    return request.body


def expected_version(request: ApiRequest) -> int | None:
    """``expected_version`` from the body, else from ``If-Match: "<version>"``."""
    value = _body(request).get("expected_version")
    if value is None and request.if_match:
        value = request.if_match.removeprefix("W/").strip('"')
        if not value.isdigit():
            raise KanbanError("INVALID_REQUEST", "If-Match muss eine Board-Version sein")
        return int(value)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise KanbanError("INVALID_REQUEST", "Feld 'expected_version' hat einen ungültigen Typ")
    return value


def _optional_bool(body: Mapping[str, object], key: str) -> bool | None:
    value = body.get(key)
    if value is not None and not isinstance(value, bool):
        raise KanbanError("INVALID_REQUEST", f"Feld '{key}' hat einen ungültigen Typ")
    return value


def board_body(board: Board, role: str) -> JsonObject:
    return {"board": board_to_json(board), "role": role, "stats": board_stats(board)}


def summary(board: Board, role: str) -> JsonObject:
    return {
        "id": board.id, "title": board.title, "icon": board.icon, "owner_id": board.owner_id,
        "pinned": board.pinned, "archived": board.archived, "version": board.version,
        "updated_at": board.updated_at, "role": role, "stats": board_stats(board),
    }


def mutation(outcome: Outcome, status: int = 200) -> Result:
    result = outcome.result
    body: JsonObject = {
        "version": outcome.board.version,
        "card": None if result.card is None else card_to_json(result.card),
        "changed_cards": [card_to_json(c) for c in result.changed_cards],
        "warnings": list(result.warnings),
        "events": [e.to_json() for e in outcome.events],
    }
    return Result(status, body, outcome.board.version)


# -- boards ------------------------------------------------------------------


def list_templates(_service: BoardService, _request: ApiRequest) -> Result:
    return Result(200, {"templates": [t.to_json() for t in TEMPLATES]})


def list_boards(service: BoardService, request: ApiRequest) -> Result:
    archived = request.query.get("archived") == "true"
    boards = service.list_boards(request.user_id, archived)
    rows: list[JsonValue] = [summary(b, r) for b, r in boards]
    return Result(200, {"boards": rows})


def create_board(service: BoardService, request: ApiRequest) -> Result:
    body = _body(request)
    outcome = service.create_board(
        request.user_id,
        title=as_str("title", body.get("title", "Neues Board")),
        icon=as_str("icon", body.get("icon", "📋")),
        template_key=as_optional_str("template", body.get("template")),
        board_id=as_optional_str("id", body.get("id")),
    )
    return Result(201, board_body(outcome.board, "owner"), outcome.board.version)


def get_board(service: BoardService, request: ApiRequest) -> Result:
    board, role = service.get_board(request.params["board_id"], request.user_id)
    return Result(200, board_body(board, role), board.version)


def patch_board(service: BoardService, request: ApiRequest) -> Result:
    body = _body(request)
    outcome = service.update_board(
        request.params["board_id"], request.user_id,
        title=as_optional_str("title", body.get("title")),
        icon=as_optional_str("icon", body.get("icon")),
        pinned=_optional_bool(body, "pinned"),
        archived=_optional_bool(body, "archived"),
        expected_version=expected_version(request),
    )
    board, role = service.get_board(outcome.board.id, request.user_id)
    return Result(200, board_body(board, role), board.version)


def delete_board(service: BoardService, request: ApiRequest) -> Result:
    service.delete_board(request.params["board_id"], request.user_id)
    return Result(204, None)


def put_columns(service: BoardService, request: ApiRequest) -> Result:
    body = _body(request)
    transitions = body.get("transitions")
    outcome = service.configure_columns(
        request.params["board_id"], request.user_id,
        columns_from_json(body.get("columns")),
        None if transitions is None else policy_from_json(transitions),
        expected_version(request),
    )
    return Result(200, board_body(outcome.board, "owner"), outcome.board.version)


# -- cards -------------------------------------------------------------------


def _set(query: Mapping[str, str], key: str) -> frozenset[str]:
    raw = query.get(key, "")
    return frozenset(v for v in raw.split(",") if v)


def card_filter(query: Mapping[str, str]) -> CardFilter:
    due = _set(query, "due")
    if not due <= set(DUE_STATES):
        raise KanbanError("INVALID_REQUEST", f"due erlaubt: {', '.join(DUE_STATES)}")
    return CardFilter(
        query=query.get("q", ""), priorities=_set(query, "priority"), tags=_set(query, "tag"),
        assignees=_set(query, "assignee"), columns=_set(query, "column"), due_states=due,
    )


def list_cards(service: BoardService, request: ApiRequest) -> Result:
    today_raw = request.query.get("today")
    try:
        today = date.fromisoformat(today_raw) if today_raw else None
    except ValueError:
        raise KanbanError("INVALID_REQUEST", "today muss ein ISO-Datum sein") from None
    cards = service.find_cards(
        request.params["board_id"], request.user_id, card_filter(request.query), today
    )
    rows: list[JsonValue] = [card_to_json(c) for c in cards]
    return Result(200, {"cards": rows})


def create_card(service: BoardService, request: ApiRequest) -> Result:
    outcome = service.create_card(
        request.params["board_id"], request.user_id, _body(request), expected_version(request)
    )
    return mutation(outcome, 201)


def patch_card(service: BoardService, request: ApiRequest) -> Result:
    p = request.params
    return mutation(service.update_card(
        p["board_id"], request.user_id, p["card_id"], _body(request), expected_version(request)
    ))


def delete_card(service: BoardService, request: ApiRequest) -> Result:
    p = request.params
    return mutation(service.delete_card(
        p["board_id"], request.user_id, p["card_id"], expected_version(request)
    ))


def _index(body: Mapping[str, object]) -> int | None:
    value = body.get("index")
    if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
        raise KanbanError("INVALID_REQUEST", "Feld 'index' hat einen ungültigen Typ")
    return value


def move_card(service: BoardService, request: ApiRequest) -> Result:
    body, p = _body(request), request.params
    return mutation(service.move_card(
        p["board_id"], request.user_id, p["card_id"], as_str("column_id", body.get("column_id")),
        before_id=as_optional_str("before_id", body.get("before_id")),
        after_id=as_optional_str("after_id", body.get("after_id")),
        index=_index(body), expected_version=expected_version(request),
    ))


def toggle_done(service: BoardService, request: ApiRequest) -> Result:
    p = request.params
    return mutation(service.toggle_done(
        p["board_id"], request.user_id, p["card_id"], expected_version(request)
    ))


# -- shares and events ---------------------------------------------------------


def list_shares(service: BoardService, request: ApiRequest) -> Result:
    board, _ = service.get_board(request.params["board_id"], request.user_id)
    authorize(board, request.user_id, Action.SHARE).raise_if_denied()
    rows: list[JsonValue] = [share_to_json(s) for s in board.shares]
    return Result(200, {"shares": rows}, board.version)


def put_share(service: BoardService, request: ApiRequest) -> Result:
    p = request.params
    permission = as_str("permission", _body(request).get("permission"))
    return mutation(service.share(p["board_id"], request.user_id, p["user_id"], permission))


def delete_share(service: BoardService, request: ApiRequest) -> Result:
    p = request.params
    return mutation(service.revoke(p["board_id"], request.user_id, p["user_id"]))


def list_events(service: BoardService, request: ApiRequest) -> Result:
    raw = request.query.get("since", "0")
    if not raw.isdigit():
        raise KanbanError("INVALID_REQUEST", "since muss eine nicht negative Zahl sein")
    events = service.events_since(request.params["board_id"], request.user_id, int(raw))
    rows: list[JsonValue] = [e.to_json() for e in events]
    return Result(200, {"events": rows})
