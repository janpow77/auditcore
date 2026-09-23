"""Deutsche Bundesbank time series (SDMX-JSON), e.g. the ECB reference rate USD per EUR.

Source behavior characterized from regulierung ``external_apis/bundesbank.py``:
``GET {url}/data/{flow_ref}/{series_key}?format=json&lastNObservations=N``
with ``Accept: application/json``. Values are text such as ``"1.1490"``; the
unit comes from the series attributes (``BBK_UNIT``, ``BBK_UNIT_MULT``) and
the key dimensions (currency and partner currency). For ``BBEX3.D.USD.EUR…``
a value means *USD per 1 EUR*.

Unlike the original, missing observations (``null``) are delivered with
status ``fehlwert`` and unreadable ones are reported as issues instead of
being skipped silently.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
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

from .observation import exact, observation, unit

ADAPTER_VERSION = "1.0.0"
PROFILE_VERSION = "2026.09.1"
DEFAULT_FLOW_REF = "BBEX3"
DEFAULT_SERIES_KEY = "D.USD.EUR.BB.AC.000"


@dataclass(frozen=True)
class SdmxObservation:
    """One parsed observation (value ``None`` = missing in the source)."""

    period: str
    value: str | None
    status: str | None


@dataclass(frozen=True)
class SdmxSeries:
    """Parsed series with unit metadata and per-item issues."""

    series_id: str
    unit: dict[str, Any]
    title: str | None
    observations: tuple[SdmxObservation, ...]
    issues: tuple[RecordIssue, ...]


def _attribute(structure: Mapping[str, Any], level: str, indexes: list[Any]) -> dict[str, Any]:
    """Resolve SDMX attribute indexes to ``{id: name}``."""
    found: dict[str, Any] = {}
    definitions = structure.get("attributes", {}).get(level, [])
    for position, definition in enumerate(definitions):
        if position >= len(indexes) or indexes[position] is None:
            continue
        values = definition.get("values", [])
        index = indexes[position]
        if isinstance(index, int) and 0 <= index < len(values) and values[index]:
            found[str(definition.get("id"))] = values[index].get("name", values[index].get("id"))
    return found


def _int_or_none(value: Any) -> int | None:
    text = str(value if value is not None else "")
    return int(text) if text.lstrip("-").isdigit() else None


def parse_sdmx_json(payload: Any, *, series_hint: str) -> list[SdmxSeries]:
    """Parse an SDMX-JSON data message; structural problems raise ``ParserError``."""
    if not isinstance(payload, Mapping) or not isinstance(payload.get("data"), Mapping):
        raise ParserError("SDMX-JSON ohne data-Block.")
    data = payload["data"]
    structure = data.get("structure", {})
    datasets = data.get("dataSets")
    if not isinstance(datasets, list):
        raise ParserError("SDMX-JSON ohne dataSets-Liste.")
    dimensions = structure.get("dimensions", {})
    obs_dims = dimensions.get("observation", [])
    periods = [v.get("id") for v in obs_dims[0].get("values", [])] if obs_dims else []
    series_dims = dimensions.get("series", [])
    result: list[SdmxSeries] = []
    for dataset in datasets:
        for key, series in (dataset.get("series") or {}).items():
            positions = [int(p) for p in str(key).split(":") if p.isdigit()]
            dims: dict[str, str] = {}
            for position, dim in zip(positions, series_dims, strict=False):
                values = dim.get("values", [])
                if 0 <= position < len(values):
                    dims[str(dim.get("id"))] = str(values[position].get("id"))
            attrs = _attribute(structure, "series", list(series.get("attributes", [])))
            series_id = str(attrs.get("BBK_ID") or series_hint)
            numerator = attrs.get("BBK_UNIT") or dims.get("BBK_STD_CURRENCY")
            denominator = dims.get("BBK_ERX_PARTNER_CURRENCY")
            multiplier = attrs.get("BBK_UNIT_MULT")
            text = (
                f"{numerator} je 1 {denominator}"
                if numerator and denominator
                else (str(numerator) if numerator else None)
            )
            unit_block = unit(
                text,
                source_text=attrs.get("BBK_TITLE"),
                origin="quelle" if numerator else "unbekannt",
                numerator=numerator,
                denominator=denominator,
                multiplier=_int_or_none(multiplier),
            )
            observations: list[SdmxObservation] = []
            issues: list[RecordIssue] = []
            for index_text, item in (series.get("observations") or {}).items():
                locator = f"{series_id}#{index_text}"
                if not str(index_text).isdigit() or int(index_text) >= len(periods):
                    issues.append(RecordIssue(locator, "Beobachtung ohne Zeitangabe (Index)"))
                    continue
                period = periods[int(index_text)]
                if not period or not isinstance(item, list) or not item:
                    issues.append(RecordIssue(locator, "Beobachtung ohne Datum oder Wertliste"))
                    continue
                try:
                    date.fromisoformat(str(period))
                except ValueError:
                    issues.append(RecordIssue(locator, f"Zeitangabe {period!r} ist kein Tag"))
                    continue
                obs_attrs = _attribute(structure, "observation", list(item[1:]))
                raw_value = item[0]
                if raw_value is not None:
                    try:
                        exact(raw_value)
                    except ValueError as exc:
                        issues.append(RecordIssue(locator, f"Wert nicht lesbar: {exc}"))
                        continue
                observations.append(
                    SdmxObservation(
                        str(period),
                        None if raw_value is None else str(raw_value),
                        obs_attrs.get("OBS_STATUS"),
                    )
                )
            result.append(
                SdmxSeries(
                    series_id,
                    unit_block,
                    attrs.get("BBK_TITLE"),
                    tuple(observations),
                    tuple(issues),
                )
            )
    return result


class BundesbankSeriesAdapter:
    """``price.bundesbank``: one Bundesbank series, last *N* daily observations (one page)."""

    source = Source(
        source_id="price.bundesbank",
        title="Deutsche Bundesbank Zeitreihen (SDMX-JSON), Vorgabe EZB-Referenzkurs USD je EUR",
        family="price",
        adapter_version=ADAPTER_VERSION,
        profile_version=PROFILE_VERSION,
        data_format="application/json (SDMX-JSON 1.0)",
        auth=AuthKind.NONE,
        capabilities=Capabilities(
            pagination=False, incremental=False, full_snapshot=False, deletions=False
        ),
        snapshot_semantics=SnapshotSemantics.APPEND_ONLY,
        filters=("flow_ref", "series_key", "last_n_observations"),
    )

    def validate_config(self, config: Mapping[str, Any]) -> None:
        """``url`` (REST base), optional ``flow_ref``, ``series_key``, ``last_n_observations``."""
        if not isinstance(config.get("url"), str) or not config["url"].startswith("http"):
            raise ConfigError("url (REST-Basisadresse) fehlt.")
        last = config.get("last_n_observations", 30)
        if not isinstance(last, int) or isinstance(last, bool) or not 1 <= last <= 1000:
            raise ConfigError("last_n_observations muss 1 bis 1000 sein.")
        for key in ("flow_ref", "series_key"):
            value = config.get(key, "x")
            if not isinstance(value, str) or not value or "/" in value:
                raise ConfigError(f"{key} ist ungültig.")

    def fetch_page(self, context: FetchContext, cursor: Mapping[str, Any] | None) -> PageResult:
        """Fetch the series once and deliver every observation as a record."""
        filters = dict(context.request.filters or {})
        flow = str(filters.get("flow_ref") or context.config.get("flow_ref", DEFAULT_FLOW_REF))
        key = str(filters.get("series_key") or context.config.get("series_key", DEFAULT_SERIES_KEY))
        last = int(
            filters.get("last_n_observations") or context.config.get("last_n_observations", 30)
        )
        url = f"{str(context.config['url']).rstrip('/')}/data/{flow}/{key}"
        response = raise_for_status(
            context.transport.request(
                "GET",
                url,
                params={"format": "json", "lastNObservations": str(last)},
                headers={"Accept": "application/json"},
                timeout=context.timeout,
            )
        )
        try:
            payload = json.loads(response.body)
        except ValueError as exc:
            raise ParserError("Antwort ist kein gültiges JSON.") from exc
        series_list = parse_sdmx_json(payload, series_hint=f"{flow}.{key}")
        records: list[HarvestRecord] = []
        issues: list[RecordIssue] = []
        for series in series_list:
            issues.extend(series.issues)
            for item in series.observations:
                normalized = observation(
                    series=series.series_id,
                    time_kind="tag",
                    period=item.period,
                    value=exact(item.value),
                    unit_block=series.unit,
                    source_status=item.status,
                    extra={"titel": series.title},
                )
                raw = {
                    "reihe": series.series_id,
                    "zeit": item.period,
                    "wert": item.value,
                    "status": item.status,
                }
                records.append(
                    HarvestRecord(
                        source_id=self.source.source_id,
                        record_id=f"{series.series_id}@{item.period}",
                        raw=raw,
                        normalized=normalized,
                        provenance=context.provenance(self.source, url, raw),
                    )
                )
        if not series_list or not any(s.observations for s in series_list):
            issues.append(RecordIssue(url, "Antwort enthält keine Beobachtungen"))
        status = PageStatus.PARTIAL if issues else PageStatus.OK
        return PageResult(tuple(records), None, complete=True, status=status, issues=tuple(issues))


def legacy_exchange_rate_rows(records: list[HarvestRecord]) -> list[dict[str, Any]]:
    """Rows as regulierung's ``Wechselkurs`` (only present values; missing ones are skipped).

    ``waehrung_basis``/``waehrung_kurs`` keep the original naming (USD/EUR);
    the value means USD per 1 EUR (see the record's ``einheit``).
    """
    rows = []
    for record in records:
        data = record.normalized
        if data.get("wert") is None:
            continue
        unit_block = data.get("einheit") or {}
        rows.append(
            {
                "waehrung_basis": unit_block.get("zaehler") or "USD",
                "waehrung_kurs": unit_block.get("nenner") or "EUR",
                "stichtag": date.fromisoformat(str(data["zeitbezug"]["wert"])),
                "kurs": exact(data["wert"]),
                "quelle": "BUNDESBANK",
            }
        )
    return rows
