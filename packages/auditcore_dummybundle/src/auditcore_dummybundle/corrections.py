"""Corrections after the declaration to the Commission, and their findings.

Two booking routes link payment applications and accounts: a *withdrawal*
(``Herausnahme``) is a negative amount in a later payment application of the
accounting year and feeds Appendix 2 of the accounts; a *direct deduction*
(``unmittelbarer Abzug``) is made in the accounts only and explains the
difference in Appendix 4. A withdrawal is only booked where the application
stays non-negative for the period; otherwise it becomes a direct deduction.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from random import Random

from auditcore_dummybundle import catalogs as cat
from auditcore_dummybundle.amounts import CENT, ZERO, share
from auditcore_dummybundle.applications import WITHDRAWAL, period_claims
from auditcore_dummybundle.config import BundleConfig, accounting_year
from auditcore_dummybundle.model import Row, amount, day, number
from auditcore_dummybundle.seeds import pick_cents, stream

DEDUCTION = "unmittelbarer Abzug"
AUDIT_TRIGGER = "Prüfung der Prüfbehörde"
_TRIGGERS = ("Verwaltungsüberprüfung", "Vor-Ort-Überprüfung", AUDIT_TRIGGER)
_PERCENT = (25, 50, 100)
#: Union share from which an irregularity is reportable (EUR, Annex XII section 1.2 CPR).
REPORTING_THRESHOLD = Decimal("10000.00")


class _Ledger:
    """Free amount per application and priority that withdrawals may still use."""

    def __init__(self, schedule: list[Row], claims: list[Row]) -> None:
        self._schedule = schedule
        self._claims = claims
        self._used: dict[tuple[int, str], Decimal] = {}

    def place(
        self, priority: str, value: Decimal, after: int, not_before: date | None
    ) -> Row | None:
        """First application after number ``after`` that can carry ``value``."""
        for head in self._schedule:
            ref = number(head, "number")
            too_early = not_before is not None and day(head, "submission_date") < not_before
            if ref <= after or too_early:
                continue
            used = self._used.get((ref, priority), ZERO)
            if period_claims(self._claims, ref, priority, "eligible") - used >= value:
                self._used[(ref, priority)] = used + value
                return head
        return None


def _base(config: BundleConfig, rng: Random, index: int, value: Decimal) -> Row:
    trigger = _TRIGGERS[rng.randrange(len(_TRIGGERS))]
    eu_amount = share(value, config.eu_rate)
    return {
        "correction_id": f"KOR-{index:03d}",
        "trigger": trigger,
        "audit_based": trigger == AUDIT_TRIGGER,
        "amount": value,
        "public_amount": share(value, config.public_share),
        "eu_amount": eu_amount,
        "reportable": eu_amount >= REPORTING_THRESHOLD,
    }


def _booking(row: Row, head: Row | None, year_end_year: int) -> None:
    """Fill kind, application and annex depending on whether a withdrawal was placed."""
    if head is None:
        final = bool(row["final_assessment"])
        row.update(
            {
                "kind": DEDUCTION,
                "application_no": None,
                "application_number": 0,
                "annex": "Anlage 4",
                "deduction_type": "Art. 98 Abs. 6 Buchst. a"
                if final
                else "Art. 98 Abs. 6 Buchst. b",
                "status": "endgültig" if final else "in Bewertung",
            }
        )
    else:
        row.update(
            {
                "kind": WITHDRAWAL,
                "application_no": head["application_no"],
                "application_number": head["number"],
                "annex": "Anlage 2",
                "deduction_type": None,
                "status": "endgültig",
            }
        )
    row.setdefault("declaration_year", year_end_year)


def _from_receipt(
    config: BundleConfig, rng: Random, index: int, receipt: Row, claim: Row, ledger: _Ledger
) -> Row:
    percent = _PERCENT[rng.randrange(len(_PERCENT))]
    value = max(CENT, share(amount(receipt, "recognised"), Decimal(percent) / 100))
    row = _base(config, rng, index, value)
    detection = day(claim, "payment_date") + timedelta(days=rng.randrange(10, 200))
    row.update(
        {
            "operation_id": claim["operation_id"],
            "claim_id": claim["claim_id"],
            "receipt_no": receipt["receipt_no"],
            "priority": claim["priority"],
            "detection_date": detection,
            "final_date": detection + timedelta(days=rng.randrange(30, 91)),
            "final_assessment": rng.randrange(3) > 0,
        }
    )
    head = None
    if index % 2 == 1:
        head = ledger.place(
            str(claim["priority"]), value, number(claim, "application_number"), detection
        )
    _booking(row, head, accounting_year(config.base_date)[1].year)
    return row


def _prior_year(
    config: BundleConfig, rng: Random, index: int, operation: Row, ledger: _Ledger
) -> Row | None:
    value = Decimal(pick_cents(rng, 50_000, 2_000_000)) / 100
    head = ledger.place(str(operation["priority"]), value, 0, None)
    if head is None:
        return None
    row = _base(config, rng, index, value)
    detection = day(head, "submission_date") - timedelta(days=rng.randrange(20, 60))
    year_end = accounting_year(config.base_date)[1]
    row.update(
        {
            "operation_id": operation["operation_id"],
            "claim_id": None,
            "receipt_no": None,
            "priority": operation["priority"],
            "detection_date": detection,
            "final_date": detection + timedelta(days=rng.randrange(10, 20)),
            "final_assessment": True,
            "declaration_year": year_end.year - 1,
        }
    )
    _booking(row, head, year_end.year)
    return row


def build_corrections(
    config: BundleConfig,
    operations: list[Row],
    claims: list[Row],
    receipts: list[Row],
    schedule: list[Row],
) -> list[Row]:
    """Corrections of the accounting year, each tied to a receipt or a prior-year operation."""
    rng = stream(config.seed, "corrections")
    ledger = _Ledger(schedule, claims)
    by_claim = {str(claim["claim_id"]): claim for claim in claims}
    candidates = [r for r in receipts if amount(r, "recognised") > ZERO]
    chosen = sorted(rng.sample(range(len(candidates)), min(config.corrections, len(candidates))))
    rows = [
        _from_receipt(
            config, rng, index, candidates[pos], by_claim[str(candidates[pos]["claim_id"])], ledger
        )
        for index, pos in enumerate(chosen, start=1)
    ]
    for _ in range(config.prior_year_withdrawals):
        operation = operations[rng.randrange(len(operations))]
        row = _prior_year(config, rng, len(rows) + 1, operation, ledger)
        if row is not None:
            rows.append(row)
    return rows


def build_findings(corrections: list[Row]) -> list[Row]:
    """One finding per correction, with neutral placeholder texts."""
    reason = cat.catalogs().placeholders["finding_reason"]
    findings: list[Row] = []
    for index, item in enumerate(corrections, start=1):
        subject = (
            f"Beleg {item['receipt_no']} des Mittelabrufs {item['claim_id']}"
            if item["claim_id"]
            else f"Ausgaben eines früheren Geschäftsjahres des Vorhabens {item['operation_id']}"
        )
        findings.append(
            {
                "finding_id": f"F-{index:03d}",
                "correction_id": item["correction_id"],
                "origin": item["trigger"],
                "operation_id": item["operation_id"],
                "claim_id": item["claim_id"],
                "receipt_no": item["receipt_no"],
                "facts": f"Synthetische Feststellung zu {subject}.",
                "amount": item["amount"],
                "eu_amount": item["eu_amount"],
                "finding_type": "finanziell",
                "reason": reason,
                "method": "konkret beziffert",
                "flat_rate": None,
                "legal_basis": None,
                "annex": item["annex"],
                "reportable": item["reportable"],
                "report_id": None,
            }
        )
    return findings
