"""Versioned precheck profiles: validation, packaged profiles and EU threshold periods.

Part of :mod:`auditcore_procurement.prechecks` (which re-exports every public
name): the ``threshold_rules``/``required_documents_by_procedure`` of the
``PROCUREMENT_HVTG`` ruleset as a validated, fingerprinted profile, and the
year-bound EU thresholds of schema 2 with their official sources.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from importlib import resources
from typing import Any

from auditcore_common.hashing import canonical_sha256
from auditcore_common.profiles import load_packaged_profile

AUTHORITY_TYPES = ("central", "sub_central")
#: Decoded profile or ruleset JSON as read from a file or passed by a consumer.
ProfileData = Mapping[str, Any]
SCHEMAS = ("auditcore_procurement.precheck-profile/1", "auditcore_procurement.precheck-profile/2")


class ProfileError(ValueError):
    """The precheck profile is missing or malformed."""


class ThresholdUnavailable(LookupError):
    """No verified EU threshold is recorded for the requested date/year."""


@dataclass(frozen=True)
class ThresholdPeriod:
    """EU thresholds valid from/to (inclusive) with their official source."""

    valid_from: date
    valid_to: date
    values: Mapping[str, int]
    source: ProfileData


@dataclass(frozen=True)
class EuThreshold:
    """The EU threshold applicable to one case."""

    value: int
    key: str
    period: ThresholdPeriod

    def to_dict(self) -> dict[str, Any]:
        """JSON view recorded in strict results."""
        return {
            "value": self.value,
            "key": self.key,
            "valid_from": self.period.valid_from.isoformat(),
            "valid_to": self.period.valid_to.isoformat(),
            "regulation": self.period.source.get("regulation"),
            "official_journal": self.period.source.get("official_journal"),
        }


@dataclass(frozen=True)
class Tier:
    """Threshold tier: inclusive upper bound (``None`` = open), expected procedure, bids."""

    name: str
    maximum: float | None
    procedure: str
    min_bids: int


@dataclass(frozen=True)
class PrecheckProfile:
    """Versioned, source-bound rules of the deterministic prechecks."""

    id: str
    version: str
    status: str
    legal_status: str
    construction_marker: str
    tiers: Mapping[str, tuple[Tier, ...]]
    fallback_tier: str
    required_documents: Mapping[str, tuple[str, ...]]
    bid_document_type: str
    default_min_bids: int
    warning_above_percent: float
    fail_above_percent: float
    fail_reference: str
    source: ProfileData
    fingerprint: str
    eu_periods: tuple[ThresholdPeriod, ...] = ()
    eu_tier: str | None = None
    eu_categories: ProfileData | None = None
    national_tiers: tuple[str, ...] = ()
    national_status: str = ""

    @property
    def reference(self) -> dict[str, str]:
        """Identity recorded in every result."""
        return {"id": self.id, "version": self.version, "fingerprint": self.fingerprint}


def profile_from_dict(data: ProfileData) -> PrecheckProfile:
    """Validate and build a profile; nothing is defaulted silently."""
    try:
        if data["schema"] not in SCHEMAS:
            raise ProfileError("Unbekanntes Profilschema.")
        tiers = {
            category: tuple(
                Tier(
                    t["tier"],
                    None if t["max"] is None else float(t["max"]),
                    str(t["procedure"]),
                    int(t["min_bids"]),
                )
                for t in rows
            )
            for category, rows in data["tiers"].items()
        }
        for category, rows in tiers.items():
            bounds = [t.maximum for t in rows if t.maximum is not None]
            if bounds != sorted(bounds) or not rows or rows[-1].maximum is not None:
                raise ProfileError(
                    f"Schwellenstufen von '{category}' sind nicht aufsteigend/offen."
                )
        deviation = data["value_deviation"]
        if not 0 <= deviation["warning_above_percent"] <= deviation["fail_above_percent"]:
            raise ProfileError("Ungültige Abweichungsschwellen.")
        periods, eu_tier, eu_categories, national, national_status = _schema2(data, tiers)
        fingerprint = canonical_sha256(data)
        return PrecheckProfile(
            id=data["id"],
            version=data["version"],
            status=data["status"],
            legal_status=data["legal_status"],
            construction_marker=data["construction_marker"],
            tiers=tiers,
            fallback_tier=data["fallback_tier"],
            required_documents={k: tuple(v) for k, v in data["required_documents"].items()},
            bid_document_type=data["bid_document_type"],
            default_min_bids=int(data["default_min_bids"]),
            warning_above_percent=float(deviation["warning_above_percent"]),
            fail_above_percent=float(deviation["fail_above_percent"]),
            fail_reference=deviation["fail_reference"],
            source=dict(data["source"]),
            fingerprint=fingerprint,
            eu_periods=periods,
            eu_tier=eu_tier,
            eu_categories=eu_categories,
            national_tiers=national,
            national_status=national_status,
        )
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ProfileError):
            raise
        raise ProfileError(f"Profil ist unvollständig oder fehlerhaft: {exc!r}") from exc


def _schema2(
    data: ProfileData, tiers: Mapping[str, tuple[Tier, ...]]
) -> tuple[tuple[ThresholdPeriod, ...], str | None, ProfileData | None, tuple[str, ...], str]:
    """Validate the year-bound EU table and the national tier block of schema 2."""
    if data["schema"].endswith("/1"):
        return (), None, None, (), ""
    table = data["eu_thresholds"]
    periods = _eu_periods(table["periods"])
    categories = dict(table["categories"])
    keys = {k for p in periods for k in p.values}
    for category, spec in categories.items():
        wanted = spec.values() if isinstance(spec, Mapping) else [spec]
        if category not in tiers or not set(wanted) <= keys:
            raise ProfileError(f"EU-Schwellenwertzuordnung für '{category}' ist unvollständig.")
    eu_tier = str(table["tier"])
    national = data["national_tiers"]
    names = tuple(str(n) for n in national["tiers"])
    for rows in tiers.values():
        known = [t.name for t in rows]
        if eu_tier not in known or not set(names) <= set(known):
            raise ProfileError("Nationale Stufen oder EU-Stufe fehlen in der Stufentabelle.")
    return tuple(periods), eu_tier, categories, names, str(national["status"])


def _eu_periods(rows: Sequence[ProfileData]) -> list[ThresholdPeriod]:
    """Validated periods in date order; overlapping periods are rejected."""
    periods = [_eu_period_row(row) for row in rows]
    periods.sort(key=lambda p: p.valid_from)
    for before, after in zip(periods, periods[1:], strict=False):
        if after.valid_from <= before.valid_to:
            raise ProfileError("EU-Schwellenwertzeiträume überschneiden sich.")
    return periods


def _eu_period_row(row: ProfileData) -> ThresholdPeriod:
    """One period with official source, ordered dates and positive values."""
    source = row["source"]
    if not all(source.get(k) for k in ("regulation", "official_journal", "url")):
        raise ProfileError("EU-Schwellenwert ohne amtliche Fundstelle.")
    start, end = date.fromisoformat(row["valid_from"]), date.fromisoformat(row["valid_to"])
    if end < start:
        raise ProfileError("Gültigkeitszeitraum endet vor seinem Beginn.")
    values = {str(k): int(v) for k, v in row["values"].items()}
    if any(v <= 0 for v in values.values()):
        raise ProfileError("EU-Schwellenwerte müssen positiv sein.")
    return ThresholdPeriod(start, end, values, dict(source))


def _packaged_eu_block(version: str) -> dict[str, Any]:
    """EU table and national block of a packaged ``procurement.hvtg`` profile version."""
    name = f"{CURRENT_PROFILE[0]}-{version}.json"
    entry = resources.files("auditcore_procurement.profiles").joinpath(name)
    if "/" in name or "\\" in name or not entry.is_file():
        raise ProfileError(f"Profil {name[:-5]} ist nicht vorhanden.")
    data = json.loads(entry.read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMAS[1]:
        raise ProfileError(f"Profil {CURRENT_PROFILE[0]} {version} hat keine Jahrestabelle.")
    return {"eu_thresholds": data["eu_thresholds"], "national_tiers": data["national_tiers"]}


#: Newest packaged year-bound profile (2014–2027). 2026.09.2 (2024–2027) stays loadable.
CURRENT_PROFILE = ("procurement.hvtg", "2026.09.3")


def profile_from_ruleset(
    ruleset: ProfileData,
    *,
    profile_id: str,
    version: str,
    source: ProfileData,
    year_bound: bool = False,
    eu_version: str = CURRENT_PROFILE[1],
) -> PrecheckProfile:
    """Profile from an application ruleset with ``threshold_rules`` and
    ``required_documents_by_procedure`` (source format), so a consumer keeps its
    own rule authority. Tier order and values are taken over unchanged.

    ``year_bound=True`` adds the verified year-bound EU table of the packaged
    ``procurement.hvtg`` profile ``eu_version`` (default: ``CURRENT_PROFILE``,
    2026.09.3; pin ``"2026.09.2"`` to reproduce 0.1.0) for ``strict`` mode
    (schema 2); the ruleset's own ``BELOW_EU`` maxima are then used only by
    ``legacy`` mode."""
    try:
        tiers = {
            category: [
                {
                    "tier": name,
                    "max": rule.get("max"),
                    "procedure": rule.get("procedure", ""),
                    "min_bids": rule.get("min_bids", 1),
                }
                for name, rule in rules.items()
            ]
            for category, rules in ruleset["threshold_rules"].items()
        }
        required = ruleset["required_documents_by_procedure"]
    except (KeyError, AttributeError, TypeError) as exc:
        raise ProfileError(f"Regelwerk ohne threshold_rules/required_documents: {exc!r}") from exc
    extra = _packaged_eu_block(eu_version) if year_bound else {}
    return profile_from_dict(
        {
            "schema": f"auditcore_procurement.precheck-profile/{2 if year_bound else 1}",
            **extra,
            "id": profile_id,
            "version": version,
            "status": "CONSUMER_RULESET",
            "legal_status": "Regelwerk der Anwendung; nicht durch diese Bibliothek geprüft.",
            "source": dict(source),
            "construction_marker": "Bau",
            "tiers": tiers,
            "fallback_tier": "ABOVE_EU",
            "required_documents": {k: list(v) for k, v in required.items()},
            "bid_document_type": "ANGEBOT",
            "default_min_bids": 1,
            "value_deviation": {
                "warning_above_percent": 10,
                "fail_above_percent": 20,
                "fail_reference": "§ 132 GWB",
            },
        }
    )


def load_profile(profile_id: str, version: str) -> PrecheckProfile:
    """Load an explicitly named packaged profile version."""
    return load_packaged_profile(
        "auditcore_procurement.profiles",
        profile_id,
        version,
        parse=profile_from_dict,
        identity=lambda profile: (profile.id, profile.version),
        error=ProfileError,
        invalid_name="missing",
    )


def eu_period(profile: PrecheckProfile, on: date) -> ThresholdPeriod:
    """Verified period containing ``on``; no fallback to a neighbouring period.

    Raises:
        ThresholdUnavailable: the profile has no year-bound table or no period for ``on``.
    """
    if not profile.eu_periods:
        raise ThresholdUnavailable(
            f"Profil {profile.id} {profile.version} enthält keine jahresbezogenen "
            "EU-Schwellenwerte."
        )
    for period in profile.eu_periods:
        if period.valid_from <= on <= period.valid_to:
            return period
    raise ThresholdUnavailable(
        f"Für den {on.strftime('%d.%m.%Y')} ist im Profil {profile.id} {profile.version} "
        "kein belegter EU-Schwellenwert hinterlegt."
    )


def eu_period_for_year(profile: PrecheckProfile, year: int) -> ThresholdPeriod:
    """Period covering the whole calendar ``year``, else ``ThresholdUnavailable``."""
    period = eu_period(profile, date(year, 1, 1))
    if period.valid_to < date(year, 12, 31):
        raise ThresholdUnavailable(f"Das Jahr {year} liegt nicht vollständig in einem Zeitraum.")
    return period


def eu_threshold(
    profile: PrecheckProfile, category: str, period: ThresholdPeriod, authority_type: str
) -> EuThreshold:
    """Threshold of a category (``construction``/``supply_service``) and authority type."""
    if profile.eu_categories is None or category not in profile.eu_categories:
        raise ThresholdUnavailable(f"Keine EU-Schwellenwertzuordnung für '{category}'.")
    spec = profile.eu_categories[category]
    if isinstance(spec, Mapping):
        if authority_type not in AUTHORITY_TYPES:
            raise ValueError(f"authority_type muss eine von {AUTHORITY_TYPES} sein.")
        spec = spec[authority_type]
    key = str(spec)
    return EuThreshold(period.values[key], key, period)
