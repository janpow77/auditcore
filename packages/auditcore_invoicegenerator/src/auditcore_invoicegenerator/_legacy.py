"""Characterized Flowinvoice demo rules, source commit fb2d18568d2eaf64574d131ceae51a936b9aac02.

Local authorized extraction; rights status UNKNOWN, see NOTICE and provenance.
Rates, parties and labels are a historical synthetic training profile, not legal findings.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from random import Random
from typing import Any

from auditcore_invoicegenerator._legacy_catalog import (
    DESTINATIONS,
    EVENTS,
    MODELS,
    PRODUCTS,
    SERVICE_TEMPLATES,
    WORK_PACKAGES,
)
from auditcore_invoicegenerator._legacy_catalog import PROBLEM_SUPPLIERS as PROBLEM_SUPPLIERS
from auditcore_invoicegenerator._legacy_catalog import SUPPLIERS as SUPPLIERS
from auditcore_invoicegenerator.models import Amounts

PROJECT_START = datetime(2025, 1, 1)

PROJECT_END = datetime(2027, 12, 31)

INVOICE_DATE_RANGE_START = datetime(2025, 1, 15)

INVOICE_DATE_RANGE_END = datetime(2026, 1, 30)


def generate_invoice_number(index: int, supplier: Mapping[str, str], *, rng: Random) -> str:
    """Generate a realistic invoice number."""
    prefix_map = {
        "GB": ["INV", "SI", "IV"],
        "DE": ["RE", "RG", "INV"],
        "FR": ["FA", "FC", "INV"],
        "NL": ["F", "INV", "FN"],
        "BE": ["F", "INV", "FB"],
        "SE": ["F", "INV", "FS"],
        "IT": ["FT", "FA", "INV"],
        "ES": ["FA", "FC", "INV"],
        "AT": ["RE", "AR", "INV"],
        "PL": ["FV", "FA", "INV"],
    }

    prefixes = prefix_map.get(supplier["country"], ["INV"])
    prefix = rng.choice(prefixes)
    year = rng.choice(["2025", "2026"])
    number = str(index).zfill(4)

    return f"{prefix}-{year}-{number}"


def generate_invoice_date(
    temporal_problem: bool = False, *, rng: Random
) -> tuple[datetime, datetime]:
    """Generate invoice date and supply date."""
    if temporal_problem:
        # Before project start
        invoice_date = datetime(2024, 11, 15)
        supply_date = datetime(2024, 11, 1)
    else:
        # Within valid range
        days_range = (INVOICE_DATE_RANGE_END - INVOICE_DATE_RANGE_START).days
        invoice_date = INVOICE_DATE_RANGE_START + timedelta(days=rng.randint(0, days_range))
        supply_date = invoice_date - timedelta(days=rng.randint(1, 14))

    return invoice_date, supply_date


def generate_line_items(
    category: str, target_amount: float, *, rng: Random
) -> list[dict[str, Any]]:
    """Generate realistic line items for an invoice."""
    templates = SERVICE_TEMPLATES.get(category, SERVICE_TEMPLATES["consulting"])
    items = []
    remaining = target_amount

    while remaining > 100:
        template = rng.choice(templates)
        description_template, min_price, max_price = template

        # Generate description with placeholders filled
        description = description_template.format(
            product=rng.choice(PRODUCTS),
            model=rng.choice(MODELS),
            event=rng.choice(EVENTS),
            destination=rng.choice(DESTINATIONS),
            qty=rng.randint(2, 10),
            hours=rng.randint(10, 80),
            days=rng.randint(1, 5),
        )

        unit_price = round(rng.uniform(min_price, min(max_price, remaining)), 2)
        quantity = 1 if unit_price > 1000 else rng.randint(1, 5)
        amount = round(unit_price * quantity, 2)

        if amount > remaining * 1.2:
            amount = round(remaining * rng.uniform(0.3, 0.9), 2)
            quantity = 1
            unit_price = amount

        items.append(
            {
                "description": description,
                "quantity": quantity,
                "unit_price": unit_price,
                "amount": amount,
            }
        )

        remaining -= amount

        if len(items) >= 5 or remaining < 200:
            break

    return items


def get_vat_rate(country: str) -> float:
    """Get VAT rate by country."""
    vat_rates = {
        "GB": 0.20,
        "DE": 0.19,
        "FR": 0.20,
        "NL": 0.21,
        "BE": 0.21,
        "SE": 0.25,
        "IT": 0.22,
        "ES": 0.21,
        "AT": 0.20,
        "PL": 0.23,
        "IE": 0.23,
        "PT": 0.23,
        "DK": 0.25,
        "FI": 0.24,
        "CZ": 0.21,
        "GR": 0.24,
        "HU": 0.27,
        "RO": 0.19,
        "LU": 0.17,
        "CY": 0.19,
        "MT": 0.18,
        "SI": 0.22,
        "SK": 0.20,
        "EE": 0.22,
        "LV": 0.21,
        "LT": 0.21,
        "HR": 0.25,
        "BG": 0.20,
        "RU": 0.00,  # No VAT for Russian supplier
    }
    return vat_rates.get(country, 0.20)


def get_currency(country: str) -> str:
    """Get currency by country."""
    currencies = {
        "GB": "GBP",
        "SE": "SEK",
        "DK": "DKK",
        "PL": "PLN",
        "CZ": "CZK",
        "HU": "HUF",
        "RO": "RON",
        "BG": "BGN",
        "RU": "EUR",  # Use EUR for clarity
    }
    return currencies.get(country, "EUR")


def generate_invoice(
    index: int, supplier: Mapping[str, str], problem_type: str | None = None, *, rng: Random
) -> dict[str, Any]:
    """Generate a complete invoice record."""

    # Determine dates
    temporal_problem = problem_type == "temporal"
    invoice_date, supply_date = generate_invoice_date(temporal_problem, rng=rng)

    # Determine work package
    wp_key = rng.choice(list(WORK_PACKAGES.keys()))
    work_package = WORK_PACKAGES[wp_key]

    # Override category for subject relevance problem
    category = supplier.get("category", "consulting")
    if problem_type == "subject_relevance":
        category = "catering"

    # Generate amounts (the random base amount is drawn even when a problem fixes it)
    base_amount = _problem_base_amount(problem_type, round(rng.uniform(500, 25000), 2))

    vat_rate = get_vat_rate(supplier["country"])
    if problem_type == "sanctions":
        vat_rate = 0.0  # Russian supplier, no VAT

    line_items = generate_line_items(category, base_amount, rng=rng)
    amounts = _amounts(line_items, vat_rate, get_currency(supplier["country"]))

    # Generate invoice number
    invoice_number = generate_invoice_number(index, supplier, rng=rng)

    # Build invoice record
    return {
        "id": f"DOC-{str(index).zfill(5)}",
        "invoice_number": invoice_number,
        "invoice_date": invoice_date.strftime("%Y-%m-%d"),
        "supply_date": supply_date.strftime("%Y-%m-%d"),
        "due_date": (invoice_date + timedelta(days=30)).strftime("%Y-%m-%d"),
        "supplier": _supplier_party(supplier, rng=rng),
        "beneficiary": dict(BENEFICIARY),
        "line_items": line_items,
        "amounts": amounts,
        "project": {
            "work_package": wp_key,
            "work_package_name": work_package["name"],
            "category": category,
        },
        "metadata": {
            "problem_type": problem_type,
            "is_problematic": problem_type is not None,
        },
    }


def _amounts(line_items: list[dict[str, Any]], vat_rate: float, currency: str) -> Amounts:
    """Totals with the source's float sum and rounding (subtotal is not rounded)."""
    subtotal = sum(item["amount"] for item in line_items)
    vat_amount = round(subtotal * vat_rate, 2)
    total = round(subtotal + vat_amount, 2)
    return {
        "subtotal": subtotal,
        "vat_rate": vat_rate,
        "vat_amount": vat_amount,
        "total": total,
        "currency": currency,
    }


