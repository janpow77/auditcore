"""Wiederholung aller aufgezeichneten Originalfälle gegen die Bibliothek.

Grundlage: ``tests/fixtures/legacy_observed.json`` aus
``tools/capture_legacy.py`` (audit_designer@030a71e0, Referenzumgebung wie
die Produktion). Abweichungen sind nur dort zulässig, wo
``docs/behavior-changes.md`` sie begründet; sie sind hier ausdrücklich
als erwartete Abweichung formuliert.
"""

from __future__ import annotations

import copy
import zipfile
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from conftest import fixture_path, observed, recorded_page_source, recorded_pages

import auditcore_documents as ad
from auditcore_documents import legacy
from auditcore_documents.errors import CompareError, ParseError
from auditcore_documents.matching import similarity
from auditcore_documents.model import CompareItem
from auditcore_documents.reasons import apply_reasons_worker
from auditcore_documents.render_docx import render_docx
from auditcore_documents.synopsis import synopsis_extra, synopsis_records

DATA = observed()
VOLATILE = ("old_modified_at", "new_modified_at")
PROFILES = {"rapidfuzz": ad.LEGACY, "difflib": ad.LEGACY_DIFFLIB}
#: DC-C02: DTD/Entitäten werden abgewiesen, das Original löste sie auf.
EXPECTED_DEVIATIONS = {("errors/entitaet_intern.docx", "text")}


def normalised(result: ad.ComparisonResult) -> dict[str, Any]:
    data = result.to_dict()
    data.pop("created_at")
    data["volatile_metadata"] = sorted(k for k in VOLATILE if k in data["metadata"])
    for key in VOLATILE:
        data["metadata"].pop(key, None)
    return data


def assert_same_error(exc: BaseException, entry: dict[str, Any]) -> None:
    assert str(exc) == entry["message"]
    expected = {"ParseError": ParseError, "CompareError": CompareError}[entry["error"]]
    assert isinstance(exc, expected), (type(exc), entry["error"])


def context() -> ad.ReadContext:
    return ad.ReadContext(page_source=recorded_page_source)


def test_source_and_environment_are_bound() -> None:
    source = DATA["source"]
    assert source["repository"] == "janpow77/audit_designer"
    assert source["commit"] == "030a71e083ef0feddc14545b095a4945bc0bbd7a"
    assert source["checkout_head"] == source["commit"]
    env = DATA["environment"]
    assert env["python"] == "3.11.16"
    assert env["pdftotext"] == "pdftotext version 22.12.0"
    assert env["packages"] == {
        "lxml": "5.1.0",
        "python-docx": "1.1.0",
        "pypdf": "6.16.2",
        "rapidfuzz": "3.14.5",
    }


def test_fixture_files_are_the_recorded_ones() -> None:
    import hashlib

    for name, digest in DATA["fixtures"].items():
        path = fixture_path(name)
        if digest is None:
            assert not path.exists()
        else:
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name


def test_constants_equal_the_original() -> None:
    constants = DATA["constants"]
    assert constants["VERSION"] == legacy.DocumentCompareService.VERSION == ad.LEGACY.result_version
    assert constants["ALLOWED_EXTENSIONS"] == sorted(ad.ALLOWED_EXTENSIONS)
    assert constants["DEFAULT_SETTINGS"] == ad.DEFAULT_SETTINGS
    assert constants["ALLOWED_SECTIONS"] == sorted(ad.settings.ALLOWED_SECTIONS)
    assert constants["HEADING_RE"] == ad.ooxml.HEADING_RE.pattern
    assert constants["PAGE_NUMBER_RE"] == ad.pdftext.PAGE_NUMBER_RE.pattern
    assert constants["LEGAL_REFERENCE_RE"] == ad.reasons.LEGAL_REFERENCE_RE.pattern
    assert constants["COMMAND_PATTERNS"] == [[k, p.pattern] for k, p in ad.COMMAND_PATTERNS]


@pytest.mark.parametrize("entry", DATA["normalise"], ids=lambda e: repr(e["text"])[:30])
def test_normalisation(entry: dict[str, Any]) -> None:
    assert ad.normalise_for_match(entry["text"]) == entry["for_match"]
    assert ad.normalise_semantic(entry["text"]) == entry["semantic"]
    assert ad.normalise_verbatim(entry["text"]) == entry["verbatim"]


