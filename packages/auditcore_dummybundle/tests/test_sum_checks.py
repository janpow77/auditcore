"""Die acht Summenproben des Vorlagenvorschlags, jede für sich aus den Tabellen nachgerechnet."""

from __future__ import annotations

from decimal import Decimal

import pytest
from conftest import config, total

from auditcore_dummybundle import Bundle, build_bundle, run_checks, share
from auditcore_dummybundle.model import Row, amount

SEEDS = [0, 1, 7, 42, 2026, 99_999]
ZERO = Decimal("0.00")


@pytest.fixture(params=SEEDS, ids=[f"seed{seed}" for seed in SEEDS])
def bundle(request: pytest.FixtureRequest) -> Bundle:
    seed = request.param
    return build_bundle(
        config(
            seed,
            operations=4 + seed % 5,
            priorities=1 + seed % 3,
            corrections=6,
            payment_applications=1 + seed % 6,
            prior_year_withdrawals=2,
        )
    )


def _priority(rows: list[Row]) -> list[Row]:
    return [row for row in rows if row["row_kind"] == "priority"]


def test_1_receipts_add_up_to_claim_request(bundle: Bundle) -> None:
    for claim in bundle.table("claims"):
        own = [r for r in bundle.table("receipts") if r["claim_id"] == claim["claim_id"]]
        assert total(own, "project_related") == claim["requested"]


def test_2_recognised_is_project_related_minus_reduction(bundle: Bundle) -> None:
    for receipt in bundle.table("receipts"):
        assert amount(receipt, "recognised") == amount(receipt, "project_related") - amount(
            receipt, "reduction"
        )
    for claim in bundle.table("claims"):
        own = [r for r in bundle.table("receipts") if r["claim_id"] == claim["claim_id"]]
        assert total(own, "recognised") == claim["eligible"]
        assert claim["eligible"] == amount(claim, "requested") - amount(claim, "reductions")


def test_3_claims_stay_within_approved_amount(bundle: Bundle) -> None:
    for operation in bundle.table("operations"):
        own = [c for c in bundle.table("claims") if c["operation_id"] == operation["operation_id"]]
        assert total(own, "eligible") <= amount(operation, "eligible_approved")
        sources = ("eu_funds", "national_public", "national_private")
        assert sum(amount(operation, key) for key in sources) == operation["eligible_approved"]


def test_4_payment_application_is_sum_of_claims_and_cumulative(bundle: Bundle) -> None:
    withdrawals = [c for c in bundle.table("corrections") if c["kind"] == "Herausnahme"]
    last: dict[object, Decimal] = {}
    for row in _priority(bundle.table("payment_applications")):

        def booked(item: Row, row: Row = row) -> bool:
            number = item["application_number"]
            assert isinstance(number, int) and isinstance(row["number"], int)
            return item["priority"] == row["priority"] and 0 < number <= row["number"]

        claims = total([c for c in bundle.table("claims") if booked(c)], "eligible")
        withdrawn = total([w for w in withdrawals if booked(w)], "amount")
        cumulative = row["eligible_cumulative"]
        assert isinstance(cumulative, Decimal)
        assert cumulative == claims - withdrawn
        assert cumulative >= last.get(row["priority"], ZERO)
        last[row["priority"]] = cumulative


def test_5_population_equals_final_payment_application(bundle: Bundle) -> None:
    final = [r for r in _priority(bundle.table("payment_applications")) if r["final"]]
    assert total(bundle.table("population"), "certified") == total(final, "eligible_cumulative")
    assert total(bundle.table("population"), "certified_public") == total(
        final, "public_cumulative"
    )


def test_6_annex4_difference_is_sum_of_deductions(bundle: Bundle) -> None:
    deductions = [c for c in bundle.table("corrections") if c["kind"] == "unmittelbarer Abzug"]
    annex1 = {row["priority"]: row for row in bundle.table("accounts_annex1")}
    final = {
        r["priority"]: r for r in _priority(bundle.table("payment_applications")) if r["final"]
    }
    for row in _priority(bundle.table("accounts_annex4")):
        own = [d for d in deductions if d["priority"] == row["priority"]]
        assert row["declared"] == final[row["priority"]]["eligible_cumulative"]
        difference = amount(row, "declared") - amount(row, "accounts")
        assert row["difference"] == difference == total(own, "amount")
        assert row["difference_public"] == amount(row, "declared_public") - amount(
            row, "accounts_public"
        )
        assert annex1[row["priority"]]["eligible"] == row["accounts"]
        assert (row["remarks"] is None) == (row["difference"] == ZERO)


def test_7_annex2_is_sum_of_withdrawals_split_by_year(bundle: Bundle) -> None:
    withdrawals = [c for c in bundle.table("corrections") if c["kind"] == "Herausnahme"]
    annex2 = bundle.table("accounts_annex2")
    for row in _priority(annex2):
        own = [w for w in withdrawals if w["priority"] == row["priority"]]
        assert row["withdrawn"] == total(own, "amount")
    years = [row for row in annex2 if row["row_kind"] == "year"]
    assert total(years, "withdrawn") == total(withdrawals, "amount")
    for row in years:
        own = [w for w in withdrawals if w["declaration_year"] == row["declaration_year"]]
        assert row["withdrawn"] == total(own, "amount")


def test_8_public_contribution_is_share_on_every_level(bundle: Bundle) -> None:
    rate = bundle.config.public_share
    for claim in bundle.table("claims"):
        assert claim["public"] == share(amount(claim, "eligible"), rate)
    for row in _priority(bundle.table("payment_applications")):
        rest = amount(row, "public_cumulative") - share(amount(row, "eligible_cumulative"), rate)
        assert row["rounding_difference"] == rest
        assert abs(rest) <= Decimal("0.01") * (len(bundle.table("claims")) + 60)


def test_run_checks_reports_all_eight_as_passed(bundle: Bundle) -> None:
    outcomes = run_checks(bundle)
    assert [outcome.number for outcome in outcomes] == list(range(1, 9))
    assert all(outcome.passed for outcome in outcomes), [o for o in outcomes if not o.passed]
