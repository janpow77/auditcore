"""Annual cost calculation with exact decimals, explicit units and a trace.

``calculate`` evaluates a :class:`~auditcore_price_analysis.tariff.Tariff`
under an explicitly chosen :class:`~auditcore_price_analysis.profiles.CalculationProfile`:

* every component line states unit, price, quantity, factor, exact and rounded
  amount and whether it was given, missing, tiered, superseded or not applicable
  on the reference day;
* missing values are never zero: a missing component makes the total a
  *lower bound* and is named in the result; missing consumption is an error;
* comparability requires all required components, the release status the
  profile demands and validity of the tariff on the reference day. The library
  only reports; it never releases a price.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from .errors import PriceAnalysisError
from .numbers import non_negative, parse_day, text
from .profiles import CalculationProfile, ComponentRule
from .tariff import ReleaseStatus, Tariff, Tier

GIVEN = "angegeben"
MISSING = "fehlt"
TIERED = "gestaffelt"
NOT_APPLICABLE = "nicht_anwendbar"


@dataclass(frozen=True)
class TierUse:
    """Quantity billed in one tier."""

    lower: Decimal
    limit: Decimal | None
    price: Decimal
    quantity: Decimal
    amount: Decimal

    def to_dict(self) -> dict[str, str | None]:
        """JSON view."""
        return {
            "lower": str(self.lower),
            "limit": text(self.limit),
            "price": str(self.price),
            "quantity": str(self.quantity),
            "amount": str(self.amount),
        }


@dataclass(frozen=True)
class Line:
    """One component of the formula on the reference day."""

    component: str
    line: str
    label: str | None
    unit: str
    status: str
    price: Decimal | None
    basis: str | None
    quantity: Decimal | None
    factor: Decimal
    amount: Decimal | None
    amount_rounded: Decimal | None
    tiers: tuple[TierUse, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """JSON view."""
        return {
            "component": self.component,
            "line": self.line,
            "label": self.label,
            "unit": self.unit,
            "status": self.status,
            "price": text(self.price),
            "basis": self.basis,
            "quantity": text(self.quantity),
            "factor": str(self.factor),
            "amount": text(self.amount),
            "amount_rounded": text(self.amount_rounded),
            "tiers": [t.to_dict() for t in self.tiers],
        }


@dataclass(frozen=True)
class CalculationResult:
    """Structured result; exact values plus values rounded by the profile rule."""

    profile: Mapping[str, str]
    kind: str
    stichtag: date
    consumption: Mapping[str, Decimal]
    lines: tuple[Line, ...]
    total: Decimal
    total_rounded: Decimal
    total_is_lower_bound: bool
    missing_required: tuple[str, ...]
    missing_optional: tuple[str, ...]
    comparable: bool
    not_comparable_reasons: tuple[str, ...]
    mixed_price_name: str
    mixed_price_unit: str
    mixed_price: Decimal | None
    fixed_share_pct: Decimal | None
    variable_share_pct: Decimal | None
    release: ReleaseStatus
    issues: tuple[str, ...]

    def line(self, name: str) -> Line:
        """The (applicable) line with the given result name, e.g. ``umlagenpreis_anteil``."""
        for item in self.lines:
            if item.line == name and item.status != NOT_APPLICABLE:
                return item
        for item in self.lines:
            if item.line == name:
                return item
        raise KeyError(name)

    def to_dict(self) -> dict[str, Any]:
        """JSON view; decimals as text so no precision is lost."""
        return {
            "profile": dict(self.profile),
            "kind": self.kind,
            "stichtag": self.stichtag.isoformat(),
            "consumption": {k: str(v) for k, v in self.consumption.items()},
            "lines": [line.to_dict() for line in self.lines],
            "total": str(self.total),
            "total_rounded": str(self.total_rounded),
            "total_is_lower_bound": self.total_is_lower_bound,
            "missing_required": list(self.missing_required),
            "missing_optional": list(self.missing_optional),
            "comparable": self.comparable,
            "not_comparable_reasons": list(self.not_comparable_reasons),
            "mixed_price": {
                "name": self.mixed_price_name,
                "unit": self.mixed_price_unit,
                "value": text(self.mixed_price),
            },
            "fixed_share_pct": text(self.fixed_share_pct),
            "variable_share_pct": text(self.variable_share_pct),
            "release": self.release.value,
            "issues": list(self.issues),
        }


def tiered_amount(
    tiers: tuple[Tier, ...], quantity: Decimal, *, open_last: bool
) -> tuple[Decimal, tuple[TierUse, ...], bool]:
    """Bill ``quantity`` through sorted tiers; returns amount, usage and "beyond last limit".

    With ``open_last`` the last tier takes the remaining quantity even when it
    declares a limit (source rule); otherwise quantity beyond the last limit is
    an error instead of being left unpriced.
    """
    uses: list[TierUse] = []
    remaining = quantity
    lower = Decimal(0)
    total = Decimal(0)
    last = tiers[-1]
    beyond = last.limit is not None and quantity > last.limit
    if beyond and not open_last:
        raise PriceAnalysisError(
            "beyond_last_tier", "Verbrauch liegt über der letzten Staffelgrenze.", field="tiers"
        )
    for index, tier in enumerate(tiers):
        if remaining <= 0:
            break
        is_last = index == len(tiers) - 1
        open_band = is_last or tier.limit is None
        band = remaining if open_band or tier.limit is None else min(remaining, tier.limit - lower)
        if band > 0:
            amount = band * tier.price
            uses.append(TierUse(lower, tier.limit, tier.price, band, amount))
            total += amount
            remaining -= band
        if tier.limit is not None:
            lower = tier.limit
    return total, tuple(uses), beyond


def _consumption(profile: CalculationProfile, consumption: Mapping[str, Any]) -> dict[str, Decimal]:
    names = [c.name for c in profile.consumption]
    unknown = set(consumption) - set(names)
    if unknown:
        raise PriceAnalysisError(
            "unknown_consumption", f"Unbekannte Verbrauchsgrößen {sorted(unknown)}."
        )
    return {name: non_negative(consumption.get(name), field=name) for name in names}


def calculate(
    tariff: Tariff,
    profile: CalculationProfile,
    *,
    consumption: Mapping[str, Any],
    stichtag: date | str,
) -> CalculationResult:
    """Annual costs of ``tariff`` on ``stichtag`` under ``profile``.

    Every consumption quantity of the profile must be given explicitly; there
    is no silent default (see PA-H03 for the conflicting water standard).
    """
    if tariff.kind != profile.kind:
        raise PriceAnalysisError(
            "profile_mismatch", f"Tarifart {tariff.kind} passt nicht zu Profil {profile.kind}."
        )
    day = parse_day(stichtag)
    quantities = _consumption(profile, consumption)
    lines: list[Line] = []
    issues: list[str] = []
    missing_required: list[str] = []
    missing_optional: list[str] = []
    for rule in profile.components:
        price = tariff.components.get(rule.name)
        quantity = quantities[rule.basis] if rule.basis else None

        def line(
            status: str,
            price: Decimal | None,
            quantity: Decimal | None,
            amount: Decimal | None,
            uses: tuple[TierUse, ...] = (),
            rule: ComponentRule = rule,
        ) -> Line:
            return Line(
                component=rule.name,
                line=rule.line,
                label=rule.label,
                unit=rule.unit,
                status=status,
                price=price,
                basis=rule.basis,
                quantity=quantity,
                factor=rule.factor,
                amount=amount,
                amount_rounded=None if amount is None else profile.money.apply(amount),
                tiers=uses,
            )

        if not rule.applies(day):
            if price is not None:
                issues.append(f"{rule.name}: am Stichtag nicht anwendbar, nicht berücksichtigt")
            lines.append(line(NOT_APPLICABLE, price, quantity, None))
            continue
        if rule.tiered_by and profile.tiers is not None and tariff.tiers:
            tier_quantity = quantities[profile.tiers.quantity]
            amount, uses, beyond = tiered_amount(
                tariff.tiers, tier_quantity, open_last=profile.tiers.open_last
            )
            if price is not None:
                issues.append(f"{rule.name}: durch Staffel {profile.tiers.field} überlagert")
            if beyond:
                issues.append(
                    f"{profile.tiers.field}: Verbrauch über der letzten Staffelgrenze, "
                    "letzte Stufe gilt unbegrenzt (Profilregel)"
                )
            for key in tariff.extra.get("ignored_tier_keys", []):
                issues.append(f"{profile.tiers.field}: Angabe {key} nicht ausgewertet")
            lines.append(line(TIERED, None, tier_quantity, amount, uses))
            continue
        if price is None:
            (missing_required if rule.required else missing_optional).append(rule.name)
            lines.append(line(MISSING, None, quantity, None))
            continue
        amount = price * (quantity if quantity is not None else Decimal(1)) * rule.factor
        lines.append(line(GIVEN, price, quantity, amount))
    amounts = [(item.component, item.amount) for item in lines if item.amount is not None]
    total = sum((amount for _, amount in amounts), Decimal(0))
    fixed = sum((amount for name, amount in amounts if profile.component(name).fixed), Decimal(0))
    mixed_rule = profile.mixed_price
    basis = quantities[mixed_rule.basis]
    mixed = profile.mixed_rounding.apply(total / basis * mixed_rule.factor) if basis > 0 else None
    fixed_share = profile.percent.apply(fixed / total * 100) if total > 0 else None
    variable_share = (
        profile.percent.apply(Decimal(100) - fixed / total * 100) if total > 0 else None
    )
    reasons = [f"fehlt:{name}" for name in missing_required]
    if profile.optional_missing_blocks_comparison:
        reasons += [f"fehlt:{name}" for name in missing_optional]
    if profile.require_released_for_comparison and tariff.release is not ReleaseStatus.FREIGEGEBEN:
        reasons.append(f"freigabe:{tariff.release.value}")
    if tariff.valid_from is not None and day < tariff.valid_from:
        reasons.append("noch_nicht_gueltig")
    if tariff.valid_to is not None and day > tariff.valid_to:
        reasons.append("nicht_mehr_gueltig")
    return CalculationResult(
        profile=profile.reference,
        kind=profile.kind,
        stichtag=day,
        consumption=quantities,
        lines=tuple(lines),
        total=total,
        total_rounded=profile.money.apply(total),
        total_is_lower_bound=bool(missing_required or missing_optional),
        missing_required=tuple(missing_required),
        missing_optional=tuple(missing_optional),
        comparable=not reasons,
        not_comparable_reasons=tuple(reasons),
        mixed_price_name=mixed_rule.name,
        mixed_price_unit=mixed_rule.unit,
        mixed_price=mixed,
        fixed_share_pct=fixed_share,
        variable_share_pct=variable_share,
        release=tariff.release,
        issues=tuple(issues),
    )
