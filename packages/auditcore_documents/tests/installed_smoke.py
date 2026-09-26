"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

from importlib.metadata import distribution
from importlib.util import find_spec

import auditcore_documents as ad
from auditcore_documents.legacy import DocumentCompareService


def pipeline_smoke() -> None:
    """Nachverarbeitung, Validierung, Stufen-Hash und Audit ohne OCR/DB."""
    import asyncio

    from auditcore_documents import pipeline as pl

    audit = pl.InMemoryAuditLog()
    context = pl.PipelineContext(document_id="d", run_id="r")
    context.artifacts.ocr_text = (
        "Rechnungsnummer: RE-1\nNettobetrag: 100,00\nMwSt 19%: 19,00\nGesamtbetrag: 119,00\n"
    )
    orchestrator = pl.PipelineOrchestrator(
        [pl.PostprocessStage(), pl.ValidationStage()], audit_service=audit
    )
    result = asyncio.run(orchestrator.run(context))
    assert result.status == pl.RunStatus.OK, result.status
    assert result.artifacts.normalized_json["total"] == 119.0
    assert len(result.hash_chain) == 2 and len(audit) == 7


def donut_smoke() -> None:
    """DONUT_PIPELINE mit FakeDonut: Plausibilität, Abgleich, LEGACY unverändert (ohne torch)."""
    import asyncio
    import tempfile
    from pathlib import Path

    from auditcore_documents import pipeline as pl

    assert pl.LEGACY_PIPELINE.fingerprint.startswith("aaec1633e2ec")
    fields = {
        "invoice_number": "RE-1",
        "invoice_date": "15.01.2026",
        "supplier": {"name": "Beispiel GmbH", "vat_id": "DE136695976"},
        "net_amount": "100,00 €",
        "vat_lines": [{"rate": "19 %", "amount": "19,00 €"}],
        "total": "119,00 €",
        "iban": "DE89 3704 0044 0532 0130 00",
    }
    text = (
        "Rechnungsnummer: RE-1\nRechnungsdatum: 15.01.2026\nUSt-IdNr.: DE136695976\n"
        "Nettobetrag: 100,00 €\nUSt 19 %: 19,00 €\nGesamtbetrag: 119,00 €\n"
        "IBAN: DE89 3704 0044 0532 0130 00\n"
    )

    class Tesseract:
        def parse(self, path: Path) -> pl.ParsedDocument:
            return pl.ParsedDocument(text, [pl.ParsedPage(text, 0.95)])

    def run(total: str) -> pl.PipelineContext:
        donut = pl.FakeDonut([pl.DonutResult(fields={**fields, "total": total})])
        ocr = pl.OcrStage(donut=donut, tesseract=Tesseract())
        pipeline = pl.build_pipeline(profile=pl.DONUT_PIPELINE, ocr=ocr)
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "beleg.png"
            source.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 32)
            context = pl.PipelineContext(document_id="d", run_id="r", input_uri=str(source))
            return asyncio.run(pipeline.run(context))

    good = run("119,00 €")
    assert good.artifacts.normalized_json["total"] == 119.0, good.validation_flags
    assert good.status == pl.RunStatus.REVIEW_NEEDED  # ohne Feldkonfidenz nie automatisch OK
    bad = run("1190,00 €")
    assert bad.status == pl.RunStatus.REVIEW_NEEDED
    assert "FAIL_VAL_DONUT_PLAUSIBILITY" in bad.validation_flags
    assert bad.artifacts.normalized_json["total"] == 119.0  # Regex-Wert aus Tesseract bleibt


def web_smoke(rows: list[ad.CompareRow]) -> None:
    """Synopse-Dienst ohne Web-Extras: Ergebnis übernehmen, Zeile abwählen, Markdown."""
    from auditcore_documents import web

    service = web.SynopsisService()
    result = ad.ComparisonResult(
        version="1.1.0",
        mode="text",
        old_filename="alt.docx",
        new_filename="neu.docx",
        old_sha256="0" * 64,
        new_sha256="1" * 64,
        old_count=1,
        new_count=2,
        matched_count=1,
        changed_count=0,
        removed_count=0,
        added_count=1,
        rows=rows,
        created_at="2026-09-25T00:00:00+00:00",
    )
    item = service.import_result("prüfer", {"title": "Synopse", "result": result.to_dict()})
    added = next(r.row_id for r in rows if r.status == "added")
    service.update_rows(
        "prüfer", item.comparison_id, {"rows": [{"row_id": added, "reason": "neu"}]}
    )
    text = service.export("prüfer", item.comparison_id, "markdown").content.decode()
    assert "## Festgestellte Änderungen" in text and "**Grund:** neu" in text, text
    if find_spec("starlette") is None:
        try:
            web.create_app  # noqa: B018
        except ad.DependencyError:
            pass
        else:
            raise AssertionError("create_app must require the optional extra 'web'")


def main() -> None:
    """Pure comparison, article-law commands, reasons port and extra boundaries."""
    package = distribution("auditcore_documents")
    assert package.version == "0.3.3"
    runtime = [r for r in package.requires or [] if "extra ==" not in r]
    assert runtime == ["auditcore_common==0.1.1"], runtime
    assert find_spec("auditcore") is None
    assert DocumentCompareService.VERSION == "1.1.0"
    old = [
        ad.CompareItem("0", text="Die Prüfbehörde prüft das Vorhaben.", location="§ 1, Absatz 1")
    ]
    new = [
        ad.CompareItem("0", text="Der Begünstigte legt Belege vor.", location="§ 1, Absatz 1"),
        ad.CompareItem("1", text="Die Prüfbehörde prüft das Vorhaben.", location="§ 1, Absatz 2"),
    ]
    rows, counts = ad.compare_items(old, new, mode="text", profile=ad.LEGACY_DIFFLIB)
    assert counts["matched_count"] == 1 and counts["added_count"] == 1, counts
    web_smoke(rows)
    base = [ad.LawParagraph("§ 11", 1, "gelten § 9 des BSI-Gesetzes sowie")]
    paragraphs, open_commands, recognised = ad.apply_commands(
        base,
        [
            "In § 11 Absatz 1 Satz 1 wird die Angabe „§ 9 des BSI-Gesetzes“ "
            "durch die Angabe „§ 52 des BSI-Gesetzes“ ersetzt."
        ],
    )
    assert recognised == 1 and not open_commands
    assert paragraphs[0].new_text == "gelten § 52 des BSI-Gesetzes sowie"
    reason, meta = ad.generate_reason(
        "Frist nach § 5", "Frist nach § 6", provider=lambda *_: {"begruendung": "Nach § 7."}
    )
    assert reason == "Nach § 7." and meta["missing_references"] == ["§ 7"]
    assert ad.sanitise_settings({"threshold": 5})["threshold"] == 70
    pipeline_smoke()
    donut_smoke()
    if find_spec("rapidfuzz") is None:
        try:
            ad.get_scorer("rapidfuzz-token-set")
        except ad.DependencyError:
            pass
        else:
            raise AssertionError("rapidfuzz scorer must require the optional extra")
    print("PASS: installed auditcore_documents comparison, synopsis, reasons and extra boundary")


if __name__ == "__main__":
    main()
