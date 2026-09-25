"""Source adapters for ``auditcore_harvest`` (contract ``auditcore_harvest.contract/1``).

Each adapter translates exactly one page of one source into harvest records.
Paging order, retries, rate limits, time limits, deduplication, sinks and
checkpoints are run by ``auditcore_harvest.HarvestEngine``. Inventory rules
stay explicit: a de-minimis run is only a complete snapshot when the register
total was reached (source rule), and the flowworkshop modes are planned by
:mod:`auditcore_funding_sources.snapshot`, not by a parser option.
"""

from __future__ import annotations

import json
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
    require,
)

from . import __version__, deminimis, flowsearch, workshop
from ._jsonsafe import json_safe, json_safe_mapping
from .errors import FundingSourceError
from .workshop import SnapshotContext

ADAPTER_VERSION = __version__
PROFILE_VERSION = "2026.09.1"


class DeMinimisRegisterAdapter:
    """``funding.de_minimis_eaid``: awards of one country from the public eAidRegister.

    Cursor ``{"page": n, "reported": total, "seen": count}``. The register total
    is requested with the first page only. A run ends as a complete snapshot
    only if the pages read reach the reported total; an empty page before
    that, or an unknown total, is reported as issue (``partial``) so that no
    consumer marks awards as vanished (source rule of ``de_minimis_ernte``).
    """

    source = Source(
        source_id="funding.de_minimis_eaid",
        title="Zentrales De-minimis-Register der Kommission (eAidRegister)",
        family="funding",
        adapter_version=ADAPTER_VERSION,
        profile_version=PROFILE_VERSION,
        data_format="application/json",
        auth=AuthKind.NONE,
        capabilities=Capabilities(
            pagination=True, incremental=False, full_snapshot=True, deletions=False
        ),
        snapshot_semantics=SnapshotSemantics.FULL_SNAPSHOT_REPLACE,
        filters=("country", "granting_date_from", "granting_date_to", "de_minimis_type"),
    )

    def validate_config(self, config: Mapping[str, Any]) -> None:
        """``country`` (ISO-2/3 or ``CountryXXX``), optional ``page_size`` 1..500."""
        country = config.get("country", "DE")
        if not isinstance(country, str) or not country.strip():
            raise ConfigError("country muss ein Länderkürzel sein.")
        size = config.get("page_size", deminimis.PAGE_SIZE)
        if not isinstance(size, int) or isinstance(size, bool) or not 1 <= size <= 500:
            raise ConfigError("page_size muss eine ganze Zahl von 1 bis 500 sein.")

    def _criteria(self, context: FetchContext, page: int) -> deminimis.SearchCriteria:
        filters = dict(context.request.filters or {})
        size = int(context.config.get("page_size", deminimis.PAGE_SIZE))
        kind = filters.get("de_minimis_type")
        return deminimis.SearchCriteria(
            country=deminimis.country_code(
                str(filters.get("country") or context.config.get("country", "DE"))
            ),
            grantingDateFrom=filters.get("granting_date_from"),
            grantingDateTo=filters.get("granting_date_to"),
            deMinimisTypes=[str(kind).upper()] if kind else None,
            pageNumber=page,
            pageSize=size,
        )

    def _post(self, context: FetchContext, request: deminimis.Request) -> Any:
        response = raise_for_status(
            context.transport.request(
                request.method,
                request.url,
                headers={"accept": "application/json", "content-type": "application/json"},
                data=json.dumps(request.json, ensure_ascii=False, sort_keys=True).encode("utf-8"),
                timeout=context.timeout,
            )
        )
        try:
            return json.loads(response.body)
        except ValueError as exc:
            raise ParserError("Antwort des Registers ist kein JSON.") from exc

    def fetch_page(self, context: FetchContext, cursor: Mapping[str, Any] | None) -> PageResult:
        """One register page; the total is requested once with the first page."""
        page = int(cursor["page"]) if cursor else 0
        reported = cursor.get("reported") if cursor else None
        seen = int(cursor.get("seen", 0)) if cursor else 0
        criteria = self._criteria(context, page)
        try:
            awards = deminimis.parse_award_list(
                self._post(context, deminimis.search_request(criteria))
            )
        except deminimis.RegisterResponseError as exc:
            raise ParserError(str(exc)) from exc
        if cursor is None:
            reported = deminimis.parse_count(self._post(context, deminimis.count_request(criteria)))
        records, issues = self._records(context, page, awards)
        seen += len(records)
        return _register_page(
            records,
            issues,
            page=page,
            awards=len(awards),
            size=criteria.pageSize,
            reported=reported,
            seen=seen,
        )

    def _records(
        self, context: FetchContext, page: int, awards: list[dict[str, Any]]
    ) -> tuple[list[HarvestRecord], list[RecordIssue]]:
        records: list[HarvestRecord] = []
        issues: list[RecordIssue] = []
        for position, award in enumerate(awards):
            reference = award.get("referenceNumber")
            locator = f"page/{page}/{position}"
            if not reference:
                issues.append(
                    RecordIssue(locator, "Meldung ohne referenceNumber; nicht übernommen.")
                )
                continue
            fields = deminimis.harvest_fields(award)
            fields.pop("raw_payload")
            normalized = {**json_safe_mapping(fields), "record_hash": deminimis.record_hash(award)}
            records.append(
                HarvestRecord(
                    source_id=self.source.source_id,
                    record_id=str(reference),
                    raw=json_safe(award),
                    normalized=normalized,
                    provenance=context.provenance(self.source, locator, json_safe(award)),
                )
            )
        return records, issues


