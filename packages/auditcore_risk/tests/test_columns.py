"""Column path: ``evaluate_columns`` decides exactly like the record path ``evaluate``."""

from __future__ import annotations

import json
import math
from datetime import datetime
from importlib.resources import files
from typing import Any

import numpy as np
import pandas as pd
import pytest
from conftest import decode, fixture
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from auditcore_risk import (
    Evaluation,
    InputError,
    ProfileError,
    column_kinds,
    evaluate,
    load_profile,
    profile_from_dict,
)
from auditcore_risk.columns import RECORDS, VECTORISED, ColumnEvaluation, evaluate_columns
from auditcore_risk.frame import evaluate_frame, evaluate_frame_columns

FLOWSTAT = load_profile("audit_designer.flowstat_belegliste", "1254591156d3")
CENTS = load_profile("audit_designer.flowstat_belegliste", "2026.10.1")
BOTH = (FLOWSTAT, CENTS)
RISKANALYSIS = load_profile("riskanalysis.legacy", "b5c523bf7eaa")
YEAR_BOUND = load_profile("riskanalysis.year_bound", "2026.09.5")
FS_CASES = fixture("flowstat_observed.json")["cases"]
RA_CASES = fixture("riskanalysis_observed.json")["cases"]
FS_COLUMNS = FS_CASES[0]["columns"]


def _same_value(left: object, right: object) -> bool:
    if isinstance(left, float) and isinstance(right, float) and math.isnan(left):
        return math.isnan(right)
    return left == right


def assert_same(columns: ColumnEvaluation, records: Evaluation) -> None:
    assert columns.size == len(records.records)
    assert dict(columns.profile) == dict(records.profile)
    assert dict(columns.skipped) == dict(records.skipped)
    for code in columns.flags:
        assert columns.record_flags(code) == [r.flags[code] for r in records.records], code
    for name, values in columns.values.items():
        expected = [r.values[name] for r in records.records]
        assert all(_same_value(a, b) for a, b in zip(values.tolist(), expected, strict=True))
    assert [dict(s) for s in columns.summary] == [dict(s) for s in records.summary]
    assert len(columns.dataset) == len(records.dataset)
    for left, right in zip(columns.dataset, records.dataset, strict=True):
        assert (left.code, left.triggered, left.reason) == (
            right.code,
            right.triggered,
            right.reason,
        )
        assert _same_value(left.value, right.value)
        assert dict(left.evidence) == dict(right.evidence)


