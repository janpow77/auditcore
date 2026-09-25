"""Pairwise sum, rounding, finite checks and percent rates (differential)."""

from __future__ import annotations

import importlib.util
import math
import struct

import legacy_reference as legacy
import pytest
from samples import FLOATS, SAMPLES, assert_same_outcome, random_float, rng

from auditcore_common.numeric import (
    numpy_pairwise_sum,
    numpy_round,
    parse_percent_rate,
    require_finite,
)

LENGTHS = [0, 1, 7, 8, 9, 15, 16, 17, 127, 128, 129, 255, 256, 257, 1000, 1024, 1031]


def _bits(value: float) -> bytes:
    return struct.pack("<d", value)


def test_pairwise_sum_is_bitwise_equal_to_all_copies() -> None:
    r = rng(31)
    lengths = LENGTHS + [r.randint(0, 2100) for _ in range(300)]
    for length in lengths:
        mode = r.random()
        if mode < 0.2:
            values = [r.choice(FLOATS) for _ in range(length)]
        elif mode < 0.6:
            values = [r.uniform(-1e3, 1e3) for _ in range(length)]
        else:
            values = [random_float(r) for _ in range(length)]
        expected = _bits(legacy.statistics_pairwise_sum(values))
        assert _bits(legacy.sampling_pairwise_sum(values)) == expected
        assert _bits(legacy.market_pairwise_sum(values)) == expected
        assert _bits(numpy_pairwise_sum(values)) == expected
        assert _bits(numpy_pairwise_sum(tuple(values))) == expected


def test_pairwise_sum_accepts_integers_like_the_copies() -> None:
    values = list(range(300))
    assert_same_outcome(
        lambda: legacy.statistics_pairwise_sum(values), lambda: numpy_pairwise_sum(values)
    )


def test_numpy_round_matches_copies() -> None:
    r = rng(32)
    for _ in range(SAMPLES * 5):
        value = random_float(r) if r.random() < 0.5 else r.randint(-(10**6), 10**6) / 1000 + 0.0005
        decimals = r.randint(-3, 10)
        for copy in (legacy.statistics_numpy_round, legacy.sampling_numpy_round):
            assert_same_outcome(
                lambda: copy(value, decimals),  # noqa: B023 - called immediately
                lambda: numpy_round(value, decimals),
            )


@pytest.mark.skipif(importlib.util.find_spec("numpy") is None, reason="numpy nicht installiert")
def test_against_numpy_itself() -> None:
    import numpy as np

    r = rng(33)
    for length in LENGTHS + [r.randint(0, 3000) for _ in range(100)]:
        values = [r.uniform(-1e6, 1e6) * 10.0 ** r.randint(-5, 5) for _ in range(length)]
        array = np.asarray(values, dtype=np.float64)
        assert _bits(numpy_pairwise_sum(values)) == _bits(float(np.add.reduce(array)))
    for _ in range(SAMPLES):
        value = r.uniform(-1e4, 1e4)
        decimals = r.randint(0, 8)
        assert _bits(numpy_round(value, decimals)) == _bits(float(np.round(value, decimals)))


FINITE_INPUTS: list[object] = [0, 1, -2, 1.5, True, False, None, "1", math.nan, math.inf, 10**400]


@pytest.mark.parametrize("value", FINITE_INPUTS)
def test_require_finite_matches_geo_and_market(value: object) -> None:
    name = "Breite"
    assert_same_outcome(
        lambda: legacy.geo_endlich(value, name),  # type: ignore[arg-type]
        lambda: require_finite(
            value,
            not_number=lambda: legacy.KoordinatenFehler(f"{name} ist keine Zahl: {value!r}"),
            not_finite=lambda: legacy.KoordinatenFehler(f"{name} ist nicht endlich: {value!r}"),
        ),
    )
    assert_same_outcome(
        lambda: legacy.market_finite(value, name),
        lambda: require_finite(
            value,
            not_number=lambda: legacy.IndicatorInputError(f"{name} muss eine Zahl sein."),
            not_finite=lambda: legacy.IndicatorInputError(f"{name} muss endlich sein."),
        ),
    )


def test_require_finite_on_random_floats() -> None:
    r = rng(34)
    for _ in range(SAMPLES):
        value = random_float(r)
        assert_same_outcome(
            lambda: legacy.market_finite(value, "x"),
            lambda: require_finite(
                value,
                not_number=lambda: legacy.IndicatorInputError("x muss eine Zahl sein."),
                not_finite=lambda: legacy.IndicatorInputError("x muss endlich sein."),
            ),
        )


def test_percent_rate_matches_documents_and_invoicesynth() -> None:
    r = rng(35)
    alphabet = "0123456789.,% \t\n-+eE٣"
    fixed = ["19 %", "19%", "19,0 %", "7.5", "0", "100", "7,55", " 7 ", "", "%", "07", "1.0%"]
    size = range(SAMPLES * 5)
    randoms = ["".join(r.choice(alphabet) for _ in range(r.randint(0, 7))) for _ in size]
    texts = fixed + randoms
    for text in texts:
        assert_same_outcome(lambda: legacy.documents_rate(text), lambda: parse_percent_rate(text))
        assert_same_outcome(
            lambda: legacy.invoicesynth_parse_rate(text), lambda: parse_percent_rate(text)
        )
