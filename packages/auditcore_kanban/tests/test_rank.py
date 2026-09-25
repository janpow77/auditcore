from __future__ import annotations

import random

import pytest

from auditcore_kanban.rank import (
    DIGITS,
    is_strictly_increasing,
    is_valid_rank,
    rank_between,
    spread_ranks,
)


def test_alphabet_is_ascii_sorted_base62() -> None:
    assert len(DIGITS) == 62 and list(DIGITS) == sorted(DIGITS)


@pytest.mark.parametrize(("a", "b", "expected"), [
    (None, None, "V"), (None, "V", "F"), ("V", None, "k"), ("A", "B", "AV"),
    ("V", "V1", "V0V"), ("z", None, "zV"), (None, "01", "00V"), ("y1", "z", "yV"),
])
def test_known_midpoints(a: str | None, b: str | None, expected: str) -> None:
    key = rank_between(a, b)
    assert key == expected
    assert (a is None or a < key) and (b is None or key < b)


@pytest.mark.parametrize(("a", "b"), [("V", "V"), ("W", "V")])
def test_order_is_enforced(a: str, b: str) -> None:
    with pytest.raises(ValueError, match="not below"):
        rank_between(a, b)


@pytest.mark.parametrize("key", ["", "V0", "A!", "Ä"])
def test_invalid_keys_are_rejected(key: str) -> None:
    assert not is_valid_rank(key)
    with pytest.raises(ValueError, match="invalid"):
        rank_between(key, None)


def test_random_inserts_stay_ordered_without_renumbering() -> None:
    rng = random.Random(7)
    keys: list[str] = []
    for _ in range(500):
        slot = rng.randint(0, len(keys))
        low = keys[slot - 1] if slot else None
        high = keys[slot] if slot < len(keys) else None
        keys.insert(slot, rank_between(low, high))
    assert is_strictly_increasing(keys)
    assert len(set(keys)) == 500


def test_repeated_insert_at_front_grows_slowly() -> None:
    first = "V"
    for _ in range(100):
        first = rank_between(None, first)
    assert len(first) < 30 and is_valid_rank(first)


@pytest.mark.parametrize("count", [0, 1, 2, 61, 62, 63, 3843, 3844, 10_000])
def test_spread_is_increasing_and_short(count: int) -> None:
    keys = spread_ranks(count)
    assert len(keys) == count and is_strictly_increasing(keys)
    assert all(len(k) <= 3 for k in keys)


def test_spread_limits() -> None:
    with pytest.raises(ValueError):
        spread_ranks(-1)
    with pytest.raises(ValueError):
        spread_ranks(62**6)
