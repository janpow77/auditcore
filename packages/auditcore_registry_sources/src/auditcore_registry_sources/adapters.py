"""Source adapters for ``auditcore_harvest`` (contract ``auditcore_harvest.contract/1``).

Each adapter reads exactly one delivery (one page) of one list or register.
Retries, rate limits, time limits, deduplication, sinks and checkpoints are
run by ``auditcore_harvest.HarvestEngine``; storage, scheduling and the
delisting of vanished entries stay with the consumer.

Snapshot rule (all adapters): a delivery is a *full snapshot*. The consumer
may mark entries that are missing from it as delisted **only** if the run
result says ``snapshot_complete``. Rows without id/name, duplicate ids, a
count that differs from a reported total or an unexpectedly short page are
issues; they make the run ``partial`` so that nothing is delisted on an
incomplete delivery (the originals delisted or hard-deleted in that case).
"""

from __future__ import annotations

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
    RecordIssue,
    SnapshotSemantics,
    Source,
    canonical_hash,
    raise_for_status,
    require,
)
from auditcore_harvest import ParserError as HarvestParserError

from . import chambers
from .errors import DependencyError, FormatError
from .model import ParsedList
from .opensanctions_csv import entry_to_row, parse_targets_simple_csv
from .sanctions_xml import FORMATS as XML_FORMATS
from .sanctions_xml import xml_entries

ADAPTER_VERSION = "0.1.0"
PROFILE_VERSION = "2026.09.1"


def _url(config: Mapping[str, Any], name: str) -> str:
    value = require(config, name, str)
    if not value.startswith(("https://", "http://", "file:")):
        raise ConfigError(f"{name} muss eine http(s)- oder file:-Adresse sein.")
    return str(value)


def _get(context: FetchContext, url: str, accept: str) -> bytes:
    response = raise_for_status(
        context.transport.request("GET", url, headers={"accept": accept}, timeout=context.timeout)
    )
    return response.body


def _list_page(
    source: Source, context: FetchContext, parsed: ParsedList, url: str, as_of: str | None
) -> PageResult:
    records: list[HarvestRecord] = []
    issues = [
        RecordIssue(f"{url}#row={i.row}", f"{i.reason} (Kennung {i.entry_id or '–'})")
        for i in parsed.issues
    ]
    seen: set[str] = set()
    for entry in parsed.entries:
        if entry.entry_id in seen:
            issues.append(RecordIssue(f"{url}#id={entry.entry_id}", "Kennung mehrfach geliefert"))
            continue
        seen.add(entry.entry_id)
        raw = entry_to_row(entry)
        normalized = {**entry.to_dict(), "as_of": as_of, "content_sha256": parsed.content_sha256}
        records.append(
            HarvestRecord(
                source_id=source.source_id,
                record_id=f"{parsed.list_key}:{entry.entry_id}",
                raw=raw,
                normalized=normalized,
                provenance=context.provenance(source, f"{url}#id={entry.entry_id}", raw),
            )
        )
    return PageResult(
        records=tuple(records),
        next_cursor=None,
        complete=True,
        status=PageStatus.PARTIAL if issues else PageStatus.OK,
        issues=tuple(issues),
        total_hint=parsed.rows_seen,
    )


class OpenSanctionsListAdapter:
    """``registry.opensanctions_lists``: one ``targets.simple.csv`` list (designer/flowworkshop).

    Configuration: ``list_key`` and ``url`` (from a list catalogue profile).
    The list state (``as_of``) is taken from the ``Last-Modified`` header when
    the provider sends one; otherwise it stays ``None``.
    """

    source = Source(
        source_id="registry.opensanctions_lists",
        title="Sanktions-/PEP-Listen im OpenSanctions-Format targets.simple.csv",
        family="registry",
        adapter_version=ADAPTER_VERSION,
        profile_version=PROFILE_VERSION,
        data_format="text/csv",
        auth=AuthKind.NONE,
        capabilities=Capabilities(
            pagination=False, incremental=False, full_snapshot=True, deletions=True
        ),
        snapshot_semantics=SnapshotSemantics.FULL_SNAPSHOT_REPLACE,
    )

    def validate_config(self, config: Mapping[str, Any]) -> None:
        """``list_key`` (text) and ``url``."""
        if not require(config, "list_key", str).strip():
            raise ConfigError("list_key darf nicht leer sein.")
        _url(config, "url")

    def fetch_page(self, context: FetchContext, cursor: Mapping[str, Any] | None) -> PageResult:
        """Download and parse the whole list."""
        url = _url(context.config, "url")
        response = raise_for_status(
            context.transport.request(
                "GET", url, headers={"accept": "text/csv"}, timeout=context.timeout
            )
        )
        try:
            parsed = parse_targets_simple_csv(response.body, list_key=context.config["list_key"])
        except FormatError as exc:
            raise HarvestParserError(str(exc)) from exc
        return _list_page(self.source, context, parsed, url, response.header("Last-Modified"))


