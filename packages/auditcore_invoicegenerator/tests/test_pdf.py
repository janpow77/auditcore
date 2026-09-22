"""Verify actual optional PDF contents, pagination, invariants and hostile plain text."""

import copy
import io
import subprocess
import sys
from datetime import date

import pytest
from pypdf import PdfReader

from auditcore_invoicegenerator import InvoiceScenario, render_pdf


def record():
    return InvoiceScenario(42, base_date=date(2026, 1, 1)).generate(1, error="wrong_total")


def test_pdf_complete_content_and_preserves_intentional_wrong_total():
    invoice = record()
    invoice["supplier"]["name"] = "Müller & Söhne GmbH"
    original = copy.deepcopy(invoice)
    result = render_pdf(invoice)
    assert result.startswith(b"%PDF-") and invoice == original
    pdf = PdfReader(io.BytesIO(result))
    text = "\n".join(page.extract_text() for page in pdf.pages)
    for key in ("id", "invoice_number", "invoice_date", "supply_date", "due_date"):
        assert invoice[key] in text
    for party in ("supplier", "beneficiary"):
        for value in invoice[party].values():
            assert value in text
    for item in invoice["line_items"]:
        assert item["description"] in text
        assert f"{item['amount']:.2f}" in text
    for key in ("subtotal", "vat_amount", "total"):
        assert f"{invoice['amounts'][key]:.2f}" in text
    assert "SYNTHETIC TEST INVOICE" in text
    assert "wrong_total" not in text and "correct_values" not in text
    assert len(pdf.pages) == 1


def test_pdf_is_byte_deterministic_and_has_no_active_content():
    invoice = record()
    payload = '<img src="https://example.invalid/secret"> javascript:alert(1)'
    invoice["line_items"][0]["description"] = payload
    first = render_pdf(invoice)
    assert first == render_pdf(invoice)
    pdf = PdfReader(io.BytesIO(first))
    assert payload in "\n".join(page.extract_text() for page in pdf.pages)
    assert "/OpenAction" not in pdf.trailer["/Root"]
    assert "/Names" not in pdf.trailer["/Root"]
    assert all("/Annots" not in page for page in pdf.pages)
    assert all("/XObject" not in page["/Resources"] for page in pdf.pages)


def test_pdf_paginates_every_position_and_wraps_long_tokens():
    invoice = record()
    invoice["line_items"] = [
        {
            "description": f"Unique item {i:04d} " + "longword" * 20,
            "quantity": 1,
            "unit_price": 1.0,
            "amount": 1.0,
        }
        for i in range(150)
    ]
    pdf = PdfReader(io.BytesIO(render_pdf(invoice)))
    assert len(pdf.pages) > 3
    text = "\n".join(page.extract_text() for page in pdf.pages)
    for i in range(150):
        assert text.count(f"Unique item {i:04d}") == 1
    for i, page in enumerate(pdf.pages, 1):
        assert f"Page {i}" in page.extract_text()
        assert "SYNTHETIC TEST INVOICE" in page.extract_text()
    assert "TOTALS" in pdf.pages[-1].extract_text()


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), True, "100", 1e16, 10**1000])
def test_pdf_rejects_invalid_amounts(bad):
    invoice = record()
    invoice["amounts"]["total"] = bad
    with pytest.raises(ValueError):
        render_pdf(invoice)


@pytest.mark.parametrize("bad", ["hidden\x00text", "line\nforgery", "東京", "😀", "x" * 2001])
def test_pdf_rejects_controls_unsupported_glyphs_and_oversized_fields(bad):
    invoice = record()
    invoice["supplier"]["name"] = bad
    with pytest.raises(ValueError):
        render_pdf(invoice)


def test_pdf_bounds_item_count_and_validates_required_shape():
    invoice = record()
    invoice["line_items"] *= 2001
    with pytest.raises(ValueError):
        render_pdf(invoice)
    with pytest.raises(ValueError):
        render_pdf({})


def test_core_import_without_pdf_dependency_and_actionable_error():
    code = """
import importlib.abc, sys
class BlockReportLab(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'reportlab' or fullname.startswith('reportlab.'):
            raise ModuleNotFoundError('intentionally absent optional extra')
sys.meta_path.insert(0, BlockReportLab())
from auditcore_invoicegenerator import InvoiceScenario, render_pdf, PDFDependencyError
from datetime import date
invoice = InvoiceScenario(42, base_date=date(2026,1,1)).generate(1)
assert invoice['line_items']
try:
    render_pdf(invoice)
except PDFDependencyError as error:
    assert 'auditcore_invoicegenerator[pdf]' in str(error)
else:
    raise AssertionError('missing extra was hidden')
"""
    subprocess.run([sys.executable, "-I", "-c", code], check=True)
