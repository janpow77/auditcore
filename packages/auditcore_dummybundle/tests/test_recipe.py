"""Freie Tabelle: strenge Rezeptprüfung, Regeln zwischen Spalten, Summenbindung, Rundlauf."""

from __future__ import annotations

import copy
from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from auditcore_dummybundle import (
    BundleError,
    RecipeLimits,
    generate_recipe,
    generate_table,
    parse_recipe,
    recipe_document,
    template_recipe,
    templates,
)

VERSION = "0.2.0"


def recipe(fields: list[dict[str, Any]], **run: Any) -> dict[str, Any]:
    settings_ = {"seed": 7, "base_date": "2026-01-01", "rows": 40, "country": "DE"}
    settings_.update(run)
    return {
        "format": "auditcore.dummybundle.recipe",
        "format_version": 1,
        "title": "Probe",
        "run": settings_,
        "fields": fields,
    }


def column(raw: dict[str, Any], name: str) -> list[Any]:
    table = generate_table(parse_recipe(raw))
    index = [c.header for c in table.columns].index(name)
    return [row[index] for row in table.rows]


BASIC = [
    {"name": "Nr", "type": "sequence"},
    {
        "name": "Rechnungsdatum",
        "type": "date",
        "params": {"start": "2025-07-01", "end": "2025-12-31"},
    },
    {
        "name": "Zahlung",
        "type": "date_offset",
        "params": {"field": "Rechnungsdatum", "min_days": 0, "max_days": 30},
    },
    {"name": "Netto", "type": "amount", "params": {"min": "10.00", "max": "5000.00"}},
    {
        "name": "USt",
        "type": "computed",
        "params": {"operation": "rate", "fields": ["Netto"], "rate": "0.19"},
    },
    {
        "name": "Brutto",
        "type": "computed",
        "params": {"operation": "sum", "fields": ["Netto", "USt"]},
    },
    {
        "name": "Kostenart",
        "type": "choice",
        "params": {"values": [{"value": "Personal", "weight": 1}, {"value": "Sach", "weight": 3}]},
    },
    {
        "name": "Stundenzettel",
        "type": "choice",
        "params": {"values": [{"value": "Ja"}]},
        "rule": {
            "kind": "when",
            "field": "Kostenart",
            "equals": "Personal",
            "value": "Ja",
            "otherwise": "Entfällt",
        },
    },
]


def test_rules_between_columns_hold() -> None:
    raw = recipe(BASIC)
    net, vat, gross = (column(raw, name) for name in ("Netto", "USt", "Brutto"))
    for n, v, g in zip(net, vat, gross, strict=True):
        assert v == (n * Decimal("0.19")).quantize(Decimal("0.01"), rounding="ROUND_HALF_UP")
        assert g == n + v
    invoice, paid = column(raw, "Rechnungsdatum"), column(raw, "Zahlung")
    assert all(date(2025, 7, 1) <= i <= date(2025, 12, 31) for i in invoice)
    assert all(0 <= (p - i).days <= 30 for i, p in zip(invoice, paid, strict=True))
    kinds, sheets = column(raw, "Kostenart"), column(raw, "Stundenzettel")
    assert {"Personal", "Sach"} == set(kinds)
    assert all((s == "Ja") == (k == "Personal") for k, s in zip(kinds, sheets, strict=True))
    assert column(raw, "Nr") == list(range(1, 41))


def test_difference_product_and_date_before() -> None:
    raw = recipe(
        [
            {"name": "A", "type": "amount"},
            {
                "name": "B",
                "type": "amount_factor",
                "params": {"field": "A", "min_factor": "0.50", "max_factor": "1.00"},
            },
            {
                "name": "D",
                "type": "computed",
                "params": {"operation": "difference", "fields": ["A", "B"]},
            },
            {"name": "Menge", "type": "integer", "params": {"min": 1, "max": 9}},
            {
                "name": "P",
                "type": "computed",
                "params": {"operation": "product", "fields": ["Menge", "A"]},
            },
            {"name": "Ende", "type": "date"},
            {
                "name": "Beginn",
                "type": "date_offset",
                "params": {"field": "Ende", "min_days": -60, "max_days": -1},
            },
        ]
    )
    a, b, d, qty, p = (column(raw, name) for name in ("A", "B", "D", "Menge", "P"))
    assert all(x - y == z and z >= 0 for x, y, z in zip(a, b, d, strict=True))
    assert all(q * x == y for q, x, y in zip(qty, a, p, strict=True))
    assert all(s < e for s, e in zip(column(raw, "Beginn"), column(raw, "Ende"), strict=True))


