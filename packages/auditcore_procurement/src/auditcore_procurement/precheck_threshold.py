"""Threshold classification of the prechecks (legacy table and strict EU periods)."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from decimal import Decimal
from typing import Any

from .precheck_common import (
    FAIL,
    PASS,
    REVIEW_REQUIRED,
    WARNING,
    CheckResult,
    category_of,
    is_missing,
    result,
)
from .precheck_profile import (
    AUTHORITY_TYPES,
    EuThreshold,
    PrecheckProfile,
    ThresholdPeriod,
    ThresholdUnavailable,
    eu_period,
    eu_period_for_year,
    eu_threshold,
)

_THRESHOLD_CHECK = ("precheck_threshold", "Schwellenwert-Klassifikation")


def _strict_threshold(
    profile: PrecheckProfile,
    estimated_value: Decimal,
    category: str,
    threshold_tier: str | None,
    reference_date: date | None,
    year: int | None,
    authority_type: str | None,
) -> CheckResult:
    """Tier with the EU threshold of the case's period (reached or exceeded = above EU)."""
    if profile.eu_tier is None:
        return result(
            *_THRESHOLD_CHECK,
            REVIEW_REQUIRED,
            f"Profil {profile.id} {profile.version} hat keine jahresbezogenen "
            "EU-Schwellenwerte; bitte procurement.hvtg verwenden.",
        )
    if authority_type is not None and authority_type not in AUTHORITY_TYPES:
        raise ValueError(f"authority_type muss eine von {AUTHORITY_TYPES} oder None sein.")
    if reference_date is None and year is None:
        return result(
            *_THRESHOLD_CHECK,
            REVIEW_REQUIRED,
            "Stichtag fehlt: Datum der Maßnahme/Bekanntmachung oder Jahr angeben; "
            "der EU-Schwellenwert gilt je Zeitraum.",
        )
    try:
        period = (
            eu_period(profile, reference_date)
            if reference_date is not None
            else eu_period_for_year(profile, int(year or 0))
        )
    except ThresholdUnavailable as exc:
        return result(*_THRESHOLD_CHECK, REVIEW_REQUIRED, str(exc))
    value = float(estimated_value)
    threshold, limits = _case_threshold(profile, category, period, value, authority_type)
    if threshold is None:
        return result(
            *_THRESHOLD_CHECK,
            REVIEW_REQUIRED,
            f"Der Auftragswert {estimated_value} EUR liegt zwischen den "
            f"EU-Schwellenwerten für zentrale ({limits[0].value} EUR) und "
            f"sonstige Auftraggeber ({limits[-1].value} EUR); Art des "
            "Auftraggebers (authority_type) angeben.",
            eu_thresholds=[c.to_dict() for c in limits],
        )
    calculated = _strict_tier(profile, category, value, threshold)
    return _strict_verdict(profile, threshold_tier, calculated, threshold, estimated_value)


def _case_threshold(
    profile: PrecheckProfile,
    category: str,
    period: ThresholdPeriod,
    value: float,
    authority_type: str | None,
) -> tuple[EuThreshold | None, list[EuThreshold]]:
    """Applicable threshold, or ``None`` with both limits when the authority type decides."""
    candidates = (
        {t: eu_threshold(profile, category, period, t) for t in AUTHORITY_TYPES}
        if isinstance((profile.eu_categories or {}).get(category), Mapping)
        else {"": eu_threshold(profile, category, period, "sub_central")}
    )
    if authority_type is not None and "" not in candidates:
        return candidates[authority_type], []
    limits = sorted(candidates.values(), key=lambda c: c.value)
    if len(limits) > 1 and limits[0].value <= value < limits[-1].value:
        return None, limits
    return (limits[-1] if value >= limits[-1].value else limits[0]), limits


def _strict_tier(
    profile: PrecheckProfile, category: str, value: float, threshold: EuThreshold
) -> str:
    """First national tier covering the value, else below/above the EU threshold."""
    calculated = next(
        (
            t.name
            for t in profile.tiers.get(category, ())
            if t.name in profile.national_tiers and t.maximum is not None and value <= t.maximum
        ),
        None,
    )
    if calculated is None:
        calculated = profile.eu_tier if value < threshold.value else profile.fallback_tier
    return str(calculated)


def _strict_verdict(
    profile: PrecheckProfile,
    threshold_tier: str | None,
    calculated: str,
    threshold: EuThreshold,
    estimated_value: Decimal,
) -> CheckResult:
    """PASS, or FAIL when the recorded tier differs from the calculated one."""
    extra: dict[str, Any] = {
        "calculated_tier": calculated,
        "eu_threshold": threshold.to_dict(),
        "national_tiers_status": profile.national_status,
    }
    if threshold_tier and threshold_tier != calculated:
        return result(
            *_THRESHOLD_CHECK,
            FAIL,
            f"Schwellenwert-Stufe '{threshold_tier}' stimmt nicht mit berechnetem Wert "
            f"'{calculated}' überein (Auftragswert: {estimated_value} EUR, "
            f"EU-Schwellenwert {threshold.value} EUR gültig "
            f"{threshold.period.valid_from:%d.%m.%Y}–{threshold.period.valid_to:%d.%m.%Y}).",
            **extra,
        )
    return result(
        *_THRESHOLD_CHECK,
        PASS,
        f"Schwellenwert korrekt: {calculated} ({estimated_value} EUR; EU-Schwellenwert "
        f"{threshold.value} EUR, {threshold.period.source.get('regulation')}).",
        **extra,
    )


def check_threshold(
    profile: PrecheckProfile,
    estimated_value: Decimal | None,
    service_type: str,
    threshold_tier: str | None,
    mode: str = "legacy",
    *,
    reference_date: date | None = None,
    year: int | None = None,
    authority_type: str | None = None,
) -> CheckResult:
    """Tier from the estimated value.

    ``legacy``: inclusive maxima of the source table in profile order.
    ``strict``: national tiers from the profile, then the EU threshold of the
    period of ``reference_date``/``year`` (schema 2 profiles only).
    """
    name = "Schwellenwert-Klassifikation"
    if is_missing(estimated_value, mode):
        return result(
            "precheck_threshold", name, WARNING, "Kein geschaetzter Auftragswert angegeben."
        )
    assert estimated_value is not None
    category = category_of(profile, service_type)
    if mode == "strict":
        return _strict_threshold(
            profile, estimated_value, category, threshold_tier, reference_date, year, authority_type
        )
    calculated = (
        next(
            (
                t.name
                for t in profile.tiers.get(category, ())
                if t.maximum is None or float(estimated_value) <= t.maximum
            ),
            None,
        )
        or profile.fallback_tier
    )
    if threshold_tier and threshold_tier != calculated:
        return result(
            "precheck_threshold",
            name,
            FAIL,
            f"Schwellenwert-Stufe '{threshold_tier}' stimmt nicht mit berechnetem Wert "
            f"'{calculated}' ueberein "
            f"(Auftragswert: {estimated_value} EUR, Kategorie: {category}).",
            calculated_tier=calculated,
        )
    return result(
        "precheck_threshold",
        name,
        PASS,
        f"Schwellenwert korrekt: {calculated} ({estimated_value} EUR).",
        calculated_tier=calculated,
    )
