"""HTTP-Vertrag über Starlette (Extra ``web``) und FastAPI (Extra ``fastapi``)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from conftest import fixture_path

pytest.importorskip("starlette")
pytest.importorskip("multipart")
pytest.importorskip("httpx")
pytest.importorskip("lxml")
pytest.importorskip("rapidfuzz")

from starlette.requests import Request  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

from auditcore_documents.web import ServiceSettings, SynopsisService, create_app  # noqa: E402


def files(old: str = "tx_block_alt.docx", new: str = "tx_block_neu.docx") -> dict[str, Any]:
    return {
        "old_file": (
            old,
            fixture_path(f"synthetic/{old}").read_bytes(),
            "application/octet-stream",
        ),
        "new_file": (
            new,
            fixture_path(f"synthetic/{new}").read_bytes(),
            "application/octet-stream",
        ),
    }


def by_header(request: Request) -> str | None:
    return request.headers.get("x-user") or None


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app(SynopsisService(), identify=by_header)
    with TestClient(app, headers={"x-user": "auditor-1"}) as test_client:
        yield test_client


def create(client: TestClient, **data: str) -> dict[str, Any]:
    response = client.post("/comparisons", files=files(), data=data)
    assert response.status_code == 201, response.text
    return response.json()  # type: ignore[no-any-return]


def test_full_flow(client: TestClient) -> None:
    assert client.get("/comparisons").json() == {"items": []}
    created = create(client, threshold="85", title="Richtlinie")
    assert created["title"] == "Richtlinie"
    assert created["result"]["new_filename"] == "tx_block_neu.docx"
    cid = created["id"]
    listed = client.get("/comparisons").json()["items"]
    assert [item["id"] for item in listed] == [cid]
    assert client.get(f"/comparisons/{cid}").json() == created
    row = created["result"]["rows"][0]["row_id"]
    patched = client.patch(
        f"/comparisons/{cid}/rows", json={"rows": [{"row_id": row, "selected": False}]}
    )
    assert patched.status_code == 200
    assert patched.json()["result"]["rows"][0]["selected"] is False
    exported = client.get(f"/comparisons/{cid}/export", params={"format": "markdown"})
    assert exported.status_code == 200
    assert exported.headers["content-type"].startswith("text/markdown")
    assert exported.headers["content-disposition"].startswith(
        'attachment; filename="Richtlinie.md"'
    )
    assert exported.headers["cache-control"] == "no-store"
    assert client.delete(f"/comparisons/{cid}").status_code == 204
    assert client.get(f"/comparisons/{cid}").status_code == 404


def test_owner_isolation_and_authentication(client: TestClient) -> None:
    cid = create(client)["id"]
    assert client.get(f"/comparisons/{cid}", headers={"x-user": "fremd"}).status_code == 404
    assert client.get("/comparisons", headers={"x-user": ""}).status_code == 401
    assert client.get("/profiles", headers={"x-user": ""}).json() == {
        "detail": "Anmeldung erforderlich."
    }


def test_profiles(client: TestClient) -> None:
    items = client.get("/profiles").json()["items"]
    assert {item["id"] for item in items} >= {"auditcore.document_compare"}
    assert [item["id"] for item in items if item["default"]] == ["auditcore.document_compare"]


@pytest.mark.parametrize(
    ("data", "status"),
    [({"threshold": "50"}, 422), ({"unbekannt": "1"}, 422), ({"mode": "x"}, 422)],
)
def test_form_validation(client: TestClient, data: dict[str, str], status: int) -> None:
    response = client.post("/comparisons", files=files(), data=data)
    assert response.status_code == status
    assert "detail" in response.json()


def test_missing_file_and_wrong_type(client: TestClient) -> None:
    only_old = {"old_file": files()["old_file"]}
    response = client.post("/comparisons", files=only_old)
    assert response.status_code == 422
    assert response.json()["detail"] == "Neue Fassung: Datei fehlt."
    wrong = {"old_file": ("x.txt", b"hallo", "text/plain"), "new_file": files()["new_file"]}
    assert client.post("/comparisons", files=wrong).status_code == 415


def test_upload_limit() -> None:
    app = create_app(SynopsisService(settings=ServiceSettings(max_upload_bytes=100)))
    with TestClient(app) as small:
        response = small.post("/comparisons", files=files())
    assert response.status_code == 413


def test_import_and_json_errors(client: TestClient) -> None:
    created = create(client)
    imported = client.post(
        "/comparisons/import", json={"result": created["result"], "title": "Kopie"}
    )
    assert imported.status_code == 201 and imported.json()["title"] == "Kopie"
    broken = client.post(
        "/comparisons/import", content=b"{kein json", headers={"content-type": "application/json"}
    )
    assert broken.status_code == 400
    assert client.post("/comparisons/import", json={"result": {"x": 1}}).status_code == 422
    huge = client.post(
        "/comparisons/import", content=b"x", headers={"content-length": str(9 * 1024 * 1024)}
    )
    assert huge.status_code in {400, 413}


def test_export_formats(client: TestClient) -> None:
    cid = create(client)["id"]
    assert client.get(f"/comparisons/{cid}/export").headers["content-type"] == "application/json"
    assert client.get(f"/comparisons/{cid}/export", params={"format": "exe"}).status_code == 422
    for fmt, magic in (("docx", b"PK"), ("pdf", b"%PDF")):
        response = client.get(f"/comparisons/{cid}/export", params={"format": fmt})
        assert response.status_code in {200, 501}
        if response.status_code == 200:
            assert response.content.startswith(magic)


def test_article_law_over_http(client: TestClient) -> None:
    response = client.post(
        "/comparisons",
        files=files("al_stamm.docx", "al_befehle.docx"),
        data={"comparison_type": "article_law"},
    )
    assert response.status_code == 201
    metadata = response.json()["result"]["metadata"]
    assert metadata["new_label"] == "Fassung nach dem Entwurf"
    assert isinstance(metadata["open_commands"], list)


def test_fastapi_router() -> None:
    fastapi = pytest.importorskip("fastapi")
    from auditcore_documents.web import create_router

    app = fastapi.FastAPI()
    app.include_router(create_router(SynopsisService(), prefix="/api/synopsis"))
    with TestClient(app) as api:
        response = api.post("/api/synopsis/comparisons", files=files())
        assert response.status_code == 201, response.text
        cid = response.json()["id"]
        assert api.get(f"/api/synopsis/comparisons/{cid}").status_code == 200
        paths = api.get("/openapi.json").json()["paths"]
    assert "/api/synopsis/comparisons/{comparison_id}/export" in paths


def test_framework_errors_use_contract_form(client: TestClient) -> None:
    three = [*files().items(), ("extra_file", ("c.docx", b"PK", "application/octet-stream"))]
    broken = client.post("/comparisons", files=three)
    assert broken.status_code == 400
    assert broken.json() == {"detail": "Die Anfrage ist fehlerhaft."}
    missing = client.get("/gibt-es-nicht")
    assert missing.status_code == 404 and "detail" in missing.json()
    wrong_method = client.put("/comparisons")
    assert wrong_method.status_code == 405 and "detail" in wrong_method.json()
