"""TED and HAD source adapters on ``auditcore_harvest`` (extra ``sources``).

The adapters fetch exactly one page each; paging, retries, rate limits,
checkpoints and sink delivery are done by :class:`auditcore_harvest.HarvestEngine`.
Records carry the canonical notice contract of :mod:`auditcore_procurement.records`
(``normalized``) and the untouched source item (``raw``).

* ``procurement.ted_awards`` — TED search API v3 (``POST``), query and field set
  of ``audit-portal@d8eefa4``. Coverage: award notices with a named contractor
  unless the consumer passes its own ``query``; winnerless notices are reported
  as issues, not dropped silently.
* ``procurement.had_search`` — HAD result page (HTML, extra ``html``); variant
  ``designer`` (default) or ``flowinvoice`` of the search URL and 404 semantics.
"""

from __future__ import annotations

import hashlib
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
    RateLimitError,
    RecordIssue,
    SnapshotSemantics,
    Source,
    raise_for_status,
    require,
)

from . import company_sources, ted
from .records import COVERAGE_AWARDS_WITH_WINNER

TED_SOURCE_ID = "procurement.ted_awards"
HAD_SOURCE_ID = "procurement.had_search"
DEFAULT_TED_URL = "https://api.ted.europa.eu/v3/notices/search"
TED_PAGE_SIZE_CAP = 250


class TedAwardsAdapter:
    """TED v3 notice search, page-based (``page``/``limit`` constant per run)."""

    source = Source(
        source_id=TED_SOURCE_ID,
        title="TED – Vergabebekanntmachungen (Zuschläge mit Auftragnehmer)",
        family="procurement",
        adapter_version="1.0.0",
        profile_version="2026.09.1",
        data_format="application/json",
        auth=AuthKind.NONE,
        capabilities=Capabilities(
            pagination=True, incremental=False, full_snapshot=False, deletions=False
        ),
        snapshot_semantics=SnapshotSemantics.APPEND_ONLY,
        filters=("query", "cpv_codes", "country", "contractor_name", "date_from", "date_to"),
    )

    def validate_config(self, config: Mapping[str, Any]) -> None:
        """``api_url`` (https), optional ``page_size`` 1–250, optional ``fields`` list."""
        url = require(config, "api_url", str)
        if not url.startswith("https://"):
            raise ConfigError("api_url muss eine https-Adresse sein.")
        size = config.get("page_size", 100)
        if (
            isinstance(size, bool)
            or not isinstance(size, int)
            or not 1 <= size <= TED_PAGE_SIZE_CAP
        ):
            raise ConfigError(f"page_size muss 1 bis {TED_PAGE_SIZE_CAP} sein.")
        fields = config.get("fields")
        if fields is not None and (
            not isinstance(fields, list) or not all(isinstance(f, str) and f for f in fields)
        ):
            raise ConfigError("fields muss eine Liste von TED-Feldcodes sein.")

    def query(self, filters: Mapping[str, Any]) -> str:
        """Query of the source application for the given filters."""
        return ted.build_ted_query(
            query=filters.get("query"),
            cpv_codes=filters.get("cpv_codes"),
            country=filters.get("country"),
            contractor_name=filters.get("contractor_name"),
            date_from=filters.get("date_from"),
            date_to=filters.get("date_to"),
        )

    def fetch_page(self, context: FetchContext, cursor: Mapping[str, Any] | None) -> PageResult:
        """One page; ``complete`` when the page is empty or the reported total is reached."""
        config = context.config
        size = int(config.get("page_size", 100))
        page = int(cursor["page"]) if cursor else 1
        query = self.query(context.request.filters)
        body = {
            "query": query,
            "fields": list(config.get("fields") or ted.DEFAULT_FIELDS),
            "page": page,
            "limit": size,
            "scope": "ALL",
        }
        response = raise_for_status(
            context.transport.request(
                "POST",
                str(config["api_url"]),
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                data=json.dumps(body).encode("utf-8"),
                timeout=context.timeout,
            )
        )
        try:
            payload = json.loads(response.body)
        except ValueError as exc:
            raise ParserError("TED-Antwort ist kein JSON.") from exc
        if not isinstance(payload, dict):
            raise ParserError("TED-Antwort ist kein JSON-Objekt.")
        notices = payload.get("notices") or payload.get("results") or payload.get("data") or []
        if not isinstance(notices, list):
            raise ParserError("TED-Antwort enthält keine Liste von Notices.")
        records: list[HarvestRecord] = []
        issues: list[RecordIssue] = []
        for index, notice in enumerate(notices):
            locator = f"page/{page}/{index}"
            number = notice.get("publication-number") if isinstance(notice, dict) else None
            normalized = ted.normalize_notice(notice)
            if normalized is None or not isinstance(number, str) or not number:
                issues.append(RecordIssue(locator, "Notice ohne Auftragnehmer oder Kennung."))
                continue
            records.append(
                HarvestRecord(
                    source_id=TED_SOURCE_ID,
                    record_id=number,
                    raw=notice,
                    normalized={**normalized, "coverage": ted.query_coverage(query)},
                    provenance=context.provenance(self.source, locator, notice),
                )
            )
        total = payload.get("totalNoticeCount") or payload.get("total")
        exhausted = not notices or (isinstance(total, int) and page * size >= total)
        return PageResult(
            records=tuple(records),
            next_cursor=None if exhausted else {"page": page + 1},
            complete=exhausted,
            status=PageStatus.PARTIAL if issues else PageStatus.OK,
            issues=tuple(issues),
            total_hint=total if isinstance(total, int) else None,
        )


