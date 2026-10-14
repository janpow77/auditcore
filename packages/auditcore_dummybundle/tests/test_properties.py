"""Eigenschaftstests: jeder Startwert ergibt ein stimmiges, wiederholbares Bündel."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from auditcore_dummybundle import (
    BundleConfig,
    accounting_year,
    build_bundle,
    document,
    generate_templates,
    run_checks,
    templates,
)
from auditcore_dummybundle.model import amount, day, number

EXAMPLES = settings(max_examples=60, deadline=None)
PUBLIC = [template.id for template in templates().values() if template.public]


@st.composite
def configs(draw: st.DrawFn) -> BundleConfig:
    claims = sorted(draw(st.tuples(st.integers(1, 6), st.integers(1, 6))))
    receipts = sorted(draw(st.tuples(st.integers(1, 20), st.integers(1, 20))))
    public = draw(st.sampled_from(["0.50", "0.75", "0.85", "1.00"]))
    return BundleConfig(
        seed=draw(st.integers(0, 2**31 - 1)),
        base_date=draw(st.dates(date(2021, 1, 1), date(2030, 12, 31))),
        country=draw(st.sampled_from(["DE", "AT", "DE+AT"])),
        operations=draw(st.integers(1, 12)),
        claims_min=claims[0],
        claims_max=claims[1],
        receipts_min=receipts[0],
        receipts_max=receipts[1],
        priorities=draw(st.integers(1, 6)),
        payment_applications=draw(st.integers(1, 6)),
        public_share=Decimal(public),
        eu_rate=Decimal(draw(st.sampled_from(["0.00", "0.40", "0.50"]))),
        vat_deduction=draw(st.sampled_from(["yes", "no", "mixed"])),
        discount_share=Decimal(draw(st.sampled_from(["0.00", "0.30", "1.00"]))),
        reduction_share=Decimal(draw(st.sampled_from(["0.00", "0.10", "1.00"]))),
        corrections=draw(st.integers(0, 12)),
        prior_year_withdrawals=draw(st.integers(0, 3)),
    )


@EXAMPLES
@given(config=configs())
def test_every_configuration_passes_all_sum_checks(config: BundleConfig) -> None:
    outcomes = run_checks(build_bundle(config))
    assert all(outcome.passed for outcome in outcomes), [o for o in outcomes if not o.passed]


@EXAMPLES
@given(config=configs())
def test_date_sequences_hold(config: BundleConfig) -> None:
    bundle = build_bundle(config)
    year_start, year_end = accounting_year(config.base_date)
    operations = {op["operation_id"]: op for op in bundle.table("operations")}
    claims = {claim["claim_id"]: claim for claim in bundle.table("claims")}
    for op in operations.values():
        assert day(op, "application_date") < day(op, "approval_date") <= day(op, "period_start")
        assert day(op, "period_start") < year_start and day(op, "period_end") > year_end
        assert day(op, "earmark_until") > day(op, "period_end")
    for claim in claims.values():
        applied, received, paid = (
            day(claim, key) for key in ("application_date", "receipt_date", "payment_date")
        )
        assert year_start <= applied <= received < paid <= year_end
        assert (paid - received).days == number(claim, "processing_days") <= 80
        assert paid <= day(claim, "application_submission_date")
    for receipt in bundle.table("receipts"):
        claim, op = claims[receipt["claim_id"]], operations[receipt["operation_id"]]
        invoice, paid = day(receipt, "invoice_date"), day(receipt, "payment_date")
        assert day(op, "period_start") <= invoice <= paid <= day(claim, "application_date")
        assert invoice <= day(op, "period_end")
    for item in bundle.table("corrections"):
        assert day(item, "detection_date") < day(item, "final_date")
        if item["claim_id"] is not None:
            assert day(item, "detection_date") > day(claims[item["claim_id"]], "payment_date")


@EXAMPLES
@given(config=configs())
def test_amount_relations_of_receipts_hold(config: BundleConfig) -> None:
    bundle = build_bundle(config)
    cent = Decimal("0.01")
    for row in bundle.table("receipts"):
        assert amount(row, "gross") == amount(row, "net") + amount(row, "vat")
        assert amount(row, "claim_basis") - amount(row, "discount_amount") == amount(
            row, "project_related"
        )
        assert Decimal(0) <= amount(row, "reduction") <= amount(row, "project_related")
        assert amount(row, "paid") <= amount(row, "gross")
        assert amount(row, "project_related") >= Decimal("10.00")
        assert all(
            amount(row, key) == amount(row, key).quantize(cent)
            for key in ("net", "vat", "gross", "paid", "project_related", "recognised")
        )
        if row["staff_cost"]:
            assert amount(row, "vat") == 0 and row["evidence_timesheet"] == "Ja"
        else:
            assert row["evidence_timesheet"] == "Entfällt"


@settings(max_examples=25, deadline=None)
@given(config=configs())
def test_same_configuration_gives_identical_output(config: BundleConfig) -> None:
    first = document(generate_templates(config, PUBLIC))
    second = document(generate_templates(config, PUBLIC))
    assert first == second
    assert first["_meta"]["seed"] == config.seed  # type: ignore[index]


def test_different_seed_or_base_date_changes_the_data() -> None:
    base = BundleConfig(seed=1, base_date=date(2026, 1, 1))
    reference = document(generate_templates(base, ["N1"]))["tables"]
    other_seed = BundleConfig(seed=2, base_date=date(2026, 1, 1))
    other_date = BundleConfig(seed=1, base_date=date(2026, 1, 1) + timedelta(days=366))
    assert document(generate_templates(other_seed, ["N1"]))["tables"] != reference
    assert document(generate_templates(other_date, ["N1"]))["tables"] != reference


def test_receipts_of_one_claim_do_not_depend_on_other_operations() -> None:
    """Teilfolgen aus fachlichen Schlüsseln: mehr Vorhaben verschieben vorhandene nicht."""
    small = build_bundle(BundleConfig(seed=5, base_date=date(2026, 1, 1), operations=2))
    large = build_bundle(BundleConfig(seed=5, base_date=date(2026, 1, 1), operations=6))
    keep = {op["operation_id"] for op in small.table("operations")}
    assert small.table("operations") == [
        op for op in large.table("operations") if op["operation_id"] in keep
    ]
    drop = ("supplier_name", "supplier_vat_id")
    strip = lambda rows: [  # noqa: E731
        {k: v for k, v in row.items() if k not in drop}
        for row in rows
        if row["operation_id"] in keep
    ]
    assert strip(small.table("receipts")) == strip(large.table("receipts"))