@settings(max_examples=80, deadline=None)
@given(seed=st.integers(0, 2**31 - 1), rows=st.integers(1, 200), cents=st.integers(0, 10**10))
def test_sum_binding_is_exact_for_every_seed(seed: int, rows: int, cents: int) -> None:
    total = Decimal(cents) / 100
    raw = recipe(
        [{"name": "Betrag", "type": "amount", "rule": {"kind": "sum_to", "total": str(total)}}],
        seed=seed,
        rows=rows,
    )
    values = column(raw, "Betrag")
    assert sum(values) == total and min(values) >= 0


def test_sum_binding_per_group_and_with_empty_cells() -> None:
    raw = recipe(
        [
            {
                "name": "Gruppe",
                "type": "choice",
                "params": {"values": [{"value": "A"}, {"value": "B"}, {"value": "C"}]},
            },
            {
                "name": "Betrag",
                "type": "amount",
                "empty_share": "0.2",
                "rule": {"kind": "sum_to", "total": "1000.00", "group_by": "Gruppe"},
            },
        ],
        rows=90,
    )
    groups, values = column(raw, "Gruppe"), column(raw, "Betrag")
    assert None in values
    for name in "ABC":
        own = [v for g, v in zip(groups, values, strict=True) if g == name and v is not None]
        assert sum(own) == Decimal("1000.00")


def test_empty_share_and_derived_cells_stay_empty() -> None:
    raw = recipe(
        [
            {"name": "A", "type": "amount", "empty_share": "0.5"},
            {
                "name": "B",
                "type": "computed",
                "params": {"operation": "rate", "fields": ["A"], "rate": "2"},
            },
            {"name": "Voll", "type": "company", "empty_share": 0},
            {"name": "Leer", "type": "company", "empty_share": 1},
        ],
        rows=200,
    )
    a, b = column(raw, "A"), column(raw, "B")
    assert 60 < a.count(None) < 140
    assert all((x is None) == (y is None) for x, y in zip(a, b, strict=True))
    assert None not in column(raw, "Voll") and set(column(raw, "Leer")) == {None}


def test_columns_are_independent_of_each_other() -> None:
    base = recipe(BASIC)
    extended = recipe([{"name": "Neu", "type": "iban"}, *BASIC[:4], {"name": "X", "type": "text"}])
    for name in ("Rechnungsdatum", "Zahlung", "Netto"):
        assert column(base, name) == column(extended, name)


def test_every_field_type_generates_and_addresses_fit_together() -> None:
    from auditcore_dummybundle.fieldtypes import FIELD_TYPES

    simple = [k for k in FIELD_TYPES if not any(p.required for p in k.params)]
    assert len(FIELD_TYPES) == 21 and len(simple) == 16
    fields = [{"name": kind.id, "type": kind.id} for kind in simple]
    fields += [
        {"name": part, "type": "address", "params": {"part": part}}
        for part in ("street", "postal_code", "city", "country")
    ]
    raw = recipe(fields, country="DE+AT", rows=60)
    table = generate_table(parse_recipe(raw))
    assert len(table.rows) == 60
    for full, street, code, city in zip(
        *(column(raw, n) for n in ("address", "street", "postal_code", "city")), strict=True
    ):
        assert full == f"{street}, {code} {city}"
    assert all(str(mail).endswith("@example.org") for mail in column(raw, "email"))
    assert set(column(raw, "person")) and all(" " in str(p) for p in column(raw, "person"))
    assert {len(str(code)) for code in column(raw, "nuts")} == {5}


