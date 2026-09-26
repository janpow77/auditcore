"""Versioned, source-bound calculation and comparison profiles.

A profile names every rule that influences a price result: formula
components with units and bases, validity windows (for example the switch of
the levy on 2025-07-01), tier rules, rounding, the handling of missing values,
the release requirement and the comparison thresholds. Results carry the
profile id, version and fingerprint. Profiles are data shipped with the
package; there is no silent default profile.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import date
from decimal import Decimal
from importlib import resources
from typing import Any

from auditcore_common.hashing import canonical_sha256

from ._profile_model import (
    CalculationProfile,
    ComparisonProfile,
    ComponentRule,
    ConsumptionRule,
    MixedPriceRule,
    TierRule,
)
from .errors import ProfileError
from .numbers import Rounding

__all__ = [
    "SCHEMA",
    "CalculationProfile",
    "ComparisonProfile",
    "ComponentRule",
    "ConsumptionRule",
    "MixedPriceRule",
    "TierRule",
    "available_profiles",
    "calculation_profile_from_dict",
    "comparison_profile_from_dict",
    "load_calculation_profile",
    "load_comparison_profile",
    "load_recommended_calculation_profile",
    "load_recommended_comparison_profile",
    "recommended_version",
    "standard_consumption",
]

SCHEMA = "auditcore_price_analysis.profile/1"




def _dec(data: Mapping[str, object], key: str, where: str) -> Decimal:
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


def _day(value: object, where: str) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ProfileError(f"{where} ist kein Datum.") from exc


def _rounding(data: object, where: str) -> Rounding:
    if not isinstance(data, Mapping):
        raise ProfileError(f"{where} fehlt.")
    return Rounding(_dec(data, "places", where), str(data.get("mode")))


def _header(data: Mapping[str, object], kind: str) -> tuple[str, str]:
    if data.get("schema") != SCHEMA or data.get("type") != kind:
        raise ProfileError(f"Profil ist kein {kind}-Profil des Schemas {SCHEMA}.")
    profile_id, version = data.get("profile_id"), data.get("version")
    if not isinstance(profile_id, str) or not isinstance(version, str) or not profile_id:
        raise ProfileError("Profil ohne Kennung oder Version.")
    if not isinstance(data.get("source"), Mapping):
        raise ProfileError("Profil ohne Quellenbindung.")
    return profile_id, version


def _consumption_rules(data: Mapping[str, Any]) -> tuple[ConsumptionRule, ...]:
    return tuple(
        ConsumptionRule(
            name=str(c["name"]),
            unit=str(c["unit"]),
            legacy_default=None
            if c.get("legacy_default") is None
            else _dec(c, "legacy_default", "consumption"),
            note=str(c.get("note", "")),
            standard=None if c.get("standard") is None else _dec(c, "standard", "consumption"),
            standard_source=c.get("standard_source"),
        )
        for c in data.get("consumption", [])
    )


def _component_rule(raw: Mapping[str, Any], names: set[str]) -> ComponentRule:
    where = f"components.{raw.get('name')}"
    basis = raw.get("basis")
    if basis is not None and basis not in names:
        raise ProfileError(f"{where}: Bezugsgröße {basis} ist keine Verbrauchsgröße.")
    return ComponentRule(
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


def _tier_rule(
    tiers_raw: Mapping[str, Any] | None, names: set[str], components: list[ComponentRule]
) -> TierRule | None:
    if tiers_raw is None:
        return None
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
    return tiers


def _mixed_price_rule(mixed: Mapping[str, Any], names: set[str]) -> MixedPriceRule:
    if mixed["basis"] not in names:
        raise ProfileError("mixed_price.basis ist keine Verbrauchsgröße.")
    return MixedPriceRule(
        str(mixed["name"]),
        str(mixed["unit"]),
        str(mixed["basis"]),
        _dec(mixed, "factor", "mixed_price"),
    )


def calculation_profile_from_dict(data: Mapping[str, Any]) -> CalculationProfile:
    """Validate and freeze a calculation profile."""
    profile_id, version = _header(data, "calculation")
    consumption = _consumption_rules(data)
    names = {c.name for c in consumption}
    components = [_component_rule(raw, names) for raw in data.get("components", [])]
    if len({c.name for c in components}) != len(components) or not components:
        raise ProfileError("Komponenten fehlen oder sind doppelt.")
    tiers = _tier_rule(data.get("tiers"), names, components)
    mixed_price = _mixed_price_rule(data["mixed_price"], names)
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
        mixed_price=mixed_price,
        money=_rounding(rounding.get("money"), "rounding.money"),
        percent=_rounding(rounding.get("percent"), "rounding.percent"),
        mixed_rounding=_rounding(rounding.get("mixed_price"), "rounding.mixed_price"),
        optional_missing_blocks_comparison=bool(missing.get("optional_missing_blocks_comparison")),
        require_released_for_comparison=bool(release.get("require_released_for_comparison", True)),
        fingerprint=canonical_sha256(data),
        raw=data,
        recommended=bool(data.get("recommended", False)),
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
        fingerprint=canonical_sha256(data),
        raw=data,
        recommended=bool(data.get("recommended", False)),
    )


def _shipped() -> dict[tuple[str, str], Mapping[str, Any]]:
    found: dict[tuple[str, str], Mapping[str, Any]] = {}
    folder = resources.files("auditcore_price_analysis") / "profiles"
    for entry in folder.iterdir():
        if entry.name.endswith(".json"):
            data = json.loads(entry.read_text(encoding="utf-8"))
            found[(str(data["profile_id"]), str(data["version"]))] = data
    return found


def available_profiles() -> list[dict[str, Any]]:
    """Shipped profiles with id, version, type, status and fingerprint."""
    return sorted(
        (
            {
                "profile_id": pid,
                "version": version,
                "type": str(data["type"]),
                "status": str(data.get("status", "UNKNOWN")),
                "recommended": bool(data.get("recommended", False)),
                "fingerprint": canonical_sha256(data),
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


def recommended_version(profile_id: str) -> str:
    """Version of ``profile_id`` marked as recommended (decided rules); exactly one must exist."""
    versions = [
        v for (pid, v), data in _shipped().items() if pid == profile_id and data.get("recommended")
    ]
    if len(versions) != 1:
        raise ProfileError(f"Für {profile_id} ist nicht genau eine empfohlene Version hinterlegt.")
    return versions[0]


def load_recommended_calculation_profile(profile_id: str) -> CalculationProfile:
    """The recommended (decided) calculation profile, e.g. ``regulierung.hpp.wasser``."""
    return load_calculation_profile(profile_id, recommended_version(profile_id))


def load_recommended_comparison_profile(profile_id: str) -> ComparisonProfile:
    """The recommended (decided) comparison profile."""
    return load_comparison_profile(profile_id, recommended_version(profile_id))


def standard_consumption(profile: CalculationProfile) -> dict[str, Decimal]:
    """Standard consumption stated by the profile (single source); error if a value is missing."""
    missing = [c.name for c in profile.consumption if c.standard is None]
    if missing:
        raise ProfileError(
            f"Profil {profile.profile_id}@{profile.version} nennt keinen Standardverbrauch "
            f"für {missing}; Verbrauch ausdrücklich angeben."
        )
    return {c.name: c.standard for c in profile.consumption if c.standard is not None}
