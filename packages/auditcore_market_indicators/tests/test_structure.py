"""Module split of 0.1.1: old import paths and the validation order stay as before."""

from __future__ import annotations

import copy
import json
from importlib import resources
from typing import Any

import pytest

import auditcore_market_indicators as mi
from auditcore_market_indicators import indicators


def base_document() -> dict[str, Any]:
    entry = resources.files("auditcore_market_indicators.profile_data").joinpath(
        "krypto.indicators_base-2026.09.1.json"
    )
    data: dict[str, Any] = json.loads(entry.read_text(encoding="utf-8"))
    return data


@pytest.mark.parametrize(
    "name",
    ["AdxResult", "MacdResult", "adx", "atr", "ema", "macd", "rsi", "true_range", "breakout"],
)
def test_names_remain_reachable_through_indicators(name: str) -> None:
    assert getattr(indicators, name) is getattr(mi, name)


def several_defects(**changes: Any) -> dict[str, Any]:
    data = copy.deepcopy(base_document())
    for key, value in changes.items():
        if value is KeyError:
            del data[key]
        else:
            data[key] = value
    return data


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        # The header is checked before any section ...
        ({"id": "", "ema": [], "summation": "x"}, "id muss"),
        ({"source": "x", "ema": []}, "source muss"),
        # ... sections in the order ema, rsi, atr, adx, macd ...
        ({"ema": {"seed": "x", "gaps": "skip"}, "rsi": []}, "ema.seed"),
        ({"rsi": [], "atr": []}, "Abschnitt 'rsi'"),
        ({"atr": {"smoothing": "x"}, "adx": []}, "atr.smoothing"),
        ({"adx": KeyError, "macd": []}, "Abschnitt 'adx' fehlt"),
        ({"macd": [], "warmup": 1}, "Abschnitt 'macd'"),
        # ... then the structural rules, the warm-up and finally the summation.
        ({"ema": None, "macd": {}, "warmup": 1}, "setzt einen ema"),
        ({"warmup": {"min_lookback": 0}, "summation": "x"}, "min_lookback"),
        ({"summation": "kahan"}, "summation"),
    ],
)
def test_first_defect_in_validation_order_is_reported(
    changes: dict[str, Any], message: str
) -> None:
    with pytest.raises(mi.ProfileError, match=message):
        mi.profile_from_dict(several_defects(**changes))
