"""Behavior-compatible functions of the source applications (replay of the characterization).

Each function reproduces one characterized original on the recorded inputs
(``tests/fixtures/legacy_observed.json``), built on the library's profiles and
functions, so that a consumer can switch without changing results. Known
defects are reproduced here on purpose and corrected only in the library
contract (``docs/behavior-changes.md``). Where an original raised a transport
exception, the functions take the recorded error text instead of calling the
network.
"""

from __future__ import annotations

import csv
import io
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from functools import cache
from typing import Any

from auditcore_entity_matching import legacy as matching_legacy
from auditcore_entity_matching import load_profile as load_normalization
from auditcore_entity_matching import normalize

from . import chambers, company, opensanctions_api, ownership
from .bulk_screening import difflib_score, pep_score
from .errors import QueryError
from .lists import find_list, list_catalog
from .profiles import RegistryProfile, load_profile
from .screening import ListIndex, ScreeningHit, ScreeningSettings, adjust_score

VERSION = "2026.09.1"


@cache
def _profile(profile_id: str) -> RegistryProfile:
    return load_profile(profile_id, VERSION)


@cache
def _settings(profile_id: str) -> ScreeningSettings:
    return ScreeningSettings.from_profile(_profile(profile_id))


@dataclass(frozen=True)
class RawRecord:
    """An index record that, unlike ``ListEntry``, may lack id or name (flowworkshop CSV path)."""

    entry_id: str
    schema: str
    name: str
    aliases: tuple[str, ...]
    birth_date: str = ""
    countries: str = ""
    addresses: str = ""
    identifiers: str = ""
    sanctions: str = ""
    program_ids: str = ""
    first_seen: str = ""
    last_seen: str = ""


# --------------------------------------------------------------- audit_designer


def designer_row(row: Mapping[str, Any], list_key: str) -> dict[str, Any] | None:
    """``SanktionslistenDienst._zu_datensatz`` for a row with id and name, else ``None``."""
    entry_id = str(row.get("id") or "").strip()
    name = str(row.get("name") or "").strip()
    if not entry_id or not name:
        return None

    def value(key: str) -> str | None:
        """Stripped field value or ``None`` (``feld`` of the source)."""
        raw = row.get(key)
        if raw is None:
            return None
        text = str(raw).strip()
        return text or None

    raw_aliases = row.get("aliases") or ""
    if isinstance(raw_aliases, (list, tuple)):
        aliases = [str(a).strip() for a in raw_aliases if str(a).strip()]
    else:
        aliases = [a.strip() for a in str(raw_aliases).split(";") if a.strip()]
    return {
        "list_key": list_key,
        "entry_id": entry_id,
        "entity_schema": str(row.get("schema") or ""),
        "name": name,
        "name_normalized": matching_legacy.designer_normalisiere_name_umschrift(name),
        "aliases": aliases or None,
        "birth_date": value("birth_date"),
        "countries": value("countries"),
        "addresses": value("addresses"),
        "identifiers": value("identifiers"),
        "sanctions_program": value("sanctions"),
        "program_ids": value("program_ids"),
        "first_seen": value("first_seen"),
        "last_seen": value("last_seen"),
        "raw_payload": {str(k): (None if v is None else str(v)) for k, v in row.items()},
        "refresh_run_id": None,
    }


def designer_records(rows: Sequence[Mapping[str, Any]], list_key: str) -> list[RawRecord]:
    """Stored rows as ``SanktionslistenDienst.eintraege`` loads them."""
    result = []
    for row in rows:
        record = designer_row(row, list_key)
        if record is None:
            continue
        result.append(
            RawRecord(
                entry_id=record["entry_id"],
                schema=record["entity_schema"],
                name=record["name"],
                aliases=tuple(record["aliases"] or ()),
                birth_date=record["birth_date"] or "",
                countries=record["countries"] or "",
                addresses=record["addresses"] or "",
                identifiers=record["identifiers"] or "",
                sanctions=record["sanctions_program"] or "",
                program_ids=record["program_ids"] or "",
                first_seen=record["first_seen"] or "",
                last_seen=record["last_seen"] or "",
            )
        )
    return result


