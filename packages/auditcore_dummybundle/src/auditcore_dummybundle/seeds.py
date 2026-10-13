"""Sub-streams of one seed, derived from domain keys instead of call order.

Changing the number of receipts of one claim must not shift the random draws of
another claim. Every entity therefore gets its own generator, seeded from the
run seed and its own key (for example ``"receipt", "MA-SYN-2025-0001-01", 3``).
"""

from __future__ import annotations

from random import Random

from auditcore_common.hashing import sha256_text


def derive_seed(seed: int, *keys: object) -> int:
    """Stable 64-bit seed for ``seed`` and the domain ``keys``."""
    text = "|".join([str(seed), *(str(key) for key in keys)])
    return int(sha256_text(text)[:16], 16)


def stream(seed: int, *keys: object) -> Random:
    """Independent random generator for ``seed`` and the domain ``keys``."""
    return Random(derive_seed(seed, *keys))


def pick_cents(rng: Random, low_cents: int, high_cents: int, *, skew: int = 1) -> int:
    """Whole cents in the inclusive range; ``skew`` > 1 favours small amounts."""
    if high_cents < low_cents:
        raise ValueError("high_cents must not be below low_cents")
    span = high_cents - low_cents + 1
    position = rng.randrange(0, 1_000_000)
    scaled = position
    for _ in range(skew - 1):
        scaled = scaled * position // 1_000_000
    return low_cents + scaled * span // 1_000_000
