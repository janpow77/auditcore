"""Operations and their payment claims: the upper half of the bundle chain.

Every entity draws from its own random stream (see :mod:`seeds`), so the
receipts of one claim never shift the values of another. Amounts flow top
down: the approved amount limits the claims, a claim's requested amount is
allocated to its receipts (:mod:`receipts`).
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from random import Random

from auditcore_dummybundle import catalogs as cat
from auditcore_dummybundle import identifiers
from auditcore_dummybundle.amounts import CENT, ZERO, quantize, share, split_random
from auditcore_dummybundle.config import BundleConfig, accounting_year
from auditcore_dummybundle.model import Row, amount, day
from auditcore_dummybundle.seeds import derive_seed, pick_cents, stream

#: Smallest project-related amount of one receipt.
MIN_RECEIPT = Decimal("10.00")
PROGRAMME_CODE = "2021XX16SYPR001"
#: Claims are filed early enough to be paid out within the accounting year.
CLAIM_LEAD_DAYS = 75


def priority_label(index: int) -> str:
    """Neutral priority name, 1-based."""
    return f"Priorität {index}"


def _party(config: BundleConfig, rng: Random, index: int) -> Row:
    country = cat.country_of(rng, config.country)
    street, postal_code, city = cat.address(rng, country)
    site_street, site_postal, site_city = (
        cat.address(rng, country) if rng.randrange(4) == 0 else (street, postal_code, city)
    )
    public_entity = rng.randrange(4) == 0
    name = cat.company_name(
        derive_seed(config.seed, "company"), index, "public" if public_entity else "private"
    )
    return {
        "beneficiary_id": f"BEN-{index:05d}",
        "beneficiary_name": name,
        "beneficiary_vat_id": identifiers.vat_id(rng, country, valid=config.identifiers_valid),
        "beneficiary_iban": identifiers.iban(rng, country, valid=config.identifiers_valid),
        "beneficiary_bic": identifiers.bic(country),
        "beneficiary_street": street,
        "beneficiary_postal_code": postal_code,
        "beneficiary_city": city,
        "beneficiary_address": f"{street}, {postal_code} {city}",
        "site_address": f"{site_postal} {site_city} / {site_street}",
        "site_city": site_city,
        "country": country,
        "country_name": cat.catalogs().country_names[country],
        "nuts3": cat.catalogs().nuts3[site_city],
        "entity_form": "öffentlich-rechtlich" if public_entity else "privatrechtlich",
        "contracting_authority": public_entity or rng.randrange(10) == 0,
    }


def _later_year(value: date, years: int) -> date:
    return date(value.year + years, value.month, min(value.day, 28))


def _dates(rng: Random, year_start: date, year_end: date) -> Row:
    approval = year_start - timedelta(days=rng.randrange(30, 540))
    period_end = year_end + timedelta(days=rng.randrange(30, 720))
    return {
        "application_date": approval - timedelta(days=rng.randrange(30, 180)),
        "approval_date": approval,
        "period_start": approval + timedelta(days=rng.randrange(0, 15)),
        "period_end": period_end,
        "earmark_until": _later_year(period_end, 5),
    }


def _finance(config: BundleConfig, rng: Random) -> Row:
    hundreds = pick_cents(rng, 5_000_000, 200_000_000, skew=2) // 10_000
    approved = (Decimal(hundreds) * 100).quantize(CENT)
    public = share(approved, config.public_share)
    eu_funds = share(approved, config.eu_rate)
    return {
        "eligible_approved": approved,
        "public_funds": public,
        "eu_funds": eu_funds,
        "national_public": public - eu_funds,
        "national_private": approved - public,
        "funding_rate": config.public_share,
        "eu_rate": config.eu_rate,
    }


def _programme(config: BundleConfig, rng: Random, index: int) -> Row:
    data = cat.catalogs()
    priority = (index - 1) % config.priorities + 1
    group_code, group_name = data.programme_groups[rng.randrange(len(data.programme_groups))]
    plan_size = rng.randrange(3, len(data.cost_categories))
    plan = sorted(rng.sample(range(len(data.cost_categories)), plan_size))
    vat = {"yes": True, "no": False}.get(config.vat_deduction, rng.randrange(10) < 6)
    title = data.operation_titles[rng.randrange(len(data.operation_titles))]
    return {
        "programme": f"Synthetisches Programm {config.fund}",
        "cci": PROGRAMME_CODE,
        "fund": config.fund,
        "programme_group": group_code,
        "programme_group_name": group_name,
        "title": title,
        "summary": f"{title} – synthetische Kurzbeschreibung ohne realen Bezug.",
        "priority": priority_label(priority),
        "specific_objective": f"Spezifisches Ziel {priority}.1 (Platzhalter)",
        "policy_objective": f"Politisches Ziel {(priority - 1) % 5 + 1}",
        "strategic": rng.randrange(20) == 0,
        "vat_deduction": vat,
        "cost_plan": "; ".join(data.cost_categories[i].name for i in plan),
        "intervention_field": f"{rng.randrange(1, 183):03d}",
    }


def build_operation(config: BundleConfig, index: int) -> Row:
    """One operation (root of the chain) with party, dates, programme and finance."""
    rng = stream(config.seed, "operation", index)
    year_start, year_end = accounting_year(config.base_date)
    row: Row = {"operation_id": f"SYN-{year_start.year}-{index:04d}", "seq": index}
    row.update(_party(config, rng, index))
    row.update(_dates(rng, year_start, year_end))
    row.update(_programme(config, rng, index))
    row.update(_finance(config, rng))
    return row


def _signatory(config: BundleConfig, rng: Random, country: str) -> str:
    if config.person_names == "catalog":
        return cat.person_name(rng, country)
    return cat.role_name(rng)


def _claim_dates(rng: Random, window_start: date, slot_days: int, slot: int) -> Row:
    application = window_start + timedelta(days=slot * slot_days + rng.randrange(slot_days))
    receipt = application + timedelta(days=rng.randrange(0, 4))
    payment = receipt + timedelta(days=rng.randrange(5, 61))
    return {
        "application_date": application,
        "receipt_date": receipt,
        "payment_date": payment,
        "processing_days": (payment - receipt).days,
    }


def build_claims(config: BundleConfig, operation: Row) -> list[Row]:
    """Payment claims of one operation; their requested amounts stay below the approval."""
    operation_id = str(operation["operation_id"])
    rng = stream(config.seed, "claims", operation_id)
    year_start, year_end = accounting_year(config.base_date)
    count = rng.randrange(config.claims_min, config.claims_max + 1)
    claimed = quantize(amount(operation, "eligible_approved") * rng.randrange(35, 96) / 100)
    minimum = MIN_RECEIPT * config.receipts_max
    parts = split_random(claimed, count, rng, spread=Decimal("0.2"), minimum=minimum)
    window_start = year_start + timedelta(days=10)
    slot_days = ((year_end - timedelta(days=CLAIM_LEAD_DAYS)) - window_start).days // count
    claims: list[Row] = []
    for index, requested in enumerate(parts, start=1):
        claim: Row = {
            "claim_id": f"MA-{operation_id}-{index:02d}",
            "operation_id": operation_id,
            "seq": index,
            "list_version": index,
            "priority": operation["priority"],
            "requested": requested,
            "status": cat.catalogs().placeholders["claim_status"],
            "final_statement": index == count,
            "signatory": _signatory(config, rng, str(operation["country"])),
        }
        claim.update(_claim_dates(rng, window_start, slot_days, index - 1))
        claims.append(claim)
    return claims


def settle_claim(config: BundleConfig, claim: Row, receipts: list[Row]) -> None:
    """Derive reductions, eligible amount and public shares from the claim's receipts."""
    reductions = sum((amount(receipt, "reduction") for receipt in receipts), ZERO)
    eligible = amount(claim, "requested") - reductions
    claim["receipt_count"] = len(receipts)
    claim["reductions"] = reductions
    claim["eligible"] = eligible
    claim["public"] = share(eligible, config.public_share)
    claim["eu"] = share(eligible, config.eu_rate)
    claim["latest_invoice_date"] = max(day(receipt, "invoice_date") for receipt in receipts)
