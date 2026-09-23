"""Corrected cumulation contract; every difference to the source is shown next to it."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from auditcore_funding_sources import cumulation as cu
from auditcore_funding_sources.profiles import load_profile

DAY = date(2026, 9, 1)


def aw(
    day: str | None,
    amount: object,
    kind: str | None = "GENERAL",
    ref: str = "B-1",
    number: str = "DM-1",
) -> dict[str, object]:
    return {
        "grantingDate": day,
        "amountEur": amount,
        "deMinimisType": kind,
        "beneficiaryReferenceNumber": ref,
        "referenceNumber": number,
    }


def test_profile_is_versioned_source_bound_and_review_required() -> None:
    profile = load_profile("designer.deminimis.cumulation")
    assert profile["status"] == "REVIEW_REQUIRED"
    assert profile["ceiling_eur"] == "300000" and profile["window"]["years"] == 3
    assert profile["valid_from"] is None and "2023/2831" in profile["legal_basis"]
    assert profile["source"]["commit"] == "030a71e083ef0feddc14545b095a4945bc0bbd7a"


def test_window_boundaries_inclusive_and_leap_day() -> None:
    assert cu.window_start(date(2024, 2, 29), 3) == date(2021, 2, 28)
    result = cu.calculate(
        [
            aw("2023-09-01", 1),
            aw("2023-08-31", 2, number="DM-2"),
            aw("2026-09-01", 4, number="DM-3"),
            aw("2026-09-02", 8, number="DM-4"),
        ],
        reference_date=DAY,
    )
    assert result.sum_considered_eur == Decimal("5")
    assert [a.status for a in result.awards] == ["considered", "excluded", "considered", "excluded"]


def test_comparison_is_arithmetic_only_and_never_a_decision() -> None:
    result = cu.calculate(
        [aw("2025-01-01", 200000), aw("2026-01-01", 150000, number="DM-2")],
        reference_date=DAY,
        undertaking_references=["B-1"],
    )
    assert result.ceiling_eur == Decimal("300000")
    assert result.arithmetic_difference_eur == Decimal("-50000") and result.exceeds_ceiling is True
    data = result.to_dict()
    assert data["decision"] is None and "verbleibend" not in str(data)
    assert any("keine verfügbare Förderreserve" in n for n in data["notices"])


def test_reference_date_must_be_explicit() -> None:
    with pytest.raises(TypeError):
        cu.calculate([], reference_date=None)  # type: ignore[arg-type]


def test_negative_amount_withholds_comparison_legacy_subtracts_it() -> None:
    """FS-D05: the source subtracted negative amounts from the sum."""
    records = [aw("2025-01-01", -500), aw("2025-02-01", 1000, number="DM-2")]
    legacy = cu.legacy_cumulation(records, reference_date=DAY)
    assert legacy["summe_im_fenster_eur"] == 500.0 and legacy["hoechstbetrag_eur"] == 300000.0
    result = cu.calculate(records, reference_date=DAY)
    assert result.sum_considered_eur == Decimal("1000") and result.ceiling_eur is None
    assert result.awards[0].status == "unclear" and not result.complete


def test_undertaking_is_explicit() -> None:
    """FS-D06: the source summed whatever records it received for one reference."""
    records = [aw("2025-01-01", 1000, ref="B-1"), aw("2025-01-02", 2000, ref="B-2", number="DM-2")]
    result = cu.calculate(records, reference_date=DAY, undertaking_references=["B-1"])
    assert result.sum_considered_eur == Decimal("1000")
    assert result.awards[1].status == "excluded"
    implicit = cu.calculate(records, reference_date=DAY)
    assert implicit.sum_considered_eur == Decimal("3000")
    assert any("vom Aufrufer vorausgesetzt" in n for n in implicit.notices)


def test_missing_values_and_other_regimes_withhold_comparison() -> None:
    for records in (
        [aw(None, 1000)],
        [aw("2025-01-01", None)],
        [aw("2025-01-01", "x")],
        [aw("2025-01-01", 1000, "AGRI")],
        [aw("2025-01-01", 1000, None)],
        [],
    ):
        result = cu.calculate(records, reference_date=DAY)
        assert result.ceiling_eur is None and result.exceeds_ceiling is None
        assert result.reasons_without_comparison


def test_legacy_and_new_agree_on_ordinary_general_case() -> None:
    records = [aw("2024-01-01", 100000), aw("2026-08-31", "150000.25", number="DM-2")]
    legacy = cu.legacy_cumulation(records, reference_date=DAY)
    result = cu.calculate(records, reference_date=DAY)
    assert Decimal(str(legacy["summe_im_fenster_eur"])) == result.sum_considered_eur
    assert Decimal(str(legacy["rechnerische_differenz_eur"])) == result.arithmetic_difference_eur