def _frame(case: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame([decode(r) for r in case["rows"]], columns=case["columns"])


@pytest.mark.parametrize("case", FS_CASES, ids=[c["name"] for c in FS_CASES])
def test_flowstat_frames_match_the_record_path(case: dict[str, Any]) -> None:
    frame = _frame(case)
    rows = [decode(r) for r in case["rows"]]
    lists = {c: [row.get(c) for row in rows] for c in case["columns"]}
    for profile in BOTH:
        assert_same(evaluate_frame_columns(frame, profile), evaluate_frame(frame, profile))
        expected = evaluate(rows, profile, columns=case["columns"])
        assert_same(evaluate_columns(lists, profile), expected)


@pytest.mark.parametrize("case", RA_CASES, ids=[c["name"] for c in RA_CASES])
def test_riskanalysis_frames_match_the_record_path(case: dict[str, Any]) -> None:
    frame = _frame(case)
    assert_same(evaluate_frame_columns(frame, RISKANALYSIS), evaluate_frame(frame, RISKANALYSIS))
    rows = [decode(r) for r in case["rows"]]
    lists = {c: [row.get(c) for row in rows] for c in case["columns"]}
    expected = evaluate(rows, RISKANALYSIS, columns=case["columns"])
    assert_same(evaluate_columns(lists, RISKANALYSIS), expected)


AMOUNT = st.one_of(
    st.none(),
    st.just(math.nan),
    st.integers(-3, 3).map(lambda k: k * 1000.0),
    st.integers(-(10**8), 10**8).map(lambda k: k / 100),
    st.integers(-(10**6), 10**6).map(lambda k: k / 1000),
    st.sampled_from([0.0, 0.01, 22_500.0, 24_999.99, 25_000.005, 2.675, 1e10, 1.00000001e10]),
    st.sampled_from([math.inf, -math.inf, 1e300]),
)
TEXT_AMOUNT = st.one_of(AMOUNT, st.sampled_from(["6,0", " 12.5 ", "inf", "abc", "1e3", ""]))
STAMP = st.one_of(
    st.none(), st.datetimes(datetime(2023, 1, 1), datetime(2024, 12, 31)).map(pd.Timestamp)
)
TEXT = st.one_of(
    st.none(), st.just(math.nan), st.sampled_from(["", " ", "ja", "nein", "V-1", "nan"])
)
GROUP = st.one_of(
    st.none(), st.just(math.nan), st.just(pd.NA), st.sampled_from(["A", "B"]), st.integers(1, 2)
)


def _rows(amount: st.SearchStrategy[object]) -> st.SearchStrategy[list[dict[str, object]]]:
    row = st.fixed_dictionaries(
        {
            "projektbetrag": amount,
            "kuerzungsbetrag": amount,
            "anerkannter_betrag": amount,
            "rechnungsdatum": STAMP,
            "zahlungsdatum": STAMP,
            "rechnungsnummer": st.one_of(st.none(), st.sampled_from(["R-1", "R-2"]), st.just(1.0)),
            "rechnungssteller": GROUP,
            "kuerzungsgrund": TEXT,
            "vergabe": TEXT,
            "direktvergabe": TEXT,
        }
    )
    return st.lists(row, max_size=25)


COLUMN_SUBSETS = st.lists(st.sampled_from(FS_COLUMNS), unique=True, min_size=1).map(
    lambda chosen: [c for c in FS_COLUMNS if c in chosen]
)
SETTINGS = settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.too_slow])


@SETTINGS
@given(_rows(AMOUNT), COLUMN_SUBSETS)
def test_random_frames_match(rows: list[dict[str, object]], columns: list[str]) -> None:
    frame = pd.DataFrame(rows, columns=columns)
    for profile in BOTH:
        assert_same(evaluate_frame_columns(frame, profile), evaluate_frame(frame, profile))


@SETTINGS
@given(_rows(TEXT_AMOUNT))
def test_random_lists_and_arrays_match(rows: list[dict[str, object]]) -> None:
    lists = {c: [row.get(c) for row in rows] for c in FS_COLUMNS}
    arrays = {c: np.array(v, dtype=object) for c, v in lists.items()}
    for profile in BOTH:
        expected = evaluate(rows, profile, columns=FS_COLUMNS)
        assert_same(evaluate_columns(lists, profile), expected)
        assert_same(evaluate_columns(arrays, profile), expected)


def test_numpy_columns_match() -> None:
    stamps = np.array(["2024-01-02", "NaT", "2024-01-01"], dtype="datetime64[s]")
    columns = {
        "projektbetrag": np.array([25_000.5, 1000.0, 22_600.0]),
        "kuerzungsbetrag": np.array([0, 0, 1], dtype=np.int64),
        "anerkannter_betrag": np.array([25_000.49, 1000.0, 22_599.0]),
        "rechnungsdatum": stamps,
        "zahlungsdatum": stamps[::-1].copy(),
        "rechnungsnummer": np.array([7, 7, 8]),
        "rechnungssteller": np.array(["A", "A", "B"]),
        "kuerzungsgrund": np.array(["", "x", ""]),
        "vergabe": np.array(["", "V", ""]),
        "direktvergabe": np.array(["ja", "", "nein"]),
    }
    result = evaluate_columns(columns, CENTS)
    rows = [{c: columns[c].astype(object)[i] for c in columns} for i in range(3)]
    assert_same(result, evaluate(rows, CENTS, columns=list(columns)))
    assert_same(
        evaluate_columns(columns, FLOWSTAT), evaluate(rows, FLOWSTAT, columns=list(columns))
    )
    assert result.record_flags("BL_RF09_DIRECT_AWARD_HIGH_AMOUNT") == [True, False, False]
    assert result.hits("BL_RF06_CUT_WITHOUT_REASON").tolist() == [2]
    assert set(result.paths.values()) == {VECTORISED}


