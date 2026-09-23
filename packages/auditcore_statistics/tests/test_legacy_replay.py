"""Every recorded flowstat ``run_benford`` output is reproduced without NumPy/SciPy."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pytest

from auditcore_statistics import legacy_run_benford
from auditcore_statistics.numeric import chi2_survival, numpy_pairwise_sum

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "flowstat_benford_observed.json").read_text()
)
DTYPES = {"int64": "int", "float64": "float", "bool": "bool"}
REPLAYABLE = [
    c
    for c in FIXTURE["cases"]
    if c["coerced"] is not None and c["parameters"].get("valueColumn") == "betrag"
]


def revive(value: Any) -> Any:
    if isinstance(value, dict) and set(value) == {"$float"}:
        return float(value["$float"])
    return value


@pytest.mark.parametrize("case", REPLAYABLE, ids=[c["name"] for c in REPLAYABLE])
def test_run_benford_is_reproduced_exactly(case: dict[str, Any]) -> None:
    values = [revive(v) for v in case["coerced"]]

    def run() -> dict[str, Any]:
        return legacy_run_benford(
            values,
            dtype=DTYPES[case["coerced_dtype"]],  # type: ignore[arg-type]
            digit=case["parameters"].get("digit", 1),
            column="betrag",
        )

    if case["exception"]:
        with pytest.raises(ValueError) as caught:
            run()
        assert type(caught.value).__name__ == case["exception"]["type"]
        assert str(caught.value) == case["exception"]["message"]
    else:
        assert json.loads(json.dumps(run())) == case["output"]


def test_parameter_and_column_errors_stay_with_the_consumer() -> None:
    names = {c["name"] for c in FIXTURE["cases"]} - {c["name"] for c in REPLAYABLE}
    assert names == {"missing-parameter", "missing-column", "empty-frame"}


@pytest.mark.parametrize("index", range(len(FIXTURE["chisquare"])))
def test_chisquare_statistic_exact_and_p_value_to_1e12(index: int) -> None:
    ref = FIXTURE["chisquare"][index]
    observed = [float(v) for v in ref["observed"]]
    statistic = numpy_pairwise_sum(
        [(o - e) ** 2 / e for o, e in zip(observed, ref["expected"], strict=True)]
    )
    assert statistic == ref["statistic"]
    p = chi2_survival(statistic, len(observed) - 1)
    assert math.isclose(p, ref["p_value"], rel_tol=1e-12, abs_tol=1e-300)


def test_fixture_covers_documented_defects() -> None:
    by_name = {c["name"]: c for c in FIXTURE["cases"]}
    assert "sum of the observed" in by_name["integers-2"]["exception"]["message"]
    assert by_name["scientific-2"]["exception"]["message"].endswith("'1e'")
    assert by_name["booleans-1"]["exception"]["type"] == "ValueError"
    # 5 (int64) and 5.0 (float64) give different two-digit groups in the source.
    assert by_name["small-ints-2"]["exception"] and not by_name["same-as-float-2"]["exception"]
    assert FIXTURE["environment"] == {
        "python": FIXTURE["environment"]["python"],
        "numpy": "1.26.2",
        "pandas": "2.1.3",
        "scipy": "1.11.4",
    }
