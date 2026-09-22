"""Observed legacy results and independent scenario invariants, not implementation mirrors."""

import copy
import hashlib
import json
import random
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import pytest

import auditcore_invoicegenerator as invoices

GOLDEN_NAME = (
    "legacy-golden-cpython311.json"
    if sys.implementation.name == "cpython" and sys.version_info[:2] == (3, 11)
    else "legacy-golden.json"
)
GOLDEN = json.loads((Path(__file__).parent / "data" / GOLDEN_NAME).read_text())


def test_observed_interpreter_profiles_differ_only_in_native_subtotal_sum():
    directory = Path(__file__).parent / "data"
    modern = json.loads((directory / "legacy-golden.json").read_text())
    previous = json.loads((directory / "legacy-golden-cpython311.json").read_text())
    assert modern["source_sha256"] == previous["source_sha256"]
    assert previous["python"]["implementation"] == "cpython"
    assert previous["python"]["version"].startswith("3.11.")
    differences = []
    for newer, older in zip(modern["cases"], previous["cases"], strict=True):
        if newer != older:
            assert newer["function"] == "generate_invoice"
            newer["expected"]["amounts"].pop("subtotal")
            older["expected"]["amounts"].pop("subtotal")
            assert newer == older
            differences.append(newer["name"])
    assert len(differences) == 9


@pytest.mark.parametrize("case", GOLDEN["cases"], ids=lambda case: case["name"])
def test_observed_legacy_characterization(case):
    profile = invoices.FlowInvoiceDemoProfile(case["seed"])
    function = getattr(profile, case["function"], None) or getattr(invoices, case["function"])
    args = copy.deepcopy(case["args"])
    before = copy.deepcopy(args)
    if case["exception"]:
        with pytest.raises(Exception) as caught:
            function(*args)
        assert type(caught.value).__name__ == case["exception"]
    else:
        actual = function(*args)
        normalized = json.loads(json.dumps(actual, default=lambda value: value.isoformat()))
        assert normalized == case["expected"]
    assert args == before
    assert (
        hashlib.sha256(repr(profile.rng.getstate()).encode()).hexdigest()
        == case["rng_after_sha256"]
    )


def test_import_and_calls_do_not_reseed_process_global_rng():
    code = (
        "import random; random.seed(98765); before=random.getstate(); "
        "import auditcore_invoicegenerator as i; "
        "i.generate_invoice(1,i.suppliers()[0]); assert random.getstate()==before"
    )
    subprocess.run([sys.executable, "-c", code], check=True)


def test_catalogs_and_input_are_independent_copies():
    first, second = invoices.suppliers(), invoices.suppliers()
    first[0]["name"] = "changed"
    assert second[0]["name"] != first[0]["name"]
    original = copy.deepcopy(second[0])
    record = invoices.generate_invoice(1, second[0])
    record["supplier"]["name"] = "changed"
    assert second[0] == original


@pytest.mark.parametrize("country", ["DE", "AT"])
def test_complete_scenario_uses_dummy_and_consistent_amounts(country, monkeypatch):
    from auditcore_dummygenerator import TestDataGenerator

    calls = []
    original = TestDataGenerator.generate_company

    def observed(self):
        calls.append("dummy-company")
        return original(self)

    monkeypatch.setattr(TestDataGenerator, "generate_company", observed)
    scenario = invoices.InvoiceScenario(71, base_date=date(2026, 1, 1), country=country)
    records = scenario.generate_batch(3)
    assert len(calls) == 6
    assert len({record["id"] for record in records}) == 3
    for record in records:
        assert record["supplier"]["country"] == country
        assert record["beneficiary"]["name"]
        assert record["supplier"]["address"]
        assert record["line_items"]
        totals = record["amounts"]
        assert totals["subtotal"] == sum(item["amount"] for item in record["line_items"])
        assert totals["vat_amount"] == round(totals["subtotal"] * totals["vat_rate"], 2)
        assert totals["total"] == round(totals["subtotal"] + totals["vat_amount"], 2)
        assert record["metadata"]["synthetic"] is True
        assert record["metadata"]["injected_errors"] == []
    assert json.loads(invoices.to_json(records)) == records


