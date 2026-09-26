"""Benford REST contract: profiles and analysis (framework-free).

Values arrive as parsed JSON; the HTTP adapters decode JSON numbers as
:class:`decimal.Decimal`, so the digits analysed are exactly the digits sent.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from decimal import Decimal
from typing import cast

from auditcore_common import rest

from .. import __version__
from ..benford import METHOD, ShortValues, StatisticsInputError, benford_test
from ..conformity import PROFILES, TESTS, Test, assess

LIBRARY = f"auditcore_statistics {__version__}"
MAX_VALUES = 1_000_000

TEST_LABELS: Mapping[str, tuple[str, int]] = {
    "first": ("Erste Ziffer (1–9)", 1),
    "first_two": ("Erste zwei Ziffern (10–99)", 2),
    "second": ("Zweite Ziffer (0–9)", 2),
}
SHORT_VALUES = (
    {"id": "exclude", "label": "Werte mit nur einer signifikanten Ziffer ausschließen"},
    {"id": "pad", "label": "Mit 0 auffüllen (5 → 50)"},
)


class ContractError(rest.ContractError):
    """Request does not satisfy the Benford REST contract (status, code, ``to_dict``)."""


def catalogue() -> dict[str, object]:
    """``GET /profiles``: tests, options for short values and assessment profiles."""
    return {
        "library": LIBRARY,
        "method": METHOD,
        "tests": [
            {"id": t, "label": TEST_LABELS[t][0], "digits": TEST_LABELS[t][1]} for t in TESTS
        ],
        "short_values": [dict(s) for s in SHORT_VALUES],
        "profiles": [p.to_dict() for p in PROFILES.values()],
        "limits": {"max_values": MAX_VALUES},
    }


def _value(raw: object, index: int) -> int | float | Decimal | None:
    if raw is None or isinstance(raw, (int, Decimal)) and not isinstance(raw, bool):
        return raw
    if isinstance(raw, float) and math.isfinite(raw):
        return raw
    raise ContractError(f"'values[{index}]' muss eine Zahl oder null sein.")


def _values(raw: object) -> list[int | float | Decimal | None]:
    entries = rest.bounded_list(raw, "values", MAX_VALUES, "Werte", error=ContractError)
    return [_value(v, i) for i, v in enumerate(entries)]


def _field(body: Mapping[str, object], key: str, allowed: tuple[str, ...]) -> str:
    return rest.choice(body.get(key), key, allowed, error=ContractError)


def analyse(payload: object) -> dict[str, object]:
    """``POST /analyze``: distribution, exclusions and conformity under a named profile."""
    if not isinstance(payload, Mapping):
        raise ContractError("Die Anfrage muss ein JSON-Objekt sein.")
    body = cast(Mapping[str, object], payload)
    test = cast(Test, _field(body, "test", TESTS))
    profile_id = _field(body, "profile", tuple(PROFILES))
    digits = TEST_LABELS[test][1]
    short = (
        cast(ShortValues, _field(body, "short_values", ("exclude", "pad"))) if digits == 2 else None
    )
    if digits == 1 and body.get("short_values") is not None:
        raise ContractError("'short_values' gilt nur für zweistellige Tests.")
    values = _values(body.get("values"))
    try:
        result = benford_test(values, digits=digits, short_values=short)
        conformity = assess(result, test, profile_id)
    except StatisticsInputError as exc:
        raise ContractError(str(exc)) from exc
    distribution = result.to_dict()
    distribution["library"] = LIBRARY
    return {
        "library": LIBRARY,
        "test": test,
        "test_label": TEST_LABELS[test][0],
        "distribution": distribution,
        "conformity": conformity.to_dict(),
    }
