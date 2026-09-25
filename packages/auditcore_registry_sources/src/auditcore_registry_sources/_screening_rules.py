"""Screening settings of a profile and the date-of-birth/country score adjustment."""

from __future__ import annotations

import re
from dataclasses import dataclass

from auditcore_entity_matching import Profile as NormalizationProfile
from auditcore_entity_matching import load_profile as load_normalization
from auditcore_entity_matching import normalize

from ._types import JsonObject
from .errors import ProfileError
from .profiles import RegistryProfile

_MULTI = re.compile(r"[;,]")
_YEAR = re.compile(r"\b(\d{4})\b")


@dataclass(frozen=True)
class LimitRule:
    """``max(value, floor) * factor`` (``floor`` ``None``: ``value * factor``)."""

    floor: int | None
    factor: int

    def apply(self, value: int) -> int:
        """Apply the rule."""
        base = value if self.floor is None else max(value, self.floor)
        return base * self.factor


@dataclass(frozen=True)
class ScreeningSettings:
    """Typed view of a ``screening`` profile using the rapidfuzz method."""

    profile: RegistryProfile
    normalization: NormalizationProfile
    default_min_score: float
    min_score_range: tuple[float, float]
    min_query_length: int
    per_list_limit: LimitRule
    extract_limit: LimitRule
    alias_output_cap: int
    dob_bonus: float
    dob_malus: float
    country_bonus: float
    country_malus: float
    score_range: tuple[float, float]
    entity_schemas: tuple[str, ...]
    notice: str
    limitations: tuple[str, ...]

    @classmethod
    def from_profile(cls, profile: RegistryProfile) -> ScreeningSettings:
        """Validate and type a screening profile; nothing is defaulted."""
        profile.require_kind("screening")
        if profile.setting("algorithm") != "rapidfuzz_token_set":
            raise ProfileError(f"Profil {profile.id} nutzt nicht den rapidfuzz-Abgleich.")
        ref = profile.setting("normalization")
        normalization = load_normalization(ref["id"], ref["version"])
        if normalization.classification is None:
            raise ProfileError("Das Normalisierungsprofil enthält keine Klassengrenzen.")
        low, high = profile.setting("min_score_range")
        dob = profile.setting("date_of_birth")
        if dob["compare"] != "year":
            raise ProfileError("Nur der Jahresabgleich des Geburtsdatums ist charakterisiert.")
        country = profile.setting("country")
        per_list = profile.setting("per_list_limit")
        extract = profile.setting("extract_limit")
        score_low, score_high = profile.setting("score_range")
        return cls(
            profile=profile,
            normalization=normalization,
            default_min_score=float(profile.setting("default_min_score")),
            min_score_range=(float(low), float(high)),
            min_query_length=int(profile.setting("min_query_length")),
            per_list_limit=LimitRule(per_list["floor"], int(per_list["factor"])),
            extract_limit=LimitRule(extract["floor"], int(extract["factor"])),
            alias_output_cap=int(profile.setting("alias_output_cap")),
            dob_bonus=float(dob["bonus"]),
            dob_malus=float(dob["malus"]),
            country_bonus=float(country["bonus"]),
            country_malus=float(country["malus"]),
            score_range=(float(score_low), float(score_high)),
            entity_schemas=tuple(profile.setting("entity_schemas")),
            notice=str(profile.setting("notice")),
            limitations=tuple(profile.setting("limitations")),
        )

    def norm(self, text: str | None) -> str:
        """Comparison form under the profile's normalisation."""
        return normalize(text, self.normalization)


def split_multivalue(raw: str | None) -> list[str]:
    """Multi-valued list field (separators ``;`` and ``,``) → stripped parts."""
    if not raw:
        return []
    return [part.strip() for part in _MULTI.split(raw) if part.strip()]


def birth_years(raw: str | None) -> set[str]:
    """Four-digit years of a birth date field; only the year is compared."""
    years = set()
    for part in split_multivalue(raw):
        found = _YEAR.search(part)
        if found:
            years.add(found.group(1))
    return years


@dataclass(frozen=True)
class Adjustment:
    """One deterministic change of the raw score, with its reason."""

    kind: str
    points: float
    reason: str

    def to_dict(self) -> JsonObject:
        """JSON view."""
        return {"kind": self.kind, "points": self.points, "reason": self.reason}


def adjust_score(
    score: float,
    settings: ScreeningSettings,
    *,
    entry_birth_date: str,
    entry_countries: str,
    birth_date: str | None,
    country: str | None,
) -> tuple[float, bool, bool, tuple[Adjustment, ...]]:
    """Date-of-birth/country bonus and malus; returns score, conflicts and adjustments.

    Only applied when both sides state a value; the score stays within the
    profile's score range.
    """
    dob_conflict = country_conflict = False
    adjustments: list[Adjustment] = []
    if birth_date:
        asked, listed = birth_years(birth_date), birth_years(entry_birth_date)
        if asked and listed:
            if asked & listed:
                score += settings.dob_bonus
                adjustments.append(
                    Adjustment("date_of_birth", settings.dob_bonus, "Geburtsjahr stimmt überein.")
                )
            else:
                score -= settings.dob_malus
                dob_conflict = True
                adjustments.append(
                    Adjustment(
                        "date_of_birth",
                        -settings.dob_malus,
                        "Geburtsjahr widerspricht dem Eintrag.",
                    )
                )
    if country:
        asked_c = {n for part in split_multivalue(country) if (n := settings.norm(part))}
        listed_c = {n for part in split_multivalue(entry_countries) if (n := settings.norm(part))}
        if asked_c and listed_c:
            if asked_c & listed_c:
                score += settings.country_bonus
                adjustments.append(
                    Adjustment("country", settings.country_bonus, "Land stimmt überein.")
                )
            else:
                score -= settings.country_malus
                country_conflict = True
                adjustments.append(
                    Adjustment("country", -settings.country_malus, "Land widerspricht dem Eintrag.")
                )
    low, high = settings.score_range
    return max(low, min(high, score)), dob_conflict, country_conflict, tuple(adjustments)
