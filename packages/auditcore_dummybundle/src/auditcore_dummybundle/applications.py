"""Payment applications to the Commission, aggregated from the paid claims.

Art. 91(1) of Regulation (EU) 2021/1060 allows at most six applications per
accounting year, one per period ending 31 October, 30 November, 31 December,
28 February, 31 May and 31 July; the last one is the final application for the
accounting year ended 30 June. Amounts are shown per period and cumulatively
for the accounting year; withdrawals reduce the application they are booked in.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from auditcore_dummybundle.amounts import ZERO, share
from auditcore_dummybundle.chain import PROGRAMME_CODE, priority_label
from auditcore_dummybundle.config import BundleConfig, accounting_year
from auditcore_dummybundle.model import Row, amount, day, number

TOTAL_LABEL = "Endsumme"
WITHDRAWAL = "Herausnahme"
#: Which of the six legal periods are used for 1 … 6 applications per year.
_SLOTS = {1: (6,), 2: (3, 6), 3: (1, 4, 6), 4: (1, 3, 4, 6), 5: (1, 3, 4, 5, 6)}


def _period_end(slot: int, start_year: int) -> date:
    ends = {
        1: date(start_year, 10, 31),
        2: date(start_year, 11, 30),
        3: date(start_year, 12, 31),
        4: date(start_year + 1, 2, 28),
        5: date(start_year + 1, 5, 31),
        6: date(start_year + 1, 7, 31),
    }
    return ends[slot]


def build_schedule(config: BundleConfig) -> list[Row]:
    """One row per payment application: number, submission and cut-off date."""
    year_start, year_end = accounting_year(config.base_date)
    slots = _SLOTS.get(config.payment_applications, (1, 2, 3, 4, 5, 6))
    schedule: list[Row] = []
    for index, slot in enumerate(slots, start=1):
        submission = _period_end(slot, year_start.year)
        schedule.append(
            {
                "number": index,
                "application_no": f"ZA-{year_end.year}-{index:02d}",
                "submission_date": submission,
                "cutoff_date": min(submission, year_end),
                "final": slot == 6,
                "accounting_year_from": year_start,
                "accounting_year_to": year_end,
                "fund": config.fund,
                "programme": f"Synthetisches Programm {config.fund}",
                "cci": PROGRAMME_CODE,
            }
        )
    return schedule


def assign_claims(schedule: list[Row], claims: list[Row]) -> None:
    """Book every claim into the first application whose cut-off covers its payment."""
    for claim in claims:
        paid = day(claim, "payment_date")
        target = next((a for a in schedule if day(a, "cutoff_date") >= paid), schedule[-1])
        claim["application_no"] = target["application_no"]
        claim["application_number"] = target["number"]
        claim["application_submission_date"] = target["submission_date"]


def period_claims(claims: list[Row], application_number: int, priority: str, key: str) -> Decimal:
    """Sum of ``key`` over the claims of one priority booked in one application."""
    return sum(
        (
            amount(claim, key)
            for claim in claims
            if claim["application_number"] == application_number and claim["priority"] == priority
        ),
        ZERO,
    )


def _withdrawn(corrections: list[Row], application_number: int, priority: str, key: str) -> Decimal:
    return sum(
        (
            amount(item, key)
            for item in corrections
            if item["kind"] == WITHDRAWAL
            and item["application_number"] == application_number
            and item["priority"] == priority
        ),
        ZERO,
    )


def _total_row(head: Row, rows: list[Row], keys: tuple[str, ...]) -> Row:
    total: Row = dict(head)
    total.update({"row_kind": "total", "priority": TOTAL_LABEL, "basis": None})
    total.update({"union_contribution": None, "technical_assistance": None})
    for key in keys:
        total[key] = sum((amount(row, key) for row in rows), ZERO)
    return total


_SUMMED = (
    "claims_period",
    "withdrawn_period",
    "eligible_period",
    "public_period",
    "eligible_cumulative",
    "public_cumulative",
    "rounding_difference",
)


def build_applications(
    config: BundleConfig, schedule: list[Row], claims: list[Row], corrections: list[Row]
) -> list[Row]:
    """Rows per application and priority plus an ``Endsumme`` row per application."""
    rows: list[Row] = []
    running: dict[str, tuple[Decimal, Decimal]] = {}
    for head in schedule:
        block: list[Row] = []
        for index in range(1, config.priorities + 1):
            priority = priority_label(index)
            ref = number(head, "number")
            claimed = period_claims(claims, ref, priority, "eligible")
            withdrawn = _withdrawn(corrections, ref, priority, "amount")
            public = period_claims(claims, ref, priority, "public") - _withdrawn(
                corrections, ref, priority, "public_amount"
            )
            before = running.get(priority, (ZERO, ZERO))
            eligible_total = before[0] + claimed - withdrawn
            public_total = before[1] + public
            running[priority] = (eligible_total, public_total)
            row: Row = dict(head)
            row.update(
                {
                    "row_kind": "priority",
                    "priority": priority,
                    "basis": "insgesamt",
                    "claims_period": claimed,
                    "withdrawn_period": withdrawn,
                    "eligible_period": claimed - withdrawn,
                    "public_period": public,
                    "eligible_cumulative": eligible_total,
                    "union_contribution": None,
                    "technical_assistance": None,
                    "public_cumulative": public_total,
                    "rounding_difference": public_total
                    - share(eligible_total, config.public_share),
                }
            )
            block.append(row)
        rows.extend(block)
        rows.append(_total_row(head, block, _SUMMED))
    return rows
