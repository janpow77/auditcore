"""Profile-dependent smoothers: EMA, RSI, true range/ATR, ADX and MACD.

The characterized source variants differ; every function requires an
explicitly chosen :class:`IndicatorProfile`. :mod:`auditcore_market_indicators.indicators`
re-exports all public names.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import NamedTuple

from ._numeric import window_mean
from ._series import (
    Series,
    Value,
    _first_full_window,
    _first_present,
    _reject_gaps,
    _rolling,
    _same_length,
    _summer,
    _values,
    _window,
)
from .errors import IndicatorInputError
from .profiles import IndicatorProfile


class AdxResult(NamedTuple):
    """+DI, -DI and ADX (unpacks like the original ``(plus_di, minus_di, adx)`` tuple)."""

    plus_di: Series
    minus_di: Series
    adx: Series


class MacdResult(NamedTuple):
    """MACD line, signal line and histogram."""

    macd: Series
    signal: Series
    histogram: Series


def ema(values: Sequence[Value], n: int, *, profile: IndicatorProfile) -> Series:
    """Exponential moving average with ``α = 2/(n+1)``.

    ``profile.ema.seed``: ``sma`` starts with the mean of the first ``n``
    consecutive present values (at the end of that window), ``first_value``
    with the first present value. ``profile.ema.gaps`` decides what happens
    to a missing value after the start: ``skip`` (output ``None``, state
    kept), ``hold`` (output the previous EMA) or ``error``. Missing values
    before the start are warm-up, not gaps.
    """
    rule = profile.require_ema()
    n = _window(n, 1)
    data = _values(values, "values")
    if rule.gaps == "error":
        _reject_gaps(data, "values", profile, leading=False)
    out: Series = [None] * len(data)
    if rule.seed == "sma":
        start = _first_full_window(data, n)
        if start is None:
            return out
        window = [v for v in data[start + 1 - n : start + 1] if v is not None]
        state = _summer(profile.summation)(window) / n
    else:
        first = _first_present(data)
        if first is None:
            return out
        start, state = first, data[first]  # type: ignore[assignment]
    alpha = 2.0 / (n + 1)
    out[start] = state
    for index in range(start + 1, len(data)):
        value = data[index]
        if value is None:
            if rule.gaps == "hold":
                out[index] = state
            continue
        state = alpha * value + (1 - alpha) * state
        out[index] = state
    return out


def _movements(data: Series, rule_gaps: str) -> tuple[list[float], list[float]]:
    gains = [0.0] * len(data)
    losses = [0.0] * len(data)
    for index in range(1, len(data)):
        current, previous = data[index], data[index - 1]
        if current is None or previous is None:
            continue  # zero_move: a missing neighbour counts as no movement
        delta = current - previous
        gains[index] = delta if delta > 0 else 0.0
        losses[index] = -delta if delta < 0 else 0.0
    return gains, losses


def rsi(close: Sequence[Value], n: int = 14, *, profile: IndicatorProfile) -> Series:
    """Relative Strength Index ``100 - 100 / (1 + AG/AL)``.

    Start: mean gain/loss of the first ``n`` movements (value at index ``n``).
    ``profile.rsi.smoothing``: ``wilder`` (``(A·(n-1) + X)/n``), ``ema``
    (``α = 2/(n+1)``) or ``sma`` (mean of the last ``n`` movements).
    ``AL = 0`` gives 100 if ``AG > 0`` and ``profile.rsi.flat_value`` if there
    was no movement at all. ``gaps``: ``zero_move`` counts a movement to or
    from a missing value as no movement (source behavior), ``error`` rejects it.
    """
    rule = profile.require_rsi()
    n = _window(n, 1)
    data = _values(close, "close")
    if rule.gaps == "error":
        _reject_gaps(data, "close", profile, leading=True)
    out: Series = [None] * len(data)
    if len(data) <= n:
        return out
    gains, losses = _movements(data, rule.gaps)
    total = _summer(profile.summation)
    avg_gain = total(gains[1 : n + 1]) / n
    avg_loss = total(losses[1 : n + 1]) / n

    def value(gain: float, loss: float) -> float:
        """RSI aus mittlerem Gewinn und Verlust."""
        if loss == 0:
            return 100.0 if gain > 0 else rule.flat_value
        return 100.0 - (100.0 / (1.0 + gain / loss))

    out[n] = value(avg_gain, avg_loss)
    alpha = 2.0 / (n + 1)
    for index in range(n + 1, len(data)):
        if rule.smoothing == "wilder":
            avg_gain = (avg_gain * (n - 1) + gains[index]) / n
            avg_loss = (avg_loss * (n - 1) + losses[index]) / n
        elif rule.smoothing == "ema":
            avg_gain = alpha * gains[index] + (1 - alpha) * avg_gain
            avg_loss = alpha * losses[index] + (1 - alpha) * avg_loss
        else:
            avg_gain = total(gains[index + 1 - n : index + 1]) / n
            avg_loss = total(losses[index + 1 - n : index + 1]) / n
        out[index] = value(avg_gain, avg_loss)
    return out


def true_range(high: Sequence[Value], low: Sequence[Value], close: Sequence[Value]) -> Series:
    """``TR_t = max(H-L, |H-C_{t-1}|, |L-C_{t-1}|)``; ``H-L`` without a previous close."""
    h, lo, c = _values(high, "high"), _values(low, "low"), _values(close, "close")
    length = _same_length(high=h, low=lo, close=c)
    out: Series = [None] * length
    for index in range(length):
        hi, low_i = h[index], lo[index]
        if hi is None or low_i is None:
            continue
        span = hi - low_i
        previous = c[index - 1] if index > 0 else None
        if previous is None:
            out[index] = span
            continue
        out[index] = max(span, abs(hi - previous), abs(low_i - previous))
    return out


def atr(
    high: Sequence[Value],
    low: Sequence[Value],
    close: Sequence[Value],
    n: int = 14,
    *,
    profile: IndicatorProfile,
) -> Series:
    """Average True Range; smoothing from ``profile.atr.smoothing``.

    ``sma``: mean of the last ``n`` true ranges (windows with a gap are
    ``None``) — this is what krypto ``indicators/base.py`` computes, although
    its module docstring names Wilder. ``wilder`` and ``ema`` start with the
    same mean at the end of the first complete window and then smooth
    recursively; a missing true range after the start is rejected.
    """
    rule = profile.require_atr()
    n = _window(n, 1)
    ranges = true_range(high, low, close)
    if rule.smoothing == "sma":
        return _rolling(ranges, n, window_mean)
    out: Series = [None] * len(ranges)
    start = _first_full_window(ranges, n)
    if start is None:
        return out
    for index in range(start + 1, len(ranges)):
        if ranges[index] is None:
            raise IndicatorInputError(
                f"True Range[{index}] fehlt; rekursive ATR-Glättung setzt lückenlose Bars voraus."
            )
    window = [v for v in ranges[start + 1 - n : start + 1] if v is not None]
    state = _summer(profile.summation)(window) / n
    out[start] = state
    alpha = 2.0 / (n + 1)
    for index in range(start + 1, len(ranges)):
        current = ranges[index]
        assert current is not None
        if rule.smoothing == "wilder":
            state = (state * (n - 1) + current) / n
        else:
            state = alpha * current + (1 - alpha) * state
        out[index] = state
    return out


def _directional_movements(
    h: Series, lo: Series, c: Series
) -> tuple[list[float], list[float], list[float]]:
    """True range, +DM and -DM per bar; a bar with a missing value counts as no movement."""
    length = len(h)
    tr = [0.0] * length
    plus_dm = [0.0] * length
    minus_dm = [0.0] * length
    for index in range(1, length):
        hi, low_i = h[index], lo[index]
        prev_hi, prev_low, prev_close = h[index - 1], lo[index - 1], c[index - 1]
        if hi is None or low_i is None or prev_hi is None or prev_low is None or prev_close is None:
            continue
        tr[index] = max(hi - low_i, abs(hi - prev_close), abs(low_i - prev_close))
        up_move = hi - prev_hi
        down_move = prev_low - low_i
        if up_move > down_move and up_move > 0:
            plus_dm[index] = up_move
        if down_move > up_move and down_move > 0:
            minus_dm[index] = down_move
    return tr, plus_dm, minus_dm


def _directional_indices(
    tr: list[float],
    plus_dm: list[float],
    minus_dm: list[float],
    n: int,
    total: Callable[[Sequence[float]], float],
) -> tuple[Series, Series, Series]:
    """Wilder-smoothed +DI, -DI and DX per bar (``None`` where undefined)."""
    length = len(tr)
    plus_di: Series = [None] * length
    minus_di: Series = [None] * length
    smooth_tr = total(tr[1 : n + 1])
    smooth_plus = total(plus_dm[1 : n + 1])
    smooth_minus = total(minus_dm[1 : n + 1])
    dx: Series = [None] * length
    for index in range(n, length):
        if index > n:
            smooth_tr = smooth_tr - smooth_tr / n + tr[index]
            smooth_plus = smooth_plus - smooth_plus / n + plus_dm[index]
            smooth_minus = smooth_minus - smooth_minus / n + minus_dm[index]
        if smooth_tr == 0:
            continue
        pdi = 100.0 * smooth_plus / smooth_tr
        mdi = 100.0 * smooth_minus / smooth_tr
        plus_di[index], minus_di[index] = pdi, mdi
        di_sum = pdi + mdi
        dx[index] = 0.0 if di_sum == 0 else 100.0 * abs(pdi - mdi) / di_sum
    return plus_di, minus_di, dx


def _average_dx(dx: Series, n: int, total: Callable[[Sequence[float]], float]) -> Series:
    """First ADX = mean DX of ``n…2n-1`` (none if one is undefined), then Wilder smoothing."""
    adx_out: Series = [None] * len(dx)
    first = 2 * n
    window = dx[n:first]
    if any(v is None for v in window):
        return adx_out
    state = total([v for v in window if v is not None]) / n
    adx_out[first] = state
    for index in range(first + 1, len(dx)):
        current = dx[index]
        if current is None:
            continue
        state = (state * (n - 1) + current) / n
        adx_out[index] = state
    return adx_out


def adx(
    high: Sequence[Value],
    low: Sequence[Value],
    close: Sequence[Value],
    n: int = 14,
    *,
    profile: IndicatorProfile,
) -> AdxResult:
    """+DI, -DI and ADX after Wilder (1978).

    Smoothed sums start at index ``n`` with the sum of the movements 1…n, then
    ``S_t = S_{t-1} - S_{t-1}/n + X_t``. DX is undefined (``None``) where the
    smoothed true range is 0; the first ADX (index ``2n``) is the mean DX of
    indices ``n…2n-1`` and later ADX values skip undefined DX. Fewer than
    ``2n + 1`` bars give only ``None``. ``profile.adx.gaps``: ``zero_move``
    treats a bar with a missing value as no movement (source behavior),
    ``error`` rejects it.
    """
    rule = profile.require_adx()
    n = _window(n, 1)
    h, lo, c = _values(high, "high"), _values(low, "low"), _values(close, "close")
    length = _same_length(high=h, low=lo, close=c)
    if rule.gaps == "error":
        for label, column in (("high", h), ("low", lo), ("close", c)):
            _reject_gaps(column, label, profile, leading=True)
    if length < 2 * n + 1:
        return AdxResult([None] * length, [None] * length, [None] * length)
    tr, plus_dm, minus_dm = _directional_movements(h, lo, c)
    total = _summer(profile.summation)
    plus_di, minus_di, dx = _directional_indices(tr, plus_dm, minus_dm, n, total)
    return AdxResult(plus_di, minus_di, _average_dx(dx, n, total))


def macd(
    close: Sequence[Value],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    *,
    profile: IndicatorProfile,
) -> MacdResult:
    """MACD after Appel: ``EMA_fast - EMA_slow``, signal = EMA of the MACD line.

    Both EMAs and the signal EMA follow ``profile.ema``; the leading ``None``
    of the MACD line are warm-up for the signal EMA.
    """
    profile.require_macd()
    fast = _window(fast, 1, "fast")
    slow = _window(slow, 1, "slow")
    signal = _window(signal, 1, "signal")
    fast_line = ema(close, fast, profile=profile)
    slow_line = ema(close, slow, profile=profile)
    line: Series = [
        None if f is None or s is None else f - s for f, s in zip(fast_line, slow_line, strict=True)
    ]
    signal_line = ema(line, signal, profile=profile)
    histogram: Series = [
        None if m is None or s is None else m - s for m, s in zip(line, signal_line, strict=True)
    ]
    return MacdResult(line, signal_line, histogram)
