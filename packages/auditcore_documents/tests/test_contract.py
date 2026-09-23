"""Vertragstests: Profile, Korrekturen DC-C01 bis DC-C10, Fehler und Grenzen."""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path
from typing import Any

import pytest
from conftest import fixture_path

import auditcore_documents as ad
from auditcore_documents import cli, legacy
from auditcore_documents.errors import (
    CompareError,
    DependencyError,
    LimitExceededError,
    ParseError,
)


def test_profiles_are_versioned_source_bound_and_fingerprinted() -> None:
    assert set(ad.PROFILES) == {
        "audit_designer.document_compare",
        "audit_designer.document_compare.difflib",
        "auditcore.document_compare",
    }
    fingerprints = {p.fingerprint for p in ad.PROFILES.values()}
    assert len(fingerprints) == 3
    for profile in ad.PROFILES.values():
        assert "030a71e083ef0feddc14545b095a4945bc0bbd7a" in profile.source
        assert len(profile.fingerprint) == 64
        assert ad.get_profile(profile.profile_id) is profile
    assert ad.LEGACY.status == "SOURCE_CHARACTERIZED"
    assert ad.CORRECTED.status.startswith("CORRECTED")
    with pytest.raises(ValueError, match="Unbekanntes Vergleichsprofil"):
        ad.get_profile("x")


def test_corrected_profile_records_its_identity_legacy_does_not() -> None:
    old, new = (
        fixture_path("synthetic/cl_basis_alt.docx"),
        fixture_path("synthetic/cl_basis_neu.docx"),
    )
    options = ad.CompareOptions(mode="checklist", threshold=70)
    legacy_result = ad.compare_files(old, new, profile=ad.LEGACY, options=options)
    corrected = ad.compare_files(old, new, profile=ad.CORRECTED, options=options)
    assert "profile" not in legacy_result.metadata
    assert corrected.metadata["profile"] == ad.CORRECTED.identity()
    assert corrected.version == ad.CORRECTED.result_version
    # Der Standardvergleich selbst ist in beiden Profilen gleich.
    assert [r.status for r in corrected.rows] == [r.status for r in legacy_result.rows]


def test_dc_c01_no_silent_fallback_without_rapidfuzz(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "rapidfuzz", None)
    with pytest.raises(DependencyError, match="fuzzy"):
        ad.get_scorer("rapidfuzz-token-set")
    # Das Rückfallmaß des Originals bleibt ausdrücklich wählbar.
    assert ad.get_scorer("difflib-ratio")("abc", "abd") == 67
    with pytest.raises(ValueError):
        ad.get_scorer("jaccard")  # type: ignore[arg-type]


def test_dc_c02_dtd_documents_are_rejected() -> None:
    for name in ("errors/entitaet_intern.docx", "errors/entitaet_extern.docx"):
        with pytest.raises(ParseError, match="enthält eine DTD"):
            ad.read_document(fixture_path(name), "text")


