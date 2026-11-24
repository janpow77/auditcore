"""Ländermischung DE+AT, Skonto auf brutto und Auszahlungsfrist bis zum Bezugsdatum (0.3.0)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from conftest import config

from auditcore_dummybundle import build_bundle, generate_templates
from auditcore_dummybundle.anomalies import PAYMENT_DEADLINE_DAYS, plant_anomalies
from auditcore_dummybundle.catalogs import catalogs
from auditcore_dummybundle.checks import run_checks
from auditcore_dummybundle.model import Row, amount, day

AT_PROCEDURES = {
    "Direktvergabe (BVergG 2018)",
    "Offenes Verfahren (BVergG 2018)",
    "Nicht offenes Verfahren mit vorheriger Bekanntmachung (BVergG 2018)",
}
DE_PROCEDURES = {"Direktauftrag", "VOL unterhalb Schwellenwert", "VOB unterhalb Schwellenwert"}
SEEDS = (4711, 1, 2, 3, 99)


def _operations(rows: list[Row]) -> dict[str, Row]:
    return {str(op["operation_id"]): op for op in rows}


@pytest.mark.parametrize("seed", SEEDS)
def test_mixed_bundle_keeps_vat_and_award_in_one_country(seed: int) -> None:
    bundle = build_bundle(config(seed, base_date=date(2026, 6, 30), operations=12, country="DE+AT"))
    operations = _operations(bundle.table("operations"))
    countries = set()
    for row in bundle.table("receipts"):
        operation = operations[str(row["operation_id"])]
        country = str(operation["country"])
        assert row["supplier_country"] == country
        if row["staff_cost"]:
            assert amount(row, "vat_rate") == 0
            continue
        countries.add(country)
        prefix = "ATU" if country == "AT" else "DE"
        assert str(row["supplier_vat_id"]).startswith(prefix), row["supplier_vat_id"]
        assert amount(row, "vat_rate") == catalogs().vat_rates[country]
        if row["award_type"] != "Entfällt":
            allowed = AT_PROCEDURES if country == "AT" else DE_PROCEDURES
            assert row["award_type"] in allowed, (country, row["award_type"])
            assert row["direct_award"] == row["award_type"].startswith("Direkt")
    assert countries == {"DE", "AT"}


def test_single_country_bundles_use_only_their_own_law() -> None:
    for country, allowed in (("DE", DE_PROCEDURES), ("AT", AT_PROCEDURES)):
        bundle = build_bundle(config(7, operations=10, country=country))
        awards = {row["award_type"] for row in bundle.table("receipts")} - {"Entfällt"}
        assert awards <= allowed, (country, awards)
        assert {row["supplier_country"] for row in bundle.table("receipts")} == {country}


def test_planted_direct_award_uses_the_name_of_the_country() -> None:
    names = set()
    for seed in SEEDS:
        bundle = build_bundle(
            config(
                seed,
                operations=12,
                country="DE+AT",
                anomalies=("direct_award_above_limit",),
                anomaly_rate=Decimal("0.5"),
            )
        )
        plant_anomalies(bundle)
        operations = _operations(bundle.table("operations"))
        for entry, row in zip(bundle.solution, bundle.solution_rows, strict=True):
            country = operations[str(row["operation_id"])]["country"]
            expected = "Direktvergabe (BVergG 2018)" if country == "AT" else "Direktauftrag"
            assert entry.planted == row["award_type"] == expected
            names.add(expected)
    assert names == {"Direktvergabe (BVergG 2018)", "Direktauftrag"}


@pytest.mark.parametrize("vat_deduction", ["yes", "no", "mixed"])
def test_gross_minus_cash_discount_is_the_paid_amount(vat_deduction: str) -> None:
    for seed in SEEDS:
        bundle = build_bundle(
            config(seed, operations=8, vat_deduction=vat_deduction, discount_share=Decimal("1"))
        )
        operations = _operations(bundle.table("operations"))
        for row in bundle.table("receipts"):
            assert amount(row, "gross") - amount(row, "discount_gross") == amount(row, "paid")
            assert amount(row, "claim_basis") - amount(row, "discount_amount") == amount(
                row, "project_related"
            )
            net_basis = row["staff_cost"] or operations[str(row["operation_id"])]["vat_deduction"]
            if not net_basis:
                assert amount(row, "paid") == amount(row, "project_related")
        assert all(outcome.passed for outcome in run_checks(bundle))


def test_n1_shows_the_cash_discount_on_the_gross_amount() -> None:
    result = generate_templates(config(5, operations=4, discount_share=Decimal("1")), ["N1"])
    for table in result.tables:
        headers = [column.header for column in table.columns]
        column = table.columns[headers.index("Skontobetrag")]
        assert "brutto" in column.note
        gross, discount, paid = (
            headers.index(name) for name in ("Betrag brutto", "Skontobetrag", "gezahlter Betrag")
        )
        for row in table.rows:
            if isinstance(row[gross], Decimal):
                assert row[gross] - row[discount] == row[paid]


def _cutoffs(bundle_rows: list[Row]) -> dict[str, date]:
    return {str(item["application_no"]): day(item, "cutoff_date") for item in bundle_rows}


@pytest.mark.parametrize("base_date", [date(2026, 6, 30), date(2026, 3, 31), date(2025, 12, 31)])
def test_planted_payment_delay_stays_before_the_base_date(base_date: date) -> None:
    planted = 0
    for seed in SEEDS:
        bundle = build_bundle(
            config(
                seed,
                base_date=base_date,
                operations=12,
                anomalies=("payment_deadline_exceeded",),
                anomaly_rate=Decimal("0.5"),
            )
        )
        plant_anomalies(bundle)
        cutoffs = _cutoffs(bundle.table("payment_applications"))
        units = {str(u["unit_id"]): u for u in bundle.table("population")}
        for entry, row in zip(bundle.solution, bundle.solution_rows, strict=True):
            paid = day(row, "payment_date")
            assert entry.planted == paid
            assert row["processing_days"] == (paid - day(row, "receipt_date")).days
            assert row["processing_days"] > PAYMENT_DEADLINE_DAYS
            assert paid <= base_date and paid <= cutoffs[str(row["application_no"])]
            assert units[f"AE-{row['claim_id']}"]["payment_date"] == paid
            for item in bundle.table("corrections"):
                if item["claim_id"] == row["claim_id"]:
                    assert paid < day(item, "detection_date")
            planted += 1
    assert planted > 0


def test_payment_delay_is_skipped_when_no_claim_leaves_room() -> None:
    bundle = build_bundle(
        config(3, base_date=date(2025, 7, 15), anomalies=("payment_deadline_exceeded",))
    )
    plant_anomalies(bundle)
    for row in bundle.solution_rows:
        assert day(row, "payment_date") <= date(2025, 7, 15)
    if not bundle.solution:
        assert bundle.skipped_anomalies == ["payment_deadline_exceeded"]


def test_same_seed_still_gives_identical_mixed_bundles() -> None:
    def make() -> list[Row]:
        bundle = build_bundle(
            config(4711, operations=12, country="DE+AT", anomalies=("payment_deadline_exceeded",))
        )
        plant_anomalies(bundle)
        return bundle.table("receipts") + bundle.table("claims")

    assert make() == make()