def _designer_hit(hit: ScreeningHit, url: str | None) -> dict[str, Any]:
    entry = hit.entry
    assert isinstance(entry, RawRecord)
    return {
        "source_url": url,
        "source_key": hit.source_key,
        "list_key": hit.list_key,
        "list_name": hit.list_name,
        "entry_id": entry.entry_id,
        "entity_schema": entry.schema,
        "name": entry.name,
        "matched_name": hit.matched_name,
        "matched_field": hit.matched_field,
        "score": hit.score,
        "confidence": hit.confidence,
        "aliases": list(hit.aliases),
        "birth_date": entry.birth_date,
        "countries": entry.countries,
        "addresses": entry.addresses,
        "identifiers": entry.identifiers,
        "sanctions_program": entry.sanctions,
        "program_ids": entry.program_ids,
        "first_seen": entry.first_seen,
        "last_seen": entry.last_seen,
        "dob_conflict": hit.dob_conflict,
        "country_conflict": hit.country_conflict,
    }


def _designer_index(list_key: str, records: Sequence[RawRecord]) -> tuple[ListIndex, str]:
    lists = list_catalog(_profile("audit_designer.sanctions_lists"))
    item = find_list(lists, list_key)
    index = ListIndex(
        _settings("audit_designer.sanctions_screening"),
        records,
        list_key=item.key,
        list_name=item.name,
        source_key=item.source_key,
    )
    return index, item.url


def designer_index_search(
    records: Sequence[RawRecord],
    list_key: str,
    name: str,
    *,
    limit: int = 15,
    min_score: float = 70.0,
    schema: str | None = None,
    birth_date: str | None = None,
    country: str | None = None,
) -> list[dict[str, Any]]:
    """``Listenindex.suche`` followed by ``Sanktionstreffer.to_dict``."""
    index, url = _designer_index(list_key, records)
    hits = index.search(
        name,
        limit=limit,
        min_score=min_score,
        schema=schema,
        birth_date=birth_date,
        country=country,
    )
    return [_designer_hit(h, url) for h in hits]


def designer_service_search(
    inventory: Mapping[str, Sequence[RawRecord]],
    list_keys: Sequence[str],
    name: str,
    *,
    as_of: datetime | None,
    limit: int = 15,
    min_score: float = 70.0,
    schema: str | None = None,
    birth_date: str | None = None,
    country: str | None = None,
) -> list[dict[str, Any]]:
    """``SanktionslistenDienst.suche``: one finding per list, also for lists without inventory."""
    result: list[dict[str, Any]] = []
    lists = list_catalog(_profile("audit_designer.sanctions_lists"))
    for key in list_keys:
        item = find_list(lists, key)
        records = inventory.get(key, ())
        if not records:
            result.append(
                {
                    "list_key": key,
                    "source_key": item.source_key,
                    "durchsucht": False,
                    "bestand": 0,
                    "stand": None,
                    "hinweis": (
                        "Für diese Liste liegt kein Bestand vor. Sie wurde nicht abgefragt; "
                        "das Ergebnis sagt über sie nichts aus."
                    ),
                    "treffer": [],
                }
            )
            continue
        result.append(
            {
                "list_key": key,
                "source_key": item.source_key,
                "durchsucht": True,
                "bestand": len(records),
                "stand": as_of,
                "hinweis": None,
                "treffer": designer_index_search(
                    records,
                    key,
                    name,
                    limit=limit,
                    min_score=min_score,
                    schema=schema,
                    birth_date=birth_date,
                    country=country,
                ),
            }
        )
    return result


def designer_dob_country(
    score: float,
    *,
    entry_birth_date: str,
    entry_countries: str,
    birth_date: str | None,
    country: str | None,
) -> tuple[float, bool, bool]:
    """``_beruecksichtige_geburtsdatum_und_land``."""
    value, dob, land, _ = adjust_score(
        score,
        _settings("audit_designer.sanctions_screening"),
        entry_birth_date=entry_birth_date,
        entry_countries=entry_countries,
        birth_date=birth_date,
        country=country,
    )
    return value, dob, land


def designer_provider_name(params: Mapping[str, Any]) -> str:
    """``SanctionsScreeningProvider._name`` (raises :class:`QueryError` with the source text)."""
    raw = params.get("name") or params.get("q")
    name = str(raw).strip() if raw else ""
    if not name:
        raise QueryError("Pflichtangabe fehlt: 'name'")
    if len(name) < 3:
        raise QueryError(
            "Bitte geben Sie mindestens drei Zeichen an. Kürzere Eingaben treffen so viele "
            "Einträge, dass das Ergebnis nichts aussagt."
        )
    return name