def test_pattern_placeholders() -> None:
    raw = recipe(
        [
            {
                "name": "Datum",
                "type": "date",
                "params": {"start": "2024-03-01", "end": "2024-03-31"},
            },
            {
                "name": "Nr",
                "type": "pattern",
                "params": {"pattern": "AZ-{JJJJ}/{MM}-{NNN}-{ZZ}{AA}", "date_field": "Datum"},
            },
        ],
        rows=5,
    )
    values = column(raw, "Nr")
    assert [v[:15] for v in values] == [f"AZ-2024/03-{i:03d}-" for i in range(1, 6)]
    assert all(v[15:17].isdigit() and v[17:].isalpha() and len(v) == 19 for v in values)


def test_recipe_round_trip_and_reproducibility() -> None:
    parsed = parse_recipe(recipe(BASIC))
    written = recipe_document(parsed, VERSION)
    assert parse_recipe(written) == parse_recipe(copy.deepcopy(written))
    assert recipe_document(parse_recipe(written), VERSION) == written
    assert written["marking"] == "SYNTHETISCH"
    assert written["generator"] == {"package": "auditcore_dummybundle", "version": VERSION}
    assert generate_table(parsed) == generate_table(parse_recipe(written))
    result = generate_recipe(parsed)
    assert result.meta["recipe"] == written and result.meta["marking"] == "SYNTHETISCH"


BROKEN: list[tuple[str, dict[str, Any], str]] = [
    ("unknown_key", {**recipe(BASIC), "sql": "x"}, "unknown_key"),
    ("wrong_format", {**recipe(BASIC), "format": "anderes"}, "unknown_format"),
    ("wrong_version", {**recipe(BASIC), "format_version": 2}, "unknown_format"),
    ("wrong_marking", {**recipe(BASIC), "marking": "ECHT"}, "invalid_input"),
    ("no_fields", recipe([]), "too_large"),
    ("unknown_type", recipe([{"name": "A", "type": "sql"}]), "unknown_value"),
    (
        "unknown_param",
        recipe([{"name": "A", "type": "amount", "params": {"mean": 1}}]),
        "unknown_key",
    ),
    (
        "unknown_field_key",
        recipe([{"name": "A", "type": "amount", "formula": "=1"}]),
        "unknown_key",
    ),
    (
        "bad_number",
        recipe([{"name": "A", "type": "amount", "params": {"min": "abc"}}]),
        "invalid_input",
    ),
    (
        "duplicate_name",
        recipe([{"name": "A", "type": "iban"}, {"name": "A", "type": "bic"}]),
        "duplicate",
    ),
    (
        "unknown_reference",
        recipe([{"name": "A", "type": "date_offset", "params": {"field": "B"}}]),
        "unknown_field",
    ),
    (
        "self_reference",
        recipe([{"name": "A", "type": "date_offset", "params": {"field": "A"}}]),
        "unknown_field",
    ),
    ("missing_required", recipe([{"name": "A", "type": "computed"}]), "missing"),
    (
        "sum_on_text",
        recipe([{"name": "A", "type": "iban", "rule": {"kind": "sum_to", "total": "1"}}]),
        "rule_not_applicable",
    ),
    (
        "unknown_rule",
        recipe([{"name": "A", "type": "amount", "rule": {"kind": "eval"}}]),
        "unknown_value",
    ),
    ("missing_seed", {**recipe(BASIC), "run": {"base_date": "2026-01-01", "rows": 1}}, "missing"),
    ("bad_date", recipe(BASIC, base_date="01.01.2026"), "invalid_input"),
    (
        "empty_share_range",
        recipe([{"name": "A", "type": "iban", "empty_share": 2}]),
        "invalid_input",
    ),
    ("control_character", recipe([{"name": "A\u0000", "type": "iban"}]), "invalid_input"),
    (
        "cycle",
        recipe(
            [
                {"name": "A", "type": "amount_factor", "params": {"field": "B"}},
                {"name": "B", "type": "amount_factor", "params": {"field": "A"}},
            ]
        ),
        "cycle",
    ),
]


