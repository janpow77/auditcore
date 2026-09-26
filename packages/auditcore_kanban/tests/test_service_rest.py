from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from auditcore_kanban import BoardService, InMemoryBoardStore, KanbanError
from auditcore_kanban.rest import KanbanApi


def _service(**kwargs: Any) -> BoardService:
    ids = iter(f"id{i}" for i in range(1, 1000))
    return BoardService(InMemoryBoardStore(), clock=lambda: "2026-09-25T12:00:00+00:00",
                        new_id=lambda: next(ids), **kwargs)


@pytest.fixture
def api() -> KanbanApi:
    service = _service(user_exists=lambda u: u != "ghost",
                       inherited_grants=lambda b: {"nb": "edit"})
    return KanbanApi(service)


def _call(api: KanbanApi, user: str | None = "u1") -> Callable[..., Any]:
    def call(method: str, path: str, body: object = None, **kw: Any) -> Any:
        return api.handle(method, path, user_id=user, body=body, **kw)
    return call


def test_board_lifecycle(api: KanbanApi) -> None:
    owner = _call(api)
    created = owner("POST", "/boards", {"title": "Prüfung", "template": "einfach", "id": "b1"})
    assert created.status == 201 and created.headers == {"ETag": '"1"'}
    assert [c["id"] for c in created.body["board"]["columns"]] == ["todo", "erledigt"]
    card = owner("POST", "/boards/b1/cards", {"title": "A"})
    assert card.status == 201 and card.body["card"]["column_id"] == "todo"
    assert card.body["version"] == 2 and card.body["events"][0]["kind"] == "card.created"
    moved = owner("POST", f"/boards/b1/cards/{card.body['card']['id']}/move",
                  {"column_id": "erledigt", "expected_version": 2})
    assert moved.status == 200 and moved.body["card"]["column_id"] == "erledigt"
    stale = owner("PATCH", "/boards/b1/cards/id1", {"title": "B"}, if_match='"2"')
    assert stale.status == 409 and stale.body["error"]["code"] == "VERSION_CONFLICT"
    patched = owner("PATCH", "/boards/b1/cards/id1", {"title": "B"}, if_match='W/"3"')
    assert patched.status == 200 and patched.body["card"]["title"] == "B"
    toggled = owner("POST", "/boards/b1/cards/id1/toggle-done")
    assert toggled.body["card"]["column_id"] == "todo"
    listed = owner("GET", "/boards/b1/cards", query={"q": "b", "column": "todo"})
    assert [c["id"] for c in listed.body["cards"]] == ["id1"]
    events = owner("GET", "/boards/b1/events", query={"since": "2"})
    assert [e["kind"] for e in events.body["events"]] == ["card.moved", "card.updated",
                                                         "card.moved"]
    assert owner("DELETE", "/boards/b1/cards/id1").status == 200
    board = owner("GET", "/boards/b1")
    assert board.body["stats"]["total"] == 0 and board.body["role"] == "owner"
    assert owner("DELETE", "/boards/b1").status == 204
    assert owner("GET", "/boards/b1").status == 404


def test_rights_and_sharing(api: KanbanApi) -> None:
    owner, editor, reader, stranger = (_call(api, u) for u in ("u1", "u2", "u3", "u9"))
    owner("POST", "/boards", {"id": "b1"})
    assert owner("PUT", "/boards/b1/shares/u2", {"permission": "edit"}).status == 200
    assert owner("PUT", "/boards/b1/shares/u3", {"permission": "read"}).status == 200
    assert owner("PUT", "/boards/b1/shares/u4", {"permission": "write"}).status == 400
    assert owner("PUT", "/boards/b1/shares/ghost", {"permission": "read"}).status == 404
    assert owner("PUT", "/boards/b1/shares/u1", {"permission": "read"}).status == 400
    assert editor("POST", "/boards/b1/cards", {"title": "x"}).status == 201
    columns = {"columns": [{"id": "a", "label": "A"}]}
    assert editor("PUT", "/boards/b1/columns", columns).status == 403
    assert editor("GET", "/boards/b1/shares").status == 403
    assert reader("POST", "/boards/b1/cards", {"title": "x"}).status == 403
    assert stranger("GET", "/boards/b1").status == 404
    assert _call(api, "nb")("POST", "/boards/b1/cards", {"title": "geerbt"}).status == 201
    assert [b["id"] for b in reader("GET", "/boards").body["boards"]] == ["b1"]
    assert reader("DELETE", "/boards/b1/shares/u3").status == 200
    assert reader("GET", "/boards/b1").status == 404
    shares = owner("GET", "/boards/b1/shares").body["shares"]
    assert [s["user_id"] for s in shares] == ["u2"]


