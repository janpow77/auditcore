"""Technical market indicators on plain sequences.

Every function takes sequences of ``float``/``int`` or ``None`` (missing
value) and returns lists of the same length. Positions without enough
history, and values that are mathematically undefined (division by zero,
logarithm of a non-positive ratio), are ``None`` — never ``NaN`` or
infinity. Non-finite inputs and booleans are rejected with
:class:`IndicatorInputError` instead of being propagated.

Indicators whose characterized source variants differ (EMA, RSI, ATR, ADX,
MACD) require an explicit :class:`IndicatorProfile`; see ``profiles.py`` and
``docs/behavior-changes.md``. Nothing here fetches data, scores coins or makes
portfolio or trading decisions.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import NamedTuple

from ._numeric import window_mean, window_std
from ._series import (
    Series,
    Value,
    _finite,
    _rolling,
    _same_length,
    _values,
    _window,
)
from ._smoothers import AdxResult, MacdResult, adx, atr, ema, macd, rsi, true_range
from .errors import IndicatorInputError
from .profiles import IndicatorProfile

METHOD = "auditcore_market_indicators.indicators/1"
_VERSION = "0.1.0"
_PROFILED = frozenset({"ema", "rsi", "atr", "adx", "macd"})
_INDICATORS = _PROFILED | frozenset(
    {
        "returns",
        "log_returns",
        "sma",
        "rolling_std",
        "zscore",
        "historical_volatility",
        "volume_factor",
        "normalized_range",
        "breakout",
        "true_range",
    }
)


class BreakoutResult(NamedTuple):
    """Breakout flag and strength; flag ``None`` where it cannot be evaluated."""

    flag: list[bool | None]
    strength: Series


def method_reference(
    indicator: str, *, profile: IndicatorProfile | None = None, **parameters: object
) -> dict[str, object]:
    """Self-description of one indicator run: library, method, parameters, profile.

    Consumers store it next to persisted values (krypto: ``pipeline_version``)
    so that a result names exactly how it was computed.
    """
    if indicator not in _INDICATORS:
        raise IndicatorInputError(f"Unbekannter Indikator {indicator!r}.")
    if indicator in _PROFILED and profile is None:
        raise IndicatorInputError(f"{indicator} benötigt ein ausdrücklich gewähltes Profil.")
    return {
        "library": f"auditcore_market_indicators {_VERSION}",
        "method": METHOD,
        "indicator": indicator,
        "parameters": dict(sorted(parameters.items())),
        "profile": None if profile is None else profile.reference,
    }


# --------------------------------------------------------------------------- #
# Validation helpers
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# Returns
# --------------------------------------------------------------------------- #
def returns(close: Sequence[Value], periods: int) -> Series:
    """Discrete return ``(P_t - P_{t-k}) / P_{t-k}``; ``None`` for the first ``periods``."""
    periods = _window(periods, 1, "periods")
    values = _values(close, "close")
    out: Series = [None] * len(values)
    for index in range(periods, len(values)):
        current, previous = values[index], values[index - periods]
        if current is None or previous is None or previous == 0.0:
            continue
        out[index] = (current - previous) / previous
    return out


def log_returns(close: Sequence[Value]) -> Series:
    """Log return ``ln(P_t / P_{t-1})``; ``None`` if the ratio is undefined or ≤ 0."""
    values = _values(close, "close")
    out: Series = [None] * len(values)
    for index in range(1, len(values)):
        current, previous = values[index], values[index - 1]
        if current is None or previous is None or previous == 0.0:
            continue
        ratio = current / previous
        if ratio > 0:
            out[index] = math.log(ratio)
    return out


# --------------------------------------------------------------------------- #
# Window statistics
# --------------------------------------------------------------------------- #
def sma(values: Sequence[Value], n: int) -> Series:
    """Simple moving average over ``n`` values; windows with a gap are ``None``."""
    n = _window(n, 1)
    return _rolling(_values(values, "values"), n, window_mean)


def rolling_std(values: Sequence[Value], n: int) -> Series:
    """Rolling sample standard deviation (ddof = 1) over ``n`` values."""
    n = _window(n, 2)
    return _rolling(_values(values, "values"), n, window_std)


def zscore(values: Sequence[Value], n: int = 20) -> Series:
    """Rolling z-score ``(X_t - μ_n) / σ_n``; ``None`` where ``σ_n = 0``."""
    n = _window(n, 2)
    data = _values(values, "values")

    def statistic(window: list[float]) -> float | None:
        """Z-Score des letzten Fensterwerts; ``None`` bei σ = 0."""
        sigma = window_std(window)
        return None if sigma == 0.0 else (window[-1] - window_mean(window)) / sigma

    return _rolling(data, n, statistic)


def historical_volatility(
    close: Sequence[Value], n: int = 20, annualization_factor: float = 365.0
) -> Series:
    """Annualised volatility: rolling sample std of log returns · √factor.

    The factor is the number of periods per year of the series (365 for daily,
    8760 for hourly crypto bars); the caller passes it explicitly.
    """
    n = _window(n, 2)
    factor = _finite(annualization_factor, "annualization_factor")
    if factor <= 0:
        raise IndicatorInputError("annualization_factor muss > 0 sein.")
    scale = math.sqrt(factor)
    return [None if v is None else v * scale for v in rolling_std(log_returns(close), n)]


def volume_factor(volume: Sequence[Value], n: int = 20) -> Series:
    """``VF_t = V_t / VMA_n(t)``; ``None`` where the moving average is 0."""
    n = _window(n, 1)
    data = _values(volume, "volume")
    average = _rolling(data, n, window_mean)
    return [
        None if v is None or a is None or a == 0.0 else v / a
        for v, a in zip(data, average, strict=True)
    ]


def normalized_range(close: Sequence[Value], n: int = 20) -> Series:
    """``NR_t = (max - min) / mean`` over ``n`` values; ``None`` where the mean is 0."""
    n = _window(n, 2)

    def statistic(window: list[float]) -> float | None:
        """Spannweite durch Mittelwert; ``None`` bei Mittelwert 0."""
        mean = window_mean(window)
        return None if mean == 0.0 else (max(window) - min(window)) / mean

    return _rolling(_values(close, "close"), n, statistic)


def breakout(
    close: Sequence[Value], volume: Sequence[Value], n: int = 20, vf_threshold: float = 1.8
) -> BreakoutResult:
    """Breakout: ``P_t`` above the maximum of the ``n`` previous closes and ``VF_t > threshold``.

    Strength ``(P_t - max) / max · VF_t`` is also reported for non-breakouts
    (it can be negative). Where the rule cannot be evaluated (missing history,
    missing or zero values) flag and strength are ``None``.
    """
    n = _window(n, 1)
    threshold = _finite(vf_threshold, "vf_threshold")
    prices = _values(close, "close")
    volumes = _values(volume, "volume")
    length = _same_length(close=prices, volume=volumes)
    factors = volume_factor(volumes, n)
    flags: list[bool | None] = [None] * length
    strength: Series = [None] * length
    for index in range(n, length):
        previous = prices[index - n : index]
        price, factor = prices[index], factors[index]
        if price is None or factor is None or any(v is None for v in previous):
            continue
        highest = max(v for v in previous if v is not None)
        if highest == 0.0:
            continue
        strength[index] = (price - highest) / highest * factor
        flags[index] = price > highest and factor > threshold
    return BreakoutResult(flags, strength)


__all__ = [
    "METHOD",
    "AdxResult",
    "BreakoutResult",
    "MacdResult",
    "adx",
    "atr",
    "breakout",
    "ema",
    "historical_volatility",
    "log_returns",
    "macd",
    "method_reference",
    "normalized_range",
    "returns",
    "rolling_std",
    "rsi",
    "sma",
    "true_range",
    "volume_factor",
    "zscore",
]
