"""pandas adapter: drop-in ``compute_red_flags``/``red_flag_summary`` for riskanalysis."""

from __future__ import annotations

from typing import Any

import pandas as pd
import pytest
from conftest import decode, fixture

from auditcore_risk import InputError, ProfileError, load_profile
from auditcore_risk.frame import annotate, compute_red_flags, evaluate_frame, red_flag_summary

FIXTURE = fixture("riskanalysis_observed.json")
PROFILE = load_profile("riskanalysis.legacy", "b5c523bf7eaa")
FLOWSTAT = load_profile("audit_designer.flowstat_belegliste", "1254591156d3")
CASES = [c for c in FIXTURE["cases"] if c["name"].startswith(("orig-", "rf"))]


def frame(case: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame([decode(r) for r in case["rows"]], columns=case["columns"])


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_frame_columns_equal_the_original(case: dict[str, Any]) -> None:
    source = frame(case)
    out = compute_red_flags(source, PROFILE)
    for column, expected in case["flags"].items():
        assert out[column].dtype == bool
        assert out[column].tolist() == expected
    assert out["red_flag_codes"].tolist() == case["red_flag_codes"]
    assert list(out.columns[: len(source.columns)]) == list(source.columns)
    assert red_flag_summary(out, PROFILE) == case["summary"]
    pd.testing.assert_frame_equal(out[source.columns], source)


def test_summary_after_consumer_reindexing() -> None:
    case = next(c for c in CASES if c["name"] == "orig-summary-alle-codes")
    out = compute_red_flags(frame(case), PROFILE).reset_index(drop=True)
    out["beleg_id"] = out.index.astype(str)
    assert red_flag_summary(out, PROFILE) == case["summary"]


def test_undetermined_flags_use_nullable_boolean() -> None:
    year_bound = load_profile("riskanalysis.year_bound", "2026.09.1")
    source = pd.DataFrame(
        {
            "bruttobetrag": [200_000.0, 200_000.0],
            "Name": ["A", "B"],
            "zahlungsempfaenger": ["C", "D"],
            "rechnungsdatum_dt": [pd.Timestamp("2025-06-30"), pd.NaT],
        }
    )
    out = compute_red_flags(source, year_bound)
    assert str(out["rf02"].dtype) == "boolean"
    assert out["rf02"].iloc[0] is True or bool(out["rf02"].iloc[0]) is True
    assert pd.isna(out["rf02"].iloc[1])


def test_adapter_errors() -> None:
    with pytest.raises(InputError):
        evaluate_frame([{"bruttobetrag": 1.0}], PROFILE)
    source = pd.DataFrame({"bruttobetrag": [1.0], "Name": ["A"], "zahlungsempfaenger": ["B"]})
    evaluation = evaluate_frame(source, PROFILE)
    with pytest.raises(ProfileError):
        annotate(source, evaluation, FLOWSTAT)
    with pytest.raises(InputError):
        annotate(pd.concat([source, source]), evaluation, PROFILE)
    with pytest.raises(ProfileError):
        red_flag_summary(source, FLOWSTAT)
    duplicated = pd.DataFrame([[1.0, 2.0]], columns=["bruttobetrag", "bruttobetrag"])
    with pytest.raises(InputError):
        evaluate_frame(duplicated, PROFILE)
