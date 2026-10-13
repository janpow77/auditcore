"""Accounts of the accounting year (Annex XXIV appendices) and the audit population.

Appendix 1 holds the final payment application minus the direct deductions,
Appendix 2 the withdrawals, Appendix 4 reconciles both. Appendices 3, 5 and 7
(financial instruments, enabling conditions, State aid advances) are present
with zero amounts: the bundle generates none of these cases.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from auditcore_dummybundle import catalogs as cat
from auditcore_dummybundle.amounts import ZERO, share
from auditcore_dummybundle.applications import TOTAL_LABEL, WITHDRAWAL
from auditcore_dummybundle.chain import PROGRAMME_CODE, priority_label
from auditcore_dummybundle.config import BundleConfig, accounting_year
from auditcore_dummybundle.corrections import DEDUCTION
from auditcore_dummybundle.model import Row, amount

AUDIT_ROW = "Davon infolge von Prüfungen in der gegenwärtigen Rechnungslegung berichtigte Beträge"
_YEAR_ROW = "In Bezug auf das am 30. Juni {year} endende Geschäftsjahr (insgesamt)"
_YEAR_AUDIT_ROW = "Insbesondere, davon infolge von Prüfungen korrigiert"


def _sum(rows: list[Row], key: str) -> Decimal:
    return sum((amount(row, key) for row in rows), ZERO)


def _select(corrections: list[Row], kind: str, priority: str | None = None) -> list[Row]:
    return [
        item
        for item in corrections
        if item["kind"] == kind and (priority is None or item["priority"] == priority)
    ]


def _with_total(rows: list[Row], keys: tuple[str, ...]) -> list[Row]:
    total: Row = {"row_kind": "total", "priority": TOTAL_LABEL}
    for key in rows[0]:
        if key not in total:
            total[key] = _sum(rows, key) if key in keys else None
    return [*rows, total]


def _final_rows(applications: list[Row]) -> dict[str, Row]:
    return {
        str(row["priority"]): row
        for row in applications
        if row["final"] and row["row_kind"] == "priority"
    }


def build_annex1(
    config: BundleConfig, applications: list[Row], corrections: list[Row]
) -> list[Row]:
    """Appendix 1: amounts entered into the accounting systems, per priority."""
    final = _final_rows(applications)
    rows: list[Row] = []
    for index in range(1, config.priorities + 1):
        priority = priority_label(index)
        deducted = _select(corrections, DEDUCTION, priority)
        rows.append(
            {
                "row_kind": "priority",
                "priority": priority,
                "eligible": amount(final[priority], "eligible_cumulative")
                - _sum(deducted, "amount"),
                "technical_assistance": None,
                "public": amount(final[priority], "public_cumulative")
                - _sum(deducted, "public_amount"),
            }
        )
    return _with_total(rows, ("eligible", "public"))


def build_annex2(config: BundleConfig, corrections: list[Row]) -> list[Row]:
    """Appendix 2: withdrawals per priority and split by accounting year of declaration."""
    rows: list[Row] = []
    for index in range(1, config.priorities + 1):
        priority = priority_label(index)
        withdrawn = _select(corrections, WITHDRAWAL, priority)
        rows.append(
            {
                "row_kind": "priority",
                "priority": priority,
                "withdrawn": _sum(withdrawn, "amount"),
                "withdrawn_public": _sum(withdrawn, "public_amount"),
            }
        )
    rows = _with_total(rows, ("withdrawn", "withdrawn_public"))
    withdrawals = _select(corrections, WITHDRAWAL)
    years = sorted({int(str(item["declaration_year"])) for item in withdrawals}, reverse=True)
    for year in years or [accounting_year(config.base_date)[1].year]:
        of_year = [item for item in withdrawals if item["declaration_year"] == year]
        audited = [item for item in of_year if item["audit_based"]]
        for kind, label, items in (
            ("year", _YEAR_ROW.format(year=year), of_year),
            ("year_audit", _YEAR_AUDIT_ROW, audited),
        ):
            rows.append(
                {
                    "row_kind": kind,
                    "priority": label,
                    "declaration_year": year,
                    "withdrawn": _sum(items, "amount"),
                    "withdrawn_public": _sum(items, "public_amount"),
                }
            )
    return rows


def _remark(deducted: list[Row]) -> str | None:
    if not deducted:
        return None
    parts = []
    for kind in sorted({str(item["deduction_type"]) for item in deducted}):
        value = _sum([item for item in deducted if item["deduction_type"] == kind], "amount")
        parts.append(f"Abzug nach {kind}: {value} EUR")
    return "; ".join(parts)


def build_annex4(
    config: BundleConfig, applications: list[Row], annex1: list[Row], corrections: list[Row]
) -> list[Row]:
    """Appendix 4: reconciliation of payment applications and accounts."""
    final = _final_rows(applications)
    booked = {str(row["priority"]): row for row in annex1}
    rows: list[Row] = []
    for index in range(1, config.priorities + 1):
        priority = priority_label(index)
        declared = amount(final[priority], "eligible_cumulative")
        declared_public = amount(final[priority], "public_cumulative")
        rows.append(
            {
                "row_kind": "priority",
                "priority": priority,
                "declared": declared,
                "declared_public": declared_public,
                "accounts": amount(booked[priority], "eligible"),
                "accounts_public": amount(booked[priority], "public"),
                "difference": declared - amount(booked[priority], "eligible"),
                "difference_public": declared_public - amount(booked[priority], "public"),
                "remarks": _remark(_select(corrections, DEDUCTION, priority)),
            }
        )
    keys = ("declared", "declared_public", "accounts", "accounts_public")
    rows = _with_total(rows, (*keys, "difference", "difference_public"))
    audited = [item for item in _select(corrections, DEDUCTION) if item["audit_based"]]
    audit_row: Row = {"row_kind": "audit", "priority": AUDIT_ROW, "remarks": None}
    audit_row.update(dict.fromkeys(keys))
    audit_row["difference"] = _sum(audited, "amount")
    audit_row["difference_public"] = _sum(audited, "public_amount")
    return [*rows, audit_row]


def build_empty_annex(config: BundleConfig, columns: tuple[str, ...]) -> list[Row]:
    """Appendix without cases in the bundle: zero amounts per priority and in total."""
    rows: list[Row] = []
    for index in range(1, config.priorities + 1):
        row: Row = {"row_kind": "priority", "priority": priority_label(index)}
        row.update(dict.fromkeys(columns, ZERO))
        rows.append(row)
    return _with_total(rows, columns)


def build_annex5(annex1: list[Row]) -> list[Row]:
    """Appendix 5: no unmet enabling conditions; columns D and E repeat Appendix 1."""
    return [
        {
            "row_kind": row["row_kind"],
            "priority": row["priority"],
            "basis": "insgesamt" if row["row_kind"] == "priority" else None,
            "unmet": ZERO,
            "unmet_public": ZERO,
            "met": row["eligible"],
            "met_public": row["public"],
        }
        for row in annex1
    ]


def build_head(config: BundleConfig) -> list[Row]:
    """Header of the accounts: programme, version, submission date, accounting year."""
    year_start, year_end = accounting_year(config.base_date)
    return [
        {
            "fund": config.fund,
            "cci": PROGRAMME_CODE,
            "programme": f"Synthetisches Programm {config.fund}",
            "version": "1.0",
            "submission_date": date(year_end.year + 1, 2, 15),
            "accounting_year_from": year_start,
            "accounting_year_to": year_end,
        }
    ]


def _unit_head(operation: Row, head: Row) -> Row:
    return {
        "application_no": head["application_no"],
        "application_submission_date": head["submission_date"],
        "operation_id": operation["operation_id"],
        "priority": operation["priority"],
        "specific_objective": operation["specific_objective"],
        "programme_group": operation["programme_group"],
        "nuts3": operation["nuts3"],
        "title": operation["title"],
        "beneficiary_name": operation["beneficiary_name"],
        "operation_application_date": operation["application_date"],
        "approval_date": operation["approval_date"],
    }


def _claim_unit(config: BundleConfig, claim: Row, result: str) -> Row:
    return {
        "unit_kind": "Mittelabruf",
        "unit_id": f"AE-{claim['claim_id']}",
        "claim_date": claim["application_date"],
        "declared": claim["requested"],
        "declared_public": share(amount(claim, "requested"), config.public_share),
        "verification_result": result,
        "certified": claim["eligible"],
        "certified_public": claim["public"],
        "payment_date": claim["payment_date"],
        "paid_eu": claim["eu"],
        "paid_public": claim["public"],
    }


def _withdrawal_unit(item: Row, result: str) -> Row:
    return {
        "unit_kind": WITHDRAWAL,
        "unit_id": f"AE-{item['correction_id']}",
        "claim_date": None,
        "declared": -amount(item, "amount"),
        "declared_public": -amount(item, "public_amount"),
        "verification_result": result,
        "certified": -amount(item, "amount"),
        "certified_public": -amount(item, "public_amount"),
        "payment_date": None,
        "paid_eu": -amount(item, "eu_amount"),
        "paid_public": -amount(item, "public_amount"),
    }


def build_population(
    config: BundleConfig,
    operations: list[Row],
    claims: list[Row],
    corrections: list[Row],
    schedule: list[Row],
) -> list[Row]:
    """Sampling units of the accounting year: paid claims plus negative withdrawal units."""
    by_operation = {str(op["operation_id"]): op for op in operations}
    by_number = {row["number"]: row for row in schedule}
    result = cat.catalogs().placeholders["verification_result"]
    rows: list[Row] = []
    for claim in claims:
        unit = _claim_unit(config, claim, result)
        unit.update(
            _unit_head(
                by_operation[str(claim["operation_id"])], by_number[claim["application_number"]]
            )
        )
        rows.append(unit)
    for item in _select(corrections, WITHDRAWAL):
        unit = _withdrawal_unit(item, result)
        unit.update(
            _unit_head(
                by_operation[str(item["operation_id"])], by_number[item["application_number"]]
            )
        )
        rows.append(unit)
    rows.sort(key=lambda row: (str(row["application_no"]), str(row["unit_id"])))
    return rows