def test_dc_c03_limits(tmp_path: Path) -> None:
    path = fixture_path("synthetic/tx_struktur_alt.docx")
    with pytest.raises(LimitExceededError, match="größer"):
        ad.read_document(path, limits=ad.ReadLimits(max_file_bytes=10))
    with pytest.raises(LimitExceededError, match="entpackt"):
        ad.read_document(path, limits=ad.ReadLimits(max_xml_bytes=100))
    pages = ["Seite mit ausreichend viel Text für den Test."] * 3
    with pytest.raises(LimitExceededError, match="mehr als 2 Seiten"):
        ad.read_document(
            fixture_path("errors/leer.pdf"),
            page_source=lambda _p: pages,
            limits=ad.ReadLimits(max_pdf_pages=2),
        )
    for bad in ({"max_file_bytes": 0}, {"max_pdf_pages": True}, {"pdftotext_timeout": 0}):
        with pytest.raises(ValueError):
            ad.ReadLimits(**bad)  # type: ignore[arg-type]
    # ZIP-Bombe: kleine Datei, großer entpackter Hauptteil.
    bomb = tmp_path / "bombe.docx"
    with zipfile.ZipFile(bomb, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", b"<a>" + b" " * 5_000_000 + b"</a>")
    assert bomb.stat().st_size < 50_000
    with pytest.raises(LimitExceededError):
        ad.read_document(bomb, "text", limits=ad.ReadLimits(max_xml_bytes=1_000_000))


def test_dc_c04_corrected_profile_reads_paragraph_commands() -> None:
    base, amendment = (
        fixture_path("synthetic/al_stamm.docx"),
        fixture_path("synthetic/al_befehle.docx"),
    )
    legacy_result = ad.compare_article_law_files(base, amendment, profile=ad.LEGACY)
    corrected = ad.compare_article_law_files(base, amendment, profile=ad.CORRECTED)
    assert legacy_result.metadata["recognised_commands"] == 3
    assert corrected.metadata["recognised_commands"] == 5
    rows = {(r.status, r.location): r for r in corrected.rows}
    recast = rows[("changed", "§ 2 Absatz 3")]
    assert (
        recast.new_text
        == "(3) Ausgaben sind tatsächlich getätigte Zahlungen des Zuwendungsempfängers."
    )
    assert rows[("removed", "§ 4 Absatz 1")].new_text == ""
    assert (
        "§ 3 Absatz 7 wird aufgehoben. [Zielstelle nicht gefunden]"
        in corrected.metadata["open_commands"]
    )
    assert (
        "§ 5 wird wie folgt gefasst: [Befehlsart nicht unterstützt]"
        in corrected.metadata["open_commands"]
    )
    assert corrected.metadata["profile"]["id"] == "auditcore.document_compare"


def test_dc_c05_pdftotext_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess

    seen: dict[str, Any] = {}

    def fake_run(command: list[str], **kwargs: Any) -> Any:
        seen["command"], seen["kwargs"] = command, kwargs
        return subprocess.CompletedProcess(command, 0, stdout=b"Seite eins\fSeite zwei\f \f")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert ad.pdftotext_pages(Path("-gefaehrlich.pdf"), timeout=5) == ["Seite eins", "Seite zwei"]
    assert seen["command"] == ["pdftotext", "-layout", "./-gefaehrlich.pdf", "-"]
    assert seen["kwargs"]["timeout"] == 5 and "text" not in seen["kwargs"]

    def bad_run(command: list[str], **kwargs: Any) -> Any:
        return subprocess.CompletedProcess(command, 0, stdout=b"\xff\xfe")

    monkeypatch.setattr(subprocess, "run", bad_run)
    with pytest.raises(ParseError, match="UTF-8"):
        ad.pdftotext_pages(Path("x.pdf"))


def test_legacy_pdf_pages_falls_back_to_pypdf(monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess

    def missing(*_a: Any, **_k: Any) -> Any:
        raise FileNotFoundError("pdftotext")

    monkeypatch.setattr(subprocess, "run", missing)
    pages = ad.legacy_pdf_pages(fixture_path("public/KassenSichV_2023-06-10.pdf"))
    assert len(pages) == 3 and "Kassensicherungsverordnung" in pages[0]


def test_ocr_is_only_used_when_explicitly_given() -> None:
    blank = fixture_path("errors/leer.pdf")
    with pytest.raises(ParseError, match="Bitte OCR vorschalten"):
        ad.read_document(blank)
    calls: list[Path] = []

    def ocr(path: Path) -> str:
        calls.append(path)
        return "§ 1 Test\nEin ausreichend langer Satz aus der OCR.\n"

    mode, items = ad.read_document(blank, ocr_callback=ocr)
    assert mode == "text" and calls == [blank]
    assert items[0].section == "§ 1 Test"


def test_dc_c06_non_object_reason_payload() -> None:
    with pytest.raises(CompareError, match="keine gültige JSON-Begründung"):
        ad.generate_reason("a", "b", provider=lambda *_: "[1, 2]")
    reason, metadata = ad.generate_reason(
        "§ 3", "§ 3 neu", provider=lambda *_: {"begruendung": "Nach § 3.", "seed": 1}
    )
    assert reason == "Nach § 3." and metadata["verified"] is True and metadata["seed"] == 1


def test_dc_c08_compat_facade_requires_a_provider() -> None:
    legacy.DocumentCompareService.reason_provider = None
    with pytest.raises(CompareError, match="Kein Begründungsdienst"):
        legacy.DocumentCompareService.generate_reason("a", "b")
    try:
        legacy.DocumentCompareService.reason_provider = lambda *_: {"begruendung": "x"}
        assert legacy.DocumentCompareService.generate_reason("a", "b")[0] == "x"
    finally:
        legacy.DocumentCompareService.reason_provider = None


def test_worker_reasons_mark_failures_and_report_progress() -> None:
    result = ad.compare_files(
        fixture_path("synthetic/cl_rich_alt.docx"),
        fixture_path("synthetic/cl_rich_neu.docx"),
        profile=ad.LEGACY,
    )
    changed = [r for r in result.rows if r.status == "changed"]
    changed[1].selected = False
    errors: list[str] = []
    progress: list[int] = []

    def provider(old: str, new: str, model: str | None) -> dict[str, str]:
        if "Auftragswert" in old:
            raise TimeoutError("zu langsam")
        return {"begruendung": "Geändert nach Art. 99.", "rechtsgrundlage": ""}

    meta = ad.apply_reasons_worker(
        result,
        provider,
        on_progress=progress.append,
        on_error=lambda row, exc: errors.append(str(exc)),
    )
    assert progress == sorted(progress) and progress[-1] == 95
    assert changed[1].reason == ""
    failed = [r for r in changed if r.reason.startswith("[FlowAgent-Vorschlag nicht verfügbar")]
    assert failed and failed[0].reason_verified is False and errors == ["zu langsam"]
    ok = [r for r in changed if r.reason == "Geändert nach Art. 99."]
    assert ok and ok[0].reason_warning.startswith(
        "Nicht in den Fassungen belegte Fundstelle: Art. 99"
    )
    assert result.metadata["llm"] is meta


def test_result_round_trip_and_unknown_fields() -> None:
    result = ad.compare_files(
        fixture_path("synthetic/tx_verschoben_alt.docx"),
        fixture_path("synthetic/tx_verschoben_neu.docx"),
        profile=ad.LEGACY,
    )
    data = json.loads(json.dumps(result.to_dict()))
    assert ad.ComparisonResult.from_dict(data) == result
    with pytest.raises(ValueError, match="Unbekannte Ergebnisfelder"):
        ad.ComparisonResult.from_dict({**data, "fremd": 1})
    data["rows"][0]["fremd"] = 1
    with pytest.raises(ValueError, match="Unbekannte Zeilenfelder"):
        ad.ComparisonResult.from_dict(data)


def test_compare_items_is_pure_and_matches_the_file_facade() -> None:
    old, new = (
        fixture_path("synthetic/tx_block_alt.docx"),
        fixture_path("synthetic/tx_block_neu.docx"),
    )
    _m, old_items = ad.read_document(old, "text")
    _m, new_items = ad.read_document(new, "text")
    rows, counts = ad.compare_items(old_items, new_items, mode="text", profile=ad.LEGACY)
    result = ad.compare_files(old, new, profile=ad.LEGACY, options=ad.CompareOptions(mode="text"))
    assert rows == result.rows
    assert counts["changed_count"] == result.changed_count


def test_unsupported_and_missing_inputs() -> None:
    with pytest.raises(ParseError, match="Nicht unterstütztes Format: .txt"):
        ad.read_document(fixture_path("errors/notiz.txt"))
    with pytest.raises(ParseError, match="Datei nicht gefunden"):
        ad.read_document(fixture_path("fehlt/da.docx"))
    with pytest.raises(CompareError, match="Dokumentarten unterscheiden sich"):
        ad.compare_files(
            fixture_path("synthetic/mix_tabelle.docx"),
            fixture_path("synthetic/tx_struktur_neu.docx"),
            profile=ad.LEGACY,
        )


def test_synopsis_records_feed_the_reporting_workbook() -> None:
    reporting = pytest.importorskip("auditcore_reporting")
    pytest.importorskip("openpyxl")
    result = ad.compare_files(
        fixture_path("synthetic/cl_rich_alt.docx"),
        fixture_path("synthetic/cl_rich_neu.docx"),
        profile=ad.LEGACY,
    )
    columns, rows = ad.synopsis_records(result)
    table = reporting.ReportTable(
        "Synopse", columns, [[r.get(c, "") for c in columns] for r in rows]
    )
    content = reporting.render_workbook([table])
    assert content[:2] == b"PK" and len(rows) == 5


def test_cli_read_compare_and_config(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    config = tmp_path / "c.json"
    assert cli.main(["create-config", str(config)]) == 0
    assert json.loads(config.read_text())["threshold"] == 85
    assert cli.main(["read", str(fixture_path("synthetic/cl_rich_alt.docx"))]) == 0
    assert json.loads(capsys.readouterr().out.split("\n", 1)[1])["mode"] == "checklist"
    out, js = tmp_path / "v.docx", tmp_path / "v.json"
    code = cli.main(
        [
            "compare",
            str(fixture_path("synthetic/al_stamm.docx")),
            str(fixture_path("synthetic/al_befehle.docx")),
            "--comparison-type",
            "article_law",
            "--profile",
            "auditcore.document_compare",
            "-o",
            str(out),
            "--json",
            str(js),
            "--config",
            str(config),
        ]
    )
    assert code == 0 and out.read_bytes()[:2] == b"PK"
    assert json.loads(js.read_text())["metadata"]["recognised_commands"] == 5
    assert "geändert=3 entfallen=1 neu=1" in capsys.readouterr().out
    assert cli.main(["compare", str(config), str(config)]) == 2
    assert "Nicht unterstütztes Format" in capsys.readouterr().err


def test_settings_have_no_implicit_path() -> None:
    import inspect

    assert "path" in inspect.signature(ad.load_settings).parameters
    assert inspect.signature(ad.load_settings).parameters["path"].default is inspect.Parameter.empty


def test_legacy_default_config_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AUDIT_DOCUMENT_COMPARE_CONFIG", str(tmp_path / "x.json"))
    assert legacy.audit_designer_config_path() == tmp_path / "x.json"
    monkeypatch.delenv("AUDIT_DOCUMENT_COMPARE_CONFIG")
    monkeypatch.setenv("HOME", str(tmp_path))
    assert (
        legacy.audit_designer_config_path()
        == tmp_path / ".config/audit_designer/document_compare.json"
    )
    assert legacy.save_default_settings().is_file()
    assert (
        legacy.read_document(fixture_path("synthetic/cl_basis_alt.docx"), "checklist")[0]["text"]
        == "Frage unverändert"
    )
