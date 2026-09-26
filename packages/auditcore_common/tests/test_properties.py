"""Property-based equality with the former package copies (Hypothesis).

Complements the seeded differential tests: Hypothesis searches the input space
of the helpers migrated from sampling, statistics and market_indicators for a
counterexample and shrinks it. Skipped when ``hypothesis`` is not installed
(it is part of the ``dev`` extra).
"""

from __future__ import annotations

import struct
from decimal import Decimal

import legacy_reference as legacy
import legacy_rest
import pytest
from samples import assert_same_outcome

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from auditcore_common import rest  # noqa: E402
from auditcore_common.hashing import canonical_sha256  # noqa: E402
from auditcore_common.numeric import numpy_pairwise_sum, numpy_round, require_finite  # noqa: E402

EXAMPLES = settings(max_examples=400, deadline=None)
FLOATS = st.floats(allow_nan=True, allow_infinity=True, width=64)
JSON = st.recursive(
    st.none()
    | st.booleans()
    | st.integers()
    | st.floats(allow_nan=False, allow_infinity=False)
    | st.text(),
    lambda children: (
        st.lists(children, max_size=4) | st.dictionaries(st.text(max_size=6), children, max_size=4)
    ),
    max_leaves=12,
)


def _bits(value: float) -> bytes:
    return struct.pack("<d", value)


@EXAMPLES
@given(st.lists(FLOATS, max_size=600))
def test_pairwise_sum_equals_sampling_statistics_and_market(values: list[float]) -> None:
    expected = _bits(numpy_pairwise_sum(values))
    assert _bits(legacy.sampling_pairwise_sum(values)) == expected
    assert _bits(legacy.statistics_pairwise_sum(values)) == expected
    assert _bits(legacy.market_pairwise_sum(values)) == expected


@EXAMPLES
@given(FLOATS, st.integers(min_value=-5, max_value=12))
def test_numpy_round_equals_sampling_and_statistics(value: float, decimals: int) -> None:
    for copy in (legacy.sampling_numpy_round, legacy.statistics_numpy_round):
        assert_same_outcome(
            lambda: copy(value, decimals),  # noqa: B023 - called immediately
            lambda: numpy_round(value, decimals),
        )


@EXAMPLES
@given(
    st.one_of(FLOATS, st.integers(), st.booleans(), st.none(), st.text(max_size=3), st.decimals()),
    st.sampled_from(("annualization_factor", "vf_threshold", "x")),
)
def test_require_finite_equals_market_finite(value: object, name: str) -> None:
    assert_same_outcome(
        lambda: legacy.market_finite(value, name),
        lambda: require_finite(
            value,
            not_number=lambda: legacy.IndicatorInputError(f"{name} muss eine Zahl sein."),
            not_finite=lambda: legacy.IndicatorInputError(f"{name} muss endlich sein."),
        ),
    )


@EXAMPLES
@given(st.dictionaries(st.text(max_size=8), JSON, max_size=6))
def test_canonical_sha256_equals_market_fingerprint(data: dict[str, object]) -> None:
    assert canonical_sha256(data) == legacy.fingerprint(data)


def _decode_outcome(function: object) -> object:
    try:
        return ("ok", function())  # type: ignore[operator]
    except (rest.ContractError, ValueError) as exc:
        return ("error", str(exc), getattr(exc, "status", None), getattr(exc, "code", None))


@EXAMPLES
@given(
    st.one_of(st.binary(max_size=40), JSON.map(lambda v: repr(v).encode())),
    st.integers(min_value=0, max_value=64),
)
def test_decode_body_equals_sampling_and_statistics(raw: bytes, limit: int) -> None:
    old_sampling = _decode_outcome(lambda: legacy_rest.sampling_decode(raw, limit))
    new_sampling = _decode_outcome(lambda: rest.decode_body(raw, limit))
    old_statistics = _decode_outcome(lambda: legacy_rest.statistics_decode(raw, limit))
    new_statistics = _decode_outcome(lambda: rest.decode_body(raw, limit, parse_float=Decimal))
    assert repr(old_sampling) == repr(new_sampling)
    assert repr(old_statistics) == repr(new_statistics)


@EXAMPLES
@given(st.one_of(st.text(max_size=12), st.none(), st.integers()), st.text(max_size=10))
def test_choice_equals_sampling_and_statistics(value: object, name: str) -> None:
    allowed = ("proportional", "equal", "first")
    old = _decode_outcome(lambda: legacy_rest.sampling_choice(value, name, allowed))
    assert repr(old) == repr(_decode_outcome(lambda: rest.choice(value, name, allowed)))
    old_field = _decode_outcome(lambda: legacy_rest.statistics_field({name: value}, name, allowed))
    assert repr(old_field) == repr(old)
