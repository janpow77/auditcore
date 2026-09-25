"""Price calculation for regulated tariffs: exact decimals, versioned profiles, no network.

Contract ``auditcore_price_analysis.contract/1``:

* :func:`calculate` — annual costs of a :class:`Tariff` under an explicitly
  chosen, versioned :class:`CalculationProfile` (units, validity windows,
  tiers, rounding, missing values, release requirement);
* :func:`select_tariff` — deterministic tariff selection by reference day,
  release status, meter size and variant;
* :func:`delta_pct`, :func:`traffic_light`, :func:`group_statistics` —
  comparison rules of a :class:`ComparisonProfile`;
* :mod:`auditcore_price_analysis.legacy` — exact replay of regulierung's
  ``calculator.py``/``preisauswahl.py`` for consumer migration.

The library never releases a price and never contacts a network.
"""

from .calculation import CalculationResult, Line, TierUse, calculate, tiered_amount
from .comparison import (
    GREEN,
    RED,
    YELLOW,
    GroupStatistics,
    delta_pct,
    group_statistics,
    traffic_light,
)
from .errors import PriceAnalysisError, ProfileError
from .numbers import Rounding, non_negative, parse_day, parse_decimal
from .profiles import (
    CalculationProfile,
    ComparisonProfile,
    ComponentRule,
    ConsumptionRule,
    TierRule,
    available_profiles,
    calculation_profile_from_dict,
    comparison_profile_from_dict,
    load_calculation_profile,
    load_comparison_profile,
    load_recommended_calculation_profile,
    load_recommended_comparison_profile,
    recommended_version,
    standard_consumption,
)
from .selection import STATUS_NONE, STATUS_OK, STATUS_Q3_FALLBACK, Selection, select_tariff
from .tariff import ReleaseStatus, Tariff, Tier, ignored_tier_keys, parse_tiers

__version__ = "0.1.1"
CONTRACT_VERSION = "auditcore_price_analysis.contract/1"

__all__ = [
    "CONTRACT_VERSION",
    "GREEN",
    "RED",
    "STATUS_NONE",
    "STATUS_OK",
    "STATUS_Q3_FALLBACK",
    "YELLOW",
    "CalculationProfile",
    "CalculationResult",
    "ComparisonProfile",
    "ComponentRule",
    "ConsumptionRule",
    "GroupStatistics",
    "Line",
    "PriceAnalysisError",
    "ProfileError",
    "ReleaseStatus",
    "Rounding",
    "Selection",
    "Tariff",
    "Tier",
    "TierRule",
    "TierUse",
    "__version__",
    "available_profiles",
    "calculate",
    "calculation_profile_from_dict",
    "comparison_profile_from_dict",
    "delta_pct",
    "group_statistics",
    "ignored_tier_keys",
    "load_calculation_profile",
    "load_comparison_profile",
    "load_recommended_calculation_profile",
    "load_recommended_comparison_profile",
    "non_negative",
    "parse_day",
    "parse_decimal",
    "parse_tiers",
    "recommended_version",
    "select_tariff",
    "standard_consumption",
    "tiered_amount",
    "traffic_light",
]
