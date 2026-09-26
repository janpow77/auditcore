"""Technical market indicators with explicit, source-bound variant profiles.

Pure standard-library computation on sequences; the polars adapter is an
optional extra. Results are indicator values, not signals for portfolio or
trading decisions. See README.md and docs/behavior-changes.md.
"""

from .errors import DependencyError, IndicatorInputError, MarketIndicatorError, ProfileError
from .indicators import (
    METHOD,
    AdxResult,
    BreakoutResult,
    MacdResult,
    adx,
    atr,
    breakout,
    ema,
    historical_volatility,
    log_returns,
    macd,
    method_reference,
    normalized_range,
    returns,
    rolling_std,
    rsi,
    sma,
    true_range,
    volume_factor,
    zscore,
)
from .profiles import (
    RECOMMENDED_PROFILE,
    IndicatorProfile,
    available_profiles,
    load_profile,
    profile_document,
    profile_from_dict,
)

__version__ = "0.1.1"

__all__ = [
    "METHOD",
    "RECOMMENDED_PROFILE",
    "AdxResult",
    "BreakoutResult",
    "DependencyError",
    "IndicatorInputError",
    "IndicatorProfile",
    "MacdResult",
    "MarketIndicatorError",
    "ProfileError",
    "__version__",
    "adx",
    "atr",
    "available_profiles",
    "breakout",
    "ema",
    "historical_volatility",
    "load_profile",
    "log_returns",
    "macd",
    "method_reference",
    "normalized_range",
    "profile_document",
    "profile_from_dict",
    "returns",
    "rolling_std",
    "rsi",
    "sma",
    "true_range",
    "volume_factor",
    "zscore",
]