def designer_provider_min_score(value: Any) -> float:
    """``SanctionsScreeningProvider._mindestwert``."""
    settings = _settings("audit_designer.sanctions_screening")
    if value in (None, ""):
        return settings.default_min_score
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise QueryError(f"'min_score' muss eine Zahl sein, nicht {value!r}.") from exc
    low, high = settings.min_score_range
    if not low <= number <= high:
        raise QueryError(
            "'min_score' liegt zwischen 50 und 100. Darunter besteht das Ergebnis aus "
            "Namensgleichheiten ohne Bezug."
        )
    return number


def designer_provider_schema(value: Any) -> str | None:
    """``SanctionsScreeningProvider._entity_schema``."""
    if value in (None, ""):
        return None
    text = str(value).strip()
    if not text:
        return None
    chosen = {"person": "Person", "organization": "Organization"}.get(text.casefold())
    if chosen is None:
        raise QueryError("'entity_schema' kennt nur 'Person' und 'Organization'.")
    return chosen


# ----------------------------------------------------------------- flowworkshop


def workshop_record(row: Mapping[str, Any]) -> dict[str, Any]:
    """``_row_to_record`` (``FsfRecord`` fields; id and name are not stripped)."""
    raw = row.get("aliases") or ""
    if isinstance(raw, list):
        aliases = [a for a in raw if a]
    else:
        aliases = [a.strip() for a in str(raw).split(";") if a.strip()]
    name = row.get("name", "") or ""
    return {
        "id": row.get("id", "") or "",
        "schema": row.get("schema", "") or "",
        "name": name,
        "aliases": aliases,
        "birth_date": row.get("birth_date", "") or "",
        "countries": row.get("countries", "") or "",
        "addresses": row.get("addresses", "") or "",
        "identifiers": row.get("identifiers", "") or "",
        "sanctions": row.get("sanctions", "") or "",
        "program_ids": row.get("program_ids", "") or "",
        "first_seen": row.get("first_seen", "") or "",
        "last_seen": row.get("last_seen", "") or "",
        "name_norm": matching_legacy.flowworkshop_normalize_name_umschrift(name),
        "alias_norms": tuple(
            matching_legacy.flowworkshop_normalize_name_umschrift(a) for a in aliases
        ),
    }


def workshop_records(rows: Sequence[Mapping[str, Any]]) -> list[RawRecord]:
    """All CSV rows, including rows without id or name (as the source indexes them)."""
    result = []
    for row in rows:
        r = workshop_record(row)
        result.append(
            RawRecord(
                entry_id=r["id"],
                schema=r["schema"],
                name=r["name"],
                aliases=tuple(r["aliases"]),
                birth_date=r["birth_date"],
                countries=r["countries"],
                addresses=r["addresses"],
                identifiers=r["identifiers"],
                sanctions=r["sanctions"],
                program_ids=r["program_ids"],
                first_seen=r["first_seen"],
                last_seen=r["last_seen"],
            )
        )
    return result


def _workshop_hit(hit: ScreeningHit, display_name: str) -> dict[str, Any]:
    entry = hit.entry
    assert isinstance(entry, RawRecord)
    return {
        "id": entry.entry_id,
        "schema": entry.schema,
        "name": entry.name,
        "matched_on": hit.matched_name,
        "matched_field": hit.matched_field,
        "score": hit.score,
        "confidence": hit.confidence,
        "aliases": list(hit.aliases),
        "birth_date": entry.birth_date,
        "countries": entry.countries,
        "addresses": entry.addresses,
        "identifiers": entry.identifiers,
        "sanctions": entry.sanctions,
        "program_ids": entry.program_ids,
        "first_seen": entry.first_seen,
        "last_seen": entry.last_seen,
        "source_key": hit.list_key,
        "source_display_name": display_name,
        "dob_conflict": hit.dob_conflict,
        "country_conflict": hit.country_conflict,
    }


def workshop_index_search(
    records: Sequence[RawRecord],
    list_key: str,
    display_name: str,
    name: str,
    *,
    limit: int = 15,
    min_score: float = 65.0,
    schema: str | None = None,
    birth_date: str | None = None,
    country: str | None = None,
) -> list[dict[str, Any]]:
    """``SanctionsListIndex.search`` (service default minimum 65)."""
    index = ListIndex(
        _settings("flowworkshop.sanctions_screening"),
        records,
        list_key=list_key,
        list_name=display_name,
        source_key=list_key,
    )
    hits = index.search(
        name,
        limit=limit,
        min_score=min_score,
        schema=schema,
        birth_date=birth_date,
        country=country,
    )
    return [_workshop_hit(h, display_name) for h in hits]


