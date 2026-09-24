from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal
from random import Random

import pytest
from auditcore_invoicegenerator import InvoiceScenario

from auditcore_invoicesynth.enrich import ALLOWED_VAT_RATES, VAT_SCHEMES, enrich
from auditcore_invoicesynth.identifiers import iban_valid, vat_id_valid
from auditcore_invoicesynth.layouts import HOLDOUT_LAYOUTS, LAYOUTS, TRAINING_LAYOUTS
from auditcore_invoicesynth.plan import SynthConfig, plan_dataset, sample_seed

FAMILIES = ("DejaVu Sans", "DejaVu Serif", "Liberation Sans")


def _record(country: str = "DE"):  # type: ignore[no-untyped-def]
    return InvoiceScenario(3, base_date=date(2026, 1, 15), country=country).generate(1)


@pytest.mark.parametrize("scheme", sorted(VAT_SCHEMES))
def test_amounts_are_consistent_for_every_scheme(scheme: str) -> None:
    country = VAT_SCHEMES[scheme][0]
    inv = enrich(_record(country), rng=Random(1), vat_scheme=scheme)
    assert inv.net_amount + inv.vat_amount == inv.total == inv.printed_total
    assert sum(p.amount for p in inv.positions) == inv.net_amount
    for line in inv.vat_lines:
        assert line.rate in ALLOWED_VAT_RATES[inv.country]
        assert line.amount == (line.base * line.rate / 100).quantize(Decimal("0.01"))
    assert iban_valid(inv.bank.iban) if inv.bank else False
    assert vat_id_valid(inv.supplier.vat_id)
    if scheme.endswith("mixed"):
        assert len(inv.vat_lines) == 2


def test_errors_change_only_the_printed_values() -> None:
    inv = enrich(
        _record(),
        rng=Random(2),
        vat_scheme="de_19",
        errors=("wrong_total", "missing_vat_id", "missing_iban"),
    )
    assert inv.printed_total != inv.total and inv.printed_total > 0
    assert inv.supplier.vat_id == "" and inv.bank is None
    with pytest.raises(ValueError):
        enrich(_record(), rng=Random(2), vat_scheme="de_19", errors=("duplicate",))
    with pytest.raises(ValueError):
        enrich(_record(), rng=Random(2), vat_scheme="fr_20")


def test_expanded_positions_keep_the_sum() -> None:
    plain = enrich(_record(), rng=Random(5), vat_scheme="de_19")
    many = enrich(_record(), rng=Random(5), vat_scheme="de_19", expand_positions=8)
    assert len(many.positions) == 8 * len(plain.positions)
    assert many.net_amount == plain.net_amount


def test_date_override() -> None:
    inv = enrich(_record(), rng=Random(1), vat_scheme="de_7", invoice_date=date(2026, 3, 1))
    assert inv.supply_date <= inv.invoice_date < inv.due_date


def test_at_least_eight_layouts_with_two_holdouts() -> None:
    assert len(LAYOUTS) >= 10 and len(TRAINING_LAYOUTS) >= 8 and len(HOLDOUT_LAYOUTS) == 2


def test_plan_is_deterministic_and_keeps_holdouts_separate() -> None:
    config = SynthConfig(
        counts={"train": 300, "validation": 20, "test_synthetic": 20, "test_layout_holdout": 40}
    )
    first, second = plan_dataset(config, FAMILIES), plan_dataset(config, FAMILIES)
    assert first == second
    for spec in first:
        holdout = spec.split == "test_layout_holdout"
        assert (spec.layout in HOLDOUT_LAYOUTS) == holdout
        assert (spec.font_family == "DejaVu Serif") == holdout
    assert {s.layout for s in first if s.split == "train"} == set(TRAINING_LAYOUTS)
    assert any(s.language == "en" for s in first) and any(s.country == "AT" for s in first)
    assert any(s.errors for s in first) and any(s.augment for s in first)
    assert all(
        s.vat_scheme == "de_kleinunternehmer" for s in first if s.layout == "kleinunternehmer"
    )
    assert all(s.kind == "credit_note" for s in first if s.layout == "gutschrift")
    other = plan_dataset(replace(config, seed=43), FAMILIES)
    assert [s.seed for s in other] != [s.seed for s in first]
    assert sample_seed(1, "a") == sample_seed(1, "a") != sample_seed(2, "a")


def test_plan_validation() -> None:
    with pytest.raises(ValueError):
        plan_dataset(SynthConfig(), ())
    with pytest.raises(ValueError):
        plan_dataset(SynthConfig(counts={"extra": 1}), FAMILIES)
    with pytest.raises(ValueError):
        plan_dataset(SynthConfig(dpi_choices=(10,)), FAMILIES)
    only_holdout_font = plan_dataset(
        SynthConfig(counts={"test_layout_holdout": 3}), ("DejaVu Serif",)
    )
    assert {s.font_family for s in only_holdout_font} == {"DejaVu Serif"}
