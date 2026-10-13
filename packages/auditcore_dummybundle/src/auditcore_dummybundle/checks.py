"""The eight sum checks every bundle without planted anomalies passes to the cent."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

from auditcore_dummybundle.amounts import ZERO, share
from auditcore_dummybundle.applications import WITHDRAWAL
from auditcore_dummybundle.bundle import Bundle
from auditcore_dummybundle.corrections import DEDUCTION
from auditcore_dummybundle.model import Row, amount, number

#: Number and German title of every check.
CHECK_TITLES = {
    1: "Summe der projektbezogenen Beträge der Belege = Anforderung des Mittelabrufs",
    2: "anerkannt = projektbezogener Betrag − Kürzung; Differenz = anerkannt − förderfähig",
    3: "Summe der förderfähigen Beträge der Mittelabrufe ≤ bewilligte förderfähige Ausgaben",
    4: "Zahlungsantrag je Priorität = Summe der Mittelabrufe bis zum Stichtag abzüglich "
    "Herausnahmen; kumulativ nicht fallend",
    5: "Summe der Grundgesamtheit = Spalte (B) des abschließenden Zahlungsantrags",
    6: "Anlage 4: (E) = (A) − (C) = Summe der Abzüge; Anlage 1 (A) = Anlage 4 (C)",
    7: "Anlage 2 (A) = Summe der Herausnahmen, Aufteilung nach Geschäftsjahr geht auf",
    8: "öffentlicher Beitrag = förderfähiger Betrag × öffentlicher Anteil je Mittelabruf; "
    "Rundungsrest der Summenzeilen ausgewiesen",
}


@dataclass(frozen=True)
class CheckOutcome:
    """Result of one sum check; ``failures`` name the rows that break it."""

    number: int
    title: str
    failures: tuple[str, ...]

    @property
    def passed(self) -> bool:
        """True when no row breaks the check."""
        return not self.failures


def _sum(rows: list[Row], key: str) -> Decimal:
    return sum((amount(row, key) for row in rows), ZERO)


def _priority_rows(rows: list[Row]) -> list[Row]:
    return [row for row in rows if row["row_kind"] == "priority"]


def _check1(bundle: Bundle) -> list[str]:
    receipts = bundle.table("receipts")
    return [
        str(claim["claim_id"])
        for claim in bundle.table("claims")
        if _sum([r for r in receipts if r["claim_id"] == claim["claim_id"]], "project_related")
        != amount(claim, "requested")
    ]


def _check2(bundle: Bundle) -> list[str]:
    return [
        f"{row['claim_id']}/{row['receipt_no']}"
        for row in bundle.table("receipts")
        if amount(row, "recognised") != amount(row, "project_related") - amount(row, "reduction")
    ]


def _check3(bundle: Bundle) -> list[str]:
    claims = bundle.table("claims")
    return [
        str(op["operation_id"])
        for op in bundle.table("operations")
        if _sum([c for c in claims if c["operation_id"] == op["operation_id"]], "eligible")
        > amount(op, "eligible_approved")
    ]


def _upto(rows: list[Row], priority: str, ref: int) -> list[Row]:
    return [
        row
        for row in rows
        if row["priority"] == priority and 0 < number(row, "application_number") <= ref
    ]


def _check4(bundle: Bundle) -> list[str]:
    claims = bundle.table("claims")
    withdrawals = [c for c in bundle.table("corrections") if c["kind"] == WITHDRAWAL]
    failures: list[str] = []
    previous: dict[str, Decimal] = {}
    for row in _priority_rows(bundle.table("payment_applications")):
        ref, priority = number(row, "number"), str(row["priority"])
        expected = _sum(_upto(claims, priority, ref), "eligible") - _sum(
            _upto(withdrawals, priority, ref), "amount"
        )
        cumulative = amount(row, "eligible_cumulative")
        if cumulative != expected or cumulative < previous.get(priority, ZERO):
            failures.append(f"{row['application_no']}/{priority}")
        previous[priority] = cumulative
    return failures


def _final_total(bundle: Bundle, key: str) -> Decimal:
    rows = bundle.table("payment_applications")
    return _sum([r for r in rows if r["final"] and r["row_kind"] == "priority"], key)


def _check5(bundle: Bundle) -> list[str]:
    population = _sum(bundle.table("population"), "certified")
    final = _final_total(bundle, "eligible_cumulative")
    return [] if population == final else [f"{population} ≠ {final}"]


def _check6(bundle: Bundle) -> list[str]:
    deductions = [c for c in bundle.table("corrections") if c["kind"] == DEDUCTION]
    annex1 = {row["priority"]: row for row in bundle.table("accounts_annex1")}
    failures: list[str] = []
    for row in _priority_rows(bundle.table("accounts_annex4")):
        priority = row["priority"]
        deducted = _sum([d for d in deductions if d["priority"] == priority], "amount")
        difference = amount(row, "declared") - amount(row, "accounts")
        consistent = amount(row, "difference") == difference == deducted
        if not consistent or amount(annex1[priority], "eligible") != amount(row, "accounts"):
            failures.append(str(priority))
    return failures


def _check7(bundle: Bundle) -> list[str]:
    withdrawals = [c for c in bundle.table("corrections") if c["kind"] == WITHDRAWAL]
    annex2 = bundle.table("accounts_annex2")
    failures = [
        str(row["priority"])
        for row in _priority_rows(annex2)
        if amount(row, "withdrawn")
        != _sum([w for w in withdrawals if w["priority"] == row["priority"]], "amount")
    ]
    total = _sum(withdrawals, "amount")
    by_year = _sum([row for row in annex2 if row["row_kind"] == "year"], "withdrawn")
    if by_year != total or _sum(_priority_rows(annex2), "withdrawn") != total:
        failures.append("Aufteilung nach Geschäftsjahr")
    return failures


def _check8(bundle: Bundle) -> list[str]:
    rate = bundle.config.public_share
    failures = [
        str(claim["claim_id"])
        for claim in bundle.table("claims")
        if amount(claim, "public") != share(amount(claim, "eligible"), rate)
    ]
    for row in _priority_rows(bundle.table("payment_applications")):
        rest = amount(row, "public_cumulative") - share(amount(row, "eligible_cumulative"), rate)
        if amount(row, "rounding_difference") != rest:
            failures.append(f"{row['application_no']}/{row['priority']}")
    return failures


_CHECKS: tuple[Callable[[Bundle], list[str]], ...] = (
    _check1,
    _check2,
    _check3,
    _check4,
    _check5,
    _check6,
    _check7,
    _check8,
)


def run_checks(bundle: Bundle) -> tuple[CheckOutcome, ...]:
    """Evaluate the eight sum checks on the canonical tables of ``bundle``."""
    return tuple(
        CheckOutcome(number, CHECK_TITLES[number], tuple(check(bundle)))
        for number, check in enumerate(_CHECKS, start=1)
    )