def workshop_multi_search(
    indices: Sequence[tuple[str, str, Sequence[RawRecord]]],
    name: str,
    *,
    limit: int = 15,
    min_score: float = 65.0,
    schema: str | None = None,
    birth_date: str | None = None,
    country: str | None = None,
) -> list[dict[str, Any]]:
    """``MultiSanctionsService.search``: lists without inventory are skipped silently."""
    per_list = _settings("flowworkshop.sanctions_screening").per_list_limit.apply(limit)
    hits: list[dict[str, Any]] = []
    for key, display, records in indices:
        if not records:
            continue
        hits.extend(
            workshop_index_search(
                records,
                key,
                display,
                name,
                limit=per_list,
                min_score=min_score,
                schema=schema,
                birth_date=birth_date,
                country=country,
            )
        )
    hits.sort(key=lambda h: h["score"], reverse=True)
    return hits[:limit]


def workshop_dob_country(
    score: float,
    *,
    entry_birth_date: str,
    entry_countries: str,
    birth_date: str | None,
    country: str | None,
) -> tuple[float, bool, bool]:
    """``_adjust_score_for_dob_country``."""
    value, dob, land, _ = adjust_score(
        score,
        _settings("flowworkshop.sanctions_screening"),
        entry_birth_date=entry_birth_date,
        entry_countries=entry_countries,
        birth_date=birth_date,
        country=country,
    )
    return value, dob, land


# ------------------------------------------------------------------ audit-portal

_VAT = re.compile(r"\b([A-Z]{2}[0-9A-Z]{8,12})\b")


def portal_vat_ids(value: str | None) -> list[str]:
    """``extract_vat_ids``: VAT id candidates of a free identifier field."""
    if not value:
        return []
    compact = re.sub(r"[\s\-\.]", "", value.upper())
    return list(dict.fromkeys(_VAT.findall(compact)))


def portal_record(row: Mapping[str, Any]) -> dict[str, Any] | None:
    """``audit_prep.sanctions.row_to_record``."""
    entry_id = (row.get("id") or "").strip()
    name = (row.get("name") or "").strip()
    if not entry_id or not name:
        return None

    def multi(value: str | None) -> list[str]:
        """``;``-separated values."""
        return [p.strip() for p in str(value).split(";") if p.strip()] if value else []

    name_profile = load_normalization("audit_portal.name", VERSION)
    folded = load_normalization("audit_portal.name_folded", VERSION)
    aliases = multi(row.get("aliases"))
    identifiers = (row.get("identifiers") or "").strip()
    return {
        "entry_id": entry_id,
        "schema": (row.get("schema") or "").strip(),
        "name": name,
        "aliases": aliases,
        "birth_date": (row.get("birth_date") or "").strip(),
        "countries": multi(row.get("countries")),
        "addresses": (row.get("addresses") or "").strip(),
        "identifiers": identifiers,
        "sanctions": (row.get("sanctions") or "").strip(),
        "program_ids": (row.get("program_ids") or "").strip(),
        "first_seen": (row.get("first_seen") or "").strip(),
        "last_seen": (row.get("last_seen") or "").strip(),
        "name_norm": normalize(name, name_profile),
        "name_folded": normalize(name, folded),
        "alias_folded": [normalize(a, folded) for a in aliases],
        "vat_ids": portal_vat_ids(identifiers),
    }