def test_typical_frame_is_fully_vectorised() -> None:
    case = next(c for c in FS_CASES if c["name"] == "rf05-dubletten")
    result = evaluate_frame_columns(_frame(case), CENTS)
    assert dict(result.paths) == {r.code: VECTORISED for r in CENTS.rules}
    legacy = evaluate_frame_columns(_frame(case), FLOWSTAT).paths  # float sums: math.fsum
    assert legacy["BL_RF10_VENDOR_CONCENTRATION"] == RECORDS
    assert result.engine and {"name", "mode"} <= set(result.engine[0])
    lists = {c: [decode(r).get(c) for r in case["rows"]] for c in case["columns"]}
    assert evaluate_columns(lists, FLOWSTAT).paths["BL_RF04_PAYMENT_BEFORE_INVOICE"] == RECORDS


def test_year_bound_thresholds_use_the_record_kind() -> None:
    frame = pd.DataFrame(
        {
            "bruttobetrag": [200_000.0, 0.0],
            "nettobetrag": [None, 190_000.0],
            "Name": ["A", "B"],
            "zahlungsempfaenger": ["C", "D"],
            "rechnungsdatum_dt": [pd.Timestamp("2025-06-30"), pd.NaT],
        }
    )
    result = evaluate_frame_columns(frame, YEAR_BOUND, reference_date=None)
    assert_same(result, evaluate_frame(frame, YEAR_BOUND))
    assert result.paths["RF02"] == RECORDS


def test_column_errors() -> None:
    with pytest.raises(InputError, match="unterschiedlich lang"):
        evaluate_columns({"projektbetrag": [1.0], "vergabe": []}, FLOWSTAT)
    with pytest.raises(InputError, match="Text"):
        evaluate_columns({1: [1.0]}, FLOWSTAT)  # type: ignore[dict-item]
    with pytest.raises(InputError, match="Liste"):
        evaluate_columns({"projektbetrag": 5.0}, FLOWSTAT)
    with pytest.raises(InputError, match="eindimensional"):
        evaluate_columns({"projektbetrag": np.zeros((1, 1))}, FLOWSTAT)
    with pytest.raises(ProfileError, match="Regelprofil"):
        evaluate_columns({}, "x")  # type: ignore[arg-type]
    with pytest.raises(ProfileError, match="Bewertung"):
        evaluate_columns({}, load_profile("flowinvoice.exante_basis", "fb2d18568d2e"))
    with pytest.raises(InputError, match="DataFrame"):
        evaluate_frame_columns([], FLOWSTAT)
    duplicate = pd.DataFrame([[1.0, 2.0]], columns=["projektbetrag", "projektbetrag"])
    with pytest.raises(InputError, match="eindeutig"):
        evaluate_frame_columns(duplicate, FLOWSTAT)
    unhashable = {"rechnungssteller": [["x"]], "projektbetrag": [1.0]}
    with pytest.raises(InputError, match="Schlüssel"):
        evaluate_columns(unhashable, FLOWSTAT)
    with pytest.raises(InputError, match="Schlüssel"):
        evaluate([{"rechnungssteller": ["x"], "projektbetrag": 1.0}], FLOWSTAT)


def test_empty_columns() -> None:
    result = evaluate_columns({c: [] for c in FS_COLUMNS}, FLOWSTAT)
    assert result.size == 0 and result.summary == ()
    assert evaluate_columns({}, FLOWSTAT).skipped.keys() == {r.code for r in FLOWSTAT.rules}


