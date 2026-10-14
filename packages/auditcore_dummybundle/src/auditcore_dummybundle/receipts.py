"""Receipts of a payment claim: amounts bound to the claim, dates and evidence.

The project-related amounts of the receipts add up to the requested amount of
their claim, to the cent. Net, VAT, gross, cash discount and paid amount are
derived backwards from the project-related amount.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from random import Random

from auditcore_dummybundle import catalogs as cat
from auditcore_dummybundle import identifiers
from auditcore_dummybundle.amounts import ZERO, quantize, share, split_random
from auditcore_dummybundle.chain import MIN_RECEIPT
from auditcore_dummybundle.config import BundleConfig
from auditcore_dummybundle.model import Row, amount, day
from auditcore_dummybundle.seeds import derive_seed, stream

YES = "Ja"
NOT_APPLICABLE = "Entfällt"
DIRECT_AWARD = "Direktauftrag"
_BELOW_THRESHOLD = ("VOL unterhalb Schwellenwert", "VOB unterhalb Schwellenwert")
_REDUCTION_PERCENT = (10, 25, 50, 100)
#: Suppliers take name positions above every possible operation index, so a
#: supplier never carries the name of a beneficiary of the same bundle.
SUPPLIER_NAME_OFFSET = 10_000


@dataclass(frozen=True)
class Supplier:
    """Recurring invoicing party of a bundle."""

    name: str
    vat_id: str
    country: str


def build_suppliers(config: BundleConfig) -> tuple[Supplier, ...]:
    """Supplier pool of the bundle; receipts draw from it so that names recur."""
    suppliers = []
    for index in range(min(60, max(6, config.operations * 2))):
        rng = stream(config.seed, "supplier", index)
        country = cat.country_of(rng, config.country)
        suppliers.append(
            Supplier(
                cat.company_name(derive_seed(config.seed, "company"), SUPPLIER_NAME_OFFSET + index),
                identifiers.vat_id(rng, country, valid=config.identifiers_valid),
                country,
            )
        )
    return tuple(suppliers)


def _category(rng: Random, operation: Row) -> cat.CostCategory:
    plan = str(operation["cost_plan"]).split("; ")
    allowed = tuple(c for c in cat.catalogs().cost_categories if c.name in plan)
    name = cat.weighted_pick(rng, tuple((c.name, c.weight) for c in allowed))
    return next(c for c in allowed if c.name == name)


def _money(config: BundleConfig, rng: Random, operation: Row, claimed: Decimal, staff: bool) -> Row:
    """Net, VAT, gross, discount and paid amount for a project-related amount."""
    rate = ZERO if staff else cat.catalogs().vat_rates[str(operation["country"])]
    discounted = not staff and rng.randrange(100) < int(config.discount_share * 100)
    discount_rate = Decimal(rng.randrange(2, 6)) / 100 if discounted else ZERO
    basis = quantize(claimed / (1 - discount_rate))
    if staff or operation["vat_deduction"]:
        net = basis
        vat = share(net, rate)
        gross = net + vat
    else:
        gross = basis
        net = quantize(gross / (1 + rate))
        vat = gross - net
    return {
        "vat_rate": rate,
        "net": net,
        "vat": vat,
        "gross": gross,
        "discount_rate": discount_rate,
        "claim_basis": basis,
        "discount_amount": basis - claimed,
        "paid": gross - share(gross, discount_rate),
        "project_related": claimed,
    }


def _reduction(config: BundleConfig, rng: Random, claimed: Decimal) -> Row:
    reduced = rng.randrange(100) < int(config.reduction_share * 100)
    percent = _REDUCTION_PERCENT[rng.randrange(len(_REDUCTION_PERCENT))] if reduced else 0
    reduction = share(claimed, Decimal(percent) / 100)
    return {
        "reduction": reduction,
        "recognised": claimed - reduction,
        "reduction_reason": cat.catalogs().placeholders["reduction_reason"] if reduced else None,
    }


def _award(config: BundleConfig, rng: Random, operation: Row, net: Decimal, staff: bool) -> Row:
    if staff or not operation["contracting_authority"]:
        award_type = NOT_APPLICABLE
    elif net < config.direct_award_limit:
        award_type = DIRECT_AWARD
    else:
        award_type = _BELOW_THRESHOLD[rng.randrange(len(_BELOW_THRESHOLD))]
    return {
        "award_type": award_type,
        "direct_award": award_type == DIRECT_AWARD,
        "evidence_award": NOT_APPLICABLE if award_type == NOT_APPLICABLE else YES,
    }


def _evidence(staff: bool) -> Row:
    return {
        "evidence_receipt": YES,
        "evidence_payment": YES,
        "evidence_contract": YES,
        "evidence_publicity": YES,
        "evidence_timesheet": YES if staff else NOT_APPLICABLE,
        "evidence_copy": YES,
    }


def _party(rng: Random, operation: Row, suppliers: tuple[Supplier, ...], staff: bool) -> Row:
    if staff:
        return {
            "supplier_name": operation["beneficiary_name"],
            "supplier_vat_id": operation["beneficiary_vat_id"],
        }
    supplier = suppliers[rng.randrange(len(suppliers))]
    return {"supplier_name": supplier.name, "supplier_vat_id": supplier.vat_id}


def _dates(rng: Random, operation: Row, claim: Row) -> Row:
    application = day(claim, "application_date")
    earliest = max(day(operation, "period_start"), application - timedelta(days=90))
    invoice = earliest + timedelta(days=rng.randrange((application - earliest).days))
    payment = invoice + timedelta(days=rng.randrange(min(30, (application - invoice).days) + 1))
    return {"invoice_date": invoice, "payment_date": payment}


def _receipt(
    config: BundleConfig,
    operation: Row,
    claim: Row,
    suppliers: tuple[Supplier, ...],
    number: int,
    claimed: Decimal,
) -> Row:
    rng = stream(config.seed, "receipt", claim["claim_id"], number)
    category = _category(rng, operation)
    row: Row = {
        "receipt_no": number,
        "claim_id": claim["claim_id"],
        "operation_id": claim["operation_id"],
        "list_version": claim["list_version"],
        "cost_category": category.name,
        "staff_cost": category.staff,
        "purpose": cat.purpose_text(rng),
        "currency": "EUR",
        "used_purchase": not category.staff and rng.randrange(25) == 0,
        "source_file": (
            f"{operation['programme_group']}_{claim['operation_id']}_BL{claim['list_version']}.xlsx"
        ),
    }
    row.update(_dates(rng, operation, claim))
    row.update(_party(rng, operation, suppliers, category.staff))
    row.update(_money(config, rng, operation, claimed, category.staff))
    row.update(_reduction(config, rng, claimed))
    row.update(_award(config, rng, operation, amount(row, "net"), category.staff))
    row.update(_evidence(category.staff))
    prefix = "PK" if category.staff else "RE"
    row["invoice_no"] = f"{prefix}-{day(row, 'invoice_date').year}-{rng.randrange(10**6):06d}"
    return row


def build_receipts(
    config: BundleConfig, operation: Row, claim: Row, suppliers: tuple[Supplier, ...]
) -> list[Row]:
    """Receipts of one claim; their project-related amounts add up to its request."""
    rng = stream(config.seed, "receipts", claim["claim_id"])
    count = rng.randrange(config.receipts_min, config.receipts_max + 1)
    parts = split_random(
        amount(claim, "requested"), count, rng, spread=Decimal("0.5"), minimum=MIN_RECEIPT
    )
    return [
        _receipt(config, operation, claim, suppliers, number, claimed)
        for number, claimed in enumerate(parts, start=1)
    ]
