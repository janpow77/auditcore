"""REST contract ``reporting_ui/1``: template list, data contract, preview and rendering."""

from __future__ import annotations

import json

import pytest

from auditcore_reporting.templates import builtin_registry, design_from_dict
from auditcore_reporting.templates.values import plain
from auditcore_reporting.web import (
    CONTRACT,
    ContractError,
    DataContractError,
    TemplateCatalogue,
    template_detail,
    template_list,
    template_preview,
    template_render,
)
from auditcore_reporting.web._templates_http import handle_detail, handle_template_render
from auditcore_reporting.web.templates_service import default_catalogue, document_filename

CATALOGUE = default_catalogue()
SAMPLE: dict[str, object] = plain(builtin_registry().get("pruefbericht").sample)  # type: ignore[assignment]


def test_list_names_templates_designs_and_formats() -> None:
    data = template_list(CATALOGUE)
    assert data["contract"] == CONTRACT
    templates = data["templates"]
    assert isinstance(templates, list)
    assert [t["id"] for t in templates] == ["pruefbericht", "vermerk"]
    assert templates[0]["kind"] == "structured" and templates[0]["versions"] == ["1.0.0"]
    assert data["formats"] == {"docx": True, "pdf": True, "html": True}
    assert [d["id"] for d in data["designs"]] == ["neutral-v1"]  # type: ignore[union-attr]


def test_detail_contains_schema_sample_and_text_blocks() -> None:
    data = template_detail(CATALOGUE, "pruefbericht")
    assert data["schema"]["type"] == "object"  # type: ignore[index]
    assert data["sample"] == SAMPLE
    blocks = {b["id"]: b for b in data["text_blocks"]}  # type: ignore[union-attr]
    assert blocks["rechtsgrundlage"]["required"] is True
    assert blocks["verwaltungsueberpruefung"]["legal_basis"] == "Art. 74 VO (EU) 2021/1060"
    json.dumps(data)  # JSON-serialisable
    with pytest.raises(ContractError) as missing:
        template_detail(CATALOGUE, "fehlt")
    assert missing.value.status == 404 and missing.value.code == "unknown_template"
    assert handle_detail(CATALOGUE, "vermerk", "version=9.9.9").status == 404


def test_preview_returns_html_or_issues() -> None:
    ok = template_preview(CATALOGUE, "pruefbericht", {"data": SAMPLE})
    assert ok["valid"] is True and "Feststellung 1" in str(ok["html"])
    assert ok["text_blocks"][0] == "rechtsgrundlage"  # type: ignore[index]
    bad = template_preview(
        CATALOGUE, "pruefbericht", {"data": {**SAMPLE, "berichtsdatum": "gestern"}}
    )
    assert bad["valid"] is False and bad["html"] is None
    assert bad["issues"] == [
        {"path": "$.berichtsdatum", "message": "muss ein ISO-Datum (JJJJ-MM-TT) sein"}
    ]
    with pytest.raises(ContractError, match="'data'"):
        template_preview(CATALOGUE, "vermerk", {})


def test_render_returns_file_with_provenance() -> None:
    content, name, media, headers = template_render(
        CATALOGUE, "pruefbericht", {"data": SAMPLE, "format": "docx", "filename": "Bericht 1"}
    )
    assert content[:2] == b"PK" and name == "Bericht 1.docx" and media.endswith("document")
    assert headers["X-Template-Version"] == "1.0.0" and len(headers["X-Data-SHA256"]) == 64
    with pytest.raises(DataContractError) as invalid:
        template_render(CATALOGUE, "pruefbericht", {"data": {}, "format": "pdf"})
    body = invalid.value.to_dict()["error"]
    assert body["code"] == "invalid_data" and len(body["issues"]) == 5  # type: ignore[index,arg-type]
    with pytest.raises(ContractError, match="'format'"):
        template_render(CATALOGUE, "pruefbericht", {"data": SAMPLE, "format": "odt"})


def test_application_catalogue_with_own_design() -> None:
    design = design_from_dict({"id": "amt-v1", "header_text": "Musteramt"})
    catalogue = TemplateCatalogue(builtin_registry(), [design])
    reply = handle_template_render(
        catalogue,
        "vermerk",
        json.dumps(
            {"data": plain(builtin_registry().get("vermerk").sample), "format": "html"}
        ).encode(),
    )
    assert reply.status == 200 and b"Musteramt" in reply.body
    assert reply.headers["Content-Disposition"].startswith('attachment; filename="vermerk.html"')
    unknown = handle_template_render(
        catalogue, "vermerk", b'{"data": {}, "format": "html", "design": "x"}'
    )
    assert unknown.status == 422 and json.loads(unknown.body)["error"]["code"] == "unknown_design"


def test_filenames_are_sanitised() -> None:
    assert document_filename("../x.PDF", "b", "pdf") == "_x.pdf"
    assert document_filename(None, "vermerk", "docx") == "vermerk.docx"
    assert document_filename("  ", "v", "html") == "bericht.html"


def test_routes_in_starlette_and_fastapi() -> None:
    from fastapi import FastAPI
    from starlette.testclient import TestClient

    from auditcore_reporting.web import create_app, create_router

    app = FastAPI()
    app.include_router(create_router("/api/reporting"))
    for client in (TestClient(create_app("/api/reporting")), TestClient(app)):
        assert client.get("/api/reporting/templates").json()["contract"] == CONTRACT
        assert client.get("/api/reporting/templates/vermerk").status_code == 200
        preview = client.post(
            "/api/reporting/templates/pruefbericht/preview", json={"data": SAMPLE}
        )
        assert preview.json()["valid"] is True
        pdf = client.post(
            "/api/reporting/templates/pruefbericht/render", json={"data": SAMPLE, "format": "pdf"}
        )
        assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF"
        assert pdf.headers["x-template-id"] == "pruefbericht"
        assert (
            client.post("/api/reporting/templates/fehlt/render", json={"data": {}}).status_code
            == 404
        )