@pytest.mark.parametrize(
    ("raw", "code"), [(r, c) for _, r, c in BROKEN], ids=[n for n, _, _ in BROKEN]
)
def test_strict_loading_rejects(raw: dict[str, Any], code: str) -> None:
    with pytest.raises(BundleError) as error:
        parse_recipe(raw)
    assert error.value.code == code
    assert str(error.value)


GENERATION_ERRORS: list[tuple[str, list[dict[str, Any]], str]] = [
    (
        "text_as_number",
        [
            {"name": "A", "type": "iban"},
            {"name": "B", "type": "amount_factor", "params": {"field": "A"}},
        ],
        "not_numeric",
    ),
    (
        "number_as_date",
        [
            {"name": "A", "type": "amount"},
            {"name": "B", "type": "date_offset", "params": {"field": "A"}},
        ],
        "not_a_date",
    ),
    (
        "reversed_range",
        [{"name": "A", "type": "amount", "params": {"min": "5", "max": "1"}}],
        "invalid_range",
    ),
    (
        "reversed_dates",
        [{"name": "A", "type": "date", "params": {"start": "2026-01-02", "end": "2026-01-01"}}],
        "invalid_range",
    ),
    (
        "placeholder",
        [{"name": "A", "type": "pattern", "params": {"pattern": "{QQ}"}}],
        "unknown_placeholder",
    ),
    (
        "rate_with_two",
        [
            {"name": "A", "type": "amount"},
            {"name": "B", "type": "amount"},
            {
                "name": "C",
                "type": "computed",
                "params": {"operation": "rate", "fields": ["A", "B"]},
            },
        ],
        "invalid_fields",
    ),
    (
        "rule_value",
        [
            {"name": "K", "type": "boolean"},
            {
                "name": "A",
                "type": "amount",
                "rule": {"kind": "when", "field": "K", "equals": "Ja", "value": "viel"},
            },
        ],
        "not_numeric",
    ),
]


@pytest.mark.parametrize(
    ("fields", "code"),
    [(f, c) for _, f, c in GENERATION_ERRORS],
    ids=[n for n, _, _ in GENERATION_ERRORS],
)
def test_impossible_definitions_are_reported_before_output(
    fields: list[dict[str, Any]], code: str
) -> None:
    with pytest.raises(BundleError) as error:
        generate_table(parse_recipe(recipe(fields)))
    assert error.value.code == code


def test_limits_apply() -> None:
    limits = RecipeLimits(max_rows=10, max_fields=2)
    with pytest.raises(BundleError):
        parse_recipe(recipe(BASIC[:2], rows=11), limits)
    with pytest.raises(BundleError):
        parse_recipe(recipe(BASIC[:3], rows=5), limits)
    assert parse_recipe(recipe(BASIC[:2], rows=10), limits).rows == 10


@pytest.mark.parametrize("template_id", ["V0", "V2", "V4", "V8", "V9", "N1"])
def test_templates_serve_as_starting_point(template_id: str) -> None:
    template = templates()[template_id]
    raw = template_recipe(
        template, seed=3, base_date=date(2026, 1, 1), rows=25, country="AT", version=VERSION
    )
    parsed = parse_recipe(raw)
    assert parsed.derived_from == template_id
    table = generate_table(parsed)
    assert [c.header for c in table.columns] == [c.header for c in template.tables[0].columns]
    assert len(table.rows) == 25


@pytest.mark.parametrize("template_id", ["V5", "V6", "V7"])
def test_aggregated_templates_are_no_starting_point(template_id: str) -> None:
    with pytest.raises(BundleError) as error:
        template_recipe(
            templates()[template_id],
            seed=1,
            base_date=date(2026, 1, 1),
            rows=5,
            country="DE",
            version=VERSION,
        )
    assert error.value.code == "no_free_start"
