"""Invariants of docs/spezifikation.md as Hypothesis properties (I1–I11)."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from auditcore_risk import (
    InputError,
    ProfileError,
    evaluate,
    flatten_record,
    load_profile,
    missing_columns,
    name_similarity,
)

FLOWSTAT = load_profile("audit_designer.flowstat_belegliste", "1254591156d3")
YEAR_BOUND = load_profile("riskanalysis.year_bound", "2026.09.5")
EXAMPLES = settings(max_examples=100, deadline=None)

AMOUNT = st.none() | st.integers(-5, 400).map(lambda k: k * 250.0) | st.floats(0, 300_000)
DAY = st.none() | st.dates().map(lambda d: d.isoformat())
FLOWSTAT_ROW = st.fixed_dictionaries(
    {
        "projektbetrag": AMOUNT,
        "vergabe": st.none() | st.sampled_from(["", "V-1", "nan"]),
        "rechnungssteller": st.sampled_from(["Alpha GmbH", "Beta KG", "Gamma AG"]),
        "rechnungsnummer": st.sampled_from(["R-1", "R-2", "R-3"]),
        "rechnungsdatum": DAY,
        "zahlungsdatum": DAY,
        "kuerzungsbetrag": st.none() | st.sampled_from([0.0, 100.0]),
        "kuerzungsgrund": st.none() | st.sampled_from(["", "Skonto"]),
        "anerkannter_betrag": AMOUNT,
        "direktvergabe": st.none() | st.sampled_from(["ja", "nein", "1"]),
    }
)
ALL_COLUMNS = [
    "projektbetrag",
    "vergabe",
    "rechnungssteller",
    "rechnungsnummer",
    "rechnungsdatum",
    "zahlungsdatum",
    "kuerzungsbetrag",
    "kuerzungsgrund",
    "anerkannter_betrag",
    "direktvergabe",
]
ROWS = st.lists(FLOWSTAT_ROW, max_size=8)


def _codes(profile) -> list[str]:
    return [rule.code for rule in profile.rules]


@EXAMPLES
@given(ROWS)
def test_i1_evaluation_is_deterministic_and_profile_bound(rows: list[dict]) -> None:
    """I1: same records and profile give the same evaluation, carrying the profile identity."""
    first = evaluate(rows, FLOWSTAT, columns=ALL_COLUMNS)
    assert first == evaluate(rows, FLOWSTAT, columns=ALL_COLUMNS)
    assert dict(first.profile) == FLOWSTAT.reference


@EXAMPLES
@given(ROWS, st.sets(st.sampled_from(ALL_COLUMNS)))
def test_i2_every_rule_is_accounted_for_and_hits_match_flags(
    rows: list[dict], dropped: set
) -> None:
    """I2: each rule is applied, skipped or dataset-wide; hits are exactly the True flags."""
    columns = [c for c in ALL_COLUMNS if c not in dropped]
    rows = [{k: v for k, v in row.items() if k in columns} for row in rows]
    result = evaluate(rows, FLOWSTAT, columns=columns)
    assert [r.index for r in result.records] == list(range(len(rows)))
    dataset_codes = {finding.code for finding in result.dataset}
    for record in result.records:
        applied = set(record.flags)
        assert applied.isdisjoint(result.skipped)
        assert applied | set(result.skipped) | dataset_codes >= set(_codes(FLOWSTAT)) - {
            r.code for r in FLOWSTAT.rules if r.scope == "dataset"
        }
        assert [h.code for h in record.hits] == [c for c, f in record.flags.items() if f is True]
        assert set(record.undetermined) == {c for c, f in record.flags.items() if f is None}


@EXAMPLES
@given(st.sets(st.sampled_from(ALL_COLUMNS)))
def test_i3_rules_are_skipped_exactly_when_columns_are_missing(dropped: set) -> None:
    """I3: a rule with when_missing_columns=skip is skipped iff a required column is absent."""
    columns = [c for c in ALL_COLUMNS if c not in dropped]
    result = evaluate([], FLOWSTAT, columns=columns)
    assert set(result.skipped) == set(missing_columns(FLOWSTAT, columns))


@EXAMPLES
@given(ROWS)
def test_i4_every_hit_is_justified(rows: list[dict]) -> None:
    """I4: every hit is a rule of the profile with reason and source origin."""
    codes = set(_codes(FLOWSTAT))
    for record in evaluate(rows, FLOWSTAT, columns=ALL_COLUMNS).records:
        for hit in record.hits:
            assert hit.code in codes
            assert hit.reason and hit.origin


def _flag(rows: list[dict], code: str, index: int = 0) -> bool | None:
    return evaluate(rows, FLOWSTAT, columns=ALL_COLUMNS).records[index].flags[code]


@EXAMPLES
@given(FLOWSTAT_ROW, st.floats(0, 300_000), st.floats(0, 300_000))
def test_i5_procurement_flag_is_monotone_in_the_amount(row: dict, a: float, b: float) -> None:
    """I5: BL_RF08 fires iff amount > 25 000 without award identifier; more never clears it."""
    low, high = sorted((a, b))
    row = {**row, "vergabe": None}
    first = _flag([{**row, "projektbetrag": low}], "BL_RF08_PROCUREMENT_MISSING")
    second = _flag([{**row, "projektbetrag": high}], "BL_RF08_PROCUREMENT_MISSING")
    assert first == (low > 25_000)
    assert not first or second


@EXAMPLES
@given(FLOWSTAT_ROW, st.integers(1, 500))
def test_i6_round_amounts_are_multiples_of_the_profile_step(row: dict, k: int) -> None:
    """I6: BL_RF01 fires for positive multiples of 1 000 and not one cent beside them."""
    assert _flag([{**row, "projektbetrag": k * 1000.0}], "BL_RF01_ROUND_AMOUNT") is True
    assert _flag([{**row, "projektbetrag": k * 1000.0 + 0.01}], "BL_RF01_ROUND_AMOUNT") is False


RECORD_LOCAL = [
    "BL_RF01_ROUND_AMOUNT",
    "BL_RF02_NEAR_THRESHOLD",
    "BL_RF03_MISSING_PAYMENT_DATE",
    "BL_RF04_PAYMENT_BEFORE_INVOICE",
    "BL_RF06_CUT_WITHOUT_REASON",
    "BL_RF07_ACCEPTED_MISMATCH",
    "BL_RF08_PROCUREMENT_MISSING",
    "BL_RF09_DIRECT_AWARD_HIGH_AMOUNT",
]


@EXAMPLES
@given(st.lists(FLOWSTAT_ROW, min_size=1, max_size=6), st.randoms(use_true_random=False))
def test_i7_record_rules_do_not_depend_on_other_records(rows: list[dict], rnd) -> None:
    """I7: record-local flags are the same alone, in the list and after reordering."""
    together = evaluate(rows, FLOWSTAT, columns=ALL_COLUMNS).records
    order = list(range(len(rows)))
    rnd.shuffle(order)
    shuffled = evaluate([rows[i] for i in order], FLOWSTAT, columns=ALL_COLUMNS).records
    for position, original in enumerate(order):
        alone = evaluate([rows[original]], FLOWSTAT, columns=ALL_COLUMNS).records[0]
        for code in RECORD_LOCAL:
            assert together[original].flags[code] == alone.flags[code]
            assert shuffled[position].flags[code] == alone.flags[code]


YB_ROW = st.fixed_dictionaries(
    {
        "bruttobetrag": st.floats(0, 200_000),
        "nettobetrag": st.none() | st.floats(0, 200_000),
        "Name": st.sampled_from(["Alpha GmbH", "Müller Bau"]),
        "zahlungsempfaenger": st.sampled_from(["Alpha GmbH", "Mueller Bau", "Omega"]),
        "Gruppennummer": st.sampled_from(["G1", "G2"]),
        "antrag": st.sampled_from(["A1", "A2"]),
        "Anzahl_Versionen": st.integers(0, 9),
        "Anzahl_ungueltige_Versionen": st.integers(0, 9),
        "rechnungsdatum_dt": st.dates().map(lambda d: d.isoformat()),
        "vergabenummer": st.none() | st.just("V-9"),
    }
)


@EXAMPLES
@given(st.lists(YB_ROW, min_size=1, max_size=5), st.booleans())
def test_i8_missing_net_amount_is_undetermined_not_clear(
    rows: list[dict], drop_column: bool
) -> None:
    """I8: without a net amount every record the amount would decide is undetermined (None).

    RF02 always depends on the amount; RF08 only when no award identifier is given.
    """
    if drop_column:
        rows = [{k: v for k, v in row.items() if k != "nettobetrag"} for row in rows]
    result = evaluate(rows, YEAR_BOUND)
    for row, record in zip(rows, result.records, strict=True):
        if row.get("nettobetrag") is None:
            assert record.flags["RF02"] is None and "RF02" in record.undetermined
            if row["vergabenummer"] is None:
                assert record.flags["RF08"] is None and "RF08" in record.undetermined
            else:
                assert record.flags["RF08"] is False


@EXAMPLES
@given(
    st.dictionaries(
        st.text(max_size=4),
        st.none() | st.integers() | st.dictionaries(st.text(max_size=3), st.integers(), max_size=3),
        max_size=5,
    )
)
def test_i9_flatten_record_is_one_level(record: dict) -> None:
    """I9: nested mappings become parent.child fields; other values stay under their key."""
    flat = flatten_record(record)
    for key, value in record.items():
        if isinstance(value, dict):
            for child, inner in value.items():
                assert flat[f"{key}.{child}"] == inner
        else:
            assert flat[key] == value


@EXAMPLES
@given(st.sampled_from(["abc", True, [1], "12,5 EUR"]))
def test_i10_invalid_input_is_an_error_not_a_guess(value: object) -> None:
    """I10: no profile → ProfileError; non-mapping rows, non-numeric amounts → InputError."""
    with pytest.raises(ProfileError):
        evaluate([], "riskanalysis.year_bound")  # type: ignore[arg-type]
    with pytest.raises(InputError):
        evaluate([["x"]], FLOWSTAT)  # type: ignore[list-item]
    row = {
        "bruttobetrag": value,
        "nettobetrag": 1.0,
        "Name": "A",
        "zahlungsempfaenger": "B",
        "Gruppennummer": "G",
        "antrag": "A",
        "Anzahl_Versionen": 0,
        "Anzahl_ungueltige_Versionen": 0,
    }
    with pytest.raises(InputError):
        evaluate([row], YEAR_BOUND)


RF09 = next(rule for rule in YEAR_BOUND.rules if rule.code == "RF09")


@EXAMPLES
@given(st.text(alphabet="abcdefgh üö", max_size=16), st.text(alphabet="abcdefgh üö", max_size=16))
def test_i11_name_similarity_is_bounded_symmetric_and_reflexive(left: str, right: str) -> None:
    """I11: RF09 similarity lies in 0–1, is symmetric and 1 for a name of sufficient length."""
    value = name_similarity(RF09, left, right)
    assert 0 <= value <= 1
    assert value == name_similarity(RF09, right, left)
    if len(left.replace(" ", "")) >= 8:
        assert name_similarity(RF09, left, left) == 1
