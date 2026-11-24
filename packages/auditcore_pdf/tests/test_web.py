"""REST contract ``pdf_redaction/1`` (Starlette and FastAPI) with synthetic PDFs."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from redaction_support import fake_ner, lines_pdf, page_text
from starlette.requests import Request

import auditcore_pdf.web.contract as contract
from auditcore_pdf import redaction as R
from auditcore_pdf.web import (
    CONTRACT,
    ContractError,
    Limits,
    RedactionService,
    create_app,
    create_router,
    routes,
)
from auditcore_pdf.web._form import _declared_length
from auditcore_pdf.web.contract import attachment, decode_json, redacted_name

PDF = lines_pdf(
    ["Rückfragen an max.muster@beispiel-firma.example", "IBAN DE89 3704 0044 0532 0130 00"],
    ["Seite zwei ohne Treffer", "Ansprechpartner Erika Beispiel"],
)
EMAIL = {"patterns": ["email"], "terms": [], "case_sensitive": False, "whole_word": True}


def client(service: RedactionService | None = None, *, fastapi: bool = False) -> TestClient:
    active = service or RedactionService()
    if fastapi:
        app = FastAPI()
        app.include_router(create_router(active, prefix="/api/redaction"))
        return TestClient(app)
    return TestClient(create_app(active, prefix="/api/redaction"))


@pytest.fixture(params=["starlette", "fastapi"])
def api(request: pytest.FixtureRequest) -> Iterator[TestClient]:
    with client(fastapi=request.param == "fastapi") as test_client:
        yield test_client


def post(api: TestClient, path: str, data: dict[str, str], pdf: bytes = PDF) -> httpx.Response:
    files = {"file": ("akte.pdf", pdf, "application/pdf")}
    return api.post(f"/api/redaction{path}", data=data, files=files)


def plan_of(api: TestClient, criteria: dict[str, object] = EMAIL) -> dict[str, Any]:
    response = post(api, "/plan", {"criteria": json.dumps(criteria)})
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    return body


def selection(plan: dict[str, Any], **extra: object) -> str:
    candidates = plan["candidates"]
    payload = {
        "sha256": plan["sha256"],
        "criteria": plan["criteria"],
        "selected": [c["id"] for c in candidates],
        "areas": [],
        "sanitize": True,
    }
    payload.update(extra)
    return json.dumps(payload)


def error_code(response: httpx.Response) -> tuple[int, str]:
    return response.status_code, response.json()["error"]["code"]


# ── Katalog ─────────────────────────────────────────────────────


def test_catalogue_lists_patterns_and_limits(api: TestClient) -> None:
    body = api.get("/api/redaction/catalogue").json()
    assert body["contract"] == CONTRACT == "pdf_redaction/1"
    assert body["library"].startswith("auditcore_pdf ")
    assert body["ner_available"] is False
    ids = {p["id"]: p for p in body["patterns"]}
    assert set(ids) == set(R.PATTERNS)
    assert ids["ki_namen"] == {**ids["ki_namen"], "ai": True, "available": False}
    assert ids["email"]["available"] is True
    assert body["limits"]["max_terms"] == R.MAX_TERMS
    assert body["limits"]["max_areas_per_page"] == R.MAX_AREAS_PER_PAGE


def test_catalogue_with_ner_offers_ai_names() -> None:
    body = RedactionService(ner=fake_ner("Erika Beispiel")).catalogue()
    assert body["ner_available"] is True
    patterns = body["patterns"]
    assert isinstance(patterns, list)
    assert all(p["available"] for p in patterns)


# ── Plan ────────────────────────────────────────────────────────


def test_plan_returns_findings_without_changing_anything(api: TestClient) -> None:
    plan = plan_of(api, {**EMAIL, "terms": ["Erika Beispiel"]})
    assert plan["contract"] == CONTRACT
    assert plan["page_count"] == 2
    texts = sorted(c["text"] for c in plan["candidates"])
    assert texts == ["Erika Beispiel", "max.muster@beispiel-firma.example"]
    first = plan["candidates"][0]
    assert all(0 <= v <= 1 for v in first["rects"][0])
    assert plan["by_source"] == {"email": 1, "begriff:Erika Beispiel": 1}


def test_plan_defaults_flags_when_omitted(api: TestClient) -> None:
    plan = plan_of(api, {"patterns": ["iban"]})
    assert plan["criteria"] == {
        "patterns": ["iban"],
        "terms": [],
        "case_sensitive": False,
        "whole_word": True,
    }


@pytest.mark.parametrize(
    ("criteria", "status", "code"),
    [
        ([], 422, "invalid_criteria"),
        ({"patterns": "email"}, 422, "invalid_criteria"),
        ({"patterns": [1]}, 422, "invalid_criteria"),
        ({"terms": ["x"], "case_sensitive": "ja"}, 422, "invalid_criteria"),
        ({"patterns": ["gibt_es_nicht"]}, 422, "invalid_criteria"),
        ({"terms": ["x" * (R.MAX_TERM_LENGTH + 1)]}, 422, "invalid_criteria"),
        ({"patterns": [], "terms": ["  "]}, 422, "empty_criteria"),
        ({"patterns": ["ki_namen"]}, 503, "ner_unavailable"),
    ],
)
def test_plan_rejects_bad_criteria(
    api: TestClient, criteria: object, status: int, code: str
) -> None:
    response = post(api, "/plan", {"criteria": json.dumps(criteria)})
    assert error_code(response) == (status, code)


@pytest.mark.parametrize("raw", ["{", '{"terms": ["x"], "n": NaN}', '{"n": 1e999}'])
def test_plan_rejects_invalid_json(api: TestClient, raw: str) -> None:
    assert error_code(post(api, "/plan", {"criteria": raw})) == (400, "invalid_json")


def test_plan_requires_file_and_field(api: TestClient) -> None:
    response = api.post("/api/redaction/plan", data={"criteria": json.dumps(EMAIL)})
    assert error_code(response) == (400, "missing_file")
    assert error_code(post(api, "/plan", {})) == (400, "missing_field")
    assert error_code(post(api, "/plan", {"criteria": json.dumps(EMAIL)}, b"")) == (
        400,
        "missing_file",
    )


def test_plan_rejects_broken_files(api: TestClient) -> None:
    response = post(api, "/plan", {"criteria": json.dumps(EMAIL)}, b"%PDF-1.7 kaputt")
    assert error_code(response) == (422, "invalid_pdf")


def test_plan_rejects_extra_fields(api: TestClient) -> None:
    files = {"file": ("a.pdf", PDF, "application/pdf")}
    data = {"criteria": json.dumps(EMAIL), "noch_eins": "x"}
    response = api.post("/api/redaction/plan", data=data, files=files)
    assert error_code(response) == (400, "bad_request")


def test_limits_for_size_pages_and_fields() -> None:
    small = RedactionService(limits=Limits(max_upload_bytes=len(PDF) - 1, max_pages=1))
    with client(small) as api:
        assert error_code(post(api, "/plan", {"criteria": json.dumps(EMAIL)})) == (
            413,
            "too_large",
        )
    pages = RedactionService(limits=Limits(max_pages=1))
    with client(pages) as api:
        assert error_code(post(api, "/plan", {"criteria": json.dumps(EMAIL)})) == (
            413,
            "too_many_pages",
        )
    tight = RedactionService(limits=Limits(max_criteria_bytes=10))
    with client(tight) as api:
        assert error_code(post(api, "/plan", {"criteria": json.dumps(EMAIL)})) == (
            413,
            "too_large",
        )


def test_declared_length_is_checked_before_reading() -> None:
    service = RedactionService(
        limits=Limits(max_upload_bytes=1, max_selection_bytes=1, max_criteria_bytes=1)
    )
    with client(service) as api:
        response = post(api, "/plan", {"criteria": "{}"}, PDF + b" " * 80_000)
    assert error_code(response) == (413, "too_large")

    def request(value: str | None) -> Request:
        headers = [] if value is None else [(b"content-length", value.encode())]
        return Request({"type": "http", "method": "POST", "headers": headers})

    assert _declared_length(request(None)) is None
    assert _declared_length(request("12")) == 12
    with pytest.raises(ContractError) as caught:
        _declared_length(request("zwölf"))
    assert caught.value.code == "bad_request"


def test_plan_maps_engine_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(*_: object) -> list[list[tuple[int, int]]]:
        raise RuntimeError("Modell defekt")

    with client(RedactionService(ner=broken)) as api:
        response = post(api, "/plan", {"criteria": json.dumps({"patterns": ["ki_namen"]})})
    assert error_code(response) == (502, "ner_failed")

    def refuse(*_: object) -> object:
        raise R.RedactionError("Die PDF enthält keine Seiten")

    monkeypatch.setattr(contract, "build_plan", refuse)
    with client() as api:
        assert error_code(post(api, "/plan", {"criteria": json.dumps(EMAIL)})) == (
            422,
            "invalid_pdf",
        )


# ── Vorschau ────────────────────────────────────────────────────


def test_preview_renders_png_with_bounded_size(api: TestClient) -> None:
    response = post(api, "/preview", {"page": "2"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.headers["cache-control"] == "no-store"
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")
    small = RedactionService(limits=Limits(preview_max_edge=100))
    image = small.preview(PDF, 1)
    width = int.from_bytes(image[16:20], "big")
    height = int.from_bytes(image[20:24], "big")
    assert max(width, height) <= 100


@pytest.mark.parametrize("page", ["0", "3", "eins", "-1", ""])
def test_preview_rejects_bad_pages(api: TestClient, page: str) -> None:
    assert error_code(post(api, "/preview", {"page": page})) == (422, "invalid_page")


def test_preview_rejects_bool_pages() -> None:
    with pytest.raises(ContractError) as caught:
        RedactionService().preview(PDF, True)
    assert caught.value.code == "invalid_page"


# ── Anwendung ───────────────────────────────────────────────────


def test_apply_redacts_selection_and_reports_counts(api: TestClient) -> None:
    plan = plan_of(api, {**EMAIL, "terms": ["Erika Beispiel"]})
    area = {"page": 2, "rect": [0.1, 0.1, 0.3, 0.2]}
    response = post(api, "/apply", {"selection": selection(plan, areas=[area])})
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["x-redactions"] == "2"
    assert response.headers["x-redaction-areas"] == "1"
    assert response.headers["x-redaction-hidden"] == "0"
    assert response.headers["x-redaction-deselected"] == "0"
    assert response.headers["x-redaction-pages"] == "2"
    assert response.headers["x-redaction-sanitized"] == "true"
    assert response.headers["x-redaction-verified"] == "true"
    assert "akte_geschw" in response.headers["content-disposition"]
    text = page_text(response.content)
    assert "beispiel-firma" not in text
    assert "Erika" not in text
    assert "IBAN" in text


def test_apply_keeps_deselected_findings(api: TestClient) -> None:
    plan = plan_of(api, {**EMAIL, "terms": ["Erika Beispiel"]})
    keep = [c["id"] for c in plan["candidates"] if c["source"] == "email"]
    response = post(api, "/apply", {"selection": selection(plan, selected=keep, sanitize=False)})
    assert response.headers["x-redactions"] == "1"
    assert response.headers["x-redaction-deselected"] == "1"
    assert response.headers["x-redaction-sanitized"] == "false"
    assert "Erika Beispiel" in page_text(response.content)


def test_apply_detects_other_file(api: TestClient) -> None:
    plan = plan_of(api)
    other = lines_pdf(["Andere Datei an max.muster@beispiel-firma.example"])
    response = post(api, "/apply", {"selection": selection(plan)}, other)
    assert error_code(response) == (409, "stale_plan")


@pytest.mark.parametrize(
    "raw",
    [
        "[]",
        '{"selected": "alle"}',
        '{"selected": [], "areas": [{"page": 1, "rect": [0, 0, 2]}]}',
    ],
)
def test_apply_rejects_bad_selection(api: TestClient, raw: str) -> None:
    assert error_code(post(api, "/apply", {"selection": raw})) == (422, "invalid_selection")


def test_apply_requires_ner_when_selected(api: TestClient) -> None:
    raw = json.dumps({"sha256": "x", "criteria": {"patterns": ["ki_namen"]}, "selected": []})
    assert error_code(post(api, "/apply", {"selection": raw})) == (503, "ner_unavailable")


@pytest.mark.parametrize(
    ("error", "status", "code"),
    [
        (R.RedactionVerificationError(["Restbefund"]), 422, "verification_failed"),
        (R.RedactionNerError("KI fehlgeschlagen"), 502, "ner_failed"),
        (R.RedactionError("Unbekannte Kennung"), 422, "invalid_selection"),
    ],
)
def test_apply_maps_engine_errors(
    monkeypatch: pytest.MonkeyPatch, error: Exception, status: int, code: str
) -> None:
    def refuse(*_: object) -> object:
        raise error

    monkeypatch.setattr(contract, "apply_plan", refuse)
    with client() as api:
        plan = plan_of(api)
        response = post(api, "/apply", {"selection": selection(plan)})
    assert error_code(response) == (status, code)
    assert "Content-Disposition" not in response.headers


def test_selection_limit() -> None:
    with client(RedactionService(limits=Limits(max_selection_bytes=20))) as api:
        plan = plan_of(api)
        response = post(api, "/apply", {"selection": selection(plan)})
    assert error_code(response) == (413, "too_large")


# ── Hilfen ──────────────────────────────────────────────────────


def test_routes_mount_under_prefix() -> None:
    paths = [route.path for route in routes(RedactionService(), "/x")]
    assert paths == ["/x/catalogue", "/x/plan", "/x/preview", "/x/apply"]


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("Prüfakte.pdf", "Prüfakte_geschwärzt.pdf"),
        ("C:\\Ablage\\akte.PDF", "akte_geschwärzt.pdf"),
        ("../../etc/passwd", "passwd_geschwärzt.pdf"),
        ("", "dokument_geschwärzt.pdf"),
        ('"\n.pdf', "dokument_geschwärzt.pdf"),
    ],
)
def test_redacted_name(given: str, expected: str) -> None:
    assert redacted_name(given) == expected


def test_attachment_header_is_ascii_safe() -> None:
    header = attachment('Prüf"akte.pdf')
    assert header.startswith('attachment; filename="Pr_f_akte.pdf"')
    assert "filename*=UTF-8''Pr%C3%BCf%22akte.pdf" in header
    header.encode("latin-1")


def test_decode_json_accepts_text_and_bytes() -> None:
    assert decode_json('{"a": 1.5}', 100, "x") == {"a": 1.5}
    assert decode_json(b"[1]", 100, "x") == [1]
    with pytest.raises(ContractError):
        decode_json(b"\xff", 100, "x")
