"""jsonable/decode_json against the verbatim package copies (differential)."""

from __future__ import annotations

import json
import math
from collections.abc import Callable
from datetime import date
from decimal import Decimal

import legacy_reference as legacy
import pytest
from samples import SAMPLES, Colour, Record, assert_same_outcome, random_value, rng

from auditcore_common.json_values import decode_json, jsonable

VARIANTS: dict[str, tuple[Callable[[object], object], Callable[[object], object]]] = {
    "risk.plain": (legacy.risk_plain, lambda v: jsonable(v)),
    "dataprotection.plain": (
        legacy.dataprotection_plain,
        lambda v: jsonable(v, enums=True, dataclasses=True, sets=True),
    ),
    "funding.json_safe": (
        legacy.funding_json_safe,
        lambda v: jsonable(v, decimals=True, nan_as_none=True),
    ),
}


@pytest.mark.parametrize("variant", sorted(VARIANTS))
def test_jsonable_matches_each_variant_on_random_values(variant: str) -> None:
    old, new = VARIANTS[variant]
    r = rng(hash(variant) & 0xFFFF)
    for _ in range(SAMPLES):
        value = random_value(r)
        assert_same_outcome(lambda: old(value), lambda: new(value))


@pytest.mark.parametrize("variant", sorted(VARIANTS))
@pytest.mark.parametrize(
    "value",
    [
        None,
        math.nan,
        [math.nan, {"x": math.inf}],
        Decimal("NaN"),
        Colour.NAN,
        {1: date(2026, 9, 25), "1": 2},
        {"b", "a"},
        frozenset({3, 1}),
        {1, "a"},
        Record("n", {"d": Decimal("1.50")}),
        Record,
        (),
        [],
        {},
        "text",
        b"raw",
    ],
)
def test_jsonable_edge_cases(variant: str, value: object) -> None:
    old, new = VARIANTS[variant]
    assert_same_outcome(lambda: old(value), lambda: new(value))


def test_funding_mapping_variant() -> None:
    r = rng(7)
    for _ in range(SAMPLES):
        value = {r.choice((1, "a", None)): random_value(r) for _ in range(3)}
        assert_same_outcome(
            lambda: legacy.funding_json_safe_mapping(value),
            lambda: jsonable(value, decimals=True, nan_as_none=True),
        )


BODIES = [b"{}", b"[1, 2]", b"", b"{", b"\xff\xfe", b"nan", b"NaN", "ä".encode(), b'"\\ud800"']


@pytest.mark.parametrize("body", BODIES + [b"x" * n for n in range(3)])
def test_decode_json_matches_legal_and_registry(body: bytes) -> None:
    what = "Quelle"
    assert_same_outcome(
        lambda: legacy.legal_json(body, what),
        lambda: decode_json(
            body, lambda exc: legacy.ParserError(f"{what}: Antwort ist kein JSON.")
        ),
    )
    assert_same_outcome(
        lambda: legacy.registry_json(body, what),
        lambda: decode_json(
            body, lambda exc: legacy.FormatError(f"{what}: keine gültige JSON-Antwort ({exc}).")
        ),
    )


def test_decode_json_on_random_documents() -> None:
    r = rng(11)
    for _ in range(SAMPLES):
        body = json.dumps(random_value(r), default=str).encode()
        if r.random() < 0.3:
            body = body[: r.randint(0, len(body))]
        assert_same_outcome(
            lambda: legacy.legal_json(body, "x"),
            lambda: decode_json(body, lambda exc: legacy.ParserError("x: Antwort ist kein JSON.")),
        )