_UNKNOWN_TOTAL = "Gesamtzahl des Registers unbekannt; Vollständigkeit nicht belegt."


def _register_page(
    records: list[HarvestRecord],
    issues: list[RecordIssue],
    *,
    page: int,
    awards: int,
    size: int,
    reported: int | None,
    seen: int,
) -> PageResult:
    """Page result and cursor; completeness only when the reported total is reached."""
    if not awards:
        if reported is None:
            issues.append(RecordIssue(f"page/{page}", _UNKNOWN_TOTAL))
        elif seen < int(reported):
            issues.append(
                RecordIssue(
                    f"page/{page}", f"Register meldete {reported} Sätze, gelesen wurden {seen}."
                )
            )
        return _final_page((), issues, reported)
    if reported is not None and seen >= int(reported):
        return _final_page(tuple(records), issues, reported)
    if reported is None and awards < size:
        issues.append(RecordIssue(f"page/{page}", _UNKNOWN_TOTAL))
        return PageResult(tuple(records), None, True, PageStatus.PARTIAL, tuple(issues), None)
    return PageResult(
        tuple(records),
        {"page": page + 1, "reported": reported, "seen": seen},
        False,
        _status(issues),
        tuple(issues),
        reported,
    )


def _status(issues: list[RecordIssue]) -> PageStatus:
    return PageStatus.PARTIAL if issues else PageStatus.OK


def _final_page(
    records: tuple[HarvestRecord, ...], issues: list[RecordIssue], total: int | None
) -> PageResult:
    """Last page of a run: no cursor, status from the issues."""
    return PageResult(records, None, True, _status(issues), tuple(issues), total)


class _FileAdapter:
    """Shared download step: one configured file, read through the injected transport."""

    source: Source

    def _download(self, context: FetchContext) -> bytes:
        response = raise_for_status(
            context.transport.request("GET", str(context.config["url"]), timeout=context.timeout)
        )
        return response.body


class WorkshopBeneficiaryAdapter(_FileAdapter):
    """``funding.eu_beneficiaries`` with the ``flowworkshop.beneficiaries`` profile.

    One page per file. Identity is ``compute_record_hash`` of the source; rows
    without beneficiary name become issues (the source counted them as
    ``failed``). Snapshot validation errors abort the run as parser error so a
    consumer never replaces its inventory with a rejected file.
    """

    source = Source(
        source_id="funding.eu_beneficiaries",
        title="Listen der Vorhaben (Transparenzlisten) — Profil flowworkshop",
        family="funding",
        adapter_version=ADAPTER_VERSION,
        profile_version=PROFILE_VERSION,
        data_format="text/csv; application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        auth=AuthKind.NONE,
        capabilities=Capabilities(
            pagination=False, incremental=False, full_snapshot=True, deletions=False
        ),
        snapshot_semantics=SnapshotSemantics.FULL_SNAPSHOT_REPLACE,
        filters=(),
    )

    def validate_config(self, config: Mapping[str, Any]) -> None:
        """``url``, ``file_name``, ``source_key`` and the snapshot context are required."""
        for name in ("url", "file_name", "source_key", "fonds", "periode", "country_code"):
            require(config, name, str)
        if config.get("typing", "legacy") not in ("legacy", "text"):
            raise ConfigError("typing muss legacy oder text sein.")
        if config.get("header_detection", "legacy") not in ("legacy", "strict"):
            raise ConfigError("header_detection muss legacy oder strict sein.")

    def fetch_page(self, context: FetchContext, cursor: Mapping[str, Any] | None) -> PageResult:
        """Download, parse, validate and translate the whole file."""
        config = context.config
        content = self._download(context)
        try:
            rows = workshop.parse_file(
                content,
                str(config["file_name"]),
                sheet=config.get("sheet"),
                header_row=int(config.get("header_row", 0)),
                field_mapping=config.get("field_mapping"),
                typing=str(config.get("typing", "legacy")),
                header_detection=str(config.get("header_detection", "legacy")),
            )
        except (FundingSourceError, ValueError) as exc:
            raise ParserError(f"Datei nicht lesbar: {exc}") from exc
        snapshot = SnapshotContext(
            source_key=str(config["source_key"]),
            bundesland=config.get("bundesland"),
            fonds=str(config["fonds"]),
            periode=str(config["periode"]),
            country_code=str(config["country_code"]),
        )
        rows, _removed = workshop.filter_by_fund(rows, snapshot.fonds)
        if not [r for r in rows if not r.get("_skip_reason")]:
            raise ParserError("Keine valide Begünstigtenzeile bzw. keine Namensspalte erkannt.")
        errors = workshop.validate_rows(rows, snapshot)
        if errors:
            raise ParserError("Snapshot abgewiesen: " + " ".join(errors[:8]))
        records: dict[str, HarvestRecord] = {}
        issues: list[RecordIssue] = []
        for row in rows:
            locator = f"row/{row.get('_row_number')}"
            if row.get("_skip_reason"):
                issues.append(
                    RecordIssue(locator, "Zeile ohne Begünstigtennamen (Summen-/Leerzeile?).")
                )
                continue
            identity = workshop.compute_record_hash(row, snapshot.source_key)
            if identity in records:
                issues.append(
                    RecordIssue(locator, "Zeile mit bereits vorhandener Kennung übersprungen.")
                )
                continue
            normalized = json_safe_mapping(workshop.harvest_values(row))
            raw = json_safe(row.get("raw_row") or {})
            records[identity] = HarvestRecord(
                source_id=self.source.source_id,
                record_id=identity,
                raw=raw,
                normalized=normalized,
                provenance=context.provenance(self.source, locator, raw),
            )
        return _final_page(tuple(records.values()), issues, len(records))


