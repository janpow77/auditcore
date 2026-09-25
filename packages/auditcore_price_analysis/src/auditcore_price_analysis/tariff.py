"""Tariffs (price records) with explicit validity, release status and tiers.

Missing components stay ``None``; an explicit ``0`` means "not charged".
The library never changes a release status: it only reads what the consumer
(its review/four-eyes process) recorded.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Any

from .errors import PriceAnalysisError
from .numbers import non_negative, optional_non_negative, parse_day
from .profiles import CalculationProfile, TierRule


class ReleaseStatus(StrEnum):
    """Release status of a price record as recorded by the consumer."""

    FREIGEGEBEN = "freigegeben"
    AUSSTEHEND = "ausstehend"
    ABGELEHNT = "abgelehnt"
    UNBEKANNT = "unbekannt"

    @classmethod
    def from_legacy(cls, value: str | None) -> ReleaseStatus:
        """Map regulierung's ``freigabe_status`` (approved/pending/rejected)."""
        return {
            "approved": cls.FREIGEGEBEN,
            "pending": cls.AUSSTEHEND,
            "rejected": cls.ABGELEHNT,
        }.get(str(value), cls.UNBEKANNT)


@dataclass(frozen=True)
class Tier:
    """One tier: price applies up to ``limit`` (``None`` = open-ended last tier)."""

    limit: Decimal | None
    price: Decimal

    def to_dict(self) -> dict[str, str | None]:
        """JSON view."""
        return {"limit": None if self.limit is None else str(self.limit), "price": str(self.price)}


def _tier_items(raw: object, rule: TierRule) -> Sequence[object]:
    """The tier list, unwrapped from the optional wrapper object."""
    if isinstance(raw, Mapping):
        if rule.wrapper_key is None or set(raw) != {rule.wrapper_key}:
            raise PriceAnalysisError(
                "invalid_tiers",
                f"{rule.field}: Objektform nur mit genau dem Schlüssel {rule.wrapper_key!r}.",
                field=rule.field,
            )
        raw = raw[rule.wrapper_key]
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise PriceAnalysisError(
            "invalid_tiers", f"{rule.field} muss eine Liste von Stufen sein.", field=rule.field
        )
    return raw


def _tier(index: int, item: object, rule: TierRule) -> Tier:
    where = f"{rule.field}[{index}]"
    if not isinstance(item, Mapping):
        raise PriceAnalysisError("invalid_tiers", f"{where} muss ein Objekt sein.", field=where)
    price = non_negative(item.get(rule.price_key), field=f"{where}.{rule.price_key}")
    limit = optional_non_negative(item.get(rule.limit_key), field=f"{where}.{rule.limit_key}")
    if limit is not None and limit <= 0:
        raise PriceAnalysisError(
            "invalid_tiers", f"{where}.{rule.limit_key} muss größer als 0 sein.", field=where
        )
    return Tier(limit, price)


def _ordered_tiers(tiers: list[Tier], rule: TierRule) -> tuple[Tier, ...]:
    """Bounded tiers by limit, then the open last tier; open/duplicate limits are errors."""
    open_tiers = [t for t in tiers if t.limit is None]
    if len(open_tiers) > 1 or (open_tiers and not rule.open_last):
        raise PriceAnalysisError(
            "invalid_tiers",
            f"{rule.field}: nur die letzte Stufe darf offen sein.",
            field=rule.field,
        )
    bounded = sorted((t for t in tiers if t.limit is not None), key=lambda t: t.limit or 0)
    if len({t.limit for t in bounded}) != len(bounded):
        raise PriceAnalysisError(
            "invalid_tiers", f"{rule.field}: Stufengrenzen müssen eindeutig sein.", field=rule.field
        )
    return tuple(bounded + open_tiers)


def parse_tiers(raw: object, rule: TierRule) -> tuple[Tier, ...] | None:
    """Validate tiers; ``None`` or an empty list means "no tiers".

    Accepted: a list of objects, or an object with exactly the wrapper key.
    Unknown shapes, a missing tier price, a non-positive or duplicate limit and
    an open limit before the last tier are errors, never silently ignored.
    Additional keys inside a tier are reported by :func:`ignored_tier_keys`.
    """
    if raw is None:
        return None
    items = _tier_items(raw, rule)
    if not items:
        return None
    return _ordered_tiers([_tier(i, item, rule) for i, item in enumerate(items, start=1)], rule)


