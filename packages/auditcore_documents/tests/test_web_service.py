"""Synopse-Dienst hinter dem REST-Vertrag (nur Standardbibliothek, Extras docx/fuzzy)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from itertools import count

import pytest
from conftest import fixture_path

from auditcore_documents import LEGACY, DependencyError
from auditcore_documents.web import (
    InMemoryComparisonStore,
    RequestError,
    ServiceSettings,
    SynopsisService,
    Upload,
    error_status,
    render_markdown,
    safe_filename,
)

pytest.importorskip("lxml")
pytest.importorskip("rapidfuzz")


def upload(name: str, as_name: str | None = None) -> Upload:
    return Upload(as_name or name, fixture_path(f"synthetic/{name}").read_bytes())


@pytest.fixture
def service() -> SynopsisService:
    ids = count(1)
    return SynopsisService(
        now=lambda: datetime(2026, 9, 25, 10, 0, tzinfo=UTC), new_id=lambda: f"c{next(ids)}"
    )


def test_create_stores_result_with_original_filenames(service: SynopsisService) -> None:
    item = service.create(
        "prüfer", upload("tx_block_alt.docx"), upload("tx_block_neu.docx"), {"threshold": "85"}
    )
    envelope = json.loads(json.dumps(item.envelope()))
    assert envelope == item.envelope()
    assert envelope["id"] == "c1"
    assert envelope["title"] == "Vergleich von tx_block_alt.docx mit tx_block_neu.docx"
    assert envelope["created_at"] == "2026-09-25T10:00:00+00:00"
    result = envelope["result"]
    assert result["old_filename"] == "tx_block_alt.docx"
    assert result["metadata"]["profile"]["id"] == "auditcore.document_compare"
    summary = json.loads(json.dumps(service.list("prüfer")))
    assert summary[0]["counts"]["changed"] == result["changed_count"]
    assert service.list("andere") == []


def test_article_law_synopsis_carries_commands(service: SynopsisService) -> None:
    item = service.create(
        "p",
        upload("al_stamm.docx"),
        upload("al_befehle.docx"),
        {"comparison_type": "article_law", "title": "KassenSichV"},
    )
    meta = item.result.metadata
    assert meta["comparison_type"] == "article_law"
    assert meta["reason_label"] == "Änderungsbefehl"
    assert all(row.reason_source == "article_law" for row in item.result.rows)
    text = render_markdown(item.result, title=item.title)
    assert "**Geltende Fassung:**" in text and "**Änderungsbefehl:**" in text


@pytest.mark.parametrize(
    ("fields", "message"),
    [
        ({"threshold": "69"}, "zwischen 70 und 100"),
        ({"threshold": "x"}, "ganze Zahl"),
        ({"mode": "tabelle"}, "Feld „mode“"),
        ({"include_notes": "vielleicht"}, "true oder false"),
        ({"output_sections": "changed,alles"}, "output_sections"),
        ({"output_sections": " , "}, "Mindestens ein"),
        ({"profile": "unbekannt"}, "Vergleichsprofil"),
        ({"schwelle": "85"}, "Unbekannte Felder: schwelle"),
        ({"title": "x" * 256}, "255 Zeichen"),
    ],
)
def test_invalid_fields_are_rejected(
    service: SynopsisService, fields: dict[str, str], message: str
) -> None:
    with pytest.raises(RequestError) as caught:
        service.create("p", upload("tx_block_alt.docx"), upload("tx_block_neu.docx"), fields)
    assert caught.value.status == 422 and message in caught.value.detail


def test_upload_checks(service: SynopsisService) -> None:
    small = SynopsisService(settings=ServiceSettings(max_upload_bytes=10))
    with pytest.raises(RequestError) as too_big:
        small.create("p", upload("tx_block_alt.docx"), upload("tx_block_neu.docx"), {})
    assert too_big.value.status == 413
    with pytest.raises(RequestError) as empty:
        service.create("p", Upload("leer.docx", b""), upload("tx_block_neu.docx"), {})
    assert empty.value.status == 422
    with pytest.raises(RequestError) as wrong:
        service.create("p", Upload("x.exe", b"MZ"), upload("tx_block_neu.docx"), {})
    assert wrong.value.status == 415


def test_same_filename_on_both_sides(service: SynopsisService) -> None:
    item = service.create(
        "p",
        upload("tx_block_alt.docx", "Richtlinie.docx"),
        upload("tx_block_neu.docx", "Richtlinie.docx"),
        {},
    )
    assert item.result.old_filename == item.result.new_filename == "Richtlinie.docx"
    assert item.result.old_sha256 != item.result.new_sha256


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("../../etc/passwd.docx", "passwd.docx"),
        ("C:\\Users\\x\\Bericht.pdf", "Bericht.pdf"),
        ("Prüf\x00bericht.docm", "Prüfbericht.docm"),
        ("a" * 300 + ".docx", "a" * 195 + ".docx"),
    ],
)
def test_safe_filename(name: str, expected: str) -> None:
    assert safe_filename(name) == expected


@pytest.mark.parametrize("name", ["", ".docx", "../", "bericht.docx.exe"])
def test_safe_filename_rejects(name: str) -> None:
    with pytest.raises(RequestError):
        safe_filename(name)


def test_corrupt_upload_maps_to_422(service: SynopsisService) -> None:
    with pytest.raises(Exception) as caught:
        service.create(
            "p", Upload("kaputt.docx", b"PK\x03\x04kaputt"), upload("tx_block_neu.docx"), {}
        )
    assert error_status(caught.value) == 422


def test_update_rows_and_owner_isolation(service: SynopsisService) -> None:
    item = service.create("p", upload("tx_block_alt.docx"), upload("tx_block_neu.docx"), {})
    first = item.result.rows[0].row_id
    changed = service.update_rows(
        "p",
        item.comparison_id,
        {"rows": [{"row_id": first, "selected": False, "reason": "redaktionell"}]},
    )
    assert changed.result.rows[0].selected is False
    assert changed.result.rows[0].reason == "redaktionell"
    assert item.result.rows[0].selected is True  # ursprüngliches Objekt unverändert
    assert service.get("p", item.comparison_id).result.rows[0].selected is False
    payload: object
    for payload in (
        {"rows": [{"row_id": "fehlt"}]},
        {"rows": [{"row_id": first, "selected": "ja"}]},
        {"rows": [{"row_id": first, "reason": "x" * 4001}]},
        {"rows": [{"row_id": first, "status": "added"}]},
        {"rows": {}},
        {"zeilen": []},
    ):
        with pytest.raises(RequestError) as caught:
            service.update_rows("p", item.comparison_id, payload)
        assert caught.value.status == 422
    with pytest.raises(RequestError) as foreign:
        service.get("fremd", item.comparison_id)
    assert foreign.value.status == 404
    service.delete("p", item.comparison_id)
    with pytest.raises(RequestError):
        service.delete("p", item.comparison_id)


def test_import_result_roundtrip(service: SynopsisService) -> None:
    item = service.create("p", upload("tx_block_alt.docx"), upload("tx_block_neu.docx"), {})
    imported = service.import_result("q", {"result": item.result.to_dict()})
    assert imported.result == item.result
    assert imported.title.startswith("Vergleich von ")
    invalid: tuple[object, ...] = (
        {"result": {"rows": [], "fremd": 1}},
        {"result": []},
        {"result": {}, "x": 1},
    )
    for payload in invalid:
        with pytest.raises(RequestError):
            service.import_result("q", payload)


def test_exports(service: SynopsisService) -> None:
    item = service.create(
        "p",
        upload("tx_block_alt.docx"),
        upload("tx_block_neu.docx"),
        {"title": "Richtlinie 2026/27"},
    )
    raw = service.export("p", item.comparison_id, "json")
    assert raw.filename == "Richtlinie_2026_27.json"
    assert json.loads(raw.content)["rows"] == item.result.to_dict()["rows"]
    markdown = service.export("p", item.comparison_id, "markdown")
    assert markdown.media_type.startswith("text/markdown")
    text = markdown.content.decode()
    assert text.startswith("# Richtlinie 2026/27\n")
    assert "SHA-256" in text and "## Festgestellte Änderungen" in text
    with pytest.raises(RequestError) as caught:
        service.export("p", item.comparison_id, "xlsx")
    assert caught.value.status == 422


def test_markdown_respects_selection_and_escapes(service: SynopsisService) -> None:
    item = service.create("p", upload("tx_block_alt.docx"), upload("tx_block_neu.docx"), {})
    result = item.result
    result.rows[0].new_text = "**fett** <script>"
    text = render_markdown(result, title="T")
    assert "\\*\\*fett\\*\\* \\<script\\>" in text
    for row in result.rows:
        row.selected = False
    assert "Keine Unterschiede in den gewählten Abschnitten." in render_markdown(result, title="T")


def test_docx_and_pdf_exports(service: SynopsisService) -> None:
    item = service.create("p", upload("tx_block_alt.docx"), upload("tx_block_neu.docx"), {})
    try:
        docx = service.export("p", item.comparison_id, "docx")
    except DependencyError:
        pytest.skip("docx-render nicht installiert")
    assert docx.content[:2] == b"PK" and docx.filename.endswith(".docx")
    try:
        pdf = service.export("p", item.comparison_id, "pdf")
    except DependencyError:
        pytest.skip("pdf-render nicht installiert")
    assert pdf.content.startswith(b"%PDF")


def test_profiles_and_settings() -> None:
    service = SynopsisService(
        settings=ServiceSettings(
            default_profile=LEGACY, allowed_profiles=frozenset({LEGACY.profile_id})
        )
    )
    assert [(p["id"], p["default"]) for p in service.profiles()] == [(LEGACY.profile_id, True)]
    with pytest.raises(ValueError):
        ServiceSettings(allowed_profiles=frozenset({LEGACY.profile_id}))
    with pytest.raises(ValueError):
        ServiceSettings(max_upload_bytes=0)


def test_in_memory_store_bounds() -> None:
    store = InMemoryComparisonStore(max_items=2)
    service = SynopsisService(store)
    ids = [
        service.import_result("p", {"result": _minimal_result()}).comparison_id for _ in range(3)
    ]
    assert [s["id"] for s in service.list("p")] == [ids[2], ids[1]]
    with pytest.raises(ValueError):
        InMemoryComparisonStore(max_items=0)


def _minimal_result() -> dict[str, object]:
    return {
        "version": "1.1.0",
        "mode": "text",
        "old_filename": "a.docx",
        "new_filename": "b.docx",
        "old_sha256": "",
        "new_sha256": "",
        "old_count": 0,
        "new_count": 0,
        "matched_count": 0,
        "changed_count": 0,
        "removed_count": 0,
        "added_count": 0,
        "rows": [],
        "created_at": "2026-09-25T00:00:00+00:00",
    }


def test_adapters_need_their_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    import sys

    from auditcore_documents import web

    adapters = ("auditcore_documents.web.asgi", "auditcore_documents.web.fastapi_router")
    for name in list(sys.modules):
        if name.split(".")[0] in {"starlette", "fastapi"} or name in adapters:
            monkeypatch.delitem(sys.modules, name)
    for name in ("starlette", "fastapi"):
        monkeypatch.setitem(sys.modules, name, None)
    with pytest.raises(DependencyError, match="Extra 'web'"):
        web.create_app  # noqa: B018
    with pytest.raises(DependencyError, match="Extra 'fastapi'"):
        web.create_router  # noqa: B018
    with pytest.raises(AttributeError):
        web.unbekannt  # noqa: B018
