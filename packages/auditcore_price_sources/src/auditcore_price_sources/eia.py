"""U.S. EIA API v2 spot prices (default: Brent, product ``EPCBRENT``, daily).

Characterized from regulierung ``external_apis/eia_brent.py``: ``GET
{url}/petroleum/pri/spt/data/`` with ``api_key``, ``frequency=daily``,
``data[0]=value``, ``facets[product][]``, ``start``/``end`` (30 days up to
today), sort by period descending, ``length=5000``. The original read one
page, hard-coded the unit ``USD/Barrel`` and skipped empty values silently.

Here the window is explicit (request filters or ``window_days`` relative to
the engine clock), pages follow ``offset``/``response.total``, the unit comes
from the row (``units``) with the profile unit only as a marked fallback, and
empty values are delivered as ``fehlwert``.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import date, timedelta
from typing import Any

from auditcore_harvest import (
    JSON,
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
    page_result,
    raise_for_status,
)

from .observation import exact, observation, unit

ADAPTER_VERSION = "1.0.0"
PROFILE_VERSION = "2026.09.1"
DEFAULT_PRODUCT = "EPCBRENT"
PROFILE_UNIT = "USD/Barrel"
#: explicit mapping of EIA unit codes; unknown codes stay as source text
UNITS = {"$/BBL": "USD/Barrel", "$/GAL": "USD/Gallone"}
MAX_PAGE = 5000


def _window(context: FetchContext) -> tuple[str, str]:
    filters = dict(context.request.filters or {})
    end = filters.get("end") or context.clock.now().date().isoformat()
    days = int(context.config.get("window_days", 30))
    start = (
        filters.get("start") or (date.fromisoformat(str(end)) - timedelta(days=days)).isoformat()
    )
    return str(start), str(end)


class EiaSpotPriceAdapter:
    """``price.eia_brent``: EIA v2 daily spot prices of one product with offset paging."""

    source = Source(
        source_id="price.eia_brent",
        title="U.S. EIA API v2 – Spotpreis Brent (täglich)",
        family="price",
        adapter_version=ADAPTER_VERSION,
        profile_version=PROFILE_VERSION,
        data_format="application/json (EIA API v2)",
        auth=AuthKind.API_KEY,
        capabilities=Capabilities(
            pagination=True, incremental=False, full_snapshot=False, deletions=False
        ),
        snapshot_semantics=SnapshotSemantics.APPEND_ONLY,
        filters=("start", "end", "product"),
    )

    def validate_config(self, config: Mapping[str, JSON]) -> None:
        """``url`` (API v2 base), optional ``product``, ``window_days`` 1..366, ``page_size``."""
        if not isinstance(config.get("url"), str) or not config["url"].startswith("http"):
            raise ConfigError("url (API-v2-Basisadresse) fehlt.")
        days = config.get("window_days", 30)
        if not isinstance(days, int) or isinstance(days, bool) or not 1 <= days <= 366:
            raise ConfigError("window_days muss 1 bis 366 sein.")
        size = config.get("page_size", MAX_PAGE)
        if not isinstance(size, int) or isinstance(size, bool) or not 1 <= size <= MAX_PAGE:
            raise ConfigError(f"page_size muss 1 bis {MAX_PAGE} sein.")
        if not isinstance(config.get("product", DEFAULT_PRODUCT), str):
            raise ConfigError("product muss ein EIA-Produktcode sein.")

    def fetch_page(self, context: FetchContext, cursor: Cursor | None) -> PageResult:
        """One page of rows; the cursor carries offset and the fixed window."""
        filters = dict(context.request.filters or {})
        if cursor:
            start, end = str(cursor["start"]), str(cursor["end"])
        else:
            start, end = _window(context)
        offset = int((cursor or {}).get("offset", 0))
        size = int(context.config.get("page_size", MAX_PAGE))
        product = str(filters.get("product") or context.config.get("product", DEFAULT_PRODUCT))
        url = f"{str(context.config['url']).rstrip('/')}/petroleum/pri/spt/data/"
        params = {
            "api_key": context.secret(self.source.source_id, "api_key"),
            "frequency": "daily",
            "data[0]": "value",
            "facets[product][]": product,
            "start": start,
            "end": end,
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "offset": str(offset),
            "length": str(size),
        }
        response = raise_for_status(
            context.transport.request("GET", url, params=params, timeout=context.timeout)
        )
        rows, total = _rows(response.body)
        records: list[HarvestRecord] = []
        issues: list[RecordIssue] = []
        for position, row in enumerate(rows):
            item = self._row(context, f"{url}?offset={offset}#{position}", row, product)
            if isinstance(item, RecordIssue):
                issues.append(item)
            else:
                records.append(item)
        read = offset + len(rows)
        more = read < total
        if more and not rows:
            raise ParserError("EIA meldet weitere Zeilen, liefert aber keine.")
        next_cursor = {"offset": read, "start": start, "end": end} if more else None
        return page_result(records, issues, next_cursor, total_hint=total)

    def _row(
        self, context: FetchContext, locator: str, row: JSON, product: str
    ) -> HarvestRecord | RecordIssue:
        """Record of one data row, or the issue why the row is unreadable."""
        if not isinstance(row, Mapping):
            return RecordIssue(locator, "Zeile ist kein Objekt")
        period = row.get("period")
        try:
            date.fromisoformat(str(period))
            value = exact(row.get("value"))
        except ValueError as exc:
            return RecordIssue(locator, f"Zeile nicht lesbar: {exc}")
        source_unit = row.get("units")
        unit_block = unit(
            UNITS.get(str(source_unit), str(source_unit)) if source_unit else PROFILE_UNIT,
            source_text=None if source_unit is None else str(source_unit),
            origin="quelle" if source_unit else "profil",
            numerator="USD",
        )
        series = str(row.get("series") or row.get("product") or product)
        normalized = observation(
            series=series,
            time_kind="handelstag",
            period=str(period),
            value=value,
            unit_block=unit_block,
            extra={
                "produkt": row.get("product"),
                "beschreibung": row.get("series-description"),
            },
        )
        return context.record(self.source, f"{series}@{period}", dict(row), normalized, locator)


def _rows(body: bytes) -> tuple[list[JSON], int]:
    """``response.data`` and ``response.total`` of an EIA answer, else a parser error."""
    try:
        payload = json.loads(body)
        response = payload["response"]
        rows = response["data"]
        total = int(response.get("total", len(rows)))
    except (ValueError, KeyError, TypeError) as exc:
        raise ParserError("EIA-Antwort ohne response.data/total.") from exc
    if not isinstance(rows, list):
        raise ParserError("response.data ist keine Liste.")
    return rows, total


def legacy_commodity_rows(
    records: list[HarvestRecord], *, commodity: str = "BRENT"
) -> list[dict[str, Any]]:
    """Rows as regulierung's ``Rohstoffpreis`` (present values only, legacy constants)."""
    rows = []
    for record in records:
        data = record.normalized
        if data.get("wert") is None:
            continue
        rows.append(
            {
                "rohstoff": commodity,
                "stichtag": date.fromisoformat(str(data["zeitbezug"]["wert"])),
                "preis_usd": exact(data["wert"]),
                "einheit": (data.get("einheit") or {}).get("text") or PROFILE_UNIT,
                "quelle": "EIA",
            }
        )
    return rows
