"""Overpass API (OpenStreetMap): fuel stations of one area as master data.

Characterized from regulierung ``external_apis/overpass.py``: ``POST`` of the
Overpass-QL query as form field ``data`` (client timeout 180 s, server
timeout 120 s), elements of type node/way with ``out center tags``; 429 is a
rate limit. The original stored new stations with placeholders ("Tankstelle",
PLZ "00000", "Unbekannt"), silently skipped elements without coordinates and
treated an answer with a ``remark`` (for example a server-side timeout) as a
complete success.

Here every element with type and id becomes a record with the source values
(missing stay ``None``) and the coordinate origin; the data timestamp
``osm3s.timestamp_osm_base`` is the time reference (kept in ``raw.datenstand``
so that a newer database state alone does not count as a changed station).
A ``remark`` makes the page ``partial``. :func:`legacy_station_fields` reproduces the original row
mapping, including its placeholders, for the consumer migration.
"""

from __future__ import annotations

import json
import urllib.parse
from collections.abc import Mapping
from typing import Any

from auditcore_harvest import (
    AuthKind,
    Capabilities,
    ConfigError,
    FetchContext,
    HarvestRecord,
    PageResult,
    PageStatus,
    ParserError,
    RecordIssue,
    SnapshotSemantics,
    Source,
    raise_for_status,
)

from .observation import STATION_SCHEMA

ADAPTER_VERSION = "1.0.0"
PROFILE_VERSION = "2026.09.1"
DEFAULT_AREA = "DE-HE"
DEFAULT_TIMEOUT_SECONDS = 180.0


def fuel_query(area_iso: str = DEFAULT_AREA, server_timeout: int = 120) -> str:
    """Overpass-QL of the original (for ``DE-HE`` byte-identical to regulierung)."""
    return (
        f"\n[out:json][timeout:{server_timeout}];\n"
        f'area["ISO3166-2"="{area_iso}"]->.hessen;\n'
        "(\n"
        '  node["amenity"="fuel"](area.hessen);\n'
        '  way["amenity"="fuel"](area.hessen);\n'
        ");\n"
        "out center tags;\n"
    )


