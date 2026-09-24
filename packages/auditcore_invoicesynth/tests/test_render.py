from __future__ import annotations

from datetime import date
from decimal import Decimal
from random import Random

import pytest
from auditcore_invoicegenerator import InvoiceScenario

from auditcore_invoicesynth.augment import augment_page
from auditcore_invoicesynth.enrich import enrich
from auditcore_invoicesynth.fonts import FontSet
from auditcore_invoicesynth.labels import SYNTHETIC_FOOTER, SYNTHETIC_MARKER, Language
from auditcore_invoicesynth.layouts import LAYOUTS, Variant, expansion
from auditcore_invoicesynth.plan import AugmentSpec
from auditcore_invoicesynth.render import render_pages


def _variant(language: Language = "de") -> Variant:
    return Variant.choose(
        Random(1),
        language=language,
        country="DE",
        amount_style="de_grouped",
        currency_style="suffix_symbol",
        date_style="de_numeric",
        rate_variant=0,
        iban_grouped=True,
    )


@pytest.mark.parametrize("layout", sorted(LAYOUTS))
def test_every_layout_marks_every_page_and_prints_required_fields(
    layout: str, fonts: FontSet
) -> None:
    record = InvoiceScenario(1, base_date=date(2026, 1, 15)).generate(1)
    scheme = "de_kleinunternehmer" if layout == "kleinunternehmer" else "de_mixed"
    inv = enrich(
        record,
        rng=Random(4),
        vat_scheme=scheme,
        expand_positions=expansion(layout, len(record["line_items"])),
    )
    pages = render_pages(
        inv, _variant(), layout, fonts, family=fonts.families[0], dpi=60, base_size_pt=10
    )
    assert (len(pages) > 1) == (layout == "mehrseitig")
    printed: dict[str, str] = {}
    for page in pages:
        text = " ".join(page.texts)
        assert SYNTHETIC_MARKER in text and SYNTHETIC_FOOTER in text
        assert page.image.size == (496, 702)
        for key, value in page.fields.items():
            if key not in {"document_type", "currency"}:  # Klassifikation, kein Text
                assert value in text  # Ziel-JSON enthält nur Gedrucktes
            printed.setdefault(key, value)
    assert printed["invoice_number"] == inv.invoice_number
    assert printed["supplier.vat_id"] == inv.supplier.vat_id
    assert printed["total"] == _variant().money(inv.printed_total)
    assert printed["iban"].replace(" ", "") == inv.bank.iban  # type: ignore[union-attr]
    if scheme == "de_mixed":
        assert printed["vat_lines.1.rate"] == "7 %"


def test_augmentation_is_seed_deterministic(fonts: FontSet) -> None:
    record = InvoiceScenario(1, base_date=date(2026, 1, 15)).generate(1)
    inv = enrich(record, rng=Random(1), vat_scheme="de_19")
    page = render_pages(
        inv, _variant("en"), "kopf_links", fonts, family=fonts.families[0], dpi=60, base_size_pt=9
    )[0]
    spec = AugmentSpec(2.5, 0.01, 0.8, 50, 0.002, "binary", True, 2, True, True)
    one = augment_page(page.image, spec, 99)
    two = augment_page(page.image, spec, 99)
    three = augment_page(page.image, spec, 100)
    assert one.tobytes() == two.tobytes() != three.tobytes()
    assert one.tobytes() != page.image.convert("L").tobytes()
    assert Decimal(inv.total) > 0
