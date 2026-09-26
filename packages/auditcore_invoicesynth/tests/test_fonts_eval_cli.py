from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from auditcore_invoicesynth.cli import main
from auditcore_invoicesynth.evaluation import (
    ACCEPTANCE_THRESHOLDS,
    canonical,
    check_acceptance,
    evaluate,
    flatten,
)
from auditcore_invoicesynth.fonts import FontError, FontSet, discover_fonts, fetch_font, sha256_file

TRUTH = {
    "invoice_number": "RE-1",
    "invoice_date": "15.01.2026",
    "supplier": {"name": "A GmbH", "vat_id": "DE136695976"},
    "net_amount": "100,00 €",
    "vat_lines": [{"rate": "19 %", "amount": "19,00 €"}],
    "total": "119,00 €",
    "iban": "DE89 3704 0044 0532 0130 00",
}


def test_font_pins_and_catalog(fonts: FontSet, tmp_path: Path) -> None:
    font = fonts.fonts[0]
    assert sha256_file(font.path) == font.sha256
    with pytest.raises(FontError):
        discover_fonts(pins={font.path.name: "0" * 64})
    with pytest.raises(FontError):
        discover_fonts(families=["Comic Sans"])
    assert discover_fonts([tmp_path]).families == ()


def test_fetch_font_requires_hash_and_catalog_name(tmp_path: Path) -> None:
    data = b"font"
    digest = hashlib.sha256(data).hexdigest()
    target = fetch_font(
        "https://example.invalid/f", digest, tmp_path / "DejaVuSans.ttf", lambda url: data
    )
    assert target.read_bytes() == data
    with pytest.raises(FontError):
        fetch_font("u", "0" * 64, tmp_path / "LiberationSans-Regular.ttf", lambda url: data)
    assert not (tmp_path / "LiberationSans-Regular.ttf").exists()
    with pytest.raises(FontError):
        fetch_font("u", digest, tmp_path / "evil.ttf", lambda url: data)


def test_normalization() -> None:
    flat = flatten(TRUTH)
    assert flat["vat_amount"] == "19.00" and flat["vat_rates"] == "19 %"
    assert canonical("iban", flat["iban"]) == "DE89370400440532013000"
    assert canonical("invoice_date", "2026-01-15") == canonical("invoice_date", "15.1.26")
    assert canonical("total", "119.00 EUR") == "119.00"
    assert canonical("vat_rates", "7%+19,0 %") == "19+7"


def test_evaluation_separates_wrong_missing_and_hallucinated() -> None:
    prediction = {
        "invoice_number": "RE-1",
        "invoice_date": "2026-01-15",
        "supplier": {"vat_id": "DE 136 695 976"},
        "total": "1.119,00",
        "iban": "DE89370400440532013000",
        "bic": "SYNTDEF3XXX",
    }
    report = evaluate([(TRUTH, prediction), (TRUTH, TRUTH)], accept=lambda flat: {"total", "iban"})
    total = report.fields["total"]
    assert (total.expected, total.correct, total.wrong, total.hallucinated) == (2, 1, 1, 1)
    assert total.wrong_rate_after_plausibility == 0.5
    assert report.fields["net_amount"].missing == 1
    assert report.fields["bic"].spurious == 1
    assert report.documents_all_required_correct == 1
    result = check_acceptance(report)
    assert not result.passed and any("total" in f for f in result.failures)
    perfect = evaluate([(TRUTH, TRUTH)] * 3)
    assert check_acceptance(perfect).passed
    assert set(ACCEPTANCE_THRESHOLDS) == {
        "total",
        "invoice_date",
        "invoice_number",
        "iban",
        "supplier.vat_id",
    }


def test_cli_round_trip(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["fonts"]) == 0
    assert json.loads(capsys.readouterr().out)["families"]
    counts = [
        "--train",
        "3",
        "--validation",
        "1",
        "--test-synthetic",
        "1",
        "--test-layout-holdout",
        "1",
        "--dpi",
        "50",
    ]
    assert main(["plan", *counts]) == 0
    assert json.loads(capsys.readouterr().out)["samples"] == 6
    out = tmp_path / "ds"
    assert main(["build", "--out", str(out), *counts]) == 0
    built = json.loads(capsys.readouterr().out)["dataset_hash"]
    assert main(["verify", str(out)]) == 0
    assert json.loads(capsys.readouterr().out)["dataset_hash"] == built
    rows = [
        json.loads(line)
        for line in (out / "test_synthetic/metadata.jsonl").read_text().splitlines()
    ]
    predictions = tmp_path / "p.jsonl"
    predictions.write_text(
        "".join(
            json.dumps(
                {"file_name": r["file_name"], "parse": json.loads(r["ground_truth"])["gt_parse"]}
            )
            + "\n"
            for r in rows
        )
    )
    assert main(["evaluate", str(out), "--predictions", str(predictions)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["fields"]["total"]["accuracy"] == 1.0
    assert main(["build", "--out", str(out), *counts]) == 2
