"""Versioned, source-bound calculation and comparison profiles.

A profile names every rule that influences a price result: formula
components with units and bases, validity windows (for example the switch of
the levy on 2025-07-01), tier rules, rounding, the handling of missing values,
the release requirement and the comparison thresholds. Results carry the
profile id, version and fingerprint. Profiles are data shipped with the
package; there is no silent default profile.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from importlib import resources
from typing import Any

from .errors import ProfileError
from .numbers import Rounding

SCHEMA = "auditcore_price_analysis.profile/1"


def _fingerprint(data: Mapping[str, Any]) -> str:
    raw = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _dec(data: Mapping[str, Any], key: str, where: str) -> Decimal:
    value = data.get(key)
    if not isinstance(value, str):
        raise ProfileError(f"{where}.{key} muss als Dezimaltext angegeben sein.")
    try:
        result = Decimal(value)
    except ArithmeticError as exc:
        raise ProfileError(f"{where}.{key} ist keine Zahl.") from exc
    if not result.is_finite():
        raise ProfileError(f"{where}.{key} muss endlich sein.")
    return result


def _day(value: Any, where: str) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ProfileError(f"{where} ist kein Datum.") from exc


def _rounding(data: Any, where: str) -> Rounding:
    if not isinstance(data, Mapping):
        raise ProfileError(f"{where} fehlt.")
    return Rounding(_dec(data, "places", where), str(data.get("mode")))


@dataclass(frozen=True)
class ConsumptionRule:
    """A consumption quantity of the formula (``legacy_default`` is documentation only)."""

    name: str
    unit: str
    legacy_default: Decimal | None
    note: str = ""


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

    @property
    def reference(self) -> dict[str, str]:
        """Identity carried by every result."""
        return {
            "profile_id": self.profile_id,
            "version": self.version,
            "fingerprint": self.fingerprint,
        }


def _header(data: Mapping[str, Any], kind: str) -> tuple[str, str]:
    if data.get("schema") != SCHEMA or data.get("type") != kind:
        raise ProfileError(f"Profil ist kein {kind}-Profil des Schemas {SCHEMA}.")
    profile_id, version = data.get("profile_id"), data.get("version")
    if not isinstance(profile_id, str) or not isinstance(version, str) or not profile_id:
        raise ProfileError("Profil ohne Kennung oder Version.")
    if not isinstance(data.get("source"), Mapping):
        raise ProfileError("Profil ohne Quellenbindung.")
    return profile_id, version


def calculation_profile_from_dict(data: Mapping[str, Any]) -> CalculationProfile:
    """Validate and freeze a calculation profile."""
    profile_id, version = _header(data, "calculation")
    consumption = tuple(
        ConsumptionRule(
            name=str(c["name"]),
            unit=str(c["unit"]),
            legacy_default=None
            if c.get("legacy_default") is None
            else _dec(c, "legacy_default", "consumption"),
            note=str(c.get("note", "")),
        )
        for c in data.get("consumption", [])
    )
    names = {c.name for c in consumption}
    components: list[ComponentRule] = []
    for raw in data.get("components", []):
        where = f"components.{raw.get('name')}"
        basis = raw.get("basis")
        if basis is not None and basis not in names:
            raise ProfileError(f"{where}: Bezugsgröße {basis} ist keine Verbrauchsgröße.")
        components.append(
            ComponentRule(
                name=str(raw["name"]),
                line=str(raw["line"]),
                unit=str(raw["unit"]),
                basis=basis,
                factor=_dec(raw, "factor", where),
                required=bool(raw["required"]),
                fixed=bool(raw["fixed"]),
                label=raw.get("label"),
                valid_from=_day(raw.get("valid_from"), f"{where}.valid_from"),
                valid_until=_day(raw.get("valid_until"), f"{where}.valid_until"),
                tiered_by=raw.get("tiered_by"),
            )
        )
    if len({c.name for c in components}) != len(components) or not components:
        raise ProfileError("Komponenten fehlen oder sind doppelt.")
    tiers_raw = data.get("tiers")
    tiers = None
    if tiers_raw is not None:
        tiers = TierRule(
            field=str(tiers_raw["field"]),
            quantity=str(tiers_raw["quantity"]),
            limit_key=str(tiers_raw["limit_key"]),
            price_key=str(tiers_raw["price_key"]),
            unit=str(tiers_raw["unit"]),
            wrapper_key=tiers_raw.get("wrapper_key"),
            open_last=bool(tiers_raw["open_last"]),
        )
        if tiers.quantity not in names:
            raise ProfileError("tiers.quantity ist keine Verbrauchsgröße.")
        if not any(c.tiered_by == tiers.field for c in components):
            raise ProfileError("Keine Komponente verweist auf die Staffel.")
    mixed = data["mixed_price"]
    if mixed["basis"] not in names:
        raise ProfileError("mixed_price.basis ist keine Verbrauchsgröße.")
    rounding = data.get("rounding", {})
    missing = data.get("missing", {})
    release = data.get("release", {})
    return CalculationProfile(
        profile_id=profile_id,
        version=version,
        kind=str(data["kind"]),
        title=str(data.get("title", "")),
        status=str(data.get("status", "UNKNOWN")),
        source=dict(data["source"]),
        formula=str(data.get("formula", "")),
        consumption=consumption,
        components=tuple(components),
        tiers=tiers,
        mixed_price=MixedPriceRule(
            str(mixed["name"]),
            str(mixed["unit"]),
            str(mixed["basis"]),
            _dec(mixed, "factor", "mixed_price"),
        ),
        money=_rounding(rounding.get("money"), "rounding.money"),
        percent=_rounding(rounding.get("percent"), "rounding.percent"),
        mixed_rounding=_rounding(rounding.get("mixed_price"), "rounding.mixed_price"),
        optional_missing_blocks_comparison=bool(missing.get("optional_missing_blocks_comparison")),
        require_released_for_comparison=bool(release.get("require_released_for_comparison", True)),
        fingerprint=_fingerprint(data),
        raw=data,
    )


def comparison_profile_from_dict(data: Mapping[str, Any]) -> ComparisonProfile:
    """Validate and freeze a comparison profile."""
    profile_id, version = _header(data, "comparison")
    light = data["traffic_light"]
    threshold = _dec(light, "threshold_pct", "traffic_light")
    fraction = _dec(light, "yellow_from_fraction", "traffic_light")
    if threshold < 0 or not 0 <= fraction <= 1:
        raise ProfileError("Ampelschwelle muss ≥ 0 und der Gelbanteil zwischen 0 und 1 liegen.")
    statistics = data["statistics"]
    if statistics.get("stddev") not in ("population", "sample"):
        raise ProfileError("statistics.stddev muss population oder sample sein.")
    selection = data["selection"]
    return ComparisonProfile(
        profile_id=profile_id,
        version=version,
        title=str(data.get("title", "")),
        status=str(data.get("status", "UNKNOWN")),
        source=dict(data["source"]),
        delta_rounding=_rounding(data["delta"]["rounding"], "delta.rounding"),
        threshold_pct=threshold,
        yellow_from_fraction=fraction,
        statistics_rounding=_rounding(statistics["rounding"], "statistics.rounding"),
        stddev=str(statistics["stddev"]),
        only_released=bool(selection["only_released"]),
        not_after_reference_date=bool(selection["not_after_reference_date"]),
        respect_valid_to=bool(selection["respect_valid_to"]),
        q3_tolerance=_dec(selection, "q3_tolerance", "selection"),
        prefer_standard_variants=bool(selection["prefer_standard_variants"]),
        fingerprint=_fingerprint(data),
        raw=data,
    )


def _shipped() -> dict[tuple[str, str], Mapping[str, Any]]:
    found: dict[tuple[str, str], Mapping[str, Any]] = {}
    folder = resources.files("auditcore_price_analysis") / "profiles"
    for entry in folder.iterdir():
        if entry.name.endswith(".json"):
            data = json.loads(entry.read_text(encoding="utf-8"))
            found[(str(data["profile_id"]), str(data["version"]))] = data
    return found


def available_profiles() -> list[dict[str, str]]:
    """Shipped profiles with id, version, type, status and fingerprint."""
    return sorted(
        (
            {
                "profile_id": pid,
                "version": version,
                "type": str(data["type"]),
                "status": str(data.get("status", "UNKNOWN")),
                "fingerprint": _fingerprint(data),
            }
            for (pid, version), data in _shipped().items()
        ),
        key=lambda row: (row["profile_id"], row["version"]),
    )


def _load(profile_id: str, version: str) -> Mapping[str, Any]:
    try:
        return _shipped()[(profile_id, version)]
    except KeyError as exc:
        raise ProfileError(
            f"Profil {profile_id} in Version {version} ist nicht vorhanden."
        ) from exc


def load_calculation_profile(profile_id: str, version: str) -> CalculationProfile:
    """Shipped calculation profile; the version must be named explicitly."""
    return calculation_profile_from_dict(_load(profile_id, version))


def load_comparison_profile(profile_id: str, version: str) -> ComparisonProfile:
    """Shipped comparison profile; the version must be named explicitly."""
    return comparison_profile_from_dict(_load(profile_id, version))