def ignored_tier_keys(raw: object, rule: TierRule) -> list[str]:
    """Keys inside tiers that the calculation does not use (reported, not dropped silently)."""
    if isinstance(raw, Mapping) and rule.wrapper_key is not None:
        raw = raw.get(rule.wrapper_key)
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return []
    keys: set[str] = set()
    for item in raw:
        if isinstance(item, Mapping):
            keys |= {str(k) for k in item} - {rule.limit_key, rule.price_key}
    return sorted(keys)


@dataclass(frozen=True)
class Tariff:
    """One price record of a provider for one kind (``nahwaerme``/``wasser``)."""

    kind: str
    components: Mapping[str, Decimal | None]
    tiers: tuple[Tier, ...] | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    release: ReleaseStatus = ReleaseStatus.UNBEKANNT
    q3: Decimal | None = None
    variant_id: int | None = None
    row_id: int | None = None
    standard_variant: bool = False
    source_ref: str | None = None
    extra: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(
        cls,
        data: Mapping[str, object],
        profile: CalculationProfile,
        *,
        valid_from: object = None,
        valid_to: object = None,
        release: ReleaseStatus | str = ReleaseStatus.UNBEKANNT,
        q3: object = None,
        **identity: Any,
    ) -> Tariff:
        """Build from the legacy ``preisdaten`` mapping; unknown keys are rejected.

        ``identity`` may name ``variant_id``, ``row_id``, ``standard_variant``
        and ``source_ref`` (selection and traceability only).
        """
        unexpected = set(identity) - {"variant_id", "row_id", "standard_variant", "source_ref"}
        if unexpected:
            raise TypeError(f"Unbekannte Angaben {sorted(unexpected)}")
        allowed = {c.name for c in profile.components}
        if profile.tiers is not None:
            allowed.add(profile.tiers.field)
        unknown = set(data) - allowed
        if unknown:
            raise PriceAnalysisError(
                "unknown_component",
                f"Unbekannte Preisbestandteile für {profile.profile_id}: {sorted(unknown)}.",
            )
        components = {
            c.name: optional_non_negative(data.get(c.name), field=c.name)
            for c in profile.components
        }
        tiers = None
        extra: dict[str, object] = {}
        if profile.tiers is not None:
            tiers = parse_tiers(data.get(profile.tiers.field), profile.tiers)
            ignored = ignored_tier_keys(data.get(profile.tiers.field), profile.tiers)
            if ignored:
                extra["ignored_tier_keys"] = ignored
        return cls(
            kind=profile.kind,
            components=components,
            tiers=tiers,
            valid_from=None if valid_from is None else parse_day(valid_from, field="valid_from"),
            valid_to=None if valid_to is None else parse_day(valid_to, field="valid_to"),
            release=release if isinstance(release, ReleaseStatus) else ReleaseStatus(release),
            q3=optional_non_negative(q3, field="q3"),
            variant_id=identity.get("variant_id"),
            row_id=identity.get("row_id"),
            standard_variant=bool(identity.get("standard_variant", False)),
            source_ref=identity.get("source_ref"),
            extra=extra,
        )

    def to_dict(self) -> dict[str, Any]:
        """JSON view."""
        return {
            "kind": self.kind,
            "components": {k: None if v is None else str(v) for k, v in self.components.items()},
            "tiers": None if self.tiers is None else [t.to_dict() for t in self.tiers],
            "valid_from": None if self.valid_from is None else self.valid_from.isoformat(),
            "valid_to": None if self.valid_to is None else self.valid_to.isoformat(),
            "release": self.release.value,
            "q3": None if self.q3 is None else str(self.q3),
            "variant_id": self.variant_id,
            "row_id": self.row_id,
            "standard_variant": self.standard_variant,
            "source_ref": self.source_ref,
        }
