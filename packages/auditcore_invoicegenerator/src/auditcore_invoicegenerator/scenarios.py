"""New explicit scenario contract using the independently installed dummy-data library."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import date, timedelta
from typing import Any, Literal, cast

from auditcore_dummygenerator import TestDataGenerator

from auditcore_invoicegenerator.models import InvoiceRecord, Party
from auditcore_invoicegenerator.profiles import FlowInvoiceDemoProfile

ScenarioError = Literal["none", "wrong_total", "missing_vat_id", "date_before_reference"]
ERRORS = {"none", "wrong_total", "missing_vat_id", "date_before_reference"}


class InvoiceScenario:
    """Generate synthetic parties and complete invoices with explicit expected defects.

    Party RNG belongs to dummygenerator; invoice RNG belongs to the named legacy
    profile. Neither consumes the other's random stream. This new scenario API
    does not claim equivalence with the legacy beneficiary/date/error contract.
    """

    def __init__(self, seed: int, *, base_date: date, country: str = "DE") -> None:
        if country not in {"DE", "AT"}:
            raise ValueError("Scenario party catalogs currently support DE and AT")
        self.seed = seed
        self.base_date = base_date
        self.country = country
        self._parties = TestDataGenerator(seed=seed, base_date=base_date, use_joblib=False)
        self._invoices = FlowInvoiceDemoProfile(seed)

    def _party(self) -> Party:
        city, postal_code = self._parties.generate_city(self.country)
        return {
            "name": self._parties.generate_company(),
            "vat_id": "SYNTHETIC-NOT-A-REGISTERED-VAT-ID",
            "country": self.country,
            "city": city,
            "address": (
                f"{self._parties.generate_street(self.country)} "
                f"{self._parties.generate_house_number()}, {postal_code} {city}"
            ),
        }

    def generate(self, index: int, *, error: ScenarioError = "none") -> InvoiceRecord:
        """Generate a record and preserve correct values before any explicit error injection."""
        if isinstance(index, bool) or not isinstance(index, int) or index < 1:
            raise ValueError("index must be a positive integer")
        if error not in ERRORS:
            raise ValueError("Unknown scenario error")
        supplier = self._party()
        record = self._invoices.generate_invoice(index, cast(dict[str, Any], supplier))
        record["beneficiary"] = self._party()
        invoice_date = self.base_date + timedelta(days=index - 1)
        record["invoice_date"] = invoice_date.isoformat()
        record["supply_date"] = (invoice_date - timedelta(days=1)).isoformat()
        record["due_date"] = (invoice_date + timedelta(days=30)).isoformat()
        correct = {
            "amounts.total": record["amounts"]["total"],
            "supplier.vat_id": record["supplier"]["vat_id"],
            "invoice_date": record["invoice_date"],
        }
        if error == "wrong_total":
            record["amounts"]["total"] = round(record["amounts"]["total"] + 1.0, 2)
        elif error == "missing_vat_id":
            record["supplier"]["vat_id"] = ""
        elif error == "date_before_reference":
            record["invoice_date"] = (self.base_date - timedelta(days=1)).isoformat()
        record["metadata"].update(
            {
                "profile": "synthetic-scenario-v1",
                "synthetic": True,
                "base_date": self.base_date.isoformat(),
                "seed": self.seed,
                "problem_type": None if error == "none" else error,
                "is_problematic": error != "none",
                "injected_errors": [] if error == "none" else [error],
                "correct_values": correct,
            }
        )
        return record

    def generate_batch(
        self, total: int, *, errors: dict[int, ScenarioError] | None = None
    ) -> list[InvoiceRecord]:
        """Generate ordered records; error positions are explicit one-based indexes."""
        if isinstance(total, bool) or not isinstance(total, int) or total < 0:
            raise ValueError("total must be a nonnegative integer")
        selected = dict(errors or {})
        if any(
            isinstance(index, bool) or not isinstance(index, int) or index < 1 or index > total
            for index in selected
        ):
            raise ValueError("Error index is outside the batch")
        if any(error not in ERRORS for error in selected.values()):
            raise ValueError("Unknown scenario error")
        return [
            self.generate(index, error=selected.get(index, "none")) for index in range(1, total + 1)
        ]


def duplicate_invoice(invoice: InvoiceRecord, *, new_id: str) -> InvoiceRecord:
    """Copy the same invoice identity into an independent record for duplicate-detection tests."""
    result = deepcopy(invoice)
    result["id"] = new_id
    result["metadata"].update(
        {
            "synthetic": True,
            "problem_type": "duplicate",
            "is_problematic": True,
            "injected_errors": ["duplicate"],
            "duplicate_of": invoice["id"],
        }
    )
    return result


def to_json(invoices: list[InvoiceRecord]) -> str:
    """Render valid UTF-8-ready JSON data without files, PDF dependencies or input mutation."""
    return json.dumps(invoices, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
