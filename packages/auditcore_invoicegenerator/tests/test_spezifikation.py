"""Invarianten aus docs/spezifikation.md als Eigenschaftstests (Hypothesis).

Alle Rechnungen sind synthetisch; kein Netz, keine Dateien.
"""

from __future__ import annotations

import json
import random
from copy import deepcopy
from datetime import date, timedelta

from hypothesis import given, settings
from hypothesis import strategies as st

from auditcore_invoicegenerator import (
    FlowInvoiceDemoProfile,
    InvoiceScenario,
    duplicate_invoice,
    render_pdf,
    suppliers,
    to_json,
)
from auditcore_invoicegenerator._legacy import INVOICE_DATE_RANGE_END, INVOICE_DATE_RANGE_START

EXAMPLES = settings(max_examples=60, deadline=None)
SEEDS = st.integers(min_value=0, max_value=2**31)
DAYS = st.dates(min_value=date(2000, 1, 1), max_value=date(2090, 12, 31))
COUNTRY = st.sampled_from(["DE", "AT"])
ERROR = st.sampled_from(["none", "wrong_total", "missing_vat_id", "date_before_reference"])
SUPPLIER = st.sampled_from(range(len(suppliers())))


@EXAMPLES
@given(SEEDS, DAYS, COUNTRY, st.integers(0, 6))
def test_i1_same_seed_and_reference_date_give_same_invoices(
    seed: int, base: date, country: str, total: int
) -> None:
    """I1: frische Szenarien mit gleichem Seed, Bezugsdatum und Land → gleiche Rechnungen."""
    first = InvoiceScenario(seed, base_date=base, country=country).generate_batch(total)
    second = InvoiceScenario(seed, base_date=base, country=country).generate_batch(total)
    assert first == second


@EXAMPLES
@given(SEEDS, DAYS, COUNTRY, st.integers(1, 40))
def test_i2_amounts_are_consistent(seed: int, base: date, country: str, index: int) -> None:
    """I2: Positions-, Netto-, Steuer- und Gesamtbetrag stimmen nach der Profilrundung überein."""
    record = InvoiceScenario(seed, base_date=base, country=country).generate(index)
    amounts = record["amounts"]
    assert record["line_items"]
    for item in record["line_items"]:
        assert item["amount"] > 0 and item["quantity"] >= 1
        assert item["amount"] in (
            round(item["unit_price"] * item["quantity"], 2),
            item["unit_price"],
        )
    assert amounts["subtotal"] == sum(item["amount"] for item in record["line_items"])
    assert amounts["vat_amount"] == round(amounts["subtotal"] * amounts["vat_rate"], 2)
    assert amounts["total"] == round(amounts["subtotal"] + amounts["vat_amount"], 2)


@EXAMPLES
@given(SEEDS, DAYS, COUNTRY, st.integers(1, 40), ERROR)
def test_i3_errors_only_when_requested(
    seed: int, base: date, country: str, index: int, error: str
) -> None:
    """I3: nur die verlangte Abweichung; correct_values sind die Werte der fehlerfreien Rechnung."""
    clean = InvoiceScenario(seed, base_date=base, country=country).generate(index)
    faulty = InvoiceScenario(seed, base_date=base, country=country).generate(
        index,
        error=error,  # type: ignore[arg-type]
    )
    meta = faulty["metadata"]
    assert meta["injected_errors"] == ([] if error == "none" else [error])
    assert meta["is_problematic"] is (error != "none")
    assert meta["correct_values"] == {
        "amounts.total": clean["amounts"]["total"],
        "supplier.vat_id": clean["supplier"]["vat_id"],
        "invoice_date": clean["invoice_date"],
    }
    changed = {
        "wrong_total": faulty["amounts"]["total"] != clean["amounts"]["total"],
        "missing_vat_id": faulty["supplier"]["vat_id"] == "",
        "date_before_reference": faulty["invoice_date"] < base.isoformat(),
        "none": faulty == clean,
    }
    assert changed[error]
    stripped = {key: value for key, value in faulty.items() if key != "metadata"}
    reference = {key: value for key, value in clean.items() if key != "metadata"}
    if error == "wrong_total":
        stripped["amounts"] = {**faulty["amounts"], "total": clean["amounts"]["total"]}
    elif error == "missing_vat_id":
        stripped["supplier"] = {**faulty["supplier"], "vat_id": clean["supplier"]["vat_id"]}
    elif error == "date_before_reference":
        stripped["invoice_date"] = clean["invoice_date"]
    assert stripped == reference


