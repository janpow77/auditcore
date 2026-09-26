"""Rank keys: ordered strings that allow inserting between two cards without renumbering.

The algorithm is a base-62 fractional index (midpoint after D. Greenspan). The
TypeScript package ``@auditcore/kanban-core`` implements it character for
character; ``tests/fixtures/parity/rank.json`` pins both implementations.

Keys use the ASCII-ordered alphabet ``0-9A-Za-z``, are never empty and never end
with ``0`` (so a key strictly between any two keys always exists). Plain string
comparison orders them.
"""

from __future__ import annotations

DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
BASE = len(DIGITS)
MAX_SPREAD_LENGTH = 6


def is_valid_rank(key: str) -> bool:
    """True for a non-empty key over the alphabet that does not end with ``0``."""
    return bool(key) and all(ch in DIGITS for ch in key) and not key.endswith("0")


def _check(key: str | None) -> None:
    if key is not None and not is_valid_rank(key):
        raise ValueError(f"invalid rank key: {key!r}")


def _midpoint(low: str, high: str | None) -> str:
    """Key strictly between ``low`` ('' = minimum) and ``high`` (None = maximum)."""
    if high is not None:
        prefix = 0
        while prefix < len(high) and (low[prefix] if prefix < len(low) else "0") == high[prefix]:
            prefix += 1
        if prefix > 0:
            return high[:prefix] + _midpoint(low[prefix:], high[prefix:])
    digit_low = DIGITS.index(low[0]) if low else 0
    digit_high = DIGITS.index(high[0]) if high is not None else BASE
    if digit_high - digit_low > 1:
        return DIGITS[(digit_low + digit_high) // 2]
    if high is not None and len(high) > 1:
        return high[:1]
    return DIGITS[digit_low] + _midpoint(low[1:], None)


def rank_between(before: str | None, after: str | None) -> str:
    """Key strictly between ``before`` and ``after``; None means open end."""
    _check(before)
    _check(after)
    if before is not None and after is not None and before >= after:
        raise ValueError(f"rank {before!r} is not below {after!r}")
    return _midpoint(before or "", after)


def _encode(value: int, length: int) -> str:
    chars: list[str] = []
    for _ in range(length):
        value, digit = divmod(value, BASE)
        chars.append(DIGITS[digit])
    return "".join(reversed(chars))


def spread_ranks(count: int) -> list[str]:
    """``count`` evenly spaced increasing keys (import, rebalancing)."""
    if count < 0:
        raise ValueError("count must not be negative")
    if count == 0:
        return []
    length = 1
    while BASE**length <= count:
        length += 1
        if length > MAX_SPREAD_LENGTH:
            raise ValueError("too many keys for one spread")
    space = BASE**length
    keys = []
    for index in range(count):
        value = (index + 1) * space // (count + 1)
        keys.append(_encode(value, length).rstrip("0"))
    return keys


def is_strictly_increasing(keys: list[str]) -> bool:
    """True when every key is valid and greater than its predecessor."""
    if not all(is_valid_rank(k) for k in keys):
        return False
    return all(a < b for a, b in zip(keys, keys[1:], strict=False))