@pytest.mark.parametrize("entry", DATA["word_diff"])
def test_word_diff(entry: dict[str, Any]) -> None:
    assert ad.word_diff(entry["old"], entry["new"]) == entry["diff"]


@pytest.mark.parametrize("entry", DATA["similarity"])
def test_similarity(entry: dict[str, Any]) -> None:
    scorer = ad.get_scorer(PROFILES[entry["scorer"]].scorer)
    left, right = CompareItem("a", text=entry["left"]), CompareItem("b", text=entry["right"])
    assert similarity(left, right, scorer) == entry["score"]


@pytest.mark.parametrize("entry", DATA["read"], ids=lambda e: f"{e['file']}-{e['mode']}-{e['ocr']}")
def test_read_document(entry: dict[str, Any]) -> None:
    ocr = {
        "none": None,
        "short": lambda _p: "zu kurz",
        "text": lambda _p: (
            "§ 1 Musterregel\n"
            "Diese Seite wurde durch eine OCR-Stelle gelesen und enthält genügend Text.\n"
            "Ein zweiter Satz folgt hier.\n"
        ),
    }[entry["ocr"]]
    path = fixture_path(entry["file"])
    if (entry["file"], entry["mode"]) in EXPECTED_DEVIATIONS:
        assert entry["items"][0]["text"] == "Absatz mit Entitätstext am Ende."
        with pytest.raises(ParseError, match="enthält eine DTD"):
            ad.read_document(path, entry["mode"])
        return
    if "error" in entry:
        with pytest.raises(CompareError) as caught:
            ad.read_document(
                path, entry["mode"], ocr_callback=ocr, page_source=recorded_page_source
            )
        assert_same_error(caught.value, entry)
        return
    mode, items = ad.read_document(
        path, entry["mode"], ocr_callback=ocr, page_source=recorded_page_source
    )
    assert mode == entry["resolved_mode"]
    assert [asdict(item) for item in items] == entry["items"]


def test_external_entity_is_rejected_like_the_original() -> None:
    assert DATA["xxe_external"]["error"] == "ParseError"
    with pytest.raises(ParseError, match="enthält eine DTD"):
        ad.read_document(fixture_path("errors/entitaet_extern.docx"), "text")


@pytest.mark.parametrize("entry", DATA["detect_mode"], ids=lambda e: e["file"])
def test_detect_mode(entry: dict[str, Any]) -> None:
    path = fixture_path(entry["file"])
    if "error" in entry:
        with pytest.raises(CompareError) as caught:
            ad.detect_mode(path)
        assert str(caught.value) == entry["message"]
    elif entry["file"] == "errors/entitaet_intern.docx":
        with pytest.raises(ParseError):
            ad.detect_mode(path)
    else:
        assert ad.detect_mode(path) == entry["mode"]


@pytest.mark.parametrize("entry", DATA["pdf_pages"], ids=lambda e: f"{e['file']}-{e['extractor']}")
def test_pdf_paragraphs_from_recorded_pages(entry: dict[str, Any]) -> None:
    assert [list(p) for p in ad.paragraphs_from_pdf_pages(entry["pages"])] == entry["paragraphs"]


@pytest.mark.parametrize("entry", DATA["pdf_pages"], ids=lambda e: f"{e['file']}-{e['extractor']}")
def test_pdf_extraction_in_this_environment(entry: dict[str, Any]) -> None:
    """pypdf immer; pdftotext nur bei gleicher Version wie in der Referenzumgebung."""
    path = fixture_path(entry["file"])
    if entry["extractor"] == "pypdf":
        # Aufgezeichnet mit pypdf 6.16.2; mit 6.19.0 nachweislich identisch.
        # Eine Abweichung späterer Versionen soll hier auffallen.
        assert ad.pypdf_pages(path) == entry["pages"]
        return
    import subprocess

    try:
        version = subprocess.run(
            ["pdftotext", "-v"], capture_output=True, text=True, check=False
        ).stderr.splitlines()[0]
    except FileNotFoundError:
        pytest.skip("pdftotext nicht installiert")
    if version != DATA["environment"]["pdftotext"]:
        pytest.skip(f"{version} statt {DATA['environment']['pdftotext']}")
    assert ad.pdftotext_pages(path) == entry["pages"]


def test_pypdf_error_contract() -> None:
    with pytest.raises(ParseError) as caught:
        ad.pypdf_pages(fixture_path("errors/kaputt.pdf"))
    assert_same_error(caught.value, DATA["pypdf_error"])


