"""Optional polars adapter (extra ``auditcore_market_indicators[polars]``).

Same functions and parameters as :mod:`auditcore_market_indicators.indicators`,
but on ``polars.Series`` — a drop-in for krypto
``app.services.indicators.base``. Results keep the original series names
(``tr`` for the ATR, ``plus_di``/``minus_di``/``adx``, ``breakout_flag``/
``breakout_strength``) and dtype ``Float64`` (``Boolean`` for the flag).
Inputs are cast to ``Float64``; nulls are missing values, ``NaN`` is rejected.
The computation itself is the pure-Python core, so polars only converts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from auditcore_common.optional import require_module

from . import indicators as core
from .errors import DependencyError, IndicatorInputError
from .profiles import IndicatorProfile

if TYPE_CHECKING:  # pragma: no cover
    import polars as pl


def _pl() -> Any:
    return require_module(
        "polars",
        DependencyError,
        "polars ist nicht installiert: auditcore_market_indicators[polars] installieren.",
    )


def _checked(series: pl.Series) -> pl.Series:
    if not isinstance(series, _pl().Series):
        raise IndicatorInputError("Es wird eine polars.Series erwartet.")
    return cast("pl.Series", series)


def _list(series: pl.Series) -> list[float | None]:
    values: list[float | None] = _checked(series).cast(_pl().Float64).to_list()
    return values


def _name(series: pl.Series) -> str:
    name: str = _checked(series).name
    return name


def _out(name: str, values: list[float | None]) -> pl.Series:
    series: pl.Series = _pl().Series(name, values, dtype=_pl().Float64)
    return series


def returns(close: pl.Series, periods: int) -> pl.Series:
    """Diskrete Rendite über ``periods`` (siehe :func:`indicators.returns`)."""
    return _out(_name(close), core.returns(_list(close), periods))


def log_returns(close: pl.Series) -> pl.Series:
    """Log-Rendite (siehe :func:`indicators.log_returns`)."""
    return _out(_name(close), core.log_returns(_list(close)))


def sma(series: pl.Series, n: int) -> pl.Series:
    """Einfacher gleitender Mittelwert (siehe :func:`indicators.sma`)."""
    return _out(_name(series), core.sma(_list(series), n))


def rolling_std(series: pl.Series, n: int) -> pl.Series:
    """Rollierende Stichproben-Standardabweichung (siehe :func:`indicators.rolling_std`)."""
    return _out(_name(series), core.rolling_std(_list(series), n))


def ema(series: pl.Series, n: int, *, profile: IndicatorProfile) -> pl.Series:
    """EMA nach ``profile.ema`` (siehe :func:`indicators.ema`)."""
    return _out(_name(series), core.ema(_list(series), n, profile=profile))


def rsi(close: pl.Series, n: int = 14, *, profile: IndicatorProfile) -> pl.Series:
    """RSI nach ``profile.rsi`` (siehe :func:`indicators.rsi`)."""
    return _out(_name(close), core.rsi(_list(close), n, profile=profile))


def true_range(high: pl.Series, low: pl.Series, close: pl.Series) -> pl.Series:
    """True Range als Serie ``tr`` (siehe :func:`indicators.true_range`)."""
    return _out("tr", core.true_range(_list(high), _list(low), _list(close)))


def atr(
    high: pl.Series, low: pl.Series, close: pl.Series, n: int = 14, *, profile: IndicatorProfile
) -> pl.Series:
    """ATR nach ``profile.atr`` als Serie ``tr`` wie im Original (siehe :func:`indicators.atr`)."""
    return _out("tr", core.atr(_list(high), _list(low), _list(close), n, profile=profile))


def adx(
    high: pl.Series, low: pl.Series, close: pl.Series, n: int = 14, *, profile: IndicatorProfile
) -> tuple[pl.Series, pl.Series, pl.Series]:
    """``(plus_di, minus_di, adx)`` nach Wilder (siehe :func:`indicators.adx`)."""
    result = core.adx(_list(high), _list(low), _list(close), n, profile=profile)
    return (
        _out("plus_di", result.plus_di),
        _out("minus_di", result.minus_di),
        _out("adx", result.adx),
    )


def historical_volatility(
    close: pl.Series, n: int = 20, annualization_factor: float = 365.0
) -> pl.Series:
    """Annualisierte Volatilität (siehe :func:`indicators.historical_volatility`)."""
    return _out(_name(close), core.historical_volatility(_list(close), n, annualization_factor))


def volume_factor(volume: pl.Series, n: int = 20) -> pl.Series:
    """Volumenfaktor (siehe :func:`indicators.volume_factor`)."""
    return _out(_name(volume), core.volume_factor(_list(volume), n))


def zscore(series: pl.Series, n: int = 20) -> pl.Series:
    """Rollierender Z-Score (siehe :func:`indicators.zscore`)."""
    return _out(_name(series), core.zscore(_list(series), n))


def normalized_range(close: pl.Series, n: int = 20) -> pl.Series:
    """Normiertes Range-Maß (siehe :func:`indicators.normalized_range`)."""
    return _out(_name(close), core.normalized_range(_list(close), n))


def breakout(
    close: pl.Series, volume: pl.Series, n: int = 20, vf_threshold: float = 1.8
) -> tuple[pl.Series, pl.Series]:
    """``(breakout_flag, breakout_strength)``; Flag ``null`` wenn nicht auswertbar."""
    result = core.breakout(_list(close), _list(volume), n, vf_threshold)
    pl_ = _pl()
    return (
        pl_.Series("breakout_flag", result.flag, dtype=pl_.Boolean),
        _out("breakout_strength", result.strength),
    )


def macd(
    close: pl.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    *,
    profile: IndicatorProfile,
) -> tuple[pl.Series, pl.Series, pl.Series]:
    """``(macd, signal, histogram)`` nach ``profile.ema`` (siehe :func:`indicators.macd`)."""
    result = core.macd(_list(close), fast, slow, signal, profile=profile)
    return (
        _out("macd", result.macd),
        _out("signal", result.signal),
        _out("histogram", result.histogram),
    )


__all__ = [
    "adx",
    "atr",
    "breakout",
    "ema",
    "historical_volatility",
    "log_returns",
    "macd",
    "normalized_range",
    "returns",
    "rolling_std",
    "rsi",
    "sma",
    "true_range",
    "volume_factor",
    "zscore",
]
