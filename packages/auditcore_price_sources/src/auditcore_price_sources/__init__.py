"""Price and market data source adapters on ``auditcore_harvest`` (contract 1).

Adapters (one bounded page per call; paging, retries, rate limits, sinks and
checkpoints are run by :class:`auditcore_harvest.HarvestEngine`):

========================================  =============================================
``price.bundesbank``                      :class:`BundesbankSeriesAdapter` (SDMX-JSON)
``price.destatis_genesis``                :class:`DestatisTableAdapter` (ffcsv)
``price.eia_brent``                       :class:`EiaSpotPriceAdapter` (API v2, API key)
``price.eu_oil_bulletin``                 :class:`PageSnapshotAdapter` (page snapshot)
``price.overpass_fuel_stations``          :class:`OverpassFuelStationAdapter` (ODbL)
``price.tankerkoenig``                    :class:`TankerkoenigListAdapter` (API key)
========================================  =============================================

Every record states unit, time reference and value status explicitly. No
network client, database, scheduler or secret store is part of the package;
the consumer injects a transport and a credential provider.
"""

from __future__ import annotations

from collections.abc import Callable

from auditcore_harvest import AdapterRegistry, SourceAdapter, deprecated_aliases

from .bundesbank import BundesbankSeriesAdapter, legacy_exchange_rate_rows, parse_sdmx_json
from .destatis import DestatisTableAdapter, parse_ffcsv
from .eia import EiaSpotPriceAdapter, legacy_commodity_rows
from .observation import MISSING, OBSERVATION_SCHEMA, PRESENT, STATION_SCHEMA, exact
from .overpass import OverpassFuelStationAdapter, fuel_query, legacy_station_fields
from .pages import PageSnapshotAdapter
from .runs import error_text, legacy_status
from .snapshots import RecordingTransport, SourceSnapshot, canonical_json_bytes, package_sha256
from .tankerkoenig import TankerkoenigListAdapter, check_list_response

__version__ = "0.1.1"
CONTRACT_VERSION = "auditcore_price_sources.contract/1"

FACTORIES: dict[str, Callable[[], SourceAdapter]] = {
    "price.bundesbank": BundesbankSeriesAdapter,
    "price.destatis_genesis": DestatisTableAdapter,
    "price.eia_brent": EiaSpotPriceAdapter,
    "price.eu_oil_bulletin": PageSnapshotAdapter,
    "price.overpass_fuel_stations": OverpassFuelStationAdapter,
    "price.tankerkoenig": TankerkoenigListAdapter,
}


__getattr__ = deprecated_aliases(
    __name__, {"DestatisTabellenAdapter": ("DestatisTableAdapter", DestatisTableAdapter)}
)


def register(registry: AdapterRegistry) -> None:
    """Register all adapters of this package explicitly."""
    for source_id, factory in FACTORIES.items():
        registry.register(source_id, factory)


__all__ = [
    "CONTRACT_VERSION",
    "FACTORIES",
    "MISSING",
    "OBSERVATION_SCHEMA",
    "PRESENT",
    "STATION_SCHEMA",
    "BundesbankSeriesAdapter",
    "DestatisTableAdapter",
    "DestatisTabellenAdapter",
    "EiaSpotPriceAdapter",
    "OverpassFuelStationAdapter",
    "PageSnapshotAdapter",
    "RecordingTransport",
    "SourceSnapshot",
    "TankerkoenigListAdapter",
    "__version__",
    "canonical_json_bytes",
    "check_list_response",
    "error_text",
    "exact",
    "fuel_query",
    "legacy_commodity_rows",
    "legacy_exchange_rate_rows",
    "legacy_station_fields",
    "legacy_status",
    "package_sha256",
    "parse_ffcsv",
    "parse_sdmx_json",
    "register",
]
