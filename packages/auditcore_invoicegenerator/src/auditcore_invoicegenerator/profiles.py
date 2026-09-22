"""Named Flowinvoice demo profile retaining observed RNG order and float rounding."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from random import Random
from typing import Any, cast

from auditcore_invoicegenerator import _legacy
from auditcore_invoicegenerator.models import InvoiceRecord

FLOWINVOICE_DEMO_PROFILE = "flowinvoice-demo-fb2d185"
PROBLEM_TYPES = (
    "sanctions",
    "ted_concentration",
    "duplicate",
    "invalid_vat",
    "subject_relevance",
    "temporal",
)


def suppliers() -> list[dict[str, Any]]:
    """Return independent copies of the historical synthetic supplier catalog."""
    return deepcopy(_legacy.SUPPLIERS)


def problem_suppliers() -> dict[str, dict[str, Any]]:
    """Return synthetic training labels; these do not assert real sanctions or wrongdoing."""
    return deepcopy(_legacy.PROBLEM_SUPPLIERS)


class FlowInvoiceDemoProfile:
    """Stateful local RNG with the exact characterized single-invoice legacy draw order.

    Independent instances do not modify process-global random state. An instance
    is sequential; concurrent sharing is not supported. Historical dates, demo
    tax rates, fixed beneficiary and numerical rounding remain unchanged.
    """

    def __init__(self, seed: int | None = 42) -> None:
        self.rng = Random(seed)

    def generate_invoice(
        self, index: int, supplier: dict[str, Any], problem_type: str | None = None
    ) -> InvoiceRecord:
        """Generate a complete historical-profile invoice without mutating its supplier."""
        return cast(
            InvoiceRecord, _legacy.generate_invoice(index, supplier, problem_type, rng=self.rng)
        )

    def generate_invoice_number(self, index: int, supplier: dict[str, Any]) -> str:
        """Observe the profile's historical invoice-number formatting and RNG calls."""
        return _legacy.generate_invoice_number(index, supplier, rng=self.rng)

    def generate_invoice_date(self, temporal_problem: bool = False) -> tuple[datetime, datetime]:
        """Generate fixed-range historical dates, including the explicit temporal error."""
        return _legacy.generate_invoice_date(temporal_problem, rng=self.rng)

    def generate_line_items(self, category: str, target_amount: float) -> list[dict[str, Any]]:
        """Retain historical target-bound generation, which need not sum to the target."""
        return _legacy.generate_line_items(category, target_amount, rng=self.rng)

    def generate_batch(self, total: int) -> list[InvoiceRecord]:
        """Generate sequential clean demo invoices; no implicit 500-record error schedule."""
        if isinstance(total, bool) or not isinstance(total, int) or total < 0:
            raise ValueError("total must be a nonnegative integer")
        return [
            self.generate_invoice(index, self.rng.choice(_legacy.SUPPLIERS))
            for index in range(1, total + 1)
        ]


def generate_invoice(
    index: int, supplier: dict[str, Any], problem_type: str | None = None, *, seed: int | None = 42
) -> InvoiceRecord:
    """Generate one repeatable legacy-profile invoice using a fresh independent RNG."""
    return FlowInvoiceDemoProfile(seed).generate_invoice(index, supplier, problem_type)


def get_vat_rate(country: str) -> float:
    """Return the historical demonstration rate; this is not current tax advice."""
    return _legacy.get_vat_rate(country)


def get_currency(country: str) -> str:
    """Return the historical demonstration currency assignment."""
    return _legacy.get_currency(country)


def generate_invoice_legacy_global(
    index: int, supplier: dict[str, Any], problem_type: str | None = None
) -> InvoiceRecord:
    """Compatibility adapter for the original demo's explicit process-global RNG contract.

    This opt-in adapter consumes and restores the advanced global RNG state just
    as the original function did, including exceptional calls. It is intended
    only for a characterized sequential legacy consumer, not concurrent use.
    """
    import random

    rng = Random(0)
    rng.setstate(random.getstate())
    try:
        return cast(InvoiceRecord, _legacy.generate_invoice(index, supplier, problem_type, rng=rng))
    finally:
        random.setstate(rng.getstate())
