"""flowsearch replays: OpenSanctions payloads and answers, UBO and SME."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any, TypedDict

from . import opensanctions_api, ownership
from ._legacy_shared import _profile
from ._types import JsonObject

SANCTIONS_SOURCES = ["EU Sanctions", "UN Security Council", "OFAC", "UK Sanctions"]


def flowsearch_sanctions_payload(name: str, country: str = "DE") -> JsonObject:
    """Request body of ``SanctionsAPIClient.check_sanctions``."""
    return {
        "queries": {
            "entity1": {
                "schema": "LegalEntity",
                "properties": {"name": [name], "country": [country]},
            }
        }
    }


def flowsearch_check_sanctions(
    response: Mapping[str, Any] | None, *, error: str | None = None
) -> JsonObject:
    """``check_sanctions`` on a recorded answer; reads ``result.entity`` like the source."""
    if response is None:
        return {
            "found": False,
            "matches": [],
            "sources": ["OpenSanctions"],
            "checked_at": "",
            "status": f"Check failed: {error}",
            "error": error,
        }
    threshold = float(_profile("flowsearch.opensanctions_match").setting("local_threshold"))
    matches = []
    for result in response.get("responses", {}).get("entity1", {}).get("results", []):
        score = result.get("score", 0.0)
        if score < threshold:
            continue
        entity = result.get("entity", {})
        properties = entity.get("properties", {})
        topics = properties.get("topics", [])
        if any("sanction" in topic.lower() for topic in topics):
            matches.append(
                {
                    "name": properties.get("name", ["Unknown"])[0],
                    "score": score,
                    "reason": ", ".join(properties.get("reason", ["No reason provided"])),
                    "source": ", ".join(entity.get("datasets", ["Unknown"])),
                    "date": properties.get("listingDate", [""])[0]
                    or properties.get("modifiedAt", [""])[0],
                    "topics": topics,
                }
            )
    return {
        "found": len(matches) > 0,
        "matches": matches,
        "sources": list(SANCTIONS_SOURCES),
        "checked_at": "<zeitabhängig>",
        "status": f"{len(matches)} sanctions found" if matches else "No sanctions found",
    }


def flowsearch_pep_payload(
    name: str, date_of_birth: str | None = None, nationality: str | None = None
) -> dict[str, Any]:
    """Request body of ``PEPScreeningAPIClient.check_person``."""
    properties: dict[str, list[str]] = {"name": [name]}
    if date_of_birth:
        properties["birthDate"] = [date_of_birth]
    if nationality:
        properties["nationality"] = [nationality]
    return {"queries": {"entity1": {"schema": "Person", "properties": properties}}}


def flowsearch_pep_authorization(api_key: str | None) -> str | None:
    """Authorization header of the source (``Bearer``; the API expects ``ApiKey``)."""
    return f"Bearer {api_key}" if api_key else None


def flowsearch_check_person(
    response: Mapping[str, Any] | None, *, name: str, error: str | None = None
) -> JsonObject:
    """``check_person`` on a recorded answer; reads ``result.entity`` like the source."""
    if response is None:
        return {
            "is_pep": False,
            "pep_category": "None",
            "match_count": 0,
            "matches": [],
            "risk_level": "none",
            "error": error,
            "note": "PEP check failed",
        }
    profile = _profile("flowsearch.pep_risk")
    labels = profile.setting("labels")
    threshold = float(profile.setting("local_threshold"))
    order = ["none", "low", "medium", "high"]
    matches, is_pep, highest = [], False, "none"
    for result in response.get("responses", {}).get("entity1", {}).get("results", []):
        score = result.get("score", 0.0)
        if score < threshold:
            continue
        entity = result.get("entity", {})
        properties = entity.get("properties", {})
        topics = properties.get("topics", [])
        if any(t in ["role.pep", "role.rca"] for t in topics):
            is_pep = True
        found = opensanctions_api.positions(properties)
        kind = opensanctions_api.pep_type(topics, found, labels)
        risk = opensanctions_api.pep_risk(kind, score, found, profile)
        if order.index(risk) > order.index(highest):
            highest = risk
        matches.append(
            {
                "name": properties.get("name", [""])[0],
                "match_score": score,
                "pep_type": kind,
                "positions": found,
                "date_of_birth": properties.get("birthDate", [""])[0],
                "nationality": properties.get("nationality", [""])[0],
                "source": entity.get("datasets", [""])[0],
                "last_updated": entity.get("last_seen"),
            }
        )
    return {
        "is_pep": is_pep,
        "pep_category": opensanctions_api.pep_category([m["pep_type"] for m in matches])
        if is_pep
        else "None",
        "match_count": len(matches),
        "matches": matches,
        "risk_level": highest,
        "checked_name": name,
        "source": "OpenSanctions",
    }


def flowsearch_assess_risk(
    pep_type: str, score: float, positions: Sequence[Mapping[str, object]]
) -> str:
    """``PEPScreeningAPIClient._assess_risk``."""
    return opensanctions_api.pep_risk(pep_type, score, positions, _profile("flowsearch.pep_risk"))


def flowsearch_pep_type(topics: Sequence[str], positions: Sequence[Mapping[str, object]]) -> str:
    """``_determine_pep_type``."""
    labels = _profile("flowsearch.pep_risk").setting("labels")
    return opensanctions_api.pep_type(topics, positions, labels)


def flowsearch_pep_category(matches: Sequence[Mapping[str, Any]]) -> str:
    """``_categorize_pep``."""
    return opensanctions_api.pep_category([m["pep_type"] for m in matches])


def flowsearch_openregister_error(error: str) -> JsonObject:
    """``OpenRegisterAPIClient.search_company`` after a failed request (endpoint answers 404)."""
    return {"found": False, "results": [], "error": error, "note": "OpenRegister API error"}


def flowsearch_handelsregister_search(name: str, location: str | None = None) -> JsonObject:
    """``HandelsregisterAPIClient.search_company``: a stub without any request."""
    return {
        "found": False,
        "results": [],
        "query": {"company_name": name, "location": location},
        "note": "API key required for full data",
    }


_COMPANY_INDICATORS = (
    "gmbh",
    "ag",
    "kg",
    "ohg",
    "gbr",
    "e.v.",
    "ev",
    "limited",
    "ltd",
    "inc",
    "corporation",
    "corp",
)


def flowsearch_entity_type(name: str) -> str:
    """``_determine_entity_type``: substring test (``Agnes`` counts as company)."""
    lower = name.lower()
    return "company" if any(i in lower for i in _COMPANY_INDICATORS) else "person"


def flowsearch_share(officer: Mapping[str, Any]) -> float:
    """``_extract_share_percentage``."""
    if "shares" in officer:
        return float(officer["shares"])
    found = re.search(r"(\d+(?:\.\d+)?)\s*%", officer.get("position", ""))
    return float(found.group(1)) if found else 0.0


class UboView(TypedDict):
    """Traversal, UBOs, chains and network graph of ``UBOEngine``."""

    nodes: list[ownership.OwnershipNode]
    ubos: list[ownership.OwnershipNode]
    chain: list[list[ownership.OwnershipNode]] | None
    self_loops: list[str]
    graph: dict[str, list[JsonObject]]


def flowsearch_ubo(structure: Mapping[str, Any]) -> UboView:
    """Traversal, UBOs, chains (acyclic graphs only) and network graph of ``UBOEngine``."""
    profile = _profile("flowsearch.ubo")
    graph = ownership.traverse(structure, profile)
    loops = graph.self_references
    return {
        "nodes": graph.nodes,
        "ubos": ownership.beneficial_owners(graph.nodes, profile),
        "chain": None
        if loops
        else [list(ownership.ownership_chain(graph, n.id).nodes) for n in graph.nodes],
        "self_loops": loops,
        "graph": ownership.network(graph),
    }


def flowsearch_kmu(company_data: Mapping[str, Any]) -> JsonObject:
    """``calculate_kmu_status``."""
    result = ownership.sme_status(company_data, _profile("flowsearch.kmu"))
    return {
        "is_kmu": result.is_sme,
        "category": result.category,
        "employees_total": result.employees,
        "revenue_total": result.turnover,
        "balance_sheet_total": result.balance_sheet,
        "note": "Aggregation with linked/partner enterprises pending",
    }
