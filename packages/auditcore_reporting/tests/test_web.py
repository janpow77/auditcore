"""REST contract ``reporting_ui/1`` and its Starlette/FastAPI adapters."""

from __future__ import annotations

import io
import json
from datetime import date

import pytest
from openpyxl import load_workbook

from auditcore_reporting.web import CONTRACT, ContractError, catalogue, export, preview
from auditcore_reporting.web._http import decode, disposition, handle_export, handle_preview
from auditcore_reporting.web.contract import filename_of

TABLE = {
    "name": "Übersicht",
    "columns": ["Vorhaben", "Betrag", "Quote %", "Datum", "Kennung"],
    "rows": [["V-001", 1234.5, 0.25, "2026-01-31", "000123"], ["V-002", 17, None, None, "=1+1"]],
    "types": {"Datum": "date", "Kennung": "text"},
    "formats": {"Kennung": "@"},
}


def request(**change: object) -> dict[str, object]:
    return {"profile": "flowlib-legacy-v1", "tables": [TABLE], **change}


def test_catalogue_lists_profiles_types_limits() -> None:
    data = catalogue()
    assert data["contract"] == CONTRACT == "reporting_ui/1"
    assert [p["id"] for p in data["profiles"]] == ["flowlib-legacy-v1", "plain-v1"]  # type: ignore[index]
    assert data["excel_available"] is True
    assert "date" in data["column_types"]  # type: ignore[operator]
    assert data["limits"]["max_rows_per_sheet"] == 100_000  # type: ignore[index]
    sources = [p["source"] for p in data["profiles"]]  # type: ignore[union-attr]
    assert sources[0].startswith("janpow77/flowlib@aca2dc6a")
    assert sources[1] == "new explicitly neutral profile"


def test_preview_reports_formats_per_column_and_renders_trial_workbook() -> None:
    result = preview(request(filename="Prüfbericht 2026"))
    table = result["tables"][0]  # type: ignore[index]
    formats = {c["name"]: (c["format"], c["source"]) for c in table["columns"]}
    assert formats["Betrag"] == ('#,##0.00 "EUR"', "profile")
    assert formats["Quote %"] == ("0.00%", "profile")
    assert formats["Datum"] == ("DD.MM.YYYY", "profile")
    assert formats["Kennung"] == ("@", "override")
    assert table["rows"] == 2 and table["sample"][0][3] == "2026-01-31"
    assert result["workbook"]["filename"] == "Prüfbericht 2026.xlsx"  # type: ignore[index]
    assert result["workbook"]["bytes"] > 1000  # type: ignore[index]


def test_plain_profile_uses_general() -> None:
    table = preview(request(profile="plain-v1"))["tables"][0]  # type: ignore[index]
    assert {c["format"] for c in table["columns"] if c["source"] == "profile"} == {"General"}


def test_export_writes_typed_cells_and_keeps_formulas_as_text() -> None:
    content, name = export(request())
    assert name == "bericht.xlsx"
    sheet = load_workbook(io.BytesIO(content))["Übersicht"]
    assert sheet["D2"].value.date() == date(2026, 1, 31)
    assert sheet["E2"].value == "000123" and sheet["E3"].value == "=1+1"
    assert sheet["E3"].data_type == "s"


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"profile": None}, "'profile'"),
        ({"profile": "jkb"}, "'profile'"),
        ({"tables": []}, "nicht leere Liste"),
        ({"tables": [{**TABLE, "columns": ["A", "A"]}]}, "doppelte"),
        ({"tables": [{**TABLE, "rows": [["x"]]}]}, "5 Werten"),
        ({"tables": [{**TABLE, "types": {"Datum": "zeit"}}]}, "types.Datum"),
        ({"tables": [{**TABLE, "types": {"Fehlt": "date"}}]}, "unbekannte Spalte"),
        ({"tables": [{**TABLE, "rows": [["V", 1, 0, "31.01.2026", "1"]]}]}, "ISO-Datum"),
        (
            {
                "tables": [
                    {**TABLE, "rows": [["V", "1", 0, None, "1"]], "types": {"Betrag": "number"}}
                ]
            },
            "Zahl oder null",
        ),
        ({"tables": [{**TABLE, "rows": [["V", [1], 0, None, "1"]]}]}, "Text, Zahl"),
        ({"filename": 3}, "'filename'"),
    ],
)
def test_rejects_invalid_requests(change: dict[str, object], message: str) -> None:
    with pytest.raises(ContractError, match=message):
        preview(request(**change))


def test_library_rejections_are_422_with_code() -> None:
    bad = {**TABLE, "name": "a/b"}
    reply = handle_preview(json.dumps(request(tables=[bad])).encode())
    body = json.loads(reply.body)
    assert reply.status == 422 and body["error"]["code"] == "workbook_rejected"
    assert "Invalid worksheet name" in body["error"]["message"]


def test_limits_and_json_errors() -> None:
    assert handle_preview(b"{", 10).status == 400
    assert handle_preview(b"x" * 11, 10).status == 413
    with pytest.raises(ContractError, match="JSON"):
        decode(b'{"a": NaN}')
    huge = {**TABLE, "rows": [["V", 12345678901234567, 0, None, "1"]]}
    assert handle_preview(json.dumps(request(tables=[huge])).encode()).status == 422


def test_filename_is_sanitised_and_header_encoded() -> None:
    assert filename_of("../../etc/passwd") == "_.._etc_passwd.xlsx"
    assert filename_of("Bericht.XLSX") == "Bericht.xlsx"
    assert filename_of("  ") == "bericht.xlsx"
    header = disposition("Prüfung.xlsx")
    assert 'filename="Pr_fung.xlsx"' in header and "Pr%C3%BCfung.xlsx" in header


def test_export_reply_is_attachment() -> None:
    reply = handle_export(json.dumps(request(filename="Liste")).encode())
    assert reply.status == 200 and reply.media_type.endswith("spreadsheetml.sheet")
    assert reply.headers["Content-Disposition"].startswith('attachment; filename="Liste.xlsx"')


def test_starlette_and_fastapi_serve_identical_contract() -> None:
    from fastapi import FastAPI
    from starlette.testclient import TestClient

    from auditcore_reporting.web import create_app, create_router

    app = FastAPI()
    app.include_router(create_router("/api/reporting"))
    for client in (TestClient(create_app("/api/reporting")), TestClient(app)):
        assert client.get("/api/reporting/profiles").json()["contract"] == "reporting_ui/1"
        preview_reply = client.post("/api/reporting/preview", json=request())
        assert preview_reply.status_code == 200
        exported = client.post("/api/reporting/export", json=request())
        assert exported.status_code == 200 and exported.content[:2] == b"PK"
        assert client.post("/api/reporting/export", json={}).status_code == 422
