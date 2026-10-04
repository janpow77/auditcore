"""Issue #238: OCR-Rasterung parametrisierbar, eingebauter Tesseract-Port."""

from __future__ import annotations

import asyncio
import io
from pathlib import Path

import pytest

from auditcore_documents.pipeline import PipelineContext, TesseractCli, pdfium_rasterizer_for
from auditcore_documents.pipeline.stages.base import StageError
from auditcore_documents.pipeline.stages.ocr import OcrStage, pdfium_rasterizer
from auditcore_documents.pipeline.stages.ocr_engines import page_from_tsv

TSV_HEADER = (
    "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext"
)


def tsv(*words: tuple[int, str, float]) -> str:
    rows = [TSV_HEADER, "1\t1\t0\t0\t0\t0\t0\t0\t100\t100\t-1\t"]
    for index, (line, word, conf) in enumerate(words, start=1):
        rows.append(f"5\t1\t1\t1\t{line}\t{index}\t0\t0\t10\t10\t{conf}\t{word}")
    return "\n".join(rows) + "\n"


def synthetic_pdf(pages: int = 3) -> bytes:
    canvas = pytest.importorskip("reportlab.pdfgen.canvas")
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(144, 144))
    for number in range(1, pages + 1):
        pdf.drawString(10, 70, f"Seite {number}")
        pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def image_width(png: bytes) -> int:
    image = pytest.importorskip("PIL.Image")
    with image.open(io.BytesIO(png)) as opened:
        return int(opened.size[0])


def test_rasterizer_dpi_and_page_limit_take_effect() -> None:
    pytest.importorskip("pypdfium2")
    data = synthetic_pdf(3)
    standard = pdfium_rasterizer(data)
    coarse = pdfium_rasterizer_for(dpi=72, max_pages=2)(data)
    fine = pdfium_rasterizer_for(dpi=144, max_pages=1)(data)
    assert standard is not None and coarse is not None and fine is not None
    assert len(standard) == 3 and len(coarse) == 2 and len(fine) == 1
    assert image_width(coarse[0][1]) == 144
    assert image_width(fine[0][1]) == 288
    assert image_width(standard[0][1]) == 400


def test_rasterizer_defaults_are_unchanged() -> None:
    assert pdfium_rasterizer_for() is pdfium_rasterizer
    assert OcrStage().rasterizer is pdfium_rasterizer


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"dpi": 50}, ValueError),
        ({"dpi": 601}, ValueError),
        ({"max_pages": 0}, ValueError),
        ({"max_pages": True}, TypeError),
    ],
)
def test_rasterizer_rejects_invalid_parameters(
    kwargs: dict[str, int], error: type[Exception]
) -> None:
    with pytest.raises(error):
        pdfium_rasterizer_for(**kwargs)


def test_ocr_stage_passes_raster_parameters() -> None:
    pytest.importorskip("pypdfium2")
    stage = OcrStage(raster_dpi=72, raster_max_pages=1)
    assert stage.rasterizer is not None
    pages = stage.rasterizer(synthetic_pdf(3))
    assert pages is not None and len(pages) == 1
    assert image_width(pages[0][1]) == 144


def test_ocr_stage_rejects_raster_parameters_for_own_rasterizer() -> None:
    def own(data: bytes) -> list[tuple[int, bytes]] | None:
        return None

    assert OcrStage(rasterizer=own).rasterizer is own
    assert OcrStage(rasterizer=None).rasterizer is None
    with pytest.raises(ValueError, match="eingebauten"):
        OcrStage(rasterizer=own, raster_dpi=300)


def test_page_from_tsv_groups_lines_and_averages_confidence() -> None:
    parsed = page_from_tsv(tsv((1, "Rechnung", 90.0), (1, "Nr.", 80.0), (2, "250", -1.0)))
    assert parsed.text == "Rechnung Nr.\n250"
    assert parsed.confidence == pytest.approx(0.85)
    assert page_from_tsv(TSV_HEADER).confidence is None


class Recorder:
    def __init__(self, output: str) -> None:
        self.output = output
        self.calls: list[tuple[list[str], bytes, float]] = []

    def __call__(self, args: list[str], data: bytes, timeout: float) -> str:
        self.calls.append((args, data, timeout))
        return self.output


def test_tesseract_cli_reads_image_via_stdin(tmp_path: Path) -> None:
    image = tmp_path / "beleg.png"
    image.write_bytes(b"\x89PNG-Daten")
    runner = Recorder(tsv((1, "Summe", 95.0), (1, "119,00", 85.0)))
    port = TesseractCli(languages="deu", psm=6, oem=1, timeout=5.0, runner=runner)
    parsed = port.parse(image)
    assert parsed.raw_text == "Summe 119,00"
    assert parsed.pages[0].confidence == pytest.approx(0.90)
    args, data, timeout = runner.calls[0]
    assert args == ["tesseract", "stdin", "stdout", "-l", "deu", "--psm", "6", "--oem", "1", "tsv"]
    assert data == b"\x89PNG-Daten" and timeout == 5.0


def test_tesseract_cli_rasterizes_pdf(tmp_path: Path) -> None:
    pdf = tmp_path / "beleg.pdf"
    pdf.write_bytes(b"%PDF-1.4 synthetisch")
    runner = Recorder(tsv((1, "Text", 90.0)))
    port = TesseractCli(rasterizer=lambda _d: [(1, b"a"), (2, b"b")], runner=runner)
    parsed = port.parse(pdf)
    assert [call[1] for call in runner.calls] == [b"a", b"b"]
    assert parsed.raw_text == "Text\n\nText"
    with pytest.raises(RuntimeError, match="ocr-raster"):
        TesseractCli(rasterizer=None, runner=runner).parse(pdf)


def run_tesseract_stage(stage: OcrStage, source: Path) -> PipelineContext:
    context = PipelineContext(document_id="d", run_id="r", input_uri=str(source))
    return asyncio.run(stage.execute(context))


def test_ocr_stage_uses_tesseract_cli(tmp_path: Path) -> None:
    image = tmp_path / "beleg.png"
    image.write_bytes(b"\x89PNG")
    port = TesseractCli(runner=Recorder(tsv((1, "Gesamtbetrag", 92.0))))
    context = run_tesseract_stage(OcrStage(backend="tesseract", tesseract=port), image)
    assert context.artifacts.ocr_text == "Gesamtbetrag"
    assert context.ocr_metrics is not None
    assert context.ocr_metrics.avg_confidence == pytest.approx(0.92)


def test_missing_tesseract_names_builtin_port(tmp_path: Path) -> None:
    image = tmp_path / "beleg.png"
    image.write_bytes(b"\x89PNG")
    with pytest.raises(StageError, match="TesseractCli") as caught:
        run_tesseract_stage(OcrStage(backend="tesseract"), image)
    assert caught.value.error_code == "TESSERACT_OCR_FAILED"
