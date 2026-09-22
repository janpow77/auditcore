"""Public JSON-compatible records for synthetic invoice scenarios."""

from typing import Any, TypedDict


class LineItem(TypedDict):
    """A displayed synthetic invoice position using the selected profile's rounding."""

    description: str
    quantity: int
    unit_price: float
    amount: float


class Party(TypedDict):
    """Synthetic organization details; identifiers are not official registrations."""

    name: str
    vat_id: str
    country: str
    city: str
    address: str


class Amounts(TypedDict):
    """Displayed numeric totals; tax rates are training profile values."""

    subtotal: float
    vat_rate: float
    vat_amount: float
    total: float
    currency: str


class InvoiceRecord(TypedDict):
    """Complete legacy-compatible record, with scenario metadata when explicitly requested."""

    id: str
    invoice_number: str
    invoice_date: str
    supply_date: str
    due_date: str
    supplier: Party
    beneficiary: Party
    line_items: list[LineItem]
    amounts: Amounts
    project: dict[str, Any]
    metadata: dict[str, Any]