class OfficialSanctionsXmlAdapter:
    """``registry.official_sanctions_xml``: EU FSF, OFAC SDN or UN list as published XML.

    Configuration: ``list_key``, ``url`` and ``format`` (``eu_fsf_xml``,
    ``ofac_sdn_xml``, ``un_sc_xml``). Needs the extra ``xml``.
    """

    source = Source(
        source_id="registry.official_sanctions_xml",
        title="Amtliche Sanktionslisten (EU FSF, OFAC SDN, UN) im XML-Original",
        family="registry",
        adapter_version=ADAPTER_VERSION,
        profile_version=PROFILE_VERSION,
        data_format="application/xml",
        auth=AuthKind.NONE,
        capabilities=Capabilities(
            pagination=False, incremental=False, full_snapshot=True, deletions=True
        ),
        snapshot_semantics=SnapshotSemantics.FULL_SNAPSHOT_REPLACE,
    )

    def validate_config(self, config: Mapping[str, Any]) -> None:
        """``list_key``, ``url`` and a known ``format``."""
        if not require(config, "list_key", str).strip():
            raise ConfigError("list_key darf nicht leer sein.")
        _url(config, "url")
        if require(config, "format", str) not in XML_FORMATS:
            raise ConfigError(f"format muss eines von {', '.join(XML_FORMATS)} sein.")

    def fetch_page(self, context: FetchContext, cursor: Mapping[str, Any] | None) -> PageResult:
        """Download and parse the whole list."""
        url = _url(context.config, "url")
        response = raise_for_status(
            context.transport.request(
                "GET", url, headers={"accept": "application/xml"}, timeout=context.timeout
            )
        )
        try:
            parsed = xml_entries(
                response.body, format=context.config["format"], list_key=context.config["list_key"]
            )
        except DependencyError as exc:
            raise ConfigError(str(exc)) from exc
        except FormatError as exc:
            raise HarvestParserError(str(exc)) from exc
        return _list_page(self.source, context, parsed, url, response.header("Last-Modified"))


def _address_page(
    source: Source,
    context: FetchContext,
    delivery: chambers.AddressDelivery,
    locator: str,
    key_fields: tuple[str, ...],
) -> PageResult:
    records = []
    issues = [RecordIssue(locator, text) for text in delivery.issues]
    seen: set[str] = set()
    for record in delivery.records:
        identity = canonical_hash({k: record.get(k) for k in key_fields})
        if identity in seen:
            continue
        seen.add(identity)
        records.append(
            HarvestRecord(
                source_id=source.source_id,
                record_id=identity,
                raw=record,
                normalized=record,
                provenance=context.provenance(source, locator, record),
            )
        )
    return PageResult(
        records=tuple(records),
        next_cursor=None,
        complete=True,
        status=PageStatus.PARTIAL if issues else PageStatus.OK,
        issues=tuple(issues),
        total_hint=delivery.rows_seen,
    )


