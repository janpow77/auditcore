"""flowworkshop replays: CSV records, single and multi-list search."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from auditcore_entity_matching import legacy as matching_legacy

from ._legacy_shared import RawRecord, _settings
from ._legacy_types import WorkshopHit, WorkshopRecord
from .screening import ListIndex, ScreeningHit, adjust_score


def workshop_record(row: Mapping[str, Any]) -> WorkshopRecord:
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


def _workshop_hit(hit: ScreeningHit, display_name: str) -> WorkshopHit:
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
) -> list[WorkshopHit]:
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
) -> list[WorkshopHit]:
    """``MultiSanctionsService.search``: lists without inventory are skipped silently."""
    per_list = _settings("flowworkshop.sanctions_screening").per_list_limit.apply(limit)
    hits: list[WorkshopHit] = []
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
