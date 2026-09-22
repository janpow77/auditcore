"""Optional deterministic, plain-text PDF rendering for synthetic invoice records."""

from __future__ import annotations

import math
from io import BytesIO
from textwrap import wrap
from typing import Any

from auditcore_invoicegenerator.models import InvoiceRecord


class PDFDependencyError(ImportError):
    """The explicitly selected PDF extra is not installed."""


def _text(value: object) -> str:
    """Reject invisible controls and unsupported glyphs instead of losing invoice data."""
    if not isinstance(value, str) or len(value) > 2000:
        raise ValueError("PDF text fields must be strings of at most 2000 characters")
    if any(ord(char) < 32 or 127 <= ord(char) < 160 for char in value):
        raise ValueError("PDF text fields cannot contain control characters")
    try:
        value.encode("cp1252")
    except UnicodeEncodeError as exc:
        raise ValueError("PDF standard fonts support Windows-1252 text only") from exc
    return value


def _number(value: object, *, money: bool = True) -> str:
    """Format provided values, without recalculating or correcting intended test defects."""
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError("PDF amounts and quantities must be finite numbers")
    if abs(value) > 1e15 or not math.isfinite(value):
        raise ValueError("PDF numbers must be finite and have magnitude at most 1e15")
    return f"{value:.2f}" if money else str(value)


def _lines(invoice: InvoiceRecord) -> list[str]:
    """Validate required record fields and create readable lines before opening a canvas."""
    try:
        lines = [
            "Document: " + _text(invoice["id"]),
            "Invoice: " + _text(invoice["invoice_number"]),
            "Invoice date: " + _text(invoice["invoice_date"]),
            "Supply date: " + _text(invoice["supply_date"]),
            "Due date: " + _text(invoice["due_date"]),
        ]
        for label, party in [
            ("SUPPLIER", invoice["supplier"]),
            ("BENEFICIARY", invoice["beneficiary"]),
        ]:
            lines.extend(["", label])
            for key in ("name", "address", "city", "country", "vat_id"):
                lines.append(key.replace("_", " ").title() + ": " + _text(party[key]))
        items = invoice["line_items"]
        if not isinstance(items, list) or not 1 <= len(items) <= 2000:
            raise ValueError("PDF invoices require between 1 and 2000 line items")
        currency = _text(invoice["amounts"]["currency"])
        lines.extend(["", "LINE ITEMS"])
        for index, item in enumerate(items, 1):
            lines.append(f"{index}. " + _text(item["description"]))
            lines.append(
                "   Quantity: "
                + _number(item["quantity"], money=False)
                + " | Unit price: "
                + _number(item["unit_price"])
                + " "
                + currency
                + " | Amount: "
                + _number(item["amount"])
                + " "
                + currency
            )
        amounts = invoice["amounts"]
        lines.extend(["", "TOTALS"])
        for label, value in [
            ("Subtotal", amounts["subtotal"]),
            ("VAT", amounts["vat_amount"]),
            ("Total", amounts["total"]),
        ]:
            lines.append(label + ": " + _number(value) + " " + currency)
        lines.append("VAT rate: " + _number(amounts["vat_rate"], money=False))
        if sum(map(len, lines)) > 200_000:
            raise ValueError("PDF invoice text exceeds 200000 characters")
        return [part for line in lines for part in (wrap(line, width=86) or [""])]
    except (KeyError, TypeError) as exc:
        raise ValueError("PDF invoice is missing a required field or has an invalid shape") from exc


def render_pdf(invoice: InvoiceRecord) -> bytes:
    """Render one synthetic invoice as deterministic PDF bytes with automatic pagination.

    Requires ``auditcore_invoicegenerator[pdf]``. Text is literal Windows-1252
    (including German umlauts); unsupported glyphs raise ValueError. No markup,
    links, images, scripts or external resources are interpreted. Provided totals
    and intentionally missing VAT IDs are preserved; ground-truth metadata is
    not printed. Bytes are reproducible for identical data and ReportLab version.
    """
    try:
        from reportlab.pdfgen.canvas import Canvas
    except ImportError as exc:
        raise PDFDependencyError("Install auditcore_invoicegenerator[pdf] to render PDFs") from exc
    lines = _lines(invoice)
    output = BytesIO()
    canvas: Any = Canvas(output, pagesize=(595.28, 841.89), invariant=1, pageCompression=1)
    canvas.setTitle("Synthetic test invoice")
    canvas.setAuthor("auditcore_invoicegenerator")
    canvas.setSubject("Synthetic training document; not a real invoice")
    for page_start in range(0, len(lines), 53):
        page = page_start // 53 + 1
        canvas.setFont("Helvetica-Bold", 13)
        canvas.drawString(44, 801, "SYNTHETIC TEST INVOICE")
        canvas.setFont("Courier", 9.5)
        for row, line in enumerate(lines[page_start : page_start + 53]):
            canvas.drawString(44, 777 - row * 13, line)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(44, 30, "Synthetic training data - not a real invoice")
        canvas.drawRightString(551, 30, f"Page {page}")
        canvas.showPage()
    canvas.save()
    return output.getvalue()