def _had_record_id(notice: Mapping[str, str]) -> str:
    """Announcement id if present, otherwise a derived hash of title, office and date."""
    if notice.get("bekanntmachung_id"):
        return f"had-{notice['bekanntmachung_id']}"
    basis = "|".join(notice.get(k, "") for k in ("titel", "vergabestelle", "datum", "url"))
    return "had-h-" + hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]


class HadSearchAdapter:
    """HAD search result page (single page, no pagination in the source)."""

    source = Source(
        source_id=HAD_SOURCE_ID,
        title="HAD – Hessische Ausschreibungsdatenbank (Suchergebnisse)",
        family="procurement",
        adapter_version="1.0.0",
        profile_version="2026.09.1",
        data_format="text/html",
        auth=AuthKind.NONE,
        capabilities=Capabilities(
            pagination=False, incremental=False, full_snapshot=False, deletions=False
        ),
        snapshot_semantics=SnapshotSemantics.UNKNOWN,
        filters=("company_name", "include_archived"),
    )

    def validate_config(self, config: Mapping[str, Any]) -> None:
        """``variant`` ``designer`` or ``flowinvoice``."""
        variant = config.get("variant", "designer")
        if variant not in company_sources.VARIANTS:
            raise ConfigError(f"variant muss eine von {company_sources.VARIANTS} sein.")

    def fetch_page(self, context: FetchContext, cursor: Mapping[str, Any] | None) -> PageResult:
        """The single result page; ``company_name`` filter is required."""
        del cursor
        variant = str(context.config.get("variant", "designer"))
        name = context.request.filters.get("company_name")
        if not isinstance(name, str) or not name.strip():
            raise ConfigError("Filter company_name fehlt.")
        spec = company_sources.had_request(
            name, context.request.filters.get("include_archived", True) is not False, variant
        )
        response = context.transport.request(
            "GET",
            spec["url"],
            params=spec["params"],
            headers=spec["headers"],
            timeout=context.timeout,
        )
        if response.status in (403, 429):
            raise RateLimitError(
                f"HAD antwortete mit HTTP {response.status} (möglicherweise Rate-Limit)."
            )
        if response.status == 404 and variant == "designer":
            return PageResult(records=(), next_cursor=None, complete=True)
        raise_for_status(response)
        content_type = (response.header("content-type") or "").lower()
        if "html" not in content_type and not response.body.lstrip()[:1] == b"<":
            raise ParserError("HAD-Antwort ist kein HTML-Dokument.")
        result = company_sources.had_result(response.status, response.body, variant)
        if result.status not in (company_sources.STATUS_OK, company_sources.STATUS_NO_HIT):
            raise ParserError(result.error or "HAD-Antwort nicht auswertbar.")
        records = tuple(
            HarvestRecord(
                source_id=HAD_SOURCE_ID,
                record_id=_had_record_id(notice),
                raw=dict(notice),
                normalized={**notice, "coverage": result.coverage, "variant": variant},
                provenance=context.provenance(self.source, f"row/{i}", dict(notice)),
            )
            for i, notice in enumerate(result.notices)
        )
        issues = tuple(RecordIssue("page", w) for w in result.warnings)
        return PageResult(
            records=records,
            next_cursor=None,
            complete=True,
            status=PageStatus.PARTIAL if issues else PageStatus.OK,
            issues=issues,
        )


__all__ = [
    "COVERAGE_AWARDS_WITH_WINNER",
    "HAD_SOURCE_ID",
    "TED_SOURCE_ID",
    "HadSearchAdapter",
    "TedAwardsAdapter",
]
