"""Run with python -I after wheel/APT installation; requires no pytest or source path."""

import importlib.metadata
import json
import sys
from datetime import date
from pathlib import Path

import auditcore_dummygenerator

import auditcore_invoicegenerator
from auditcore_invoicegenerator import FlowInvoiceDemoProfile, InvoiceScenario, suppliers

origin = Path(auditcore_invoicegenerator.__file__).resolve()
assert "site-packages" in origin.parts or "dist-packages" in origin.parts
assert "/src/" not in str(origin)
assert importlib.metadata.version("auditcore_invoicegenerator") == "0.2.2"
assert importlib.metadata.version("auditcore_dummygenerator") == "0.1.2"
legacy = FlowInvoiceDemoProfile(42).generate_invoice(1, suppliers()[0])
assert legacy["line_items"] and legacy["supplier"]["name"] and legacy["beneficiary"]["name"]
records = InvoiceScenario(42, base_date=date(2026, 1, 1)).generate_batch(
    2, errors={2: "wrong_total"}
)
clean, broken = records
assert clean["line_items"]
amounts = clean["amounts"]
assert amounts["subtotal"] == sum(item["amount"] for item in clean["line_items"])
assert amounts["vat_amount"] == round(amounts["subtotal"] * amounts["vat_rate"], 2)
assert amounts["total"] == round(amounts["subtotal"] + amounts["vat_amount"], 2)
assert broken["amounts"]["total"] != broken["metadata"]["correct_values"]["amounts.total"]
assert broken["metadata"]["injected_errors"] == ["wrong_total"]
print(
    json.dumps(
        {
            "status": "PASS",
            "python": sys.executable,
            "invoice_origin": str(origin),
            "dummy_origin": auditcore_dummygenerator.__file__,
            "records": len(records),
        }
    )
)