@EXAMPLES
@given(SEEDS, DAYS, st.integers(1, 400))
def test_i4_scenario_dates_follow_the_reference_date(seed: int, base: date, index: int) -> None:
    """I4: Rechnungsdatum = Bezugsdatum + (Index − 1); Leistung einen Tag davor; Fälligkeit +30."""
    record = InvoiceScenario(seed, base_date=base).generate(index)
    invoice = base + timedelta(days=index - 1)
    assert record["invoice_date"] == invoice.isoformat()
    assert record["supply_date"] == (invoice - timedelta(days=1)).isoformat()
    assert record["due_date"] == (invoice + timedelta(days=30)).isoformat()


@EXAMPLES
@given(SEEDS, DAYS, st.integers(1, 5), st.data())
def test_i5_inputs_are_not_mutated(seed: int, base: date, total: int, data: st.DataObject) -> None:
    """I5: Fehlerplan, Vorlage und Eingaberechnung bleiben unverändert; Duplikat ist unabhängig."""
    errors = data.draw(st.dictionaries(st.integers(1, total), ERROR.filter(lambda e: e != "none")))
    plan = dict(errors)
    batch = InvoiceScenario(seed, base_date=base).generate_batch(total, errors=errors)  # type: ignore[arg-type]
    assert errors == plan
    original = deepcopy(batch[0])
    copy = duplicate_invoice(batch[0], new_id="DOC-DUPLIKAT")
    assert batch[0] == original
    assert copy["id"] == "DOC-DUPLIKAT" and copy["metadata"]["duplicate_of"] == original["id"]
    assert copy["metadata"]["injected_errors"] == ["duplicate"]
    assert {k: v for k, v in copy.items() if k not in ("id", "metadata")} == {
        k: v for k, v in original.items() if k not in ("id", "metadata")
    }
    copy["line_items"].clear()
    assert batch[0] == original


@EXAMPLES
@given(SEEDS, DAYS, st.integers(0, 4))
def test_i6_json_round_trip(seed: int, base: date, total: int) -> None:
    """I6: ``json.loads(to_json(r)) == r``; kein NaN, UTF-8-Text endet mit Zeilenumbruch."""
    batch = InvoiceScenario(seed, base_date=base).generate_batch(total)
    text = to_json(batch)
    assert text.endswith("\n") and json.loads(text) == batch


@EXAMPLES
@given(SEEDS, st.integers(1, 9999), SUPPLIER)
def test_i7_legacy_profile_dates_and_identity(seed: int, index: int, supplier: int) -> None:
    """I7: Altprofil: fester Datumsbereich, Leistung 1–14 Tage davor, Fälligkeit +30."""
    record = FlowInvoiceDemoProfile(seed).generate_invoice(index, suppliers()[supplier])
    invoice = date.fromisoformat(record["invoice_date"])
    assert INVOICE_DATE_RANGE_START.date() <= invoice <= INVOICE_DATE_RANGE_END.date()
    supply = date.fromisoformat(record["supply_date"])
    assert timedelta(days=1) <= invoice - supply <= timedelta(days=14)
    assert date.fromisoformat(record["due_date"]) == invoice + timedelta(days=30)
    assert record["id"] == f"DOC-{index:05d}"
    assert record["metadata"] == {"problem_type": None, "is_problematic": False}


@EXAMPLES
@given(SEEDS, DAYS, st.integers(0, 3))
def test_i8_generation_leaves_the_global_random_state_alone(
    seed: int, base: date, total: int
) -> None:
    """I8: InvoiceScenario und FlowInvoiceDemoProfile verbrauchen keinen globalen Zufall."""
    state = random.getstate()
    InvoiceScenario(seed, base_date=base).generate_batch(total)
    FlowInvoiceDemoProfile(seed).generate_batch(total)
    assert random.getstate() == state


@EXAMPLES
@given(st.one_of(st.integers(max_value=0), st.booleans(), st.floats(), st.text(max_size=3)))
def test_i9_invalid_positions_are_rejected(value: object) -> None:
    """I9: Index < 1, Wahrheitswerte und Nicht-Ganzzahlen werden mit ValueError abgewiesen."""
    scenario = InvoiceScenario(1, base_date=date(2026, 1, 1))
    for call in (
        lambda: scenario.generate(value),  # type: ignore[arg-type]
        lambda: scenario.generate_batch(1, errors={value: "wrong_total"}),  # type: ignore[dict-item]
    ):
        try:
            call()
        except ValueError:
            continue
        raise AssertionError(f"{value!r} wurde angenommen")


@settings(max_examples=10, deadline=None)
@given(SEEDS, DAYS)
def test_i10_pdf_is_deterministic(seed: int, base: date) -> None:
    """I10: gleiche Rechnung → byte-gleiches PDF; die Eingabe bleibt unverändert."""
    record = InvoiceScenario(seed, base_date=base).generate(1, error="wrong_total")
    before = deepcopy(record)
    first = render_pdf(record)
    assert first.startswith(b"%PDF") and render_pdf(record) == first
    assert record == before
