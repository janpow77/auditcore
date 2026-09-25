"""flowinvoice replays: local and network sanctions checks, PEP bulk check."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, TypedDict

from auditcore_entity_matching import legacy as matching_legacy

from ._legacy_shared import _profile
from ._legacy_types import PepEntry
from .bulk_screening import difflib_score, pep_score


def flowinvoice_to_list(value: object) -> list[str] | None:
    """``SanctionsDownloader._to_list``."""
    if value is None:
        return None
    if isinstance(value, list):
        result = [str(v).strip() for v in value if v]
        return result or None
    if isinstance(value, str):
        items = [v.strip() for v in value.split(",") if v.strip()]
        return items or None
    return None


@dataclass
class LocalEntity:
    """What ``check_entity_local`` reads of a ``sanctioned_entities`` row."""

    name: str
    aliases: list[str]
    list_type: str
    entity_type: str | None
    sanction_programs: list[str]
    vat_ids: list[str]


@dataclass
class SanctionMatch:
    """flowinvoice ``SanctionMatch`` (field order as in the source)."""

    list_name: str
    entity_name: str
    match_score: float
    entity_type: str = "entity"
    sanctions_programs: list[str] = field(default_factory=list)
    identifiers: dict[str, Any] = field(default_factory=dict)
    supplier_name: str = ""
    match_method: str = ""
    sanctioned_name_on_list: str = ""


class LocalCheck(TypedDict):
    """``SanctionsChecker.check_entity_local`` result without its timestamp."""

    is_sanctioned: bool
    matches: list[SanctionMatch]
    lists_checked: list[str]
    query_name: str
    query_country: None
    error_message: None
    lists_info: list[str]


def flowinvoice_check_entity_local(
    name: str, entities: Sequence[LocalEntity], *, min_score: float = 0.75
) -> LocalCheck:
    """``SanctionsChecker.check_entity_local`` without its timestamp."""
    profile = _profile("flowinvoice.sanctions_local")
    exact = float(profile.setting("exact_from"))
    matches = []
    for entity in entities:
        best, best_name = 0.0, entity.name
        for candidate in [entity.name, *(entity.aliases or [])]:
            if not candidate:
                continue
            value = difflib_score(name, candidate)
            if value > best:
                best, best_name = value, candidate
        if best >= min_score:
            matches.append(
                SanctionMatch(
                    list_name=entity.list_type,
                    entity_name=entity.name,
                    match_score=round(best, 3),
                    entity_type=(entity.entity_type or "entity").lower(),
                    sanctions_programs=list(entity.sanction_programs or []),
                    identifiers={"vat_ids": list(entity.vat_ids or [])},
                    supplier_name=name,
                    match_method="exact" if best >= exact else "fuzzy",
                    sanctioned_name_on_list=best_name,
                )
            )
    return {
        "is_sanctioned": len(matches) > 0,
        "matches": matches,
        "lists_checked": ["LOCAL_DB"],
        "query_name": name,
        "query_country": None,
        "error_message": None,
        "lists_info": [],
    }


def flowinvoice_sanctions_network(
    response: Mapping[str, Any], name: str, *, min_score: float = 0.8
) -> list[SanctionMatch]:
    """``_check_sanctions_network`` on a recorded answer (endpoint unreachable since 2026-09-23)."""
    exact = float(_profile("flowinvoice.sanctions_network").setting("exact_from"))
    matches = []
    for hit in response.get("results", []):
        score = hit.get("score", 0.0)
        if score < min_score:
            continue
        matches.append(
            SanctionMatch(
                list_name=hit.get("source", "unknown"),
                entity_name=hit.get("name", ""),
                match_score=round(score, 3),
                entity_type=hit.get("type", "entity"),
                sanctions_programs=hit.get("programs", []),
                identifiers=hit.get("identifiers", {}),
                supplier_name=name,
                match_method="exact" if score >= exact else "fuzzy",
                sanctioned_name_on_list=hit.get("name", ""),
            )
        )
    return matches


def flowinvoice_extract_position(properties: str) -> str:
    """``PEPChecker._extract_position`` (the CSV has no ``properties`` column)."""
    if not properties:
        return ""
    try:
        props = json.loads(properties)
        if isinstance(props, dict):
            for key in ("position", "role", "title", "description"):
                value = props.get(key)
                if value:
                    if isinstance(value, list):
                        return "; ".join(str(v) for v in value)
                    return str(value)
    except (json.JSONDecodeError, TypeError):
        pass
    return ""


def flowinvoice_pep_entries(data: bytes) -> list[PepEntry]:
    """``PEPChecker._download_and_parse`` on a downloaded CSV."""
    entries: list[PepEntry] = []
    for row in csv.DictReader(io.StringIO(data.decode("utf-8"))):
        name = row.get("name", "").strip()
        if not name:
            continue
        raw_aliases = row.get("aliases", "")
        aliases = [a.strip() for a in raw_aliases.split(";") if a.strip()] if raw_aliases else []
        entries.append(
            {
                "id": row.get("id", ""),
                "name": name,
                "name_normalized": matching_legacy.flowinvoice_pep_normalize_name(name),
                "aliases": aliases,
                "aliases_normalized": [
                    matching_legacy.flowinvoice_pep_normalize_name(a) for a in aliases
                ],
                "countries": row.get("countries", ""),
                "dataset": row.get("dataset", "peps"),
                "first_seen": row.get("first_seen") or None,
                "last_seen": row.get("last_seen") or None,
                "position": flowinvoice_extract_position(row.get("properties", "")),
            }
        )
    return entries


@dataclass
class PEPMatch:
    """flowinvoice ``PEPMatch``."""

    person_name: str
    position: str
    country: str
    match_score: float
    match_method: str
    source: str
    dataset: str
    first_seen: str | None = None
    last_seen: str | None = None
    matched_name: str = ""
    via_alias: bool = False


@dataclass
class PEPResult:
    """flowinvoice ``PEPResult``."""

    is_clean: bool
    hit_count: int
    checked_entities: int
    matches: list[PEPMatch] = field(default_factory=list)
    data_source: str = "opensanctions"
    dataset_size: int = 0
    last_update: str | None = None
    error_message: str | None = None


def flowinvoice_pep_check(
    name: str,
    entries: Sequence[Mapping[str, Any]] | None,
    *,
    country: str | None = None,
    min_score: float | None = None,
    dataset_size: int = 0,
    last_update: str | None = None,
    load_error: str | None = None,
) -> PEPResult:
    """``PEPChecker.check_entity`` (a failed load is reported as *clean*, as in the source)."""
    if not name or not name.strip():
        return PEPResult(is_clean=True, hit_count=0, checked_entities=0)
    profile = _profile("flowinvoice.pep_bulk")
    if load_error is not None or entries is None:
        return PEPResult(
            is_clean=True,
            hit_count=0,
            checked_entities=1,
            error_message=f"PEP-Daten konnten nicht geladen werden: {load_error}",
        )
    threshold = float(profile.setting("default_min_score") if min_score is None else min_score)
    exact = float(profile.setting("exact_from"))
    query = matching_legacy.flowinvoice_pep_normalize_name(name)
    matches = []
    for entry in entries:
        pairs = [(entry.get("name", ""), entry.get("name_normalized", ""))]
        pairs.extend(
            zip(entry.get("aliases", []), entry.get("aliases_normalized", []), strict=True)
        )
        best, method, best_name = 0.0, "fuzzy", ""
        for display, form in pairs:
            if not form:
                continue
            value = pep_score(
                query, form, profile, country=country, entry_countries=entry.get("countries", "")
            )
            if value > best:
                best, best_name = value, display
                method = "exact" if value >= exact else "fuzzy"
        if best >= threshold:
            matches.append(
                PEPMatch(
                    person_name=entry.get("name", ""),
                    position=entry.get("position", ""),
                    country=entry.get("countries", ""),
                    match_score=round(best, 3),
                    match_method=method,
                    source="opensanctions",
                    dataset=entry.get("dataset", "peps"),
                    first_seen=entry.get("first_seen"),
                    last_seen=entry.get("last_seen"),
                    matched_name=best_name,
                    via_alias=bool(best_name and best_name != entry.get("name", "")),
                )
            )
    matches.sort(key=lambda m: m.match_score, reverse=True)
    matches = matches[: int(profile.setting("max_hits"))]
    return PEPResult(
        is_clean=len(matches) == 0,
        hit_count=len(matches),
        checked_entities=1,
        matches=matches,
        dataset_size=dataset_size,
        last_update=last_update,
    )
