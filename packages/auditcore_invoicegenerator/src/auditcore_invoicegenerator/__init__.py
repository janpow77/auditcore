"""Synthetic invoices with distinct characterized legacy and new scenario contracts."""

from auditcore_invoicegenerator.models import Amounts, InvoiceRecord, LineItem, Party
from auditcore_invoicegenerator.pdf import PDFDependencyError, render_pdf
from auditcore_invoicegenerator.profiles import (
    FLOWINVOICE_DEMO_PROFILE,
    PROBLEM_TYPES,
    FlowInvoiceDemoProfile,
    generate_invoice,
    generate_invoice_legacy_global,
    get_currency,
    get_vat_rate,
    problem_suppliers,
    suppliers,
)
from auditcore_invoicegenerator.scenarios import (
    InvoiceScenario,
    ScenarioError,
    duplicate_invoice,
    to_json,
)

__all__ = [
    "Amounts",
    "InvoiceRecord",
    "LineItem",
    "Party",
    "PDFDependencyError",
    "render_pdf",
    "FLOWINVOICE_DEMO_PROFILE",
    "PROBLEM_TYPES",
    "FlowInvoiceDemoProfile",
    "InvoiceScenario",
    "ScenarioError",
    "generate_invoice",
    "generate_invoice_legacy_global",
    "get_currency",
    "get_vat_rate",
    "problem_suppliers",
    "suppliers",
    "duplicate_invoice",
    "to_json",
]
