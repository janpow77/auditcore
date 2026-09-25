"""audit_designer replays: sanctions list rows, index and service search, provider checks."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from auditcore_entity_matching import legacy as matching_legacy

from ._legacy_shared import RawRecord, _profile, _settings
from ._legacy_types import DesignerHit, DesignerListFinding, DesignerRecord
from .errors import QueryError
from .lists import find_list, list_catalog
from .screening import ListIndex, ScreeningHit, adjust_score


def designer_row(row: Mapping[str, object], list_key: str) -> DesignerRecord | None:
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


def designer_records(rows: Sequence[Mapping[str, object]], list_key: str) -> list[RawRecord]:
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


def _designer_hit(hit: ScreeningHit, url: str | None) -> DesignerHit:
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
) -> list[DesignerHit]:
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
) -> list[DesignerListFinding]:
    """``SanktionslistenDienst.suche``: one finding per list, also for lists without inventory."""
    result: list[DesignerListFinding] = []
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


def designer_provider_name(params: Mapping[str, object]) -> str:
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


def designer_provider_schema(value: object) -> str | None:
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