@pytest.mark.parametrize("entry", DATA["page_paragraphs"])
def test_page_margin_and_paragraph_rules(entry: dict[str, Any]) -> None:
    assert ad.remove_repeating_margins(entry["pages"]) == entry["margins"]
    assert [list(p) for p in ad.paragraphs_from_pdf_pages(entry["pages"])] == entry["paragraphs"]


@pytest.mark.parametrize("entry", DATA["compare"], ids=lambda e: f"{e['case']}-{e['scorer']}")
def test_standard_compare(entry: dict[str, Any]) -> None:
    ocr = (
        (
            lambda _p: (
                "§ 1 Musterregel\nDiese Seite wurde durch eine OCR-Stelle gelesen "
                "und enthält genügend Text.\nEin zweiter Satz folgt hier.\n"
            )
        )
        if entry.get("ocr")
        else None
    )
    kwargs = dict(entry["kwargs"])
    options = ad.CompareOptions(**kwargs)
    call = lambda: ad.compare_files(  # noqa: E731
        fixture_path(entry["old"]),
        fixture_path(entry["new"]),
        profile=PROFILES[entry["scorer"]],
        options=options,
        context=ad.ReadContext(page_source=recorded_page_source, ocr_callback=ocr),
    )
    if "error" in entry:
        with pytest.raises(CompareError) as caught:
            call()
        assert str(caught.value) == entry["message"]
        return
    assert normalised(call()) == entry["result"]


@pytest.mark.parametrize("entry", DATA["article_law"], ids=lambda e: str(e["case"]))
def test_article_law_legacy_profile(entry: dict[str, Any]) -> None:
    call = lambda: ad.compare_files(  # noqa: E731
        fixture_path(entry["old"]),
        fixture_path(entry["new"]),
        profile=ad.LEGACY,
        options=ad.CompareOptions(comparison_type="article_law"),
        context=context(),
    )
    if "error" in entry:
        with pytest.raises(CompareError) as caught:
            call()
        assert str(caught.value) == entry["message"]
        return
    assert normalised(call()) == entry["result"]


def test_compat_facade_matches_original_signature_results() -> None:
    entry = DATA["compare"][0]
    result = legacy.DocumentCompareService.compare(
        fixture_path(entry["old"]), fixture_path(entry["new"]), **entry["kwargs"]
    )
    assert normalised(result) == entry["result"]


# --------------------------------------------------------------------------- Einstellungen


@pytest.mark.parametrize("entry", DATA["settings"]["sanitise"], ids=lambda e: repr(e["input"])[:40])
def test_sanitise_settings(entry: dict[str, Any]) -> None:
    value = copy.deepcopy(entry["input"])
    if "error" in entry:
        with pytest.raises((ValueError, TypeError)) as caught:
            ad.sanitise_settings(value)
        assert type(caught.value).__name__ == entry["error"]
        assert str(caught.value) == entry["message"]
        return
    assert ad.sanitise_settings(value) == entry["output"]


@pytest.mark.parametrize("entry", DATA["settings"]["merge"])
def test_merge_settings(entry: dict[str, Any]) -> None:
    effective, sources = ad.merge_settings(entry["department"], entry["personal"], entry["run"])
    assert effective == entry["effective"]
    assert sources == entry["sources"]


@pytest.mark.parametrize("entry", DATA["settings"]["load"], ids=lambda e: e["file"])
def test_load_settings(entry: dict[str, Any], tmp_path: Path) -> None:
    path = tmp_path / entry["file"]
    if entry["content"] is not None:
        path.write_text(entry["content"], encoding="utf-8")
    if "error" in entry:
        with pytest.raises(ValueError) as caught:
            ad.load_settings(path)
        assert str(caught.value) == entry["message"]
        return
    assert ad.load_settings(path) == entry["output"]


def test_save_settings(tmp_path: Path) -> None:
    entry = DATA["settings"]["save"]
    target = tmp_path / "neu" / "s.json"
    assert ad.save_settings(entry["input"], target) == entry["returned"]
    assert target.read_text(encoding="utf-8") == entry["file"]


# --------------------------------------------------------------------------- Begründungen


@pytest.mark.parametrize("entry", DATA["verify_references"])
def test_verify_legal_references(entry: dict[str, Any]) -> None:
    result = ad.verify_legal_references(
        entry["reason"], entry["legal_basis"], entry["old"], entry["new"]
    )
    assert [result[0], result[1]] == entry["result"]