class ZerRegisterAdapter:
    """``registry.zer``: Zuwendungsempfängerregister (§ 60b AO), full dump.

    The register has no stable id in the reduced record; identity is the
    content hash of name and address. The status endpoint's total is
    compared with the delivered rows.
    """

    source = Source(
        source_id="registry.zer",
        title="Zuwendungsempfängerregister des BZSt (§ 60b AO)",
        family="registry",
        adapter_version=ADAPTER_VERSION,
        profile_version=PROFILE_VERSION,
        data_format="application/json",
        auth=AuthKind.NONE,
        capabilities=Capabilities(
            pagination=False, incremental=False, full_snapshot=True, deletions=True
        ),
        snapshot_semantics=SnapshotSemantics.FULL_SNAPSHOT_REPLACE,
    )

    def validate_config(self, config: Mapping[str, Any]) -> None:
        """``register_url`` and ``status_url``."""
        _url(config, "register_url")
        _url(config, "status_url")

    def fetch_page(self, context: FetchContext, cursor: Mapping[str, Any] | None) -> PageResult:
        """Status first, then the dump."""
        try:
            total = chambers.parse_zer_status(
                _get(context, _url(context.config, "status_url"), "application/json")
            )
            url = _url(context.config, "register_url")
            delivery = chambers.parse_zer_register(
                _get(context, url, "application/json"), reported_total=total
            )
        except FormatError as exc:
            raise HarvestParserError(str(exc)) from exc
        return _address_page(
            self.source, context, delivery, url, ("name", "plz", "ort", "strasse", "hnr")
        )


class IhkLocationsAdapter:
    """``registry.ihk``: chambers of industry and commerce with coordinates."""

    source = Source(
        source_id="registry.ihk",
        title="Industrie- und Handelskammern (DIHK-App-Service)",
        family="registry",
        adapter_version=ADAPTER_VERSION,
        profile_version=PROFILE_VERSION,
        data_format="application/json",
        auth=AuthKind.NONE,
        capabilities=Capabilities(
            pagination=False, incremental=False, full_snapshot=True, deletions=True
        ),
        snapshot_semantics=SnapshotSemantics.FULL_SNAPSHOT_REPLACE,
    )

    def validate_config(self, config: Mapping[str, Any]) -> None:
        """``url``."""
        _url(config, "url")

    def fetch_page(self, context: FetchContext, cursor: Mapping[str, Any] | None) -> PageResult:
        """One request, all chambers."""
        url = _url(context.config, "url")
        try:
            delivery = chambers.parse_ihk_locations(_get(context, url, "application/json"))
        except FormatError as exc:
            raise HarvestParserError(str(exc)) from exc
        if not delivery.records:
            raise HarvestParserError("Die Antwort enthält keine Kammer.")
        return _address_page(self.source, context, delivery, url, ("name", "plz"))


class HwkPageAdapter:
    """``registry.hwk``: chambers of crafts from the ZDH address page (extra ``html``).

    ``expected`` (default 53) is the number of chambers the source expects;
    fewer is an issue.
    """

    source = Source(
        source_id="registry.hwk",
        title="Handwerkskammern (Adressseite des ZDH)",
        family="registry",
        adapter_version=ADAPTER_VERSION,
        profile_version=PROFILE_VERSION,
        data_format="text/html",
        auth=AuthKind.NONE,
        capabilities=Capabilities(
            pagination=False, incremental=False, full_snapshot=True, deletions=True
        ),
        snapshot_semantics=SnapshotSemantics.FULL_SNAPSHOT_REPLACE,
    )

    def validate_config(self, config: Mapping[str, Any]) -> None:
        """``url`` and optional ``expected`` (positive integer)."""
        _url(config, "url")
        expected = config.get("expected", chambers.EXPECTED_HWK)
        if not isinstance(expected, int) or isinstance(expected, bool) or expected < 1:
            raise ConfigError("expected muss eine positive ganze Zahl sein.")

    def fetch_page(self, context: FetchContext, cursor: Mapping[str, Any] | None) -> PageResult:
        """One page, all chambers found by the text pattern."""
        url = _url(context.config, "url")
        try:
            delivery = chambers.parse_hwk_page(
                _get(context, url, "text/html"),
                expected=int(context.config.get("expected", chambers.EXPECTED_HWK)),
            )
        except DependencyError as exc:
            raise ConfigError(str(exc)) from exc
        if not delivery.records:
            raise HarvestParserError("Auf der Seite wurde keine Handwerkskammer erkannt.")
        return _address_page(self.source, context, delivery, url, ("name", "plz"))


ADAPTERS = (
    OpenSanctionsListAdapter,
    OfficialSanctionsXmlAdapter,
    ZerRegisterAdapter,
    IhkLocationsAdapter,
    HwkPageAdapter,
)