def test_configure_and_pin(api: KanbanApi) -> None:
    owner = _call(api)
    owner("POST", "/boards", {"id": "b1"})
    owner("POST", "/boards/b1/cards", {"title": "x", "column_id": "in_arbeit"})
    body = {"columns": [{"id": "offen", "label": "Offen"},
                        {"id": "fertig", "label": "Fertig", "done": True, "wip_limit": 3}],
            "transitions": {"mode": "restricted", "allowed": [["offen", "fertig"]]}}
    configured = owner("PUT", "/boards/b1/columns", body)
    assert configured.status == 200
    assert configured.body["board"]["cards"][0]["column_id"] == "offen"
    assert configured.body["board"]["transitions"]["mode"] == "restricted"
    pinned = owner("PATCH", "/boards/b1", {"pinned": True, "title": "Neu"})
    assert pinned.body["board"]["pinned"] and pinned.body["board"]["title"] == "Neu"
    assert owner("GET", "/templates").body["templates"][0]["key"] == "standard"


@pytest.mark.parametrize(("method", "path", "body", "status", "code"), [
    ("GET", "/nope", None, 404, "ROUTE_NOT_FOUND"),
    ("PUT", "/boards", None, 405, "METHOD_NOT_ALLOWED"),
    ("POST", "/boards", [1], 422, "INVALID_REQUEST"),
    ("POST", "/boards", {"title": 3}, 422, "INVALID_REQUEST"),
    ("POST", "/boards", {"template": "x"}, 400, "VALIDATION_ERROR"),
    ("GET", "/boards/b1/cards?", None, 404, "ROUTE_NOT_FOUND"),
])
def test_errors(api: KanbanApi, method: str, path: str, body: object, status: int,
                code: str) -> None:
    response = _call(api)(method, path, body)
    assert (response.status, response.body["error"]["code"]) == (status, code)


def test_query_and_header_errors(api: KanbanApi) -> None:
    owner = _call(api)
    owner("POST", "/boards", {"id": "b1"})
    assert owner("GET", "/boards/b1/events", query={"since": "-1"}).status == 422
    assert owner("GET", "/boards/b1/cards", query={"due": "bald"}).status == 422
    assert owner("GET", "/boards/b1/cards", query={"today": "x"}).status == 422
    assert owner("PATCH", "/boards/b1", {"pinned": "ja"}).status == 422
    assert owner("PATCH", "/boards/b1", {}, if_match="abc").status == 422
    bad_index = {"column_id": "offen", "index": "1"}
    assert owner("POST", "/boards/b1/cards/x/move", bad_index).status == 422
    assert owner("POST", "/boards", {"id": "b1"}).status == 409
    assert _call(api, None)("GET", "/boards").status == 401


def test_service_direct_use() -> None:
    service = _service()
    service.create_board("u1", board_id="b1")
    with pytest.raises(KanbanError, match="VERSION_CONFLICT"):
        service.create_card("b1", "u1", {"title": "x"}, expected_version=7)
    assert service.list_boards("u2") == []
    service.share("b1", "u1", "u2", "read")
    with pytest.raises(KanbanError, match="FORBIDDEN"):
        service.delete_board("b1", "u2")
    archived = service.update_board("b1", "u1", archived=True)
    assert archived.board.archived and service.list_boards("u1") == []
    assert [b.id for b, _ in service.list_boards("u1", include_archived=True)] == ["b1"]

