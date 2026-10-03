"""Money in exact integer cents: interest on repayment claims and quotas.

Amounts enter through ``to_cents``/``to_cents_buffer`` (ROUND_HALF_UP) and stay
int64 cents; rates are exact fractions or whole basis points. No money value
is ever represented as float64.
"""

from __future__ import annotations

from ._interest import (
    CONVENTIONS,
    RatePeriod,
    RateTable,
    interest_cents,
    interest_cents_batch,
    rate_table,
    scaled_days,
)
from ._quotas import (
    QUOTA_ABOVE_MAXIMUM,
    QUOTA_BELOW_MINIMUM,
    QUOTA_OK,
    QUOTA_UNDEFINED,
    QuotaCheck,
    Split,
    apply_reduction,
    check_quota,
    cofinancing,
    percent,
    rate,
    share_cents,
)

__all__ = [
    "CONVENTIONS",
    "QUOTA_ABOVE_MAXIMUM",
    "QUOTA_BELOW_MINIMUM",
    "QUOTA_OK",
    "QUOTA_UNDEFINED",
    "QuotaCheck",
    "RatePeriod",
    "RateTable",
    "Split",
    "apply_reduction",
    "check_quota",
    "cofinancing",
    "interest_cents",
    "interest_cents_batch",
    "percent",
    "rate",
    "rate_table",
    "scaled_days",
    "share_cents",
]