class FlowsearchBeneficiaryAdapter(_FileAdapter):
    """``funding.eu_beneficiaries.flowsearch``: the separate flowsearch variant.

    Column mapping per source key (``mapping`` in the configuration, as in
    ``bundesland_mappings.json``), identity ``project_id`` (MD5, 16 hex).
    Amounts that the variant defaults to ``0.0`` are listed in
    ``normalized["defaulted"]`` instead of being hidden.
    """

    source = Source(
        source_id="funding.eu_beneficiaries.flowsearch",
        title="Listen der Vorhaben — Profil flowsearch (EUBeneficiaryHarvesterV2)",
        family="funding",
        adapter_version=ADAPTER_VERSION,
        profile_version=PROFILE_VERSION,
        data_format=(
            "text/csv; application/vnd.openxmlformats-officedocument.spreadsheetml.sheet; "
            "application/zip"
        ),
        auth=AuthKind.NONE,
        capabilities=Capabilities(
            pagination=False, incremental=None, full_snapshot=None, deletions=False
        ),
        snapshot_semantics=SnapshotSemantics.INCREMENTAL_UPSERT,
        filters=(),
    )

    def validate_config(self, config: Mapping[str, Any]) -> None:
        """``url``, ``source`` (key, bundesland, fonds) and ``mapping`` are required."""
        require(config, "url", str)
        source = require(config, "source", dict)
        for name in ("source_key", "bundesland", "fonds"):
            require(source, name, str)
        require(config, "mapping", dict)

    def fetch_page(self, context: FetchContext, cursor: Mapping[str, Any] | None) -> PageResult:
        """Download (unzip), parse with the mapping and translate every record."""
        config = context.config
        url = str(config["url"])
        source = dict(config["source"])
        mapping = dict(config["mapping"])
        mappings = {source["source_key"]: mapping, **dict(config.get("fallback") or {})}
        content = self._download(context)
        try:
            items = flowsearch.read_items(content, url, source, mapping)
        except (FundingSourceError, ValueError, KeyError) as exc:
            raise ParserError(f"Datei nicht lesbar: {exc}") from exc
        name_column = dict(mapping.get("columns") or {}).get("beneficiary_name")
        if not items or (
            name_column
            and not any(name_column in item for item in items)
            and not config.get("fallback")
        ):
            raise ParserError(
                "Keine Datensätze mit der zugeordneten Namensspalte gefunden; "
                "Datei oder Zuordnung prüfen."
            )
        records: dict[str, HarvestRecord] = {}
        issues: list[RecordIssue] = []
        for position, item in enumerate(items, start=1):
            locator = f"row/{position}"
            values = flowsearch.record_values(item, source, mappings)
            if values is None:
                issues.append(
                    RecordIssue(locator, "Kein Begünstigtenname; Zeile nicht übernommen.")
                )
                continue
            identity = str(values["project_id"])
            if identity in records:
                issues.append(RecordIssue(locator, "project_id bereits in dieser Datei vorhanden."))
                continue
            raw = json_safe(item)
            records[identity] = HarvestRecord(
                source_id=self.source.source_id,
                record_id=identity,
                raw=raw,
                normalized=json_safe_mapping(values),
                provenance=context.provenance(self.source, locator, raw),
            )
        return _final_page(tuple(records.values()), issues, len(records))


def register(registry: Any) -> None:
    """Register all adapters of this package explicitly (no plugin discovery)."""
    registry.register(DeMinimisRegisterAdapter.source.source_id, DeMinimisRegisterAdapter)
    registry.register(WorkshopBeneficiaryAdapter.source.source_id, WorkshopBeneficiaryAdapter)
    registry.register(FlowsearchBeneficiaryAdapter.source.source_id, FlowsearchBeneficiaryAdapter)