class OverpassFuelStationAdapter:
    """``price.overpass_fuel_stations``: all ``amenity=fuel`` nodes/ways of one ISO area."""

    source = Source(
        source_id="price.overpass_fuel_stations",
        title="Overpass API – Tankstellen eines Gebiets (OpenStreetMap, ODbL)",
        family="price",
        adapter_version=ADAPTER_VERSION,
        profile_version=PROFILE_VERSION,
        data_format="application/json (Overpass)",
        auth=AuthKind.NONE,
        capabilities=Capabilities(
            pagination=False, incremental=False, full_snapshot=True, deletions=False
        ),
        snapshot_semantics=SnapshotSemantics.APPEND_ONLY,
        filters=("area_iso",),
    )

    def validate_config(self, config: Mapping[str, Any]) -> None:
        """``url`` (interpreter endpoint), optional ``area_iso`` and ``timeout_seconds``."""
        if not isinstance(config.get("url"), str) or not config["url"].startswith("http"):
            raise ConfigError("url (Interpreter-Adresse) fehlt.")
        area = config.get("area_iso", DEFAULT_AREA)
        if not isinstance(area, str) or not area.replace("-", "").isalnum() or len(area) > 8:
            raise ConfigError("area_iso muss ein ISO-3166-2-Kürzel sein.")
        timeout = config.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
            raise ConfigError("timeout_seconds muss positiv sein.")

    def fetch_page(self, context: FetchContext, cursor: Mapping[str, Any] | None) -> PageResult:
        """Post the query once and turn every element into a station record."""
        area = str(
            context.request.filters.get("area_iso") or context.config.get("area_iso", DEFAULT_AREA)
        )
        url = str(context.config["url"])
        body = urllib.parse.urlencode({"data": fuel_query(area)}).encode()
        response = raise_for_status(
            context.transport.request(
                "POST",
                url,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=body,
                timeout=float(context.config.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)),
            )
        )
        try:
            payload = json.loads(response.body)
        except ValueError as exc:
            raise ParserError("Overpass-Antwort ist kein JSON.") from exc
        if not isinstance(payload, Mapping) or not isinstance(payload.get("elements"), list):
            raise ParserError("Overpass-Antwort ohne elements-Liste.")
        osm = payload.get("osm3s") or {}
        stand = osm.get("timestamp_osm_base") if isinstance(osm, Mapping) else None
        issues: list[RecordIssue] = []
        if payload.get("remark"):
            issues.append(RecordIssue(url, f"Overpass-Hinweis: {str(payload['remark'])[:200]}"))
        records: list[HarvestRecord] = []
        for position, element in enumerate(payload["elements"]):
            locator = f"{url}#elements[{position}]"
            if (
                not isinstance(element, Mapping)
                or not element.get("type")
                or element.get("id") is None
            ):
                issues.append(RecordIssue(locator, "Element ohne Typ oder Kennung"))
                continue
            kind, ident = str(element["type"]), element["id"]
            lat, lon, origin = element.get("lat"), element.get("lon"), "element"
            if lat is None or lon is None:
                center = element.get("center") or {}
                lat, lon, origin = center.get("lat"), center.get("lon"), "center"
            if lat is None or lon is None:
                origin = "fehlt"
            tags = element.get("tags") or {}
            normalized = {
                "schema": STATION_SCHEMA,
                "station_id": f"osm-{kind}-{ident}",
                "osm_typ": kind,
                "osm_id": ident,
                "name": tags.get("name"),
                "marke": tags.get("brand"),
                "strasse": tags.get("addr:street"),
                "hausnummer": tags.get("addr:housenumber"),
                "plz": tags.get("addr:postcode"),
                "ort": tags.get("addr:city") or tags.get("addr:place"),
                "lat": lat,
                "lng": lon,
                "koordinaten_herkunft": origin,
                "tags": dict(tags),
                "zeitbezug": {"art": "datenstand", "wert": None, "quelle": "raw.datenstand"},
                "lizenz": "ODbL (OpenStreetMap)",
                "gebiet": area,
            }
            raw = {"element": dict(element), "datenstand": stand}
            records.append(
                HarvestRecord(
                    source_id=self.source.source_id,
                    record_id=f"osm-{kind}-{ident}",
                    raw=raw,
                    normalized=normalized,
                    provenance=context.provenance(self.source, locator, raw),
                )
            )
        status = PageStatus.PARTIAL if issues else PageStatus.OK
        return PageResult(tuple(records), None, complete=True, status=status, issues=tuple(issues))


def legacy_station_fields(
    normalized: Mapping[str, Any], *, bundesland: str = "HE"
) -> dict[str, Any] | None:
    """Row values exactly as regulierung stored a new ``Tankstelle`` (``None`` = skipped).

    Keeps the original placeholders and truncations; ``stamm_id``,
    ``gueltig_von`` and the duplicate check stay with the consumer.
    """
    lat, lng = normalized.get("lat"), normalized.get("lng")
    if lat is None or lng is None:
        return None
    name = normalized.get("name") or normalized.get("marke") or "Tankstelle"
    strasse = normalized.get("strasse") or ""
    hausnummer = normalized.get("hausnummer")
    if hausnummer and hausnummer not in strasse:
        strasse = f"{strasse} {hausnummer}".strip()
    plz = (normalized.get("plz") or "")[:8] or "00000"
    ort = (normalized.get("ort") or "")[:128]
    return {
        "mtsk_id": normalized["station_id"],
        "name": str(name)[:256],
        "marke": normalized.get("marke"),
        "strasse": (strasse or "Unbekannt")[:256],
        "hausnummer": hausnummer,
        "plz": plz,
        "ort": ort or "Unbekannt",
        "bundesland": bundesland,
        "standort": f"SRID=4326;POINT({lng} {lat})",
        "aenderungsgrund": "Import OpenStreetMap (Overpass)",
    }
