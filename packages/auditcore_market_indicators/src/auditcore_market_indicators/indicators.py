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
from collections.abc import Callable, Sequence
from typing import NamedTuple

from ._numeric import neumaier_sum, numpy_pairwise_sum, window_mean, window_std
from .errors import IndicatorInputError
from .profiles import IndicatorProfile, Summation

Value = float | int | None
Series = list[float | None]

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


class AdxResult(NamedTuple):
    """+DI, -DI and ADX (unpacks like the original ``(plus_di, minus_di, adx)`` tuple)."""

    plus_di: Series
    minus_di: Series
    adx: Series


class BreakoutResult(NamedTuple):
    """Breakout flag and strength; flag ``None`` where it cannot be evaluated."""

    flag: list[bool | None]
    strength: Series


class MacdResult(NamedTuple):
    """MACD line, signal line and histogram."""

    macd: Series
    signal: Series
    histogram: Series


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
def _values(series: Sequence[Value], label: str) -> Series:
    if isinstance(series, (str, bytes)) or not isinstance(series, Sequence):
        raise IndicatorInputError(f"{label} muss eine Folge von Zahlen oder None sein.")
    out: Series = []
    for index, value in enumerate(series):
        if value is None:
            out.append(None)
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise IndicatorInputError(f"{label}[{index}] ist keine Zahl ({type(value).__name__}).")
        number = float(value)
        if not math.isfinite(number):
            raise IndicatorInputError(
                f"{label}[{index}] ist nicht endlich ({number!r}); fehlende Werte als None angeben."
            )
        out.append(number)
    return out


def _same_length(**columns: Series) -> int:
    lengths = {len(v) for v in columns.values()}
    if len(lengths) > 1:
        detail = ", ".join(f"{k}={len(v)}" for k, v in columns.items())
        raise IndicatorInputError(f"Reihen sind unterschiedlich lang ({detail}).")
    return lengths.pop() if lengths else 0


def _window(n: object, minimum: int, name: str = "n") -> int:
    if isinstance(n, bool) or not isinstance(n, int):
        raise IndicatorInputError(f"{name} muss eine ganze Zahl sein.")
    if n < minimum:
        raise IndicatorInputError(f"{name} muss > {minimum - 1} sein")
    return n


def _finite(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise IndicatorInputError(f"{name} muss eine Zahl sein.")
    number = float(value)
    if not math.isfinite(number):
        raise IndicatorInputError(f"{name} muss endlich sein.")
    return number


def _summer(summation: Summation) -> Callable[[Sequence[float]], float]:
    return neumaier_sum if summation == "neumaier" else numpy_pairwise_sum


def _first_present(values: Series) -> int | None:
    for index, value in enumerate(values):
        if value is not None:
            return index
    return None


def _reject_gaps(values: Series, label: str, profile: IndicatorProfile, *, leading: bool) -> None:
    """Raise if a value is missing (after the first present value unless ``leading``)."""
    first = _first_present(values)
    if first is None and not leading:
        return
    start = 0 if leading else (first or 0)
    for index in range(start, len(values)):
        if values[index] is None:
            raise IndicatorInputError(
                f"{label}[{index}] fehlt; Profil {profile.id} lässt keine Lücken zu."
            )


def _first_full_window(values: Series, n: int) -> int | None:
    """End index of the first run of ``n`` consecutive present values."""
    run = 0
    for index, value in enumerate(values):
        run = run + 1 if value is not None else 0
        if run >= n:
            return index
    return None


def _rolling(values: Series, n: int, statistic: Callable[[list[float]], float | None]) -> Series:
    out: Series = [None] * len(values)
    for index in range(n - 1, len(values)):
        window = values[index + 1 - n : index + 1]
        if any(v is None for v in window):
            continue
        out[index] = statistic([v for v in window if v is not None])
    return out


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


# --------------------------------------------------------------------------- #
# Profile-dependent smoothers
# --------------------------------------------------------------------------- #
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
    plus_di: Series = [None] * length
    minus_di: Series = [None] * length
    adx_out: Series = [None] * length
    if length < 2 * n + 1:
        return AdxResult(plus_di, minus_di, adx_out)

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

    total = _summer(profile.summation)
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

    first = 2 * n
    window = dx[n:first]
    if any(v is None for v in window):
        return AdxResult(plus_di, minus_di, adx_out)
    state = total([v for v in window if v is not None]) / n
    adx_out[first] = state
    for index in range(first + 1, length):
        current = dx[index]
        if current is None:
            continue
        state = (state * (n - 1) + current) / n
        adx_out[index] = state
    return AdxResult(plus_di, minus_di, adx_out)


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
