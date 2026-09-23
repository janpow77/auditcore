"""OpenSanctions matching API (``/match/{dataset}``) for sanctions and PEP checks.

Source: flowsearch ``SanctionsAPIClient`` and ``PEPScreeningAPIClient``.
Verified on 2026-09-23 against the published OpenAPI description (yente
5.5.0): the API requires a key in ``Authorization: ApiKey …`` and answers
``responses.<query>.results[]`` with entities that carry ``score``,
``properties.topics`` and ``datasets`` directly — there is no ``entity``
wrapper. flowsearch sends no key (sanctions) or ``Bearer`` (PEP) and reads
``result.entity``; with the documented response it never finds anything.

This module builds requests, calls the API through an injected
``auditcore_harvest`` transport and interprets responses under the
explicit profiles ``flowsearch.opensanctions_match`` and ``flowsearch.pep_risk``.
Errors are raised (``AuthError``, ``RateLimitError``, ``TransportError``,
``ParserError``); a failed check is never reported as "no hit".
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from auditcore_harvest import (
    AuthError,
    CredentialProvider,
    ParserError,
    Transport,
    raise_for_status,
)

from .profiles import RegistryProfile

SOURCE_ID = "registry.opensanctions_match"
BASE_URL = "https://api.opensanctions.org"
#: Environment variable a consumer may use for its own key (decision A3, 23.09.2026).
ENV_VAR = "OPENSANCTIONS_API_KEY"
#: Where an operator obtains a key (free for academia, non-profits and journalism).
KEY_INFO_URL = "https://www.opensanctions.org/api/"
NOT_CONFIGURED = (
    "NOT_CONFIGURED: kein OpenSanctions-API-Schlüssel. Jeder Betreiber beschafft einen "
    f"eigenen Schlüssel ({KEY_INFO_URL}) und übergibt ihn als Parameter api_key oder über "
    f"die Umgebungsvariable {ENV_VAR} (credentials_from_environment)."
)


@dataclass(frozen=True)
class KeyCredentials:
    """Credential provider holding one operator key for the matching API."""

    api_key: str | None

    def get(self, source_id: str, name: str) -> str | None:
        """The key for this source, else ``None``."""
        if source_id == SOURCE_ID and name == "api_key" and self.api_key:
            return self.api_key
        return None


def credentials_from_environment(environ: Mapping[str, str]) -> KeyCredentials:
    """Key from ``environ[ENV_VAR]`` (pass ``os.environ``); empty values count as missing."""
    value = (environ.get(ENV_VAR) or "").strip()
    return KeyCredentials(value or None)


def configuration_status(credentials: CredentialProvider) -> str:
    """``CONFIGURED`` or ``NOT_CONFIGURED`` without revealing the key."""
    return "CONFIGURED" if credentials.get(SOURCE_ID, "api_key") else "NOT_CONFIGURED"


@dataclass(frozen=True)
class MatchQuery:
    """One entity example of a match request."""

    schema: str
    properties: Mapping[str, Sequence[str]]

    def to_dict(self) -> dict[str, Any]:
        """JSON view of the query."""
        return {
            "schema": self.schema,
            "properties": {k: list(v) for k, v in self.properties.items() if v},
        }


def sanctions_query(name: str, country: str | None) -> MatchQuery:
    """flowsearch sanctions request: ``LegalEntity`` with name and country."""
    properties: dict[str, list[str]] = {"name": [name]}
    if country:
        properties["country"] = [country]
    return MatchQuery("LegalEntity", properties)


def person_query(
    name: str, *, birth_date: str | None = None, nationality: str | None = None
) -> MatchQuery:
    """flowsearch PEP request: ``Person`` with optional birth date and nationality."""
    properties: dict[str, list[str]] = {"name": [name]}
    if birth_date:
        properties["birthDate"] = [birth_date]
    if nationality:
        properties["nationality"] = [nationality]
    return MatchQuery("Person", properties)


def build_request(queries: Mapping[str, MatchQuery]) -> bytes:
    """JSON body ``{"queries": {...}}``."""
    if not queries:
        raise ValueError("Mindestens eine Abfrage ist nötig.")
    body = {"queries": {key: q.to_dict() for key, q in queries.items()}}
    return json.dumps(body, ensure_ascii=False).encode("utf-8")


@dataclass(frozen=True)
class Candidate:
    """A scored entity of the API answer."""

    id: str
    caption: str
    schema: str
    score: float
    api_match: bool | None
    datasets: tuple[str, ...]
    topics: tuple[str, ...]
    properties: Mapping[str, Any]
    first_seen: str | None
    last_seen: str | None
    last_change: str | None

    def first(self, prop: str) -> str:
        """First value of a property or ``""``."""
        values = self.properties.get(prop) or []
        return str(values[0]) if values else ""

    def to_dict(self) -> dict[str, Any]:
        """JSON view."""
        return {
            "id": self.id,
            "caption": self.caption,
            "schema": self.schema,
            "score": self.score,
            "api_match": self.api_match,
            "datasets": list(self.datasets),
            "topics": list(self.topics),
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "last_change": self.last_change,
        }


@dataclass(frozen=True)
class MatchResponse:
    """Answer to one query of a match request."""

    query_key: str
    status: int
    total: int | None
    candidates: tuple[Candidate, ...]


def parse_response(body: bytes) -> dict[str, MatchResponse]:
    """Interpret a ``/match`` answer; missing required parts are parser errors."""
    try:
        data = json.loads(body)
        responses = data["responses"]
        if not isinstance(responses, dict):
            raise TypeError("responses")
        result = {}
        for key, answer in responses.items():
            candidates = []
            for item in answer["results"]:
                props = item.get("properties") or {}
                candidates.append(
                    Candidate(
                        id=str(item["id"]),
                        caption=str(item.get("caption", "")),
                        schema=str(item.get("schema", "")),
                        score=float(item["score"]),
                        api_match=item.get("match"),
                        datasets=tuple(item.get("datasets") or ()),
                        topics=tuple(props.get("topics") or ()),
                        properties=props,
                        first_seen=item.get("first_seen"),
                        last_seen=item.get("last_seen"),
                        last_change=item.get("last_change"),
                    )
                )
            total = answer.get("total") or {}
            result[key] = MatchResponse(
                query_key=key,
                status=int(answer.get("status", 200)),
                total=int(total["value"]) if "value" in total else None,
                candidates=tuple(candidates),
            )
        return result
    except (ValueError, KeyError, TypeError) as exc:
        raise ParserError(f"Antwort der Abgleichs-API nicht lesbar: {exc!r}") from exc


class MatchClient:
    """Calls ``/match/{dataset}`` through an injected transport; the key comes from credentials."""

    def __init__(
        self,
        transport: Transport,
        credentials: CredentialProvider | None = None,
        *,
        api_key: str | None = None,
        base_url: str = BASE_URL,
        timeout: float = 30.0,
    ) -> None:
        self.transport = transport
        self.credentials = credentials if credentials is not None else KeyCredentials(api_key)
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @property
    def status(self) -> str:
        """``CONFIGURED`` or ``NOT_CONFIGURED``."""
        return configuration_status(self.credentials)

    def match(
        self,
        queries: Mapping[str, MatchQuery],
        *,
        dataset: str = "default",
        threshold: float | None = None,
        limit: int | None = None,
    ) -> dict[str, MatchResponse]:
        """Send one request; raises harvest errors instead of returning empty results."""
        key = self.credentials.get(SOURCE_ID, "api_key")
        if not key:
            raise AuthError(NOT_CONFIGURED)
        params: dict[str, str] = {}
        if threshold is not None:
            params["threshold"] = str(threshold)
        if limit is not None:
            params["limit"] = str(limit)
        response = self.transport.request(
            "POST",
            f"{self.base_url}/match/{dataset}",
            params=params or None,
            headers={"Authorization": f"ApiKey {key}", "Content-Type": "application/json"},
            data=build_request(queries),
            timeout=self.timeout,
        )
        raise_for_status(response)
        return parse_response(response.body)


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

    def to_dict(self) -> dict[str, Any]:
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
    positions: tuple[Mapping[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        """JSON view."""
        return {
            "candidate": self.candidate.to_dict(),
            "pep_type": self.pep_type,
            "risk": self.risk,
            "positions": [dict(p) for p in self.positions],
        }


@dataclass(frozen=True)
class PepAssessment:
    """PEP reading of a match answer; ``risk_level`` is the highest single risk."""

    is_pep: bool
    category: str
    risk_level: str
    matches: tuple[PepMatch, ...]
    profile: Mapping[str, str]
    decisions: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """JSON view."""
        return {
            "is_pep": self.is_pep,
            "category": self.category,
            "risk_level": self.risk_level,
            "matches": [m.to_dict() for m in self.matches],
            "profile": dict(self.profile),
            "decisions": [dict(d) for d in self.decisions],
        }


def positions(properties: Mapping[str, Any]) -> list[dict[str, Any]]:
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
    topics: Sequence[str], found_positions: Sequence[Mapping[str, Any]], labels: Mapping[str, str]
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
    found_positions: Sequence[Mapping[str, Any]],
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
