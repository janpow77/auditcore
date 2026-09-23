"""Error contract of the market indicator library."""

from __future__ import annotations


class MarketIndicatorError(Exception):
    """Base class; ``code`` is stable and machine readable."""

    code = "market_indicator_error"


class IndicatorInputError(MarketIndicatorError, ValueError):
    """Input series or parameters violate the documented contract.

    Subclass of :class:`ValueError`, so callers that caught the ``ValueError``
    of the original krypto functions (``"n muss > 0 sein"``) keep working.
    """

    code = "indicator_input_error"


class ProfileError(MarketIndicatorError, ValueError):
    """A profile is missing, malformed or does not define the requested indicator."""

    code = "profile_error"


class DependencyError(MarketIndicatorError, ImportError):
    """The optional polars extra (``auditcore_market_indicators[polars]``) is not installed."""

    code = "missing_optional_dependency"
