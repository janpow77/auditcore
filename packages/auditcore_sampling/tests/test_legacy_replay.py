"""All recorded flowstat and audit-portal sampling results are reproduced without NumPy."""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

import pytest
from conftest import LEGACY, column

from auditcore_sampling import legacy

SIZE_FUNCTIONS = {
    "mus_size:flowstat": legacy.flowstat_mus_size,
    "mus_size:portal": legacy.portal_mus_size,
    "mus_size:portal_legacy": legacy.portal_mus_size_legacy,
    "srs_size:flowstat": legacy.flowstat_srs_size,
    "srs_size:portal": legacy.portal_srs_size,
}
CASES = LEGACY["cases"]


def plain(value: Any) -> Any:
    return json.loads(json.dumps(value))


@pytest.mark.parametrize("operation", sorted(SIZE_FUNCTIONS))
def test_sample_size_functions_including_errors(operation: str) -> None:
    cases = [c for c in CASES if c["operation"] == operation]
    assert len(cases) in (2401, 768)
    for case in cases:
        function = SIZE_FUNCTIONS[operation]
        if case["exception"]:
            with pytest.raises(Exception) as caught:  # noqa: B017 - exact type checked below
                function(**case["inputs"])
            assert type(caught.value).__name__ == case["exception"]["type"], case["name"]
            assert str(caught.value) == case["exception"]["message"], case["name"]
        else:
            result = function(**case["inputs"])
            assert plain(list(result) if isinstance(result, tuple) else result) == case["output"], (
                case["name"]
            )


@pytest.mark.parametrize("variant", ["flowstat", "portal"])
@pytest.mark.parametrize("template", ["run_mus_standard", "run_mus_conservative"])
def test_mus_templates_with_recorded_starts(variant: str, template: str) -> None:
    cases = [c for c in CASES if c["operation"] == f"{variant}:{template}" and not c["exception"]]
    assert cases
    rate = 0.005 if template == "run_mus_standard" else 0.01
    for case in cases:
        params = case["inputs"]["parameters"]
        values = column(case["inputs"]["frame"], "amount")
        function = legacy.flowstat_mus if variant == "flowstat" else legacy.portal_mus
        result = function(
            values,
            template=template,
            materiality=params["materiality"],
            confidence_level=params["confidenceLevel"],
            expected_error_rate=rate,
            start=case["legacy_start"],
        )
        meta = case["output"]["meta"]
        assert plain(result[0]) == case["output"]["rows"][0], case["name"]
        assert result[1] == meta["sample_indices"], case["name"]
        assert meta["sample_data"]["rows"] == len(result[1])
        if variant == "portal":
            assert result[2] == meta["negative_records"]["indices"]
            assert result[3] == meta["negative_records"]["zero_or_nan_indices"]


def test_stratified_mus_and_srs_allocation() -> None:
    checked = Counter()
    for case in CASES:
        frame = case["inputs"].get("frame")
        params = case["inputs"].get("parameters", {})
        if case["operation"] == "flowstat:run_mus_stratified":
            values, strata = column(frame, "amount"), column(frame, "category")

            def run(
                p: dict[str, Any] = params,
                v: list[Any] = values,
                s: list[Any] = strata,
                c: dict[str, Any] = case,
            ) -> Any:
                return legacy.flowstat_mus_stratified(
                    v,
                    s,
                    materiality=p["materiality"],
                    confidence_level=0.95,
                    expected_error_rate=0.005,
                    starts=c["legacy_starts"],
                )

            if case["exception"]:
                with pytest.raises(ValueError, match=case["exception"]["message"]):
                    run()
            else:
                rows, selected, _ = run()
                assert plain(rows) == case["output"]["rows"]
                assert selected == case["output"]["meta"]["sample_indices"]
            checked["mus"] += 1
        elif case["operation"] == "flowstat:run_srs_stratified":
            rows = legacy.flowstat_srs_stratified_sizes(
                column(frame, "category"),
                confidence_level=0.95,
                margin_of_error=params["marginOfError"],
                allocation_method=params["allocationMethod"],
            )
            assert plain(rows) == case["output"]["rows"]
            checked["srs"] += 1
        elif case["operation"] == "flowstat:run_srs_standard":
            size = legacy.flowstat_srs_size(
                len(column(frame, "amount")), 0.95, params["marginOfError"]
            )
            assert (
                min(size, len(column(frame, "amount")))
                == case["output"]["rows"][0]["Stichprobenumfang"]
            )
            checked["srs_standard"] += 1
    assert checked == {"mus": 10, "srs": 20, "srs_standard": 10}


def test_fixture_is_bound_to_pinned_sources() -> None:
    sources = LEGACY["sources"]
    assert sources["flowstat"]["observed_blob"] == "c2423b1efab65f1eb1118b97f6eebe83348be706"
    assert sources["portal"]["observed_blob"] == "2358a38fc9c4b0ff414018b54ed7bf31f4f422fe"
    assert LEGACY["environment"]["numpy"] == "1.26.2"
    assert len(CASES) == 8883
