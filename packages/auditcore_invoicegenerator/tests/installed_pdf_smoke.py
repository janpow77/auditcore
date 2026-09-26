"""Run with installed optional ReportLab; stdlib assertions need no PDF parser."""

from datetime import date
from importlib.metadata import version
from pathlib import Path

import auditcore_invoicegenerator as invoice

origin = Path(invoice.__file__).resolve()
assert {"site-packages", "dist-packages"} & set(origin.parts)
assert version("auditcore_invoicegenerator") == "0.2.3"
record = invoice.InvoiceScenario(42, base_date=date(2026, 1, 1)).generate(1)
payload = invoice.render_pdf(record)
assert payload.startswith(b"%PDF-") and payload.rstrip().endswith(b"%%EOF")
assert payload == invoice.render_pdf(record)
assert len(payload) > 1000
print(
    {
        "status": "PASS",
        "scope": "INSTALLED_OPTIONAL_PDF",
        "origin": str(origin),
        "bytes": len(payload),
        "reportlab_version": version("reportlab"),
    }
)