def portal_parse_sanctions_csv(
    data: bytes,
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    """``audit_prep.sanctions.parse_sanctions_csv`` (with its Latin-1 fallback)."""
    validation: dict[str, Any] = {"errors": [], "warnings": []}
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data.decode("latin-1")
        validation["warnings"].append("Datei nicht UTF-8-kodiert — Latin-1-Fallback verwendet.")
    reader = csv.DictReader(io.StringIO(text))
    columns = [c.strip() for c in (reader.fieldnames or [])]
    missing = [c for c in ("id", "name") if c not in columns]
    if missing:
        validation["errors"].append(
            f"Pflichtspalten fehlen: {', '.join(missing)} — erwartet wird "
            "das OpenSanctions-Format targets.simple.csv."
        )
        return [], columns, validation
    records, skipped = [], 0
    for row in reader:
        record = portal_record(row)
        if record is None:
            skipped += 1
            continue
        records.append(record)
    if skipped:
        validation["warnings"].append(f"{skipped} Zeile(n) ohne id/name übersprungen.")
    if not records:
        validation["errors"].append("Die Datei enthält keine verwertbaren Sanktionseinträge.")
    return records, columns, validation


# -------------------------------------------------------------------- flowsearch

SANCTIONS_SOURCES = ["EU Sanctions", "UN Security Council", "OFAC", "UK Sanctions"]


def flowsearch_sanctions_payload(name: str, country: str = "DE") -> dict[str, Any]:
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
) -> dict[str, Any]:
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
) -> dict[str, Any]:
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
    pep_type: str, score: float, positions: Sequence[Mapping[str, Any]]
) -> str:
    """``PEPScreeningAPIClient._assess_risk``."""
    return opensanctions_api.pep_risk(pep_type, score, positions, _profile("flowsearch.pep_risk"))


def flowsearch_pep_type(topics: Sequence[str], positions: Sequence[Mapping[str, Any]]) -> str:
    """``_determine_pep_type``."""
    labels = _profile("flowsearch.pep_risk").setting("labels")
    return opensanctions_api.pep_type(topics, positions, labels)


def flowsearch_pep_category(matches: Sequence[Mapping[str, Any]]) -> str:
    """``_categorize_pep``."""
    return opensanctions_api.pep_category([m["pep_type"] for m in matches])


def flowsearch_openregister_error(error: str) -> dict[str, Any]:
    """``OpenRegisterAPIClient.search_company`` after a failed request (endpoint answers 404)."""
    return {"found": False, "results": [], "error": error, "note": "OpenRegister API error"}


def flowsearch_handelsregister_search(name: str, location: str | None = None) -> dict[str, Any]:
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


def flowsearch_ubo(structure: Mapping[str, Any]) -> dict[str, Any]:
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


def flowsearch_kmu(company_data: Mapping[str, Any]) -> dict[str, Any]:
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


# ----------------------------------------------------------------------- osint