class Scripted:
    def __init__(self, responses: list[Any]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def execute(self, name: str, arguments: dict[str, Any]) -> str:
        import json

        self.calls.append({"name": name, "arguments": copy.deepcopy(arguments)})
        response = self.responses.pop(0)
        if isinstance(response, dict) and set(response) == {"raise"}:
            raise RuntimeError(response["raise"].split("'")[1])
        return response if isinstance(response, str) else json.dumps(response, ensure_ascii=False)


@pytest.mark.parametrize("entry", DATA["generate_reason"], ids=lambda e: e["raw"][:30])
def test_generate_reason(entry: dict[str, Any]) -> None:
    scripted = Scripted([entry["raw"]])
    provider = ad.mcp_tool_provider(scripted.execute)
    if "error" in entry:
        with pytest.raises(CompareError) as caught:
            ad.generate_reason(entry["old"], entry["new"], entry["model"], provider=provider)
        assert str(caught.value) == entry["message"]
    else:
        reason, metadata = ad.generate_reason(
            entry["old"], entry["new"], entry["model"], provider=provider
        )
        assert reason == entry["reason"]
        assert metadata == entry["metadata"]
    assert scripted.calls == entry["calls"]


# --------------------------------------------------------------------------- Rendering


def docx_parts(path: Path) -> dict[str, str]:
    import hashlib

    with zipfile.ZipFile(path) as archive:
        parts = {
            name: archive.read(name).decode("utf-8")
            for name in sorted(archive.namelist())
            if name in {"word/document.xml", "word/header1.xml", "word/footer1.xml"}
        }
        parts["word/styles.xml#sha256"] = hashlib.sha256(
            archive.read("word/styles.xml")
        ).hexdigest()
    return parts


@pytest.mark.parametrize("entry", DATA["render"], ids=lambda e: str(e["case"]))
def test_render_docx_is_identical(entry: dict[str, Any], tmp_path: Path) -> None:
    import importlib.metadata

    if importlib.metadata.version("python-docx") != DATA["environment"]["packages"]["python-docx"]:
        pytest.skip("andere python-docx-Version als bei der Aufzeichnung")
    result = ad.ComparisonResult.from_dict(copy.deepcopy(entry["input"]))
    target = tmp_path / "out.docx"
    if "error" in entry:
        with pytest.raises(CompareError) as caught:
            legacy.DocumentCompareService.render_docx(result, target, **entry["render"])
        assert str(caught.value) == entry["message"]
        return
    render_docx(result, target, **entry["render"])
    assert docx_parts(target) == entry["parts"]


def test_render_bytes_equal_file_output(tmp_path: Path) -> None:
    from auditcore_documents.render_docx import render_docx_bytes

    entry = DATA["render"][0]
    result = ad.ComparisonResult.from_dict(copy.deepcopy(entry["input"]))
    target = tmp_path / "a" / "b.docx"
    render_docx(result, target, **entry["render"])
    payload = render_docx_bytes(result, **entry["render"])
    copy_path = tmp_path / "c.docx"
    copy_path.write_bytes(payload)
    assert docx_parts(copy_path) == docx_parts(target)


# --------------------------------------------------------------------------- Consumer


@pytest.mark.parametrize("index", range(len(DATA["cli"])))
def test_cli_compare_documents(index: int, tmp_path: Path) -> None:
    entry = DATA["cli"][index]
    config = tmp_path / "department.json"
    ad.save_settings(entry["config"], config)
    scripted = Scripted(entry["responses"])
    returned = legacy.compare_documents(
        fixture_path(entry["old"]),
        fixture_path(entry["new"]),
        output=tmp_path / f"cli-{index}.docx",
        config=config,
        reason_provider=ad.mcp_tool_provider(scripted.execute),
        **entry["overrides"],
    )
    returned.pop("created_at")
    returned["output"] = Path(returned["output"]).name
    for key in VOLATILE:
        returned["metadata"].pop(key, None)
    assert returned == entry["returned"]
    assert scripted.calls == entry["calls"]
    assert len(scripted.responses) == entry["remaining_responses"]


@pytest.mark.parametrize("index", range(len(DATA["task"])))
def test_celery_task_flow(index: int) -> None:
    """Ablauf der Celery-Aufgabe mit der Bibliothek (Consumer-Anbindung, ohne DB)."""
    entry = DATA["task"][index]
    options = entry["options"]
    scripted = Scripted(entry["responses"])
    states: list[dict[str, Any]] = []
    try:
        result = legacy.DocumentCompareService.compare(
            fixture_path(entry["old"]),
            fixture_path(entry["new"]),
            mode=options.get("mode", "auto"),
            threshold=int(options.get("threshold", 85)),
            include_answers=bool(options.get("include_answers", True)),
            include_notes=bool(options.get("include_notes", True)),
            include_editorial=bool(options.get("include_editorial", False)),
            highlight_words=bool(options.get("highlight_words", True)),
            output_sections=list(
                options.get("output_sections") or ["changed", "removed", "added", "moved"]
            ),
            comparison_type=str(options.get("comparison_type", "standard")),
            ocr_callback=lambda _p: (
                "§ 1 Musterregel\nDiese Seite wurde durch eine OCR-Stelle gelesen und "
                "enthält genügend Text.\nEin zweiter Satz folgt hier.\n"
            ),
        )
    except CompareError as exc:
        assert entry["status"] == "failed"
        assert entry["error_message"] == str(exc)
        return
    result.metadata.update(
        {
            "old_label": options.get("old_label")
            or result.metadata.get("old_label")
            or "Alte Fassung",
            "new_label": options.get("new_label")
            or result.metadata.get("new_label")
            or "Neue Fassung",
        }
    )
    states.append({"state": "PROGRESS", "meta": {"progress": 35}})
    if options.get("generate_reasons") and options.get("comparison_type", "standard") == "standard":
        apply_reasons_worker(
            result,
            ad.mcp_tool_provider(scripted.execute),
            options.get("model"),
            on_progress=lambda p: states.append({"state": "PROGRESS", "meta": {"progress": p}}),
        )
    data = result.to_dict()
    data.pop("created_at")
    for key in VOLATILE:
        data["metadata"].pop(key, None)
    assert entry["status"] == "preview"
    assert data == entry["result_json"]
    assert states == entry["states"]
    assert scripted.calls == entry["calls"]


@pytest.mark.parametrize("index", range(len(DATA["worker"])))
def test_ecohesion_worker_flow(index: int) -> None:
    entry = DATA["worker"][index]
    spec = entry["spec"]
    try:
        result = ad.compare_files(
            fixture_path(entry["old"]),
            fixture_path(entry["new"]),
            profile=ad.LEGACY,
            options=ad.CompareOptions(
                mode=spec["mode"],
                threshold=spec["threshold"],
                include_editorial=spec["include_editorial"],
                highlight_words=True,
            ),
            context=context(),
        )
    except CompareError as exc:
        # Der Worker liest umbenannte Dateien (alt/neu + Endung).
        expected = entry["error"]["error"]
        assert (
            str(exc).replace(Path(entry["new"]).name, f"neu{Path(entry['new']).suffix}") == expected
        )
        return
    result.old_filename = spec["old_filename"]
    result.new_filename = spec["new_filename"]
    for key in VOLATILE:
        result.metadata.pop(key, None)
    data = result.to_dict()
    data.pop("created_at")
    assert data == entry["result"]
    columns, rows = synopsis_records(result)
    extra = synopsis_extra(result)
    recorded = entry["recorded"]["research_result"]
    assert rows == recorded["rows"]
    assert columns == recorded["columns"]
    assert len(rows) == recorded["total"]
    assert extra["notes"] == recorded["notes"]
    assert extra["extra"] == recorded["extra"]


def test_task_for_missing_record_is_consumer_logic() -> None:
    assert DATA["task_missing"] == {"status": "missing", "id": "gibt-es-nicht"}


def test_recorded_pages_cover_all_public_pdfs() -> None:
    assert set(recorded_pages()) == {
        "KassenSichV_2023-06-10.pdf",
        "KassenSichV_2026-08-27.pdf",
        "bgbl-2025-I-301-seite55.pdf",
    }


def test_injected_clock_sets_created_at() -> None:
    fixed = datetime(2026, 9, 23, 8, 15, tzinfo=UTC)
    result = ad.compare_files(
        fixture_path("synthetic/cl_basis_alt.docx"),
        fixture_path("synthetic/cl_basis_neu.docx"),
        profile=ad.LEGACY,
        options=ad.CompareOptions(mode="checklist", threshold=70),
        context=ad.ReadContext(now=lambda: fixed),
    )
    assert result.created_at == "2026-09-23T08:15:00+00:00"
