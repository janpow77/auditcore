from __future__ import annotations

import pytest

from auditcore_kanban import BoardService, InMemoryBoardStore


def test_starlette_app(tmp_path) -> None:  # type: ignore[no-untyped-def]
    pytest.importorskip("starlette")
    testclient = pytest.importorskip("starlette.testclient")
    from auditcore_kanban.rest.asgi import create_app

    (tmp_path / "index.html").write_text("<p>ui</p>")
    app = create_app(BoardService(InMemoryBoardStore()), lambda h: h.get("x-user"),
                     ui_directory=tmp_path)
    client = testclient.TestClient(app)
    assert client.get("/boards").status_code == 401
    created = client.post("/boards", json={"id": "b1"}, headers={"X-User": "u1"})
    assert created.status_code == 201 and created.headers["etag"] == '"1"'
    broken = client.post("/boards/b1/cards", content=b"{", headers={"X-User": "u1"})
    assert broken.status_code == 422
    assert client.delete("/boards/b1", headers={"X-User": "u1"}).status_code == 204
    assert client.get("/ui/").text == "<p>ui</p>"


def test_fastapi_router() -> None:
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from auditcore_kanban.rest.fastapi_router import create_router

    class User:
        id = 7

    app = fastapi.FastAPI()
    app.include_router(create_router(BoardService(InMemoryBoardStore()), lambda: User()),
                       prefix="/api/kanban")
    client = testclient.TestClient(app)
    created = client.post("/api/kanban/boards", json={"id": "b1", "title": "Prüfung"})
    assert created.status_code == 201 and created.json()["board"]["owner_id"] == "7"
    assert client.post("/api/kanban/boards/b1/cards", content=b"x").status_code == 422
    assert client.get("/api/kanban/boards/b1").json()["role"] == "owner"
    assert client.delete("/api/kanban/boards/b1").status_code == 204
