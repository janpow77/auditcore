"""Receipts of a payment claim: amounts bound to the claim, dates and evidence.

The project-related amounts of the receipts add up to the requested amount of
their claim, to the cent. Net, VAT, gross, cash discount and paid amount are
derived backwards from the project-related amount.

Suppliers come from the country of the operation. A cross-border supply
between businesses would carry no domestic VAT of the supplier (reverse
charge or tax-free intra-Community supply), so the bundle keeps every invoice
domestic: the VAT rate and the award procedure follow one country. Award
procedures of Austrian contracting authorities use the procedure names of the
Bundesvergabegesetz 2018 (§ 31 Abs. 2, 3 and 11, free choice by § 33).
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
_DIRECT_AWARD = {"DE": "Direktauftrag", "AT": "Direktvergabe (BVergG 2018)"}
_PROCEDURES = {
    "DE": ("VOL unterhalb Schwellenwert", "VOB unterhalb Schwellenwert"),
    "AT": (
        "Offenes Verfahren (BVergG 2018)",
        "Nicht offenes Verfahren mit vorheriger Bekanntmachung (BVergG 2018)",
    ),
}
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
        # Alternating countries: a mixed bundle always has suppliers of both.
        country = cat.COUNTRIES[index % 2] if config.country == "DE+AT" else config.country
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


def direct_award_label(country: str) -> str:
    """Name of the direct award in the country of the contracting authority."""
    return _DIRECT_AWARD[country]


def _money(
    config: BundleConfig, rng: Random, claimed: Decimal, country: str | None, net_basis: bool
) -> Row:
    """Net, VAT, gross, discount and paid amount for a project-related amount.

    ``country`` is the supplier's country, ``None`` for staff costs (no VAT, no
    cash discount); ``net_basis`` says whether the claim basis is net (staff
    costs or VAT deduction). ``discount_amount`` is the cash discount on the
    claim basis, ``discount_gross`` the one on the invoice: gross minus
    ``discount_gross`` is the paid amount, to the cent.
    """
    staff = country is None
    rate = ZERO if country is None else cat.catalogs().vat_rates[country]
    discounted = not staff and rng.randrange(100) < int(config.discount_share * 100)
    discount_rate = Decimal(rng.randrange(2, 6)) / 100 if discounted else ZERO
    basis = quantize(claimed / (1 - discount_rate))
    if net_basis:
        net = basis
        vat = share(net, rate)
        gross = net + vat
        discount_gross = share(gross, discount_rate)
    else:
        gross = basis
        net = quantize(gross / (1 + rate))
        vat = gross - net
        discount_gross = basis - claimed
    return {
        "vat_rate": rate,
        "net": net,
        "vat": vat,
        "gross": gross,
        "discount_rate": discount_rate,
        "claim_basis": basis,
        "discount_amount": basis - claimed,
        "discount_gross": discount_gross,
        "paid": gross - discount_gross,
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
    """Award procedure by the law of the contracting authority's country."""
    country = str(operation["country"])
    direct = False
    if staff or not operation["contracting_authority"]:
        award_type = NOT_APPLICABLE
    elif net < config.direct_award_limit:
        award_type = direct_award_label(country)
        direct = True
    else:
        procedures = _PROCEDURES[country]
        award_type = procedures[rng.randrange(len(procedures))]
    return {
        "award_type": award_type,
        "direct_award": direct,
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
    """Invoicing party: the beneficiary for staff costs, else a domestic supplier."""
    if staff:
        return {
            "supplier_name": operation["beneficiary_name"],
            "supplier_vat_id": operation["beneficiary_vat_id"],
            "supplier_country": operation["country"],
        }
    domestic = tuple(s for s in suppliers if s.country == operation["country"])
    supplier = domestic[rng.randrange(len(domestic))]
    return {
        "supplier_name": supplier.name,
        "supplier_vat_id": supplier.vat_id,
        "supplier_country": supplier.country,
    }


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
    country = None if category.staff else str(row["supplier_country"])
    net_basis = category.staff or bool(operation["vat_deduction"])
    row.update(_money(config, rng, claimed, country, net_basis))
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
