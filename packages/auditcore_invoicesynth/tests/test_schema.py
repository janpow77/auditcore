from __future__ import annotations

import pytest

from auditcore_invoicesynth.schema import (
    TASK_TOKEN,
    from_sequence,
    nest_fields,
    ordered,
    special_tokens,
    to_sequence,
)

GT = {
    "invoice_number": "RE-1",
    "supplier": {"name": "A GmbH", "vat_id": "DE136695976"},
    "vat_lines": [{"rate": "19 %", "amount": "19,00"}],
    "total": "119,00 €",
}


def test_sequence_round_trip_keeps_single_item_lists() -> None:
    sequence = to_sequence(GT)
    assert sequence.startswith(TASK_TOKEN)
    assert "<s_vat_lines><s_rate>19 %</s_rate>" in sequence
    assert from_sequence(sequence + "</s>") == ordered(GT)
    two = {**GT, "vat_lines": [{"rate": "19 %"}, {"rate": "7 %"}]}
    assert from_sequence(to_sequence(two))["vat_lines"] == [{"rate": "19 %"}, {"rate": "7 %"}]


def test_malformed_model_output_is_tolerated() -> None:
    assert from_sequence(f"{TASK_TOKEN}<s_total>1,00</s_total><s_iban>DE") == {"total": "1,00"}


def test_special_tokens_are_unique_and_complete() -> None:
    tokens = special_tokens()
    assert len(tokens) == len(set(tokens))
    for token in ("<s_total>", "</s_vat_id>", "<sep/>", TASK_TOKEN):
        assert token in tokens


def test_nest_and_reject() -> None:
    nested = nest_fields(
        {"supplier.name": "A", "vat_lines.1.rate": "7 %", "vat_lines.0.rate": "19 %"}
    )
    assert nested == {"supplier": {"name": "A"}, "vat_lines": [{"rate": "19 %"}, {"rate": "7 %"}]}
    with pytest.raises(ValueError):
        ordered({"positions": []})
    with pytest.raises(ValueError):
        to_sequence({"total": "<s_x>"})
