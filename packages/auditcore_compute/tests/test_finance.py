"""Interest and quotas: cent-exact against the Fraction reference, bit-identical engines."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from fractions import Fraction

import _reference as ref
import numpy as np
import pytest
from conftest import bits, both_paths
from hypothesis import given, settings
from hypothesis import strategies as st

from auditcore_compute import finance
from auditcore_compute._intmath import civil_from_days, days_from_civil
from auditcore_compute.finance import (
    CONVENTIONS,
    QUOTA_ABOVE_MAXIMUM,
    QUOTA_BELOW_MINIMUM,
    QUOTA_OK,
    QUOTA_UNDEFINED,
    RateTable,
    apply_reduction,
    check_quota,
    cofinancing,
    interest_cents,
    interest_cents_batch,
    percent,
    rate,
    rate_table,
    share_cents,
)

# Synthetic table (not the official base rate): changes half-yearly, one negative value.
TABLE_ROWS = [
    (dt.date(2019, 1, 1), Decimal("-0.88")),
    (dt.date(2019, 7, 1), Decimal("-0.88")),
    (dt.date(2020, 1, 1), Decimal("-0.88")),
    (dt.date(2023, 1, 1), Decimal("1.62")),
    (dt.date(2023, 7, 1), Decimal("3.12")),
    (dt.date(2024, 1, 1), Decimal("3.62")),
]
BASE = rate_table(TABLE_ROWS)
SURCHARGED = BASE.plus_points(5)
SURCHARGED_ROWS = [(day, value + 5) for day, value in TABLE_ROWS]

dates = st.dates(min_value=dt.date(2019, 1, 1), max_value=dt.date(2032, 12, 31))
cents = st.integers(min_value=-(10**12), max_value=10**12)
conventions = st.sampled_from(sorted(CONVENTIONS))


def test_reference_example_act_360() -> None:
    # 100.000 € vom 15.03.2022 bis 29.02.2024: 292 Tage zu 4,12 %, 181 zu 6,62 %,
    # 184 zu 8,12 % und 59 zu 8,62 % (Basiszins der Tabelle plus 5 Prozentpunkte).
    result = interest_cents(
        10_000_000, dt.date(2022, 3, 15), dt.date(2024, 2, 29), SURCHARGED, "act/360"
    )
    expected = (
        Fraction(10_000_000)
        * (
            292 * Fraction("0.0412")
            + 181 * Fraction("0.0662")
            + 184 * Fraction("0.0812")
            + 59 * Fraction("0.0862")
        )
        / 360
    )
    assert result == ref.round_half_up(expected) == 1_223_311


@pytest.mark.parametrize("convention", sorted(CONVENTIONS))
@pytest.mark.parametrize(
    ("begin", "end"),
    [
        (dt.date(2023, 12, 31), dt.date(2024, 3, 1)),  # Schaltjahr
        (dt.date(2024, 2, 29), dt.date(2025, 2, 28)),  # vom 29.02. aus
        (dt.date(2023, 1, 31), dt.date(2023, 2, 28)),  # Monatsende Februar als Ende
        (dt.date(2023, 2, 28), dt.date(2023, 3, 31)),  # Monatsende Februar als Beginn
        (dt.date(2023, 3, 31), dt.date(2023, 5, 31)),  # 31. auf 31.
        (dt.date(2023, 6, 30), dt.date(2024, 2, 29)),  # Satzwechsel, Schalttag als Ende
        (dt.date(2023, 5, 5), dt.date(2023, 5, 5)),  # leerer Zeitraum
    ],
)
def test_edge_dates_match_reference(convention: str, begin: dt.date, end: dt.date) -> None:
    for principal in (1_234_567, -98_765, 1):
        got = interest_cents(principal, begin, end, SURCHARGED, convention)
        assert got == ref.interest(principal, begin, end, SURCHARGED_ROWS, convention)


def test_scaled_days_public_helper() -> None:
    start = (dt.date(2024, 1, 1) - dt.date(1970, 1, 1)).days
    assert finance.scaled_days(start, start, 2, True) == 0
    assert finance.scaled_days(start, start + 366, 2, True) == 366 * 365  # 1 Jahr = 133590
    assert finance.scaled_days(start, start + 10, 0, True) == 10


def test_thirty_e_conventions_differ_only_where_isda_says() -> None:
    begin, end = dt.date(2023, 2, 28), dt.date(2023, 8, 31)
    assert ref.year_fraction(begin, end, "30e/360", True) == Fraction(182, 360)
    assert ref.year_fraction(begin, end, "30e/360-isda", True) == Fraction(180, 360)
    # Termination date at the end of February keeps its actual day under § 4.16(h).
    feb = ref.year_fraction(dt.date(2023, 1, 31), dt.date(2023, 2, 28), "30e/360-isda", True)
    assert feb == Fraction(28, 360)
    table = rate_table([(dt.date(2023, 1, 1), "10")])
    assert interest_cents(36_000, begin, end, table, "30e/360") == 1820
    assert interest_cents(36_000, begin, end, table, "30e/360-isda") == 1800


@settings(max_examples=150, deadline=None)
@given(principal=cents, first=dates, second=dates, convention=conventions)
def test_interest_matches_reference(
    principal: int, first: dt.date, second: dt.date, convention: str
) -> None:
    begin, end = min(first, second), max(first, second)
    got = interest_cents(principal, begin, end, SURCHARGED, convention)
    assert got == ref.interest(principal, begin, end, SURCHARGED_ROWS, convention)


@settings(max_examples=40, deadline=None)
@given(
    rows=st.lists(st.tuples(cents, dates, dates), min_size=0, max_size=40),
    convention=conventions,
)
def test_interest_batch_bit_identical(
    rows: list[tuple[int, dt.date, dt.date]], convention: str
) -> None:
    principals = [r[0] for r in rows]
    begins = [min(r[1], r[2]) for r in rows]
    ends = [max(r[1], r[2]) for r in rows]
    jit, python = both_paths(
        lambda: interest_cents_batch(principals, begins, ends, SURCHARGED, convention)
    )
    assert bits(jit) == bits(python)
    assert jit.tolist() == [
        ref.interest(p, b, e, SURCHARGED_ROWS, convention)
        for p, b, e in zip(principals, begins, ends, strict=True)
    ]


@given(st.integers(min_value=-200_000, max_value=200_000))
def test_day_numbers_roundtrip(days: int) -> None:
    year, month, day = civil_from_days(days)
    assert dt.date(1970, 1, 1) + dt.timedelta(days=days) == dt.date(year, month, day)
    assert days_from_civil(year, month, day) == days


def test_interest_input_errors() -> None:
    day = dt.date(2023, 1, 1)
    with pytest.raises(ValueError, match="Zinsmethode"):
        interest_cents(1, day, day, BASE, "act/364")
    with pytest.raises(ValueError, match="vor dem Zinsbeginn"):
        interest_cents(1, day, dt.date(2022, 12, 31), BASE, "act/360")
    with pytest.raises(ValueError, match="ersten Tabelleneintrag"):
        interest_cents(1, dt.date(2018, 1, 1), day, BASE, "act/360")
    with pytest.raises(ValueError, match="1900"):
        interest_cents(1, day, dt.date(2200, 1, 1), BASE, "act/360")
    with pytest.raises(ValueError, match="gleich lang"):
        interest_cents_batch([1, 2], [day], [day], BASE, "act/360")
    with pytest.raises(ValueError, match="10 Mrd"):
        interest_cents(10**12 + 1, day, day, BASE, "act/360")
    assert interest_cents_batch([], [], [], BASE, "act/360").shape == (0,)


def test_rate_table_validation() -> None:
    with pytest.raises(ValueError, match="leer"):
        RateTable(())
    with pytest.raises(ValueError, match="aufsteigend"):
        rate_table([(dt.date(2024, 1, 1), "1"), (dt.date(2023, 1, 1), "1")])
    with pytest.raises(ValueError, match="Basispunkte"):
        rate_table([(dt.date(2024, 1, 1), "1.005")])
    with pytest.raises(ValueError, match="Basispunkte"):
        rate_table([(dt.date(2024, 1, 1), "100.01")])
    with pytest.raises(ValueError, match="gültiger"):
        rate_table([(dt.date(2024, 1, 1), "abc")])
    with pytest.raises(ValueError, match="endlicher"):
        rate_table([(dt.date(2024, 1, 1), Decimal("NaN"))])
    with pytest.raises(TypeError):
        rate_table([(dt.date(2024, 1, 1), 1.5)])  # type: ignore[list-item]
    assert BASE.plus_points("5").periods[-1].rate_percent == Decimal("8.62")


rates = st.fractions(min_value=0, max_value=1, max_denominator=10**6)


@given(amounts=st.lists(cents, max_size=60), value=rates)
def test_shares_match_reference_and_add_up(amounts: list[int], value: Fraction) -> None:
    jit, python = both_paths(lambda: share_cents(amounts, value))
    assert bits(jit) == bits(python)
    assert jit.tolist() == [ref.share(a, value) for a in amounts]
    split = cofinancing(amounts, value)
    assert (split.share + split.rest).tolist() == amounts


@given(data=st.lists(st.tuples(cents, rates), max_size=60))
def test_per_row_rates(data: list[tuple[int, Fraction]]) -> None:
    amounts = [a for a, _ in data]
    values = [r for _, r in data]
    split = apply_reduction(amounts, values)
    assert split.share.tolist() == [ref.share(a, r) for a, r in data]


def test_half_up_rounding_cases() -> None:
    assert share_cents([5, -5, 15, 1], "0.5").tolist() == [3, -3, 8, 1]
    assert share_cents([333], percent("40")).tolist() == [133]
    assert cofinancing([10_000], Decimal("0.4")).rest.tolist() == [6000]
    assert share_cents([100], 0.1).tolist() == [10]


def test_rate_validation() -> None:
    assert rate("0.25") == Fraction(1, 4)
    assert percent("12.5") == Fraction(1, 8)
    for bad in ("1.1", "-0.1"):
        with pytest.raises(ValueError, match="zwischen 0 und 1"):
            rate(bad)
    assert rate(Fraction(1, 3)) == Fraction(1, 3)
    with pytest.raises(ValueError, match="Nenner"):
        rate(Fraction(1, 10**6 + 1))
    with pytest.raises(TypeError):
        rate(True)
    with pytest.raises(ValueError, match="genau eine Quote"):
        share_cents([1, 2], ["0.1"])


parts = st.integers(min_value=-(10**12), max_value=10**12)


@settings(max_examples=150)
@given(
    rows=st.lists(st.tuples(parts, parts), max_size=50),
    minimum=st.none() | rates,
    maximum=st.none() | rates,
)
def test_quota_check_matches_reference(
    rows: list[tuple[int, int]], minimum: Fraction | None, maximum: Fraction | None
) -> None:
    part_values = [p for p, _ in rows]
    totals = [t for _, t in rows]
    jit, python = both_paths(
        lambda: check_quota(part_values, totals, minimum=minimum, maximum=maximum)
    )
    assert bits(jit.status) == bits(python.status)
    assert bits(jit.basis_points) == bits(python.basis_points)
    expected = [ref.quota_status(p, t, minimum, maximum) for p, t in rows]
    assert list(zip(jit.basis_points.tolist(), jit.status.tolist(), strict=True)) == expected


def test_quota_threshold_is_exact_not_rounded() -> None:
    # 50,004 % rounds to 5000 basis points but still exceeds a 50 % maximum.
    check = check_quota([50_004], [100_000], maximum="0.5", minimum="0.1")
    assert check.basis_points.tolist() == [5000]
    assert check.status.tolist() == [QUOTA_ABOVE_MAXIMUM]
    low = check_quota([1, 50, 7], [100, 100, 0], minimum="0.02")
    assert low.status.tolist() == [QUOTA_BELOW_MINIMUM, QUOTA_OK, QUOTA_UNDEFINED]
    with pytest.raises(ValueError, match="gleich lang"):
        check_quota([1], [1, 2])


def test_finance_exports_are_complete() -> None:
    assert set(finance.__all__) <= set(dir(finance))
    assert np.dtype(share_cents([1], "1").dtype) == np.int64
