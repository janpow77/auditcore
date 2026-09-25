"""Frozen rule objects of calculation and comparison profiles.

:mod:`auditcore_price_analysis.profiles` validates profile documents into
these objects and re-exports them.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from .errors import ProfileError
from .numbers import Rounding


@dataclass(frozen=True)
class ConsumptionRule:
    """A consumption quantity of the formula (``legacy_default`` is documentation only)."""

    name: str
    unit: str
    legacy_default: Decimal | None
    note: str = ""
    standard: Decimal | None = None
    standard_source: str | None = None


@dataclass(frozen=True)
class ComponentRule:
    """One price component: amount = price × quantity(basis) × factor."""

    name: str
    line: str
    unit: str
    basis: str | None
    factor: Decimal
    required: bool
    fixed: bool
    label: str | None = None
    valid_from: date | None = None
    valid_until: date | None = None
    tiered_by: str | None = None

    def applies(self, day: date) -> bool:
        """Whether the component belongs to the formula on ``day``."""
        if self.valid_from is not None and day < self.valid_from:
            return False
        return not (self.valid_until is not None and day > self.valid_until)


@dataclass(frozen=True)
class TierRule:
    """Tiered price for one component (for example the water work price)."""

    field: str
    quantity: str
    limit_key: str
    price_key: str
    unit: str
    wrapper_key: str | None
    open_last: bool


@dataclass(frozen=True)
class MixedPriceRule:
    """Average price = total / quantity × factor (undefined for quantity 0)."""

    name: str
    unit: str
    basis: str
    factor: Decimal


@dataclass(frozen=True)
class CalculationProfile:
    """Versioned rules of one annual cost calculation."""

    profile_id: str
    version: str
    kind: str
    title: str
    status: str
    source: Mapping[str, Any]
    formula: str
    consumption: tuple[ConsumptionRule, ...]
    components: tuple[ComponentRule, ...]
    tiers: TierRule | None
    mixed_price: MixedPriceRule
    money: Rounding
    percent: Rounding
    mixed_rounding: Rounding
    optional_missing_blocks_comparison: bool
    require_released_for_comparison: bool
    fingerprint: str
    raw: Mapping[str, Any]
    recommended: bool = False

    @property
    def reference(self) -> dict[str, str]:
        """Identity carried by every result."""
        return {
            "profile_id": self.profile_id,
            "version": self.version,
            "fingerprint": self.fingerprint,
        }

    def component(self, name: str) -> ComponentRule:
        """Rule by component name."""
        for rule in self.components:
            if rule.name == name:
                return rule
        raise ProfileError(f"Profil {self.profile_id} kennt die Komponente {name} nicht.")


@dataclass(frozen=True)
class ComparisonProfile:
    """Versioned rules for deviation, traffic light, statistics and tariff selection."""

    profile_id: str
    version: str
    title: str
    status: str
    source: Mapping[str, Any]
    delta_rounding: Rounding
    threshold_pct: Decimal
    yellow_from_fraction: Decimal
    statistics_rounding: Rounding
    stddev: str
    only_released: bool
    not_after_reference_date: bool
    respect_valid_to: bool
    q3_tolerance: Decimal
    prefer_standard_variants: bool
    fingerprint: str
    raw: Mapping[str, Any]
    recommended: bool = False

    @property
    def reference(self) -> dict[str, str]:
        """Identity carried by every result."""
        return {
            "profile_id": self.profile_id,
            "version": self.version,
            "fingerprint": self.fingerprint,
        }
