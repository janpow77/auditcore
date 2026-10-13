"""Anomalies for practice, planted after the consistent bundle has been built.

Every planted anomaly is recorded as a :class:`~model.SolutionEntry`. The data
tables themselves carry no column that gives the result away; the solution is
a separate output and only produced on request. Aggregated tables (payment
applications, accounts) keep the values of the consistent bundle.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from random import Random

from auditcore_dummybundle import catalogs as cat
from auditcore_dummybundle.amounts import ZERO, quantize
from auditcore_dummybundle.bundle import Bundle
from auditcore_dummybundle.model import Cell, Row, SolutionEntry, amount, day
from auditcore_dummybundle.receipts import DIRECT_AWARD
from auditcore_dummybundle.seeds import stream

_AMOUNT_KEYS = ("net", "vat", "gross", "paid", "claim_basis", "project_related", "recognised")
#: Days within which the beneficiary must receive the payment (Art. 74(1)(b) CPR).
PAYMENT_DEADLINE_DAYS = 80


@dataclass(frozen=True)
class Planted:
    """What a planter changed: field, values, amount at issue and reason."""

    changed_field: str
    original: Cell
    planted: Cell
    expected_amount: Decimal
    reason: str
    row: Row | None = None


Planter = Callable[[Bundle, Row, Random], Planted | None]


@dataclass(frozen=True)
class AnomalyKind:
    """One anomaly: code, German title and description, target table, broken checks."""

    code: str
    title: str
    description: str
    table: str
    planter: Planter
    checks: tuple[int, ...] = ()


def _operation(bundle: Bundle, row: Row) -> Row:
    return next(
        op for op in bundle.table("operations") if op["operation_id"] == row["operation_id"]
    )


def _paid_before_invoice(_: Bundle, row: Row, rng: Random) -> Planted | None:
    original = row["payment_date"]
    row["payment_date"] = day(row, "invoice_date") - timedelta(days=rng.randrange(1, 31))
    return Planted(
        "payment_date",
        original,
        row["payment_date"],
        amount(row, "project_related"),
        "Das Bezahldatum liegt vor dem Rechnungsdatum.",
    )


def _eligible_above_paid(_: Bundle, row: Row, rng: Random) -> Planted | None:
    original = amount(row, "paid")
    factor = Decimal(rng.randrange(110, 151)) / 100
    row["paid"] = quantize(amount(row, "project_related") / factor)
    return Planted(
        "paid",
        original,
        row["paid"],
        amount(row, "project_related") - amount(row, "paid"),
        "Der projektbezogene Betrag übersteigt den tatsächlich gezahlten Betrag.",
    )


def _negative_amount(_: Bundle, row: Row, __: Random) -> Planted | None:
    if amount(row, "reduction") != ZERO:
        return None
    original = amount(row, "project_related")
    for key in _AMOUNT_KEYS:
        row[key] = -amount(row, key)
    return Planted(
        "project_related", original, -original, original, "Die Beträge des Belegs sind negativ."
    )


def _outside_period(bundle: Bundle, row: Row, rng: Random) -> Planted | None:
    original = row["invoice_date"]
    start = day(_operation(bundle, row), "period_start")
    row["invoice_date"] = start - timedelta(days=rng.randrange(1, 61))
    row["payment_date"] = day(row, "invoice_date") + timedelta(days=rng.randrange(0, 15))
    return Planted(
        "invoice_date",
        original,
        row["invoice_date"],
        amount(row, "project_related"),
        "Das Rechnungsdatum liegt vor Beginn des Durchführungszeitraums.",
    )


def _duplicate_receipt(bundle: Bundle, row: Row, _: Random) -> Planted | None:
    receipts = bundle.table("receipts")
    own = [r for r in receipts if r["claim_id"] == row["claim_id"]]
    copy: Row = dict(row)
    copy["receipt_no"] = len(own) + 1
    receipts.insert(receipts.index(own[-1]) + 1, copy)
    return Planted(
        "invoice_no",
        None,
        row["invoice_no"],
        amount(row, "project_related"),
        f"Der Beleg wiederholt die Rechnung von Beleg {row['receipt_no']} desselben Mittelabrufs.",
        copy,
    )


def _missing_payment_date(_: Bundle, row: Row, __: Random) -> Planted | None:
    original = row["payment_date"]
    row["payment_date"] = None
    row["evidence_payment"] = "Nein"
    return Planted(
        "payment_date",
        original,
        None,
        amount(row, "project_related"),
        "Das Bezahldatum fehlt, ein Zahlungsnachweis liegt nicht vor.",
    )


def _discount_not_deducted(_: Bundle, row: Row, __: Random) -> Planted | None:
    discount = amount(row, "discount_amount")
    if discount <= ZERO:
        return None
    original = amount(row, "project_related")
    row["project_related"] = original + discount
    row["recognised"] = amount(row, "recognised") + discount
    return Planted(
        "project_related",
        original,
        row["project_related"],
        discount,
        "Angemeldet ist der Betrag vor Abzug des in Anspruch genommenen Skontos.",
    )


def _vat_despite_deduction(bundle: Bundle, row: Row, _: Random) -> Planted | None:
    vat = amount(row, "vat")
    if not _operation(bundle, row)["vat_deduction"] or vat <= ZERO:
        return None
    original = amount(row, "project_related")
    row["project_related"] = original + vat
    row["recognised"] = amount(row, "recognised") + vat
    return Planted(
        "project_related",
        original,
        row["project_related"],
        vat,
        "Trotz Vorsteuerabzugsberechtigung ist die Umsatzsteuer mit angemeldet.",
    )


def _ineligible_cost_category(_: Bundle, row: Row, __: Random) -> Planted | None:
    if row["staff_cost"]:
        return None
    original = row["cost_category"]
    row["cost_category"] = cat.catalogs().ineligible_cost_category
    return Planted(
        "cost_category",
        original,
        row["cost_category"],
        amount(row, "project_related"),
        "Die Kostenart ist im Kostenplan des Vorhabens nicht vorgesehen.",
    )


def _arithmetic_error(_: Bundle, row: Row, rng: Random) -> Planted | None:
    if amount(row, "vat") <= ZERO:
        return None
    original = amount(row, "gross")
    row["gross"] = original + Decimal(rng.randrange(1_000, 50_001)) / 100
    return Planted(
        "gross",
        original,
        row["gross"],
        ZERO,
        "Brutto entspricht nicht der Summe aus Netto und Umsatzsteuer.",
    )


def _direct_award_above_limit(bundle: Bundle, row: Row, _: Random) -> Planted | None:
    eligible = _operation(bundle, row)["contracting_authority"] and not row["staff_cost"]
    if not eligible or amount(row, "net") < bundle.config.direct_award_limit:
        return None
    original = row["award_type"]
    row["award_type"] = DIRECT_AWARD
    row["direct_award"] = True
    return Planted(
        "award_type",
        original,
        DIRECT_AWARD,
        amount(row, "project_related"),
        f"Direktauftrag trotz Nettobetrag ab der eingestellten Wertgrenze von "
        f"{bundle.config.direct_award_limit} EUR.",
    )


def _claim_above_receipts(_: Bundle, row: Row, rng: Random) -> Planted | None:
    original = amount(row, "requested")
    surplus = Decimal(rng.randrange(10_000, 500_001)) / 100
    row["requested"] = original + surplus
    return Planted(
        "requested",
        original,
        row["requested"],
        surplus,
        "Die Anforderung des Mittelabrufs übersteigt die Summe seiner Belege.",
    )


def _payment_deadline_exceeded(_: Bundle, row: Row, rng: Random) -> Planted | None:
    original = row["payment_date"]
    days = rng.randrange(PAYMENT_DEADLINE_DAYS + 1, 141)
    row["payment_date"] = day(row, "receipt_date") + timedelta(days=days)
    row["processing_days"] = days
    return Planted(
        "payment_date",
        original,
        row["payment_date"],
        ZERO,
        f"Auszahlung {days} Tage nach Eingang des Mittelabrufs; die Frist beträgt "
        f"{PAYMENT_DEADLINE_DAYS} Tage (Art. 74 Abs. 1 Buchst. b VO (EU) 2021/1060).",
    )


ANOMALIES: tuple[AnomalyKind, ...] = (
    AnomalyKind("paid_before_invoice", "Bezahlt vor Rechnung",
                "Das Bezahldatum liegt 1 bis 30 Tage vor dem Rechnungsdatum.",
                "receipts", _paid_before_invoice),
    AnomalyKind("eligible_above_paid", "Förderfähig über gezahlt",
                "Der projektbezogene Betrag liegt 10 bis 50 % über dem gezahlten Betrag.",
                "receipts", _eligible_above_paid),
    AnomalyKind("negative_amount", "Negative Beträge",
                "Die Betragsspalten eines Belegs tragen ein negatives Vorzeichen.",
                "receipts", _negative_amount, (1,)),
    AnomalyKind("outside_period", "Beleg außerhalb des Durchführungszeitraums",
                "Das Rechnungsdatum liegt vor Beginn des Durchführungszeitraums.",
                "receipts", _outside_period),
    AnomalyKind("duplicate_receipt", "Doppelbeleg",
                "Dieselbe Rechnung steht ein zweites Mal im selben Mittelabruf.",
                "receipts", _duplicate_receipt, (1,)),
    AnomalyKind("missing_payment_date", "Fehlendes Zahlungsdatum",
                "Das Bezahldatum ist leer, der Zahlungsnachweis steht auf „Nein“.",
                "receipts", _missing_payment_date),
    AnomalyKind("discount_not_deducted", "Skonto nicht abgezogen",
                "Angemeldet ist der Betrag vor Skonto, obwohl Skonto gezogen wurde.",
                "receipts", _discount_not_deducted, (1,)),
    AnomalyKind("vat_despite_deduction", "Umsatzsteuer trotz Vorsteuerabzug",
                "Angemeldet ist der Bruttobetrag, obwohl das Vorhaben zum Vorsteuerabzug "
                "berechtigt ist.", "receipts", _vat_despite_deduction, (1,)),
    AnomalyKind("ineligible_cost_category", "Kostenart außerhalb des Kostenplans",
                "Die Kostenart des Belegs kommt im Kostenplan des Vorhabens nicht vor.",
                "receipts", _ineligible_cost_category),
    AnomalyKind("arithmetic_error", "Rechenfehler",
                "Brutto weicht von der Summe aus Netto und Umsatzsteuer ab.",
                "receipts", _arithmetic_error),
    AnomalyKind("direct_award_above_limit", "Direktauftrag über der Wertgrenze",
                "Vergabeart „Direktauftrag“ bei einem Nettobetrag ab der eingestellten "
                "Wertgrenze (Parameter des Generators, keine Rechtsaussage).",
                "receipts", _direct_award_above_limit),
    AnomalyKind("claim_above_receipts", "Mittelabruf über der Summe der Belege",
                "Die Anforderung des Mittelabrufs ist höher als die Summe seiner Belege.",
                "claims", _claim_above_receipts, (1,)),
    AnomalyKind("payment_deadline_exceeded", "Auszahlungsfrist von 80 Tagen überschritten",
                "Die Auszahlung liegt mehr als 80 Tage nach dem Eingang des Mittelabrufs.",
                "claims", _payment_deadline_exceeded),
)  # fmt: skip


def anomaly_codes() -> tuple[str, ...]:
    """Codes of all anomalies in catalogue order."""
    return tuple(kind.code for kind in ANOMALIES)


def _row_key(row: Row) -> str:
    return f"{row['claim_id']}/{row['receipt_no']}" if "receipt_no" in row else str(row["claim_id"])


def _plant_kind(bundle: Bundle, kind: AnomalyKind, rows: list[Row], used: set[int]) -> bool:
    """Plant ``kind`` on the first unused row it applies to; False if none fits."""
    for row in rows:
        if id(row) in used:
            continue
        rng = stream(bundle.config.seed, "anomaly", kind.code, _row_key(row))
        planted = kind.planter(bundle, row, rng)
        if planted is None:
            continue
        target = planted.row if planted.row is not None else row
        used.update((id(row), id(target)))
        bundle.solution.append(
            SolutionEntry(
                kind.code,
                kind.title,
                kind.table,
                _row_key(target),
                planted.changed_field,
                planted.original,
                planted.planted,
                planted.expected_amount,
                planted.reason,
                kind.checks,
            )  # fmt: skip
        )
        bundle.solution_rows.append(target)
        return True
    return False


def plant_anomalies(bundle: Bundle, tables: frozenset[str] | None = None) -> None:
    """Plant the configured anomalies; ``tables`` limits them to tables that are output."""
    config = bundle.config
    chosen = [
        kind
        for kind in ANOMALIES
        if kind.code in config.anomalies and (tables is None or kind.table in tables)
    ]
    used: set[int] = set()
    for table in ("receipts", "claims"):
        kinds = [kind for kind in chosen if kind.table == table]
        if not kinds:
            continue
        rows = list(bundle.table(table))
        stream(config.seed, "anomaly-order", table).shuffle(rows)
        wanted = max(len(kinds), int(quantize(config.anomaly_rate * len(rows), Decimal(1))))
        active = list(kinds)
        for index in range(wanted):
            if not active:
                break
            kind = active[index % len(active)]
            if not _plant_kind(bundle, kind, rows, used):
                active.remove(kind)
                if not any(entry.code == kind.code for entry in bundle.solution):
                    bundle.skipped_anomalies.append(kind.code)