def _count(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def osint_zer(status: bytes, register: bytes) -> dict[str, Any]:
    """``zer_holen``: returned count, written file and console output."""
    total = json.loads(status).get("total", 0)
    delivery = chambers.parse_zer_register(register)
    return {
        "return": len(delivery.records),
        "file": list(delivery.records),
        "stdout": f"  Register meldet {_count(total)} Einträge, lade …\n",
        "stderr": "",
    }


def osint_ihk(data: bytes) -> list[dict[str, Any]]:
    """``ihk_holen``."""
    return list(chambers.parse_ihk_locations(data).records)


def osint_hwk(html: bytes) -> list[dict[str, Any]]:
    """``hwk_holen``."""
    return list(chambers.parse_hwk_page(html, expected=None).records)


def osint_kammern(ihk: bytes, html: bytes) -> dict[str, Any]:
    """``kammern_holen``: IHK and HWK with the warning below 53 chambers of crafts."""
    first, second = osint_ihk(ihk), osint_hwk(html)
    warning = (
        "  Achtung: Die ZDH-Seite hat sich offenbar geändert — es sollten 53 "
        "Handwerkskammern sein.\n"
        if len(second) < chambers.EXPECTED_HWK
        else ""
    )
    return {
        "return": len(first) + len(second),
        "file": first + second,
        "stdout": f"  {len(first)} Industrie- und Handelskammern, {len(second)} Handwerkskammern\n",
        "stderr": warning,
    }


# ------------------------------------------------------------------- flowinvoice


def flowinvoice_to_list(value: Any) -> list[str] | None:
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


def flowinvoice_check_entity_local(
    name: str, entities: Sequence[LocalEntity], *, min_score: float = 0.75
) -> dict[str, Any]:
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


def flowinvoice_pep_entries(data: bytes) -> list[dict[str, Any]]:
    """``PEPChecker._download_and_parse`` on a downloaded CSV."""
    entries = []
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


def flowinvoice_validate_vat(
    vat_id: str, *, response_text: str | None = None, error: str | None = None
) -> dict[str, Any]:
    """``CompanyVerifier.validate_vat_id`` without ``request_date`` (text search for ``valid``)."""
    compact = vat_id.replace(" ", "").upper()
    match = re.match(r"^([A-Z]{2})(.+)$", compact)
    if not match:
        return {
            "is_valid": False,
            "vat_id": compact,
            "country_code": "",
            "company_name": None,
            "company_address": None,
            "error_message": "Ungültiges Format",
        }
    country = match.group(1)
    if response_text is None:
        return {
            "is_valid": False,
            "vat_id": compact,
            "country_code": country,
            "company_name": None,
            "company_address": None,
            "error_message": error,
        }
    name = re.search(r"<name>(.+?)</name>", response_text, re.DOTALL)
    address = re.search(r"<address>(.+?)</address>", response_text, re.DOTALL)
    return {
        "is_valid": "<valid>true</valid>" in response_text.lower(),
        "vat_id": compact,
        "country_code": country,
        "company_name": name.group(1).strip() if name else None,
        "company_address": address.group(1).strip() if address else None,
        "error_message": None,
    }


def flowinvoice_register_accepts(name: str) -> bool:
    """Input check of ``search_offene_register`` (the source then builds SQL text from the name).

    The library itself sends bound parameters (:func:`company.register_query`);
    the recorded legacy request text is reproduced only in the tests.
    """
    return len(name) <= 100 and bool(re.match(r"^[\w\s\.\-\,\&\(\)GmbH]+$", name))


def flowinvoice_register_company(
    status: int, body: Mapping[str, Any] | None
) -> dict[str, Any] | None:
    """Result of ``search_offene_register`` for a recorded answer."""
    if status != 200 or body is None:
        return None
    rows = body.get("rows", [])
    if not rows:
        return None
    row = rows[0]
    text = row.get("current_status", "").lower()
    if "dissolved" in text or "liquidation" in text:
        state = "dissolved"
    elif "registered" in text:
        state = "active"
    else:
        state = "unknown"
    return {
        "name": row.get("name", ""),
        "legal_form": row.get("company_type"),
        "status": state,
        "registration_number": row.get("company_number"),
        "registration_authority": row.get("native_company_number"),
        "address": row.get("registered_address"),
        "founded_date": None,
        "directors": [],
        "source": "offeneregister.de",
    }


def flowinvoice_normalize_company_name(name: str) -> str:
    """``_normalize_company_name``: legal forms removed as *substrings* (``Hagen AG → hen``)."""
    forms = _profile("flowinvoice.company_verification").setting("legal_forms")
    name = name.lower().strip()
    for form in sorted(forms, key=len, reverse=True):
        name = name.replace(form, "").strip()
    return " ".join(name.split())


def flowinvoice_names_match(a: str, b: str) -> bool:
    """``_names_match`` with the substring normalisation."""
    rule = _profile("flowinvoice.company_verification").setting("name_match")
    n1, n2 = flowinvoice_normalize_company_name(a), flowinvoice_normalize_company_name(b)
    if n1 == n2 or n1 in n2 or n2 in n1:
        return True
    w1, w2 = n1.split()[: int(rule["leading_words"])], n2.split()[: int(rule["leading_words"])]
    if w1 and w2:
        common = len(set(w1) & set(w2))
        if common >= min(len(w1), len(w2)) * float(rule["threshold"]):
            return True
    return False


def flowinvoice_verify_company(
    name: str,
    *,
    vat: Mapping[str, Any] | None,
    register: Mapping[str, Any] | None,
    country: str = "DE",
) -> dict[str, Any]:
    """``verify_company`` from recorded VIES/register results (``None`` register = not found)."""
    profile = _profile("flowinvoice.company_verification")
    indicators = []
    if vat is not None:
        if not vat["is_valid"]:
            if vat.get("error_message") and "SERVICE_UNAVAILABLE" in vat["error_message"]:
                indicators.append("VIES_SERVICE_UNAVAILABLE")
            else:
                indicators.append("INVALID_VAT_ID")
        elif vat.get("company_name") and not flowinvoice_names_match(name, vat["company_name"]):
            indicators.append("VAT_NAME_MISMATCH")
    if country == "DE":
        if register:
            if register["status"] == "dissolved":
                indicators.append("COMPANY_DISSOLVED")
            elif register["status"] == "inactive":
                indicators.append("COMPANY_INACTIVE")
        else:
            indicators.append("NOT_IN_REGISTER")
    verified, score = company.score_indicators(indicators, profile)
    return {
        "is_verified": verified,
        "vat_validation": vat,
        "company_info": register,
        "risk_indicators": indicators,
        "verification_score": score,
    }