def test_scenarios_repeat_across_instances_and_independent_threads():
    def generate(_):
        return invoices.InvoiceScenario(42, base_date=date(2026, 2, 1)).generate_batch(5)

    before = random.getstate()
    baseline = generate(0)
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert all(value == baseline for value in pool.map(generate, range(8)))
    assert random.getstate() == before


@pytest.mark.parametrize("error", ["wrong_total", "missing_vat_id", "date_before_reference"])
def test_explicit_defects_keep_ground_truth(error):
    base_date = date(2026, 5, 1)
    clean = invoices.InvoiceScenario(42, base_date=base_date).generate(1)
    broken = invoices.InvoiceScenario(42, base_date=base_date).generate(1, error=error)
    assert broken["metadata"]["injected_errors"] == [error]
    correct = broken["metadata"]["correct_values"]
    assert correct["amounts.total"] == clean["amounts"]["total"]
    assert correct["supplier.vat_id"] == clean["supplier"]["vat_id"]
    assert correct["invoice_date"] == clean["invoice_date"]
    if error == "wrong_total":
        assert broken["amounts"]["total"] != correct["amounts.total"]
    elif error == "missing_vat_id":
        assert broken["supplier"]["vat_id"] == ""
    else:
        assert date.fromisoformat(broken["invoice_date"]) < base_date


def test_explicit_batch_errors_and_duplicate_preserve_input():
    scenario = invoices.InvoiceScenario(42, base_date=date(2025, 1, 1))
    errors = {2: "wrong_total"}
    records = scenario.generate_batch(2, errors=errors)
    assert errors == {2: "wrong_total"}
    original = copy.deepcopy(records[0])
    duplicate = invoices.duplicate_invoice(records[0], new_id="copy")
    assert records[0] == original
    assert duplicate["invoice_number"] == original["invoice_number"]
    assert duplicate["metadata"]["duplicate_of"] == original["id"]
    duplicate["line_items"][0]["description"] = "changed"
    assert records[0] == original


@pytest.mark.parametrize("total", [-1, 1.1, True])
def test_invalid_batch_total_rejected(total):
    with pytest.raises(ValueError):
        invoices.InvoiceScenario(1, base_date=date(2025, 1, 1)).generate_batch(total)
    with pytest.raises(ValueError):
        invoices.FlowInvoiceDemoProfile(1).generate_batch(total)


@pytest.mark.parametrize(
    "errors", [{0: "wrong_total"}, {4: "wrong_total"}, {True: "wrong_total"}, {1: "unknown"}]
)
def test_invalid_error_plan_rejected_before_rng_consumption(errors):
    scenario = invoices.InvoiceScenario(1, base_date=date(2025, 1, 1))
    with pytest.raises(ValueError):
        scenario.generate_batch(3, errors=errors)
    assert scenario.generate(1) == invoices.InvoiceScenario(1, base_date=date(2025, 1, 1)).generate(
        1
    )


def test_empty_batch_and_unsupported_country():
    assert invoices.InvoiceScenario(1, base_date=date(2025, 1, 1)).generate_batch(0) == []
    with pytest.raises(ValueError):
        invoices.InvoiceScenario(1, base_date=date(2025, 1, 1), country="XX")


@pytest.mark.parametrize(
    "case",
    [c for c in GOLDEN["cases"] if c["function"] == "generate_invoice"],
    ids=lambda c: c["name"],
)
def test_explicit_global_legacy_adapter_preserves_original_draw_state(case):
    original_state = random.getstate()
    try:
        random.seed(case["seed"])
        if case["exception"]:
            with pytest.raises(Exception) as caught:
                invoices.generate_invoice_legacy_global(*case["args"])
            assert type(caught.value).__name__ == case["exception"]
        else:
            assert invoices.generate_invoice_legacy_global(*case["args"]) == case["expected"]
        assert (
            hashlib.sha256(repr(random.getstate()).encode()).hexdigest() == case["rng_after_sha256"]
        )
    finally:
        random.setstate(original_state)
