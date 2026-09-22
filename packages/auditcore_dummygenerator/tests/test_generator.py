"""Observed legacy contracts and explicit corrections to unsafe batch behavior."""

from __future__ import annotations

import copy
import json
import random
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from auditcore_dummygenerator import BatchGenerationError, TestDataGenerator
from auditcore_dummygenerator import generator as module

RECORDS = json.loads((Path(__file__).parent / "fixtures" / "legacy_observed.json").read_text())[
    "records"
]


@pytest.mark.parametrize("record", RECORDS, ids=lambda record: record["method"])
def test_observed_original_behavior(record: dict[str, Any]) -> None:
    generator = TestDataGenerator(seed=record["seed"], use_joblib=False)
    args = copy.deepcopy(record["args"])
    method = getattr(generator, record["method"])
    if "exception" in record:
        with pytest.raises(Exception) as caught:
            method(*args)
        assert type(caught.value).__name__ == record["exception"]
    else:
        actual = method(*args)
        assert json.loads(json.dumps(actual)) == record["output"]


def _request(rows: int = 2200) -> dict[str, Any]:
    return {
        "rows": rows,
        "fields": [
            {"name": "id", "type": "auto_increment", "params": {"start": 10, "step": 3}},
            {"name": "value", "type": "number"},
            {"name": "date", "type": "date_after", "params": {"minDays": 1, "maxDays": 1}},
        ],
    }


@pytest.mark.parametrize("use_joblib", [False, True])
def test_parallel_no_nested_pools_complete_ordered_and_immutable(use_joblib: bool) -> None:
    if use_joblib and not module.JOBLIB_AVAILABLE:
        pytest.skip("optional joblib backend unavailable")
    request = _request()
    before = copy.deepcopy(request)
    first = TestDataGenerator(
        seed=42, max_workers=2, use_joblib=use_joblib, base_date=date(2024, 1, 1)
    ).generate_rows(request)
    second = TestDataGenerator(
        seed=42, max_workers=2, use_joblib=use_joblib, base_date=date(2024, 1, 1)
    ).generate_rows(request)
    assert first == second
    assert request == before
    assert [row["id"] for row in first] == list(range(10, 10 + 2200 * 3, 3))
    assert {row["date"] for row in first} == {"2024-01-02"}


def test_worker_never_dispatches_again_or_mutates_request(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("worker must not enter automatic dispatcher")

    monkeypatch.setattr(TestDataGenerator, "generate_rows", forbidden)
    request = _request()
    before = copy.deepcopy(request)
    result = module._generate_batch(
        {
            "seed": 42,
            "request": request,
            "start_idx": 100,
            "batch_size": 1100,
            "base_date": date(2024, 1, 1),
        }
    )
    assert len(result) == 1100
    assert result[0]["id"] == 310
    assert request == before


@pytest.mark.parametrize("use_joblib", [False, True])
def test_worker_failure_is_an_exception_never_partial_success(use_joblib: bool) -> None:
    if use_joblib and not module.JOBLIB_AVAILABLE:
        pytest.skip("optional joblib backend unavailable")
    request = {
        "rows": 200,
        "fields": [
            {"name": "invalid", "type": "number", "params": {"min": 5, "max": 1}},
        ],
    }
    with pytest.raises(BatchGenerationError) as caught:
        TestDataGenerator(seed=42, use_joblib=use_joblib).generate_rows_parallel(request, 2)
    assert isinstance(caught.value.__cause__, ValueError)


def test_incomplete_backend_results_are_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    class IncompleteParallel:
        def __init__(self, **kwargs: Any) -> None:
            pass

        def __call__(self, tasks: Any) -> list[list[dict[str, Any]]]:
            return [[], []]

    monkeypatch.setattr(module, "JOBLIB_AVAILABLE", True)
    monkeypatch.setattr(module, "Parallel", IncompleteParallel, raising=False)
    monkeypatch.setattr(module, "delayed", lambda fn: fn, raising=False)
    with pytest.raises(BatchGenerationError, match="count"):
        TestDataGenerator(seed=42, use_joblib=True).generate_rows_parallel(_request(200), 2)


def test_fixed_date_and_sequential_replay_do_not_touch_global_rng() -> None:
    state = random.getstate()
    first = TestDataGenerator(42, base_date=date(2024, 1, 1)).generate_rows(_request(5))
    second = TestDataGenerator(42, base_date=date(2024, 1, 1)).generate_rows(_request(5))
    assert first == second
    assert random.getstate() == state
    assert {row["date"] for row in first} == {"2024-01-02"}


def test_max_workers_one_keeps_sequential_call_sequence() -> None:
    request = _request()
    a = TestDataGenerator(42, base_date=date(2024, 1, 1), max_workers=1)
    b = TestDataGenerator(42, base_date=date(2024, 1, 1))
    assert a.generate_rows(request) == b._generate_rows_sequential(request)


@pytest.mark.parametrize("value", [0, -1])
def test_invalid_worker_limits(value: int, monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValueError):
        TestDataGenerator(max_workers=value)
    with pytest.raises(ValueError):
        TestDataGenerator().generate_rows_parallel(_request(200), value)
    monkeypatch.setenv("MAX_WORKERS", str(value))
    with pytest.raises(ValueError):
        module.get_optimal_workers()


def test_explicit_missing_optional_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(module, "JOBLIB_AVAILABLE", False)
    with pytest.raises(ImportError, match="parallel"):
        TestDataGenerator(use_joblib=True)
    rows = TestDataGenerator(42, base_date=date(2024, 1, 1)).generate_rows_parallel_joblib(
        _request(200), n_jobs=2
    )
    assert len(rows) == 200


def test_identifiers_are_synthetic_not_validated() -> None:
    iban = TestDataGenerator(42).generate_iban("DE")
    numeric = "".join(
        str(ord(char) - 55) if char.isalpha() else char for char in iban[4:] + iban[:4]
    )
    assert len(iban) == 22
    assert int(numeric) % 97 != 1  # Observed legacy case: no validity promise.


def test_deviation_preserves_documented_in_place_contract() -> None:
    row = {"betrag": 100.0}
    result = TestDataGenerator(42).apply_deviation(row, "NEGATIVE_AMOUNTS", 1)
    assert result is row
    assert row == {"betrag": -100.0}
