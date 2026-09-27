"""Invariants of docs/spezifikation.md as Hypothesis properties (I1–I12)."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from auditcore_price_analysis import (
    GREEN,
    RED,
    YELLOW,
    PriceAnalysisError,
    ReleaseStatus,
    Rounding,
    Tariff,
    Tier,
    calculate,
    delta_pct,
    group_statistics,
    legacy_parse_decimal,
    load_calculation_profile,
    load_comparison_profile,
    parse_decimal,
    select_tariff,
    tiered_amount,
    traffic_light,
)

WATER = load_calculation_profile("regulierung.hpp.wasser", "2026.09.2")
HEAT = load_calculation_profile("regulierung.hpp.nahwaerme", "2026.09.2")
COMPARISON = load_comparison_profile("regulierung.hpp.vergleich", "2026.09.2")
EXAMPLES = settings(max_examples=150, deadline=None)

MONEY = st.decimals(min_value=0, max_value=10_000, places=4, allow_nan=False)
SIGNED = st.decimals(min_value=-10_000, max_value=10_000, places=4, allow_nan=False)
POSITIVE = st.decimals(min_value=Decimal("0.01"), max_value=10_000, places=2, allow_nan=False)
SEVERITY = {GREEN: 0, YELLOW: 1, RED: 2}


def _code(function, *args, **kwargs) -> str | None:
    try:
        function(*args, **kwargs)
    except PriceAnalysisError as exc:
        return exc.code
    return None


@EXAMPLES
@given(SIGNED | st.integers(-(10**12), 10**12).map(Decimal))
def test_i1_numbers_are_read_exactly(value: Decimal) -> None:
    """I1: Decimal, int and plain point text keep their exact value."""
    assert parse_decimal(value, field="x") == value
    assert parse_decimal(format(value, "f"), field="x") == value
    if value == value.to_integral_value():
        assert parse_decimal(int(value), field="x") == value


@EXAMPLES
@given(st.integers(0, 10**9), st.integers(0, 99))
def test_i2_german_notation_is_read_and_ambiguity_rejected(whole: int, cents: int) -> None:
    """I2: „1.234,56“ and „1234,56“ are exact; three digits after a single comma are not guessed."""
    expected = Decimal(whole) + Decimal(cents) / 100
    grouped = f"{whole:,}".replace(",", ".")
    assert parse_decimal(f"{grouped},{cents:02d}", field="x") == expected
    assert parse_decimal(f"{whole},{cents:02d} €", field="x") == expected
    if 1 <= whole <= 999:
        assert _code(parse_decimal, f"{whole},{cents:02d}5", field="x") in {
            "ambiguous_number",
            "invalid_number",
        }


@EXAMPLES
@given(st.sampled_from([None, True, False, float("nan"), float("inf"), "1e2", "", "x"]))
def test_i3_missing_is_never_zero(value: object) -> None:
    """I3: None is missing_value; booleans, non-finite values and exponents are rejected."""
    code = _code(parse_decimal, value, field="x")
    assert code == ("missing_value" if value is None else "invalid_number")


@EXAMPLES
@given(
    SIGNED,
    st.sampled_from(["0.01", "0.1", "1"]),
    st.sampled_from(["ROUND_HALF_UP", "ROUND_HALF_EVEN"]),
)
def test_i4_rounding_is_idempotent_and_within_half_a_step(
    value: Decimal, places: str, mode: str
) -> None:
    """I4: a rounding rule moves a value by at most half a step and only once."""
    rule = Rounding(Decimal(places), mode)
    rounded = rule.apply(value)
    assert abs(rounded - value) <= Decimal(places) / 2
    assert rule.apply(rounded) == rounded


TIER_LISTS = st.lists(
    st.tuples(st.integers(1, 500), st.decimals(0, 10, places=2)), min_size=1, max_size=4
).map(
    lambda raw: tuple(
        Tier(Decimal(limit), price)
        for limit, price in sorted({limit: price for limit, price in raw}.items())
    )
)


@EXAMPLES
@given(TIER_LISTS, MONEY, MONEY)
def test_i5_tiers_bill_every_unit_once_and_monotonically(tiers, a: Decimal, b: Decimal) -> None:
    """I5: with open_last all quantity is billed exactly once; more quantity never costs less."""
    low, high = sorted((a, b))
    amount_low, uses, _ = tiered_amount(tiers, low, open_last=True)
    amount_high, _, _ = tiered_amount(tiers, high, open_last=True)
    assert sum((u.quantity for u in uses), Decimal(0)) == low
    assert amount_low == sum((u.quantity * u.price for u in uses), Decimal(0))
    assert amount_low <= amount_high
    if high > tiers[-1].limit:
        assert _code(tiered_amount, tiers, high, open_last=False) == "beyond_last_tier"


COMPONENTS = st.fixed_dictionaries(
    {
        "grundpreis_eur_monat": st.none() | MONEY,
        "arbeitspreis_eur_m3": st.none() | MONEY,
        "verrechnungspreis_eur_monat": st.none() | MONEY,
        "wasserentnahmeentgelt_eur_m3": st.none() | MONEY,
    }
)


@EXAMPLES
@given(COMPONENTS, MONEY, st.sampled_from(list(ReleaseStatus)))
def test_i6_total_is_the_exact_sum_and_missing_is_a_lower_bound(
    components, m3: Decimal, release: ReleaseStatus
) -> None:
    """I6: total = Σ line amounts; missing parts mark a lower bound; comparable ⇔ no reason."""
    tariff = Tariff.from_mapping(components, WATER, release=release)
    result = calculate(tariff, WATER, consumption={"q3": 4, "m3": m3}, stichtag="2026-01-01")
    lines = [line.amount for line in result.lines if line.amount is not None]
    assert result.total == sum(lines, Decimal(0))
    assert result.total_rounded == WATER.money.apply(result.total)
    missing = [k for k, v in components.items() if v is None]
    assert result.total_is_lower_bound == bool(missing)
    assert set(result.missing_required) | set(result.missing_optional) == set(missing)
    assert result.comparable == (not result.not_comparable_reasons)
    if release is not ReleaseStatus.FREIGEGEBEN:
        assert not result.comparable
    if m3 == 0:
        assert result.mixed_price is None


@EXAMPLES
@given(SIGNED, SIGNED)
def test_i7_deviation_has_the_sign_of_the_difference(value: Decimal, reference: Decimal) -> None:
    """I7: no deviation without a positive reference; else its sign follows value − reference."""
    delta = delta_pct(value, reference, COMPARISON)
    if reference <= 0:
        assert delta is None
        return
    assert delta is not None
    if value == reference:
        assert delta == 0
    elif value > reference:
        assert delta >= 0
    else:
        assert delta <= 0


@EXAMPLES
@given(SIGNED, SIGNED, SIGNED)
def test_i8_traffic_light_is_monotone(a: Decimal, b: Decimal, median: Decimal) -> None:
    """I8: a higher value never gets a milder light; no light without a positive median."""
    low, high = sorted((a, b))
    first, second = traffic_light(low, median, COMPARISON), traffic_light(high, median, COMPARISON)
    if median <= 0:
        assert first is None and second is None
    else:
        assert SEVERITY[first] <= SEVERITY[second]


@EXAMPLES
@given(st.lists(SIGNED, max_size=12), st.randoms(use_true_random=False))
def test_i9_group_statistics_are_ordered_and_order_free(values, rnd) -> None:
    """I9: min ≤ median, mean ≤ max, stddev ≥ 0, independent of input order; empty → None."""
    stats = group_statistics(values, COMPARISON)
    shuffled = list(values)
    rnd.shuffle(shuffled)
    assert group_statistics(shuffled, COMPARISON) == stats
    if not values:
        assert stats.count == 0 and stats.median is None and stats.mean is None
        return
    assert stats.minimum <= stats.median <= stats.maximum
    assert stats.minimum <= stats.mean <= stats.maximum
    assert stats.stddev is None or stats.stddev >= 0


CANDIDATE = st.tuples(
    st.integers(-400, 400),
    st.sampled_from(list(ReleaseStatus)),
    st.booleans(),
    st.integers(0, 3),
)


@EXAMPLES
@given(st.lists(CANDIDATE, max_size=6), st.randoms(use_true_random=False))
def test_i10_selection_is_deterministic_and_only_picks_eligible(raw, rnd) -> None:
    """I10: the chosen tariff is eligible on the day and independent of input order."""
    day = date(2026, 1, 1)
    tariffs = [
        Tariff(
            kind="wasser",
            components={},
            valid_from=day + timedelta(days=offset),
            release=release,
            standard_variant=standard,
            variant_id=variant,
            row_id=row,
        )
        for row, (offset, release, standard, variant) in enumerate(raw)
    ]
    chosen = select_tariff(tariffs, stichtag=day, profile=COMPARISON)
    shuffled = list(tariffs)
    rnd.shuffle(shuffled)
    again = select_tariff(shuffled, stichtag=day, profile=COMPARISON)
    assert again.tariff == chosen.tariff and again.datenstatus == chosen.datenstatus
    assert len(chosen.excluded) <= len(tariffs)
    if chosen.tariff is not None:
        assert chosen.tariff.valid_from is not None and chosen.tariff.valid_from <= day
        if COMPARISON.only_released:
            assert chosen.tariff.release is ReleaseStatus.FREIGEGEBEN


@EXAMPLES
@given(SIGNED, st.integers(0, 999), st.integers(0, 99))
def test_i11_legacy_reader_rejects_every_comma(value: Decimal, whole: int, cents: int) -> None:
    """I11: legacy_parse_decimal agrees on point text and rejects every comma."""
    text = format(value, "f")
    assert legacy_parse_decimal(text, field="x") == parse_decimal(text, field="x")
    assert _code(legacy_parse_decimal, f"{whole},{cents:02d}", field="x") == "invalid_number"


def test_heat_profile_is_loaded() -> None:
    """Both calculation profiles of the specification are packaged."""
    assert HEAT.kind == "nahwaerme" and WATER.kind == "wasser"
    with pytest.raises(PriceAnalysisError):
        load_calculation_profile("regulierung.hpp.wasser", "0000.00.0")


@EXAMPLES
@given(COMPONENTS, POSITIVE)
def test_i12_fixed_and_variable_share_differ_from_100_by_at_most_one_step(
    components, m3: Decimal
) -> None:
    """I12: both shares are rounded separately, so their sum may miss 100 by one step."""
    tariff = Tariff.from_mapping(components, WATER, release=ReleaseStatus.FREIGEGEBEN)
    result = calculate(tariff, WATER, consumption={"q3": 4, "m3": m3}, stichtag="2026-01-01")
    if result.total > 0:
        total = result.fixed_share_pct + result.variable_share_pct
        assert abs(total - 100) <= WATER.percent.places
    else:
        assert result.fixed_share_pct is None and result.variable_share_pct is None


def test_i12_shares_can_add_up_to_100_1() -> None:
    """I12 (Befund): 33.35 % and 66.65 % round half up to 33.4 % and 66.7 %."""
    data = {
        "grundpreis_eur_monat": "6.67",
        "arbeitspreis_eur_m3": "1",
        "verrechnungspreis_eur_monat": "0",
        "wasserentnahmeentgelt_eur_m3": "0",
    }
    tariff = Tariff.from_mapping(data, WATER, release=ReleaseStatus.FREIGEGEBEN)
    result = calculate(tariff, WATER, consumption={"q3": 4, "m3": "159.96"}, stichtag="2026-01-01")
    assert (result.fixed_share_pct, result.variable_share_pct) == (Decimal("33.4"), Decimal("66.7"))