#: Fixed synthetic beneficiary of every legacy-profile invoice.
BENEFICIARY = {
    "name": "European Green Technology Institute",
    "vat_id": "BE0123456789",
    "country": "BE",
    "city": "Brussels",
    "address": "42 Innovation Boulevard, 1000 Brussels",
}


#: Fixed net base amount of each error scenario, in the source's comparison order.
_PROBLEM_BASE_AMOUNTS = {
    "sanctions": 6450.00,
    "ted_concentration": 24000.00,
    "duplicate": 9840.00,
    "invalid_vat": 1320.00,
    "subject_relevance": 3600.00,
    "temporal": 15625.00,
}


def _problem_base_amount(problem_type: str | None, drawn: float) -> float:
    """Fixed base of the error scenario (compared with ``==``); otherwise the drawn amount."""
    for name, amount in _PROBLEM_BASE_AMOUNTS.items():
        if problem_type == name:
            return amount
    return drawn


def _supplier_party(supplier: Mapping[str, str], *, rng: Random) -> dict[str, str]:
    """Supplier block; the fallback street number is drawn even when an address exists."""
    return {
        "name": supplier["name"],
        "vat_id": supplier.get("vat_id", ""),
        "country": supplier["country"],
        "city": supplier.get("city", ""),
        "address": supplier.get(
            "address", f"{rng.randint(1, 200)} Business Street, {supplier.get('city', 'City')}"
        ),
    }
