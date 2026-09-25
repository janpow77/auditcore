"""Framework-free REST handler implementing docs/kanban/rest-api.md.

Adapters (``asgi.create_app``, ``fastapi_router.create_router``) only translate
their request into :meth:`KanbanApi.handle` and the :class:`ApiResponse` back.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

from ..errors import JsonValue, KanbanError
from ..service import BoardService
from . import handlers as h
from .handlers import ApiRequest


@dataclass(frozen=True)
class ApiResponse:
    status: int
    body: JsonValue
    headers: dict[str, str] = field(default_factory=dict)


Handler = Callable[[BoardService, ApiRequest], h.Result]

_ID = r"(?P<{}>[A-Za-z0-9][A-Za-z0-9_.-]{{0,127}})"
_BOARD = _ID.format("board_id")
_CARD = _ID.format("card_id")
_USER = r"(?P<user_id>[^/]{1,128})"

#: Declarative route table: (method, path pattern, handler).
ROUTES: tuple[tuple[str, str, Handler], ...] = (
    ("GET", r"/templates", h.list_templates),
    ("GET", r"/boards", h.list_boards),
    ("POST", r"/boards", h.create_board),
    ("GET", rf"/boards/{_BOARD}", h.get_board),
    ("PATCH", rf"/boards/{_BOARD}", h.patch_board),
    ("DELETE", rf"/boards/{_BOARD}", h.delete_board),
    ("PUT", rf"/boards/{_BOARD}/columns", h.put_columns),
    ("GET", rf"/boards/{_BOARD}/cards", h.list_cards),
    ("POST", rf"/boards/{_BOARD}/cards", h.create_card),
    ("PATCH", rf"/boards/{_BOARD}/cards/{_CARD}", h.patch_card),
    ("DELETE", rf"/boards/{_BOARD}/cards/{_CARD}", h.delete_card),
    ("POST", rf"/boards/{_BOARD}/cards/{_CARD}/move", h.move_card),
    ("POST", rf"/boards/{_BOARD}/cards/{_CARD}/toggle-done", h.toggle_done),
    ("GET", rf"/boards/{_BOARD}/shares", h.list_shares),
    ("PUT", rf"/boards/{_BOARD}/shares/{_USER}", h.put_share),
    ("DELETE", rf"/boards/{_BOARD}/shares/{_USER}", h.delete_share),
    ("GET", rf"/boards/{_BOARD}/events", h.list_events),
)
_COMPILED = tuple((m, re.compile(p + r"/?"), fn) for m, p, fn in ROUTES)
METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")


def _error(error: KanbanError) -> ApiResponse:
    return ApiResponse(error.status, error.to_json())


class KanbanApi:
    """Dispatches one request; never raises for domain errors."""

    def __init__(self, service: BoardService) -> None:
        self.service = service

    def _route(self, method: str, path: str) -> tuple[Handler, dict[str, str]]:
        matched_path = False
        for route_method, pattern, handler in _COMPILED:
            found = pattern.fullmatch(path)
            if found is None:
                continue
            matched_path = True
            if route_method == method:
                return handler, found.groupdict()
        if matched_path:
            raise KanbanError("METHOD_NOT_ALLOWED", "Methode nicht erlaubt")
        raise KanbanError("ROUTE_NOT_FOUND", "Pfad nicht gefunden")

    def handle(
        self,
        method: str,
        path: str,
        *,
        user_id: str | None,
        query: Mapping[str, str] | None = None,
        body: object = None,
        if_match: str | None = None,
    ) -> ApiResponse:
        """Status, JSON body and headers (``ETag`` with the board version)."""
        try:
            handler, params = self._route(method.upper(), path)
            if user_id is None:
                raise KanbanError("UNAUTHENTICATED", "Anmeldung erforderlich")
            request = ApiRequest(user_id, params, query or {}, body, if_match)
            result = handler(self.service, request)
        except KanbanError as error:
            return _error(error)
        headers = {} if result.version is None else {"ETag": f'"{result.version}"'}
        return ApiResponse(result.status, result.body, headers)
