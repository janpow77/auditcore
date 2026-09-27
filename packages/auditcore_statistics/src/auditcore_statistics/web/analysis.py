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
from ..benford import METHOD, BenfordResult, ShortValues, StatisticsInputError, benford_test
from ..conformity import PROFILES, TESTS, Test, assess
from ..significance import STANDARD_LEVELS, chi_square_test, digit_z_test

LIBRARY = f"auditcore_statistics {__version__}"
MAX_VALUES = 1_000_000

TEST_LABELS: Mapping[str, tuple[str, int]] = {
    "first": ("Erste Ziffer (1–9)", 1),
    "first_two": ("Erste zwei Ziffern (10–99)", 2),
    "second": ("Zweite Ziffer (0–9)", 2),
}
METRICS = (
    {
        "id": "chi_square",
        "label": "Chi²-Test mit kritischen Werten",
        "parameters": {"significance_level": "optional, 0 < α < 1"},
    },
    {
        "id": "digit_z",
        "label": "Auffällige Ziffern (z je Ziffer)",
        "parameters": {
            "continuity_correction": "Pflicht, true oder false",
            "z_critical": "optional, > 0",
        },
    },
)
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
        "metrics": [dict(m) for m in METRICS],
        "standard_levels": list(STANDARD_LEVELS),
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


def _options(raw: object, name: str, allowed: tuple[str, ...]) -> Mapping[str, object]:
    if not isinstance(raw, Mapping):
        raise ContractError(f"'metrics.{name}' muss ein Objekt sein.")
    unknown = sorted(str(k) for k in raw if k not in allowed)
    if unknown:
        raise ContractError(f"'metrics.{name}': unbekannte Felder {', '.join(unknown)}.")
    return cast(Mapping[str, object], raw)


def _number(raw: object, where: str) -> float | None:
    if raw is None:
        return None
    if isinstance(raw, bool) or not isinstance(raw, (int, float, Decimal)):
        raise ContractError(f"'{where}' muss eine Zahl sein.")
    return float(raw)


def _metrics(raw: object, result: BenfordResult, test: Test) -> dict[str, object]:
    """Requested optional measures (``chi_square``, ``digit_z``) of the result."""
    if not isinstance(raw, Mapping):
        raise ContractError("'metrics' muss ein Objekt sein.")
    unknown = sorted(str(k) for k in raw if k not in ("chi_square", "digit_z"))
    if unknown:
        raise ContractError(f"Unbekannte Kennzahlen: {', '.join(unknown)}.")
    out: dict[str, object] = {}
    if "chi_square" in raw:
        chi = _options(raw["chi_square"], "chi_square", ("significance_level",))
        level = _number(chi.get("significance_level"), "metrics.chi_square.significance_level")
        out["chi_square"] = chi_square_test(result, test, significance_level=level).to_dict()
    if "digit_z" in raw:
        z = _options(raw["digit_z"], "digit_z", ("continuity_correction", "z_critical"))
        correction = z.get("continuity_correction")
        if not isinstance(correction, bool):
            raise ContractError("'metrics.digit_z.continuity_correction' ist true oder false.")
        critical = _number(z.get("z_critical"), "metrics.digit_z.z_critical")
        out["digit_z"] = digit_z_test(
            result, test, continuity_correction=correction, z_critical=critical
        ).to_dict()
    return out


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
        metrics = None if body.get("metrics") is None else _metrics(body["metrics"], result, test)
    except StatisticsInputError as exc:
        raise ContractError(str(exc)) from exc
    distribution = result.to_dict()
    distribution["library"] = LIBRARY
    answer: dict[str, object] = {
        "library": LIBRARY,
        "test": test,
        "test_label": TEST_LABELS[test][0],
        "distribution": distribution,
        "conformity": conformity.to_dict(),
    }
    if metrics is not None:
        answer["metrics"] = metrics
    return answer
