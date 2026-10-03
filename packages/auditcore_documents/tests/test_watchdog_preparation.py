"""Prepared values are shared within one evaluation and discarded afterwards."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from auditcore_documents.pipeline.watchdog import portfolio_checks
from auditcore_documents.pipeline.watchdog.cache import current, prepared_values
from auditcore_documents.pipeline.watchdog.values import normalize_supplier_name


def test_formal_check_reused_only_inside_run(monkeypatch: pytest.MonkeyPatch) -> None:
    original = portfolio_checks._formal_issues
    calls = []

    def count(document: dict) -> list[str]:
        calls.append(document)
        return original(document)

    monkeypatch.setattr(portfolio_checks, "_formal_issues", count)
    doc = {"invoice_number": "steuer"}
    with prepared_values():
        first = portfolio_checks.formal_issues(doc)
        with prepared_values():
            assert portfolio_checks.formal_issues(doc) == first
        assert len(calls) == 1
    doc["supplier_name"] = "Beispiel GmbH"
    with prepared_values():
        assert portfolio_checks.formal_issues(doc) != first
    assert len(calls) == 2 and current() is None


def test_preparation_cleared_after_error() -> None:
    with pytest.raises(RuntimeError), prepared_values():
        normalize_supplier_name("Beispiel GmbH")
        raise RuntimeError("failed")
    assert current() is None
    with prepared_values() as values:
        assert not values.suppliers and not values.formal and not values.numeric_text


def test_concurrent_evaluations_have_separate_values() -> None:
    barrier = Barrier(2)

    def run(name: str) -> None:
        with prepared_values() as values:
            normalize_supplier_name(name)
            barrier.wait(timeout=2)
            assert list(values.suppliers) == [name]
        assert current() is None

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(run, ["Erste GmbH", "Zweite GmbH"]))