def _custom(changes: dict[str, dict[str, Any]]) -> Any:
    """Flowstat profile with changed params/requires per rule code (other rules dropped)."""
    raw = files("auditcore_risk.profile_data").joinpath(
        "audit_designer.flowstat_belegliste-2026.10.1.json"
    )
    data = json.loads(raw.read_text(encoding="utf-8"))
    rules = []
    for rule in data["rules"]:
        if rule["code"] in changes:
            change = changes[rule["code"]]
            rule["params"] = {**rule["params"], **change.get("params", {})}
            rule["requires"] = change.get("requires", rule["requires"])
            rules.append(rule)
    data["rules"] = rules
    return profile_from_dict(data)


RELEVANCE = {
    "field": "kostenart",
    "exclude_pattern": "personal",
    "ignore_case": True,
    "column_missing": "relevant",
}
PARTIAL = _custom(
    {
        "BL_RF06_CUT_WITHOUT_REASON": {"requires": ["kuerzungsbetrag"]},
        "BL_RF07_ACCEPTED_MISMATCH": {"requires": ["projektbetrag"]},
        "BL_RF08_PROCUREMENT_MISSING": {
            "requires": ["projektbetrag"],
            "params": {"id_column_missing": "counts_as_missing", "relevance": RELEVANCE},
        },
        "BL_RF10_VENDOR_CONCENTRATION": {"requires": ["rechnungssteller"]},
        "BL_RF05_DUPLICATE_INVOICE": {"requires": ["rechnungssteller"]},
    }
)
STRICT_IDS = _custom({"BL_RF08_PROCUREMENT_MISSING": {"requires": ["projektbetrag"]}})


@SETTINGS
@given(_rows(TEXT_AMOUNT), st.lists(st.sampled_from(["Personal", "Bau", None]), max_size=25))
def test_partial_requirements_match(rows: list[dict[str, object]], kinds: list[object]) -> None:
    for row, kind in zip(rows, kinds, strict=False):
        row["kostenart"] = kind
    for columns in (["projektbetrag", "kuerzungsbetrag", "kostenart"], ["rechnungssteller"]):
        subset = [{c: row[c] for c in columns if c in row} for row in rows]
        lists = {c: [row.get(c) for row in subset] for c in columns}
        expected = evaluate(subset, PARTIAL, columns=columns)
        assert_same(evaluate_columns(lists, PARTIAL), expected)


def test_missing_identifier_column_raises_in_both_paths() -> None:
    rows = [{"projektbetrag": 30_000.0}]
    with pytest.raises(InputError, match="vergabe"):
        evaluate(rows, STRICT_IDS)
    with pytest.raises(InputError, match="vergabe"):
        evaluate_columns({"projektbetrag": [30_000.0]}, STRICT_IDS)


def test_large_tables_sum_with_python_integers(monkeypatch: pytest.MonkeyPatch) -> None:
    case = next(c for c in FS_CASES if c["name"] == "rf10-konzentration")
    frame = _frame(case)
    expected = evaluate_frame_columns(frame, CENTS)
    monkeypatch.setattr(column_kinds, "_SAFE_SUM_ROWS", 0)
    assert_same(evaluate_frame_columns(frame, CENTS), evaluate_frame(frame, CENTS))
    assert evaluate_frame_columns(frame, CENTS).summary == expected.summary


def test_radix_compaction_and_unhashable_texts(monkeypatch: pytest.MonkeyPatch) -> None:
    case = next(c for c in FS_CASES if c["name"] == "rf05-dubletten")
    frame = _frame(case)
    expected = evaluate_frame(frame, FLOWSTAT)
    monkeypatch.setattr(column_kinds, "_RADIX_LIMIT", 1)
    assert_same(evaluate_frame_columns(frame, FLOWSTAT), expected)
    rows = [{"projektbetrag": 30_000.0, "vergabe": ["x"], "direktvergabe": ["ja"]}]
    columns = {c: [rows[0][c]] for c in rows[0]}
    assert_same(evaluate_columns(columns, FLOWSTAT), evaluate(rows, FLOWSTAT))
