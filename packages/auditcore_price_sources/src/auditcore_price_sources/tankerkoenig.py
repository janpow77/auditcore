"""Tankerkönig ``list.php`` (consumer information service under § 6 MTSKraftV).

Characterized from regulierung ``external_apis/tankerkoenig.py``: the health
check requests ``{url}/list.php?lat&lng&rad=1&type=all&apikey`` and treats
``ok: false`` as failure with the source message; live ingestion is disabled
there on purpose (ADR-005) because ``list.php`` states only the *current*
price without the time of the price change.

This adapter therefore marks every record explicitly: time reference
``abrufzeitpunkt`` (retrieval time from the engine clock, **not** a price
change time), purpose ``vorpruefung`` and ``beweismittel: false``. Prices
are EUR per litre; ``false``/``null`` mean "no price" and stay ``None``.
Decision PS-H02 (2026-09-23): regulierung does **not** store these records as
a pre-check source; the adapter serves the health check only.
"""

from __future__ import annotations

import json
from collections.abc import Mapping

from auditcore_harvest import (
    JSON,
    AuthError,
    AuthKind,
    Capabilities,
    ConfigError,
    Cursor,
    FetchContext,
    HarvestRecord,
    PageResult,
    ParserError,
    RecordIssue,
    SnapshotSemantics,
    Source,
    decode_json,
    page_result,
    raise_for_status,
)

from .observation import RETRIEVAL_TIME, STATION_SCHEMA, exact, unit

ADAPTER_VERSION = "1.0.0"
PROFILE_VERSION = "2026.09.1"
FUELS = ("diesel", "e5", "e10")
MAX_RADIUS_KM = 25


def check_list_response(status: int, body: bytes) -> tuple[bool, str | None]:
    """Health semantics of the original: HTTP 200 and ``ok: true``, else the reason."""
    if status != 200:
        return False, f"HTTP {status}"
    try:
        payload = json.loads(body)
    except ValueError:
        return False, "Antwort ist kein JSON"
    if not isinstance(payload, Mapping):
        return False, "Antwort ist kein Objekt"
    if not payload.get("ok"):
        return False, str(payload.get("message", "API meldet Fehler"))
    return True, None


def _postcode(value: object) -> tuple[str | None, bool]:
    """Postcode as five-digit text; numbers lose leading zeros at the source and are padded."""
    if value is None or value == "":
        return None, False
    text = str(value).strip()
    if isinstance(value, int) and not isinstance(value, bool) and 0 < value < 100000:
        return f"{value:05d}", len(text) < 5
    return text, False


class TankerkoenigListAdapter:
    """``price.tankerkoenig``: stations and current prices around one point (one page)."""

    source = Source(
        source_id="price.tankerkoenig",
        title="Tankerkönig list.php – aktueller Preisstand im Umkreis (Vorprüfung)",
        family="price",
        adapter_version=ADAPTER_VERSION,
        profile_version=PROFILE_VERSION,
        data_format="application/json",
        auth=AuthKind.API_KEY,
        capabilities=Capabilities(
            pagination=False, incremental=False, full_snapshot=False, deletions=False
        ),
        snapshot_semantics=SnapshotSemantics.UNKNOWN,
        filters=("lat", "lng", "rad"),
    )

    def validate_config(self, config: Mapping[str, JSON]) -> None:
        """``url``, ``lat``, ``lng`` and ``rad`` (km, 1..25; the service limit)."""
        if not isinstance(config.get("url"), str) or not config["url"].startswith("http"):
            raise ConfigError("url (JSON-Basisadresse) fehlt.")
        for key, low, high in (("lat", -90, 90), ("lng", -180, 180), ("rad", 0, MAX_RADIUS_KM)):
            value = config.get(key)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ConfigError(f"{key} fehlt oder ist keine Zahl.")
            if not low <= value <= high or (key == "rad" and value <= 0):
                raise ConfigError(f"{key} liegt außerhalb von {low}..{high}.")

    def fetch_page(self, context: FetchContext, cursor: Cursor | None) -> PageResult:
        """Request the list once; ``ok: false`` with an API-key message is an auth error."""
        url = f"{str(context.config['url']).rstrip('/')}/list.php"
        params = {
            "lat": str(context.config["lat"]),
            "lng": str(context.config["lng"]),
            "rad": str(context.config["rad"]),
            "type": "all",
            "apikey": context.secret(self.source.source_id, "api_key"),
        }
        response = raise_for_status(
            context.transport.request("GET", url, params=params, timeout=context.timeout)
        )
        payload = _checked_payload(decode_json(response.body))
        stations = payload.get("stations")
        if not isinstance(stations, list):
            raise ParserError("Antwort ohne stations-Liste.")
        records: list[HarvestRecord] = []
        issues: list[RecordIssue] = []
        for position, station in enumerate(stations):
            item = self._station(context, f"{url}#stations[{position}]", station, payload)
            if isinstance(item, RecordIssue):
                issues.append(item)
            else:
                records.append(item)
        return page_result(records, issues)

    def _station(
        self, context: FetchContext, locator: str, station: JSON, payload: Mapping[str, JSON]
    ) -> HarvestRecord | RecordIssue:
        """Record of one station, or the issue why it cannot be used."""
        if not isinstance(station, Mapping) or not station.get("id"):
            return RecordIssue(locator, "Station ohne Kennung")
        prices: dict[str, str | None] = {}
        try:
            for fuel in FUELS:
                value = exact(station.get(fuel))
                prices[fuel] = None if value is None else str(value)
        except ValueError as exc:
            return RecordIssue(locator, f"Preis nicht lesbar: {exc}")
        postcode, padded = _postcode(station.get("postCode"))
        normalized = {
            "schema": STATION_SCHEMA,
            "station_id": str(station["id"]),
            "name": station.get("name") or None,
            "marke": station.get("brand") or None,
            "strasse": station.get("street") or None,
            "hausnummer": station.get("houseNumber") or None,
            "plz": postcode,
            "plz_aufgefuellt": padded,
            "ort": station.get("place") or None,
            "lat": station.get("lat"),
            "lng": station.get("lng"),
            "geoeffnet": station.get("isOpen"),
            "preise": prices,
            "einheit": unit("EUR/Liter", origin="profil", numerator="EUR", denominator="l"),
            "zeitbezug": dict(RETRIEVAL_TIME),
            "zweck": "vorpruefung",
            "beweismittel": False,
            "lizenz_quelle": payload.get("license"),
        }
        return context.record(self.source, str(station["id"]), dict(station), normalized, locator)


def _checked_payload(payload: JSON) -> Mapping[str, JSON]:
    """The answer object; ``ok: false`` is an auth error (API key) or a parser error."""
    if not isinstance(payload, Mapping):
        raise ParserError("Antwort ist kein Objekt.")
    if not payload.get("ok"):
        message = str(payload.get("message", "API meldet Fehler"))
        if "apikey" in message.lower():
            raise AuthError(f"Tankerkönig: {message}")
        raise ParserError(f"Tankerkönig: {message}")
    return payload
