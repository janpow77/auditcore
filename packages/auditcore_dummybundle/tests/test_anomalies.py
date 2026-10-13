"""Auffälligkeiten: eingestreut nach dem stimmigen Bündel, Lösung getrennt und vollständig."""

from __future__ import annotations

from decimal import Decimal

import pytest
from conftest import config

from auditcore_dummybundle import (
    ANOMALIES,
    Options,
    anomaly_codes,
    build_bundle,
    document,
    generate_templates,
    plant_anomalies,
    run_checks,
)
from auditcore_dummybundle.model import day

ALL = anomaly_codes()


def test_catalogue_names_thirteen_anomalies_with_german_texts() -> None:
    assert len(ALL) == len(set(ALL)) == 13
    for kind in ANOMALIES:
        assert kind.title and kind.description.endswith((".", ")"))
        assert kind.table in {"receipts", "claims"}


@pytest.mark.parametrize("code", ALL)
def test_each_anomaly_is_planted_and_recorded(code: str) -> None:
    bundle = build_bundle(
        config(
            11, operations=8, anomalies=(code,), vat_deduction="yes", discount_share=Decimal("1.00")
        )
    )
    plant_anomalies(bundle)
    assert bundle.solution, code
    assert {entry.code for entry in bundle.solution} == {code}
    entry = bundle.solution[0]
    assert entry.reason and entry.row_key and entry.expected_amount >= 0
    assert all(key.startswith("gt_") for key in entry.as_row())


def test_broken_checks_are_exactly_the_declared_ones() -> None:
    for seed in range(12):
        bundle = build_bundle(
            config(seed, operations=6, anomalies=ALL, anomaly_rate=Decimal("0.10"))
        )
        plant_anomalies(bundle)
        declared = {check for entry in bundle.solution for check in entry.affected_checks}
        broken = {outcome.number for outcome in run_checks(bundle) if not outcome.passed}
        assert broken <= declared, (seed, broken, declared)


def test_without_anomalies_nothing_is_planted() -> None:
    bundle = build_bundle(config(1))
    plant_anomalies(bundle)
    assert bundle.solution == [] and bundle.skipped_anomalies == []


def test_anomaly_rate_controls_the_number() -> None:
    low = build_bundle(
        config(4, operations=10, anomalies=("paid_before_invoice",), anomaly_rate=Decimal("0.02"))
    )
    high = build_bundle(
        config(4, operations=10, anomalies=("paid_before_invoice",), anomaly_rate=Decimal("0.30"))
    )
    plant_anomalies(low)
    plant_anomalies(high)
    assert 1 <= len(low.solution) < len(high.solution)
    receipts = len(high.table("receipts"))
    assert abs(len(high.solution) - receipts * 0.30) <= 1


def test_planted_values_match_the_description() -> None:
    bundle = build_bundle(
        config(9, operations=6, anomalies=("paid_before_invoice", "payment_deadline_exceeded"))
    )
    plant_anomalies(bundle)
    for entry, row in zip(bundle.solution, bundle.solution_rows, strict=True):
        if entry.code == "paid_before_invoice":
            assert day(row, "payment_date") < day(row, "invoice_date")
        else:
            assert (day(row, "payment_date") - day(row, "receipt_date")).days > 80


def test_solution_is_separate_and_only_on_request() -> None:
    cfg = config(21, anomalies=ALL, anomaly_rate=Decimal("0.10"))
    plain = generate_templates(cfg, ["N1", "V4"])
    solved = generate_templates(cfg, ["N1", "V4"], Options(solution=True))
    assert plain.solution is None and "solution" not in document(plain)
    assert solved.solution and document(solved)["tables"] == document(plain)["tables"]
    for table in plain.tables:
        for column in table.columns:
            assert not column.header.startswith("gt_")
            assert "Auffälligkeit" not in column.header and "Fehler" not in column.header
    meta = plain.meta["anomalies"]
    assert isinstance(meta, dict) and meta["planted"] == len(solved.solution)


def test_solution_points_to_output_table_and_row() -> None:
    cfg = config(
        21, anomalies=("paid_before_invoice", "duplicate_receipt"), anomaly_rate=Decimal("0.05")
    )
    result = generate_templates(cfg, ["V2"], Options(solution=True))
    tables = {table.name: table for table in result.tables}
    assert result.solution
    for entry in result.solution:
        table = tables[entry.table]
        row = table.rows[entry.row_number - 1]  # Zeile 1 ist die Summenzeile der Vorlage V2
        headers = [column.header for column in table.columns]
        invoice = row[headers.index("Rechnungsdatum")]
        paid = row[headers.index("Bezahldatum (Wertstellung)")]
        if entry.code == "paid_before_invoice":
            assert paid < invoice  # type: ignore[operator]
        else:
            numbers = [r[headers.index("Beleg-Nr. / Rechnungs-Nr.")] for r in table.rows]
            assert numbers.count(row[headers.index("Beleg-Nr. / Rechnungs-Nr.")]) == 2


def test_solution_names_every_output_table_of_a_row() -> None:
    cfg = config(21, anomalies=("paid_before_invoice",), anomaly_rate=Decimal("0.05"))
    result = generate_templates(cfg, ["V4", "N1", "V2"], Options(solution=True))
    assert result.solution
    for entry in result.solution:
        names = entry.table.split("; ")
        assert names[0] == "Belegübersicht" and names[1] == "Belegliste"
        assert names[2].startswith("Belegliste ") and names[2].endswith(")")
        assert result.tables[1].name == "Belegübersicht" and entry.row_number >= 1


def test_anomalies_only_for_tables_in_the_output() -> None:
    cfg = config(21, anomalies=ALL, anomaly_rate=Decimal("0.10"))
    result = generate_templates(cfg, ["V5", "V6"], Options(solution=True))
    assert result.solution == ()
    claims_only = generate_templates(cfg, ["V9"], Options(solution=True))
    assert claims_only.solution == ()
