"""Interpretation of match answers: sanctions topics, PEP type and risk (flowsearch profiles)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, TypedDict, cast

from ._opensanctions_match import Candidate, MatchResponse
from ._types import JsonObject, JsonValue
from .profiles import RegistryProfile


class Position(TypedDict):
    """A position as flowsearch builds it from an entity's properties."""

    title: str
    organization: str
    country: str
    from_date: str
    to_date: str
    is_current: bool


def _position_view(position: Mapping[str, object]) -> JsonObject:
    """Copy of a position; its values are the JSON values :func:`positions` produced."""
    return cast(JsonObject, dict(position))


@dataclass(frozen=True)
class SanctionsAssessment:
    """Sanctions reading of a match answer under ``flowsearch.opensanctions_match``."""

    found: bool
    matches: tuple[Candidate, ...]
    below_threshold: int
    without_sanction_topic: int
    api_match_disagrees: tuple[str, ...]
    profile: Mapping[str, str]
    notice: str = "Ein Treffer ist ein Prüfhinweis, keine Feststellung."

    def to_dict(self) -> JsonObject:
        """JSON view."""
        return {
            "found": self.found,
            "matches": [m.to_dict() for m in self.matches],
            "below_threshold": self.below_threshold,
            "without_sanction_topic": self.without_sanction_topic,
            "api_match_disagrees": list(self.api_match_disagrees),
            "profile": dict(self.profile),
            "notice": self.notice,
        }


def assess_sanctions(answer: MatchResponse, profile: RegistryProfile) -> SanctionsAssessment:
    """Candidates at or above the local threshold with a topic containing ``sanction``."""
    profile.require_kind("match_api")
    threshold = float(profile.setting("local_threshold"))
    needle = str(profile.setting("sanctions_topic_substring"))
    matches, below, no_topic, disagree = [], 0, 0, []
    for candidate in answer.candidates:
        if candidate.score < threshold:
            below += 1
            continue
        if not any(needle in t.lower() for t in candidate.topics):
            no_topic += 1
            continue
        matches.append(candidate)
        if candidate.api_match is False:
            disagree.append(candidate.id)
    return SanctionsAssessment(
        found=bool(matches),
        matches=tuple(matches),
        below_threshold=below,
        without_sanction_topic=no_topic,
        api_match_disagrees=tuple(disagree),
        profile=profile.reference,
    )


@dataclass(frozen=True)
class PepMatch:
    """A PEP candidate with type and risk under ``flowsearch.pep_risk``."""

    candidate: Candidate
    pep_type: str
    risk: str
    positions: tuple[Mapping[str, object], ...]

    def to_dict(self) -> JsonObject:
        """JSON view."""
        return {
            "candidate": self.candidate.to_dict(),
            "pep_type": self.pep_type,
            "risk": self.risk,
            "positions": [_position_view(p) for p in self.positions],
        }


@dataclass(frozen=True)
class PepAssessment:
    """PEP reading of a match answer; ``risk_level`` is the highest single risk."""

    is_pep: bool
    category: str
    risk_level: str
    matches: tuple[PepMatch, ...]
    profile: Mapping[str, str]
    decisions: tuple[Mapping[str, JsonValue], ...] = field(default_factory=tuple)

    def to_dict(self) -> JsonObject:
        """JSON view."""
        return {
            "is_pep": self.is_pep,
            "category": self.category,
            "risk_level": self.risk_level,
            "matches": [m.to_dict() for m in self.matches],
            "profile": dict(self.profile),
            "decisions": [dict(d) for d in self.decisions],
        }


def positions(properties: Mapping[str, Any]) -> list[Position]:
    """Positions as flowsearch builds them (first organisation/country/start/end per entity)."""

    def first(name: str) -> str:
        """First value of a property or ``""``."""
        values = properties.get(name) or [""]
        return str(values[0])

    return [
        {
            "title": title,
            "organization": first("organization"),
            "country": first("country"),
            "from_date": first("startDate"),
            "to_date": first("endDate"),
            "is_current": not properties.get("endDate"),
        }
        for title in properties.get("position", [])
    ]


def pep_type(
    topics: Sequence[str],
    found_positions: Sequence[Mapping[str, object]],
    labels: Mapping[str, str],
) -> str:
    """Active/former PEP, RCA or unknown from topics and positions."""
    if "role.pep" in topics:
        current = any(p["is_current"] for p in found_positions)
        return labels["active"] if current else labels["former"]
    if "role.rca" in topics:
        return labels["rca"]
    return labels["unknown"]


def pep_risk(
    type_label: str,
    score: float,
    found_positions: Sequence[Mapping[str, object]],
    profile: RegistryProfile,
) -> str:
    """Risk rules of ``_assess_risk`` (see the profile's decision)."""
    if "aktiv" in type_label and score > float(profile.setting("active_high_above")):
        return "high"
    keywords = profile.setting("senior_keywords")
    senior = any(
        any(k in str(p["title"]).lower() for k in keywords)
        for p in found_positions
        if p.get("title")
    )
    if senior and score > float(profile.setting("senior_high_above")):
        return "high"
    low, high = profile.setting("medium_band")
    if "Former" in type_label or (float(low) <= score < float(high)):
        return "medium"
    if "RCA" in type_label or score < float(profile.setting("low_below")):
        return "low"
    return "none"


def pep_category(types: Sequence[str]) -> str:
    """Highest PEP status of the matches."""
    if any("aktiv" in t for t in types):
        return "PEP (aktiv)"
    if any("Former" in t for t in types):
        return "Former PEP"
    if any("RCA" in t for t in types):
        return "RCA"
    return "None"


def assess_pep(answer: MatchResponse, profile: RegistryProfile) -> PepAssessment:
    """PEP type and risk of every candidate at or above the local threshold."""
    profile.require_kind("match_api")
    threshold = float(profile.setting("local_threshold"))
    labels = profile.setting("labels")
    order = ["none", "low", "medium", "high"]
    highest = "none"
    matches = []
    is_pep = False
    for candidate in answer.candidates:
        if candidate.score < threshold:
            continue
        found = positions(candidate.properties)
        if any(t in ("role.pep", "role.rca") for t in candidate.topics):
            is_pep = True
        type_label = pep_type(candidate.topics, found, labels)
        risk = pep_risk(type_label, candidate.score, found, profile)
        if order.index(risk) > order.index(highest):
            highest = risk
        matches.append(PepMatch(candidate, type_label, risk, tuple(found)))
    return PepAssessment(
        is_pep=is_pep,
        category=pep_category([m.pep_type for m in matches]) if is_pep else "None",
        risk_level=highest,
        matches=tuple(matches),
        profile=profile.reference,
        decisions=profile.decisions,
    )
