"""Seeded random inputs and a strict structural comparison for the differential tests."""

from __future__ import annotations

import math
import random
import struct
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum, IntEnum
from types import MappingProxyType

#: Samples per differential test; large enough to hit every branch many times.
SAMPLES = 4000

FLOATS = (
    0.0,
    -0.0,
    1.0,
    -1.5,
    0.1,
    1e-308,
    5e-324,
    1.7976931348623157e308,
    math.inf,
    -math.inf,
    math.nan,
    2.5,
    3.5,
    -2.5,
    1e16,
)
TEXTS = ("", "a", "Müller", "ß", "日本", "x y", "  ", "İ", "a\nb", "€", "\x00", "ǅ")


class Colour(Enum):
    """Plain enum."""

    RED = "red"
    NAN = math.nan


class Level(IntEnum):
    """Int enum."""

    LOW = 1


@dataclass
class Record:
    """Dataclass sample."""

    name: str
    value: object


def rng(seed: int) -> random.Random:
    """Seeded generator per test."""
    return random.Random(seed)


def random_float(r: random.Random) -> float:
    """Special values, random magnitudes and random bit patterns."""
    choice = r.random()
    if choice < 0.3:
        return r.choice(FLOATS)
    if choice < 0.6:
        return r.uniform(-1e6, 1e6)
    if choice < 0.8:
        return r.uniform(-1, 1) * 10.0 ** r.randint(-300, 300)
    return struct.unpack("<d", r.getrandbits(64).to_bytes(8, "little"))[0]


def random_scalar(r: random.Random) -> object:
    """Every scalar type the helpers distinguish."""
    kind = r.randrange(14)
    makers: tuple[Callable[[], object], ...] = (
        lambda: r.randint(-(10**12), 10**12),
        lambda: random_float(r),
        lambda: r.choice(TEXTS) + str(r.randint(0, 99)),
        lambda: r.choice((True, False, None)),
        lambda: Decimal(str(round(r.uniform(-1e4, 1e4), r.randint(0, 6)))),
        lambda: r.choice((Decimal("NaN"), Decimal("-0"), Decimal("1E+3"))),
        lambda: date(r.randint(1, 9999), r.randint(1, 12), r.randint(1, 28)),
        lambda: datetime(2026, 9, 25, 12, 0, tzinfo=r.choice((None, UTC))),
        lambda: datetime(2020, 1, 1, tzinfo=timezone(timedelta(hours=2))),
        lambda: r.choice(list(Colour)),
        lambda: Level.LOW,
        lambda: b"bytes",
        lambda: complex(1, 2),
        lambda: r.choice(TEXTS),
    )
    return makers[kind]()


def random_value(r: random.Random, depth: int = 0) -> object:
    """Nested mappings, sequences, sets, dataclasses and scalars."""
    if depth > 3 or r.random() < 0.45:
        return random_scalar(r)
    kind = r.randrange(9)
    size = r.randint(0, 4)
    if kind == 0:
        return {random_key(r): random_value(r, depth + 1) for _ in range(size)}
    if kind == 1:
        return [random_value(r, depth + 1) for _ in range(size)]
    if kind == 2:
        return tuple(random_value(r, depth + 1) for _ in range(size))
    if kind == 3:
        return {r.randint(-5, 5) for _ in range(size)}
    if kind == 4:
        return frozenset(r.choice(TEXTS) for _ in range(size))
    if kind == 5:
        return Record(r.choice(TEXTS), random_value(r, depth + 1))
    if kind == 6:
        return MappingProxyType({random_key(r): random_value(r, depth + 1) for _ in range(size)})
    if kind == 7:
        return {r.choice((1, "1", 2.5, None, True)): random_value(r, depth + 1)}
    return {r.randint(0, 3), "mixed"}


def random_key(r: random.Random) -> str:
    """Text keys including non-ASCII."""
    return r.choice(TEXTS) + r.choice(("", "k", "Ä", "1"))


def random_json(r: random.Random, depth: int = 0) -> object:
    """Values ``json.dumps`` accepts (plus NaN/inf), with text keys."""
    if depth > 3 or r.random() < 0.4:
        return r.choice(
            (
                r.randint(-(10**6), 10**6),
                random_float(r),
                r.choice(TEXTS),
                True,
                False,
                None,
            )
        )
    if r.random() < 0.5:
        return {random_key(r): random_json(r, depth + 1) for _ in range(r.randint(0, 4))}
    return [random_json(r, depth + 1) for _ in range(r.randint(0, 4))]


def outcome(function: Callable[[], object]) -> tuple[str, object]:
    """Result or ``(exception type, message, cause type)`` of a call."""
    try:
        return ("ok", function())
    except Exception as exc:  # noqa: BLE001 - the oracle compares every failure
        cause = type(exc.__cause__).__name__ if exc.__cause__ else None
        return ("error", (type(exc).__name__, str(exc), cause))


def same(left: object, right: object) -> bool:
    """Equal including types, float bit patterns, NaN and key order."""
    if type(left) is not type(right):
        return False
    if isinstance(left, float):
        return struct.pack("<d", left) == struct.pack("<d", right)  # type: ignore[arg-type]
    if isinstance(left, dict | MappingProxyType):
        assert isinstance(right, dict | MappingProxyType)
        return list(left) == list(right) and all(same(left[k], right[k]) for k in left)
    if isinstance(left, list | tuple):
        assert isinstance(right, list | tuple)
        return len(left) == len(right) and all(same(a, b) for a, b in zip(left, right, strict=True))
    if isinstance(left, Decimal):
        return str(left) == str(right)
    return left is right or left == right


def assert_same_outcome(legacy: Callable[[], object], new: Callable[[], object]) -> None:
    """Both calls return structurally equal values or fail identically."""
    expected, actual = outcome(legacy), outcome(new)
    assert expected[0] == actual[0], (expected, actual)
    if expected[0] == "error":
        assert expected == actual
    else:
        assert same(expected[1], actual[1]), (expected, actual)
