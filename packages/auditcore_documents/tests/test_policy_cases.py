"""Anwendbare Katalogfälle des verwaltung-app-framework für die Bibliothek."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
from conftest import fixture_path

import auditcore_documents as ad


def test_t14_library_writes_no_logs(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    ad.compare_files(
        fixture_path("synthetic/cl_rich_alt.docx"),
        fixture_path("synthetic/cl_rich_neu.docx"),
        profile=ad.LEGACY,
    )
    ad.apply_reasons_worker(
        ad.compare_files(
            fixture_path("synthetic/cl_rich_alt.docx"),
            fixture_path("synthetic/cl_rich_neu.docx"),
            profile=ad.LEGACY,
        ),
        lambda *_: (_ for _ in ()).throw(RuntimeError("Dienst aus")),
    )
    assert caplog.records == []


def test_t11_document_content_stays_in_memory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Vergleich schreibt nichts; nur ausdrücklich benannte Ausgaben entstehen."""
    monkeypatch.chdir(tmp_path)
    before = set(tmp_path.rglob("*"))
    result = ad.compare_files(
        fixture_path("synthetic/cl_rich_alt.docx"),
        fixture_path("synthetic/cl_rich_neu.docx"),
        profile=ad.LEGACY,
    )
    assert set(tmp_path.rglob("*")) == before
    from auditcore_documents.render_docx import render_docx

    target = tmp_path / "ausgabe" / "synopse.docx"
    render_docx(result, target)
    assert set(tmp_path.rglob("*")) - before == {target.parent, target}


def test_inputs_are_never_modified() -> None:
    import hashlib

    path = fixture_path("synthetic/cl_tracked_neu.docx")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    ad.read_document(path, "checklist")  # nimmt Nachverfolgung nur im Speicher an
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest


def test_work_aid_notice_is_part_of_every_article_law_result() -> None:
    result = ad.compare_article_law_files(
        fixture_path("synthetic/al_stamm.docx"),
        fixture_path("synthetic/al_befehle.docx"),
        profile=ad.LEGACY,
    )
    assert result.metadata["work_aid_notice"].startswith("Arbeitshilfe ohne amtlichen Charakter")


def test_t09_docx_export_scope_records_metadata_and_version(tmp_path: Path) -> None:
    """F-04/T-09: Auswahl mit bekannter Zahl exportieren; Umfang, Metadaten, Version."""
    import zipfile

    docx = pytest.importorskip("docx")
    from auditcore_documents.render_docx import render_docx

    result = ad.compare_files(
        fixture_path("synthetic/cl_rich_alt.docx"),
        fixture_path("synthetic/cl_rich_neu.docx"),
        profile=ad.LEGACY,
        options=ad.CompareOptions(output_sections=["changed", "removed"]),
    )
    changed = [r for r in result.rows if r.status == "changed"]
    changed[0].selected = False  # vom Prüfer abgewählt
    expected = [r for r in result.rows if r.selected and r.status in {"changed", "removed"}]
    groups = {r.status for r in expected}
    target = tmp_path / "export.docx"
    render_docx(result, target, user="Prüfer")
    table = docx.Document(str(target)).tables[0]
    assert len(table.rows) == 1 + len(groups) + len(expected)
    exported = {row.cells[1].text for row in table.rows[1:]}
    assert changed[0].old_text not in "".join(exported)
    body = zipfile.ZipFile(target).read("word/document.xml").decode()
    assert result.old_sha256 in body and result.new_sha256 in body
    assert f"Vergleichsmodul {result.version}" in body
