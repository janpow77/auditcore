"""Source adapters for ``auditcore_harvest`` (contract version 1).

Each adapter fetches exactly one page through the injected transport and
returns records; paging order, retries, rate limits, checkpoints and sinks
belong to :class:`auditcore_harvest.HarvestEngine`. Configuration names an
explicit profile and contains no secrets; the DIP API key comes from the
consumer's credential provider under the name ``api_key``.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

from auditcore_harvest import (
    AdapterRegistry,
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

from . import dip, eurlex, feeds
from .errors import ConfigurationError, LegalSourceError, ParseError, ProfileError
from .model import ADAPTER_VERSION, LegalDocument
from .profile import SourceProfile, load_profile

FAMILY = "legal"


def _profile(config: Mapping[str, Any]) -> SourceProfile:
    spec = config.get("profile")
    if not isinstance(spec, Mapping) or not all(
        isinstance(spec.get(k), str) for k in ("id", "version")
    ):
        raise ConfigError("Konfiguration 'profile' mit 'id' und 'version' fehlt.")
    try:
        return load_profile(str(spec["id"]), str(spec["version"]))
    except ProfileError as exc:
        raise ConfigError(str(exc)) from exc


def _json(response_body: bytes, what: str) -> Any:
    try:
        return json.loads(response_body)
    except ValueError as exc:
        raise ParserError(f"{what}: Antwort ist kein JSON.") from exc


def _record(
    source: Source, context: FetchContext, document: LegalDocument, raw: Any, locator: str
) -> HarvestRecord:
    normalized = document.to_dict()
    return HarvestRecord(
        source_id=source.source_id,
        record_id=document.external_id,
        raw=raw,
        normalized=normalized,
        provenance=context.provenance(source, locator, raw),
    )


def _page(
    records: Sequence[HarvestRecord],
    issues: Sequence[RecordIssue],
    next_cursor: Mapping[str, Any] | None,
    total: int | None = None,
) -> PageResult:
    return PageResult(
        records=tuple(records),
        next_cursor=dict(next_cursor) if next_cursor is not None else None,
        complete=next_cursor is None,
        status=PageStatus.PARTIAL if issues else PageStatus.OK,
        issues=tuple(issues),
        total_hint=total,
    )


def _issues(errors: Sequence[ParseError]) -> list[RecordIssue]:
    return [RecordIssue(error.location or "?", str(error)) for error in errors]


def _since(value: str | None) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError as exc:
        raise ConfigError(f"'since' ist kein ISO-Datum: {value!r}.") from exc


class DipDrucksachenAdapter:
    """Bundestag DIP ``/drucksache`` title search, one keyword page per call.

    Cursor ``{"keyword": i, "dip": cursor}``: the DIP cursor pages one search
    term until it no longer changes, then the next profile term starts.
    """

    source = Source(
        source_id="legal.dip_bundestag",
        title="Bundestag DIP – Drucksachen",
        family=FAMILY,
        adapter_version=ADAPTER_VERSION,
        profile_version="2026.09.1",
        data_format="application/json",
        auth=AuthKind.API_KEY,
        capabilities=Capabilities(
            pagination=True, incremental=True, full_snapshot=False, deletions=False
        ),
        snapshot_semantics=SnapshotSemantics.INCREMENTAL_UPSERT,
        filters=("keywords",),
    )

    def validate_config(self, config: Mapping[str, Any]) -> None:
        """Profile must exist; optional ``keywords`` must be a subset of its terms."""
        profile = _profile(config)
        self._keywords(profile, config)

    @staticmethod
    def _keywords(profile: SourceProfile, config: Mapping[str, Any]) -> tuple[str, ...]:
        selected = config.get("keywords")
        if selected is not None and (
            not isinstance(selected, list) or not all(isinstance(k, str) for k in selected)
        ):
            raise ConfigError("'keywords' muss eine Liste von Texten sein.")
        try:
            return dip.keywords(profile, selected)
        except ConfigurationError as exc:
            raise ConfigError(str(exc)) from exc

    def fetch_page(self, context: FetchContext, cursor: Mapping[str, Any] | None) -> PageResult:
        """One DIP result page of the current search term."""
        profile = _profile(context.config)
        terms = self._keywords(profile, context.config)
        index = int((cursor or {}).get("keyword", 0))
        previous = (cursor or {}).get("dip")
        if not 0 <= index < len(terms):
            raise ParserError("DIP-Cursor verweist auf keinen Suchbegriff des Profils.")
        header = dip.auth_header_value(context.secret(self.source.source_id, "api_key"))
        params = dip.drucksache_query(
            profile,
            terms[index],
            cursor=str(previous) if previous else None,
            updated_since=_since(context.request.since),
        )
        response = raise_for_status(
            context.transport.request(
                "GET",
                dip.drucksache_url(profile),
                params=params,
                headers={dip.AUTH_HEADER: header, "Accept": "application/json"},
                timeout=context.timeout,
            )
        )
        try:
            page = dip.parse_page(_json(response.body, "DIP"))
        except ParseError as exc:
            raise ParserError(str(exc)) from exc
        documents, errors = dip.normalize_page(page, profile)
        items = {f"dip_{item.get('id')}": item for item in page.items}
        records = [
            _record(
                self.source, context, d, items.get(d.external_id), f"{terms[index]}/{d.external_id}"
            )
            for d in documents
        ]
        if not page.is_last(str(previous) if previous else None):
            next_cursor: dict[str, Any] | None = {"keyword": index, "dip": page.cursor}
        elif index + 1 < len(terms):
            next_cursor = {"keyword": index + 1, "dip": None}
        else:
            next_cursor = None
        return _page(records, _issues(errors), next_cursor, page.num_found)


class EurLexAdapter:
    """EUR-Lex/Cellar SPARQL: each profile query is one page; core documents come first.

    With ``request.since`` and a profile update query, a single incremental
    page is fetched instead. The cursor carries the CELEX numbers already
    delivered, so the first occurrence wins like in the source applications.
    """

    source = Source(
        source_id="legal.eurlex",
        title="EUR-Lex (Cellar SPARQL)",
        family=FAMILY,
        adapter_version=ADAPTER_VERSION,
        profile_version="2026.09.1",
        data_format="application/sparql-results+json",
        auth=AuthKind.NONE,
        capabilities=Capabilities(
            pagination=True, incremental=True, full_snapshot=False, deletions=False
        ),
        snapshot_semantics=SnapshotSemantics.INCREMENTAL_UPSERT,
        filters=(),
    )

    def validate_config(self, config: Mapping[str, Any]) -> None:
        """Profile must exist."""
        _profile(config)

    def fetch_page(self, context: FetchContext, cursor: Mapping[str, Any] | None) -> PageResult:
        """Core documents (step 0) or one SPARQL query result."""
        profile = _profile(context.config)
        names = list(profile.eurlex_queries)
        step = int((cursor or {}).get("step", 0))
        seen = set((cursor or {}).get("seen", ()))
        since = _since(context.request.since)
        if since is not None and profile.eurlex_update_query_template is not None:
            query = eurlex.update_query(profile, since)
            rows = self._query(context, profile, query)
            documents, issues = self._normalize(rows, profile, "update", seen)
            return _page(
                [
                    _record(self.source, context, d, r, f"update/{d.external_id}")
                    for d, r in documents
                ],
                issues,
                None,
            )
        if not 0 <= step < len(names):
            raise ParserError("EUR-Lex-Cursor außerhalb der Profilabfragen.")
        name = names[step]
        rows = self._query(context, profile, profile.eurlex_queries[name])
        documents, issues = [], []
        if step == 0:
            # Core documents are delivered with the first query page (source order).
            documents, issues = self._normalize(eurlex.core_rows(profile), profile, None, seen)
            seen = seen | {d.external_id for d, _ in documents}
        more, more_issues = self._normalize(rows, profile, name, seen)
        documents, issues = documents + more, issues + more_issues
        records = [
            _record(self.source, context, d, r, f"step{step}/{d.external_id}") for d, r in documents
        ]
        next_cursor = (
            {"step": step + 1, "seen": sorted(seen | {d.external_id for d, _ in documents})}
            if step + 1 < len(names)
            else None
        )
        return _page(records, issues, next_cursor)

    @staticmethod
    def _query(context: FetchContext, profile: SourceProfile, query: str) -> list[dict[str, str]]:
        response = raise_for_status(
            context.transport.request(
                "GET",
                profile.eurlex_endpoint,
                params=eurlex.sparql_form(query),
                headers={"Accept": eurlex.RESULTS_MEDIA_TYPE},
                timeout=context.timeout,
            )
        )
        try:
            return eurlex.parse_results(_json(response.body, "EUR-Lex"))
        except ParseError as exc:
            raise ParserError(str(exc)) from exc

    @staticmethod
    def _normalize(
        rows: Sequence[Mapping[str, str]],
        profile: SourceProfile,
        query_name: str | None,
        seen: set[str],
    ) -> tuple[list[tuple[LegalDocument, dict[str, str]]], list[RecordIssue]]:
        documents: list[tuple[LegalDocument, dict[str, str]]] = []
        issues: list[RecordIssue] = []
        for index, row in enumerate(rows):
            data = dict(row) if query_name is None else {**row, "source": query_name}
            celex = data.get("celex", "")
            if not celex:
                issues.append(RecordIssue(f"rows[{index}]", "EUR-Lex-Eintrag ohne CELEX-Nummer."))
                continue
            if celex in seen or any(d.external_id == celex for d, _ in documents):
                continue
            try:
                documents.append((eurlex.normalize_row(data, profile), data))
            except LegalSourceError as exc:
                issues.append(RecordIssue(f"rows[{index}]", str(exc)))
        return documents, issues


class FeedAdapter:
    """RSS/Atom feeds of one profile feed source (``bafin`` or ``curia``); one feed per page.

    Needs the ``feeds`` extra (feedparser). ``relevant_only`` applies the
    profile keywords explicitly; without matches the page is simply empty.
    """

    key = "bafin"

    def __init__(self) -> None:
        self.source = Source(
            source_id=f"legal.{self.key}",
            title=f"{self.key.upper()} RSS",
            family=FAMILY,
            adapter_version=ADAPTER_VERSION,
            profile_version="2026.09.1",
            data_format="application/rss+xml",
            auth=AuthKind.NONE,
            capabilities=Capabilities(
                pagination=False, incremental=None, full_snapshot=False, deletions=False
            ),
            snapshot_semantics=SnapshotSemantics.APPEND_ONLY,
            filters=("relevant_only",),
        )

    def validate_config(self, config: Mapping[str, Any]) -> None:
        """Profile must contain this feed source."""
        try:
            feeds.feed_source(_profile(config), self.key)
        except ConfigurationError as exc:
            raise ConfigError(str(exc)) from exc
        if not isinstance(config.get("relevant_only", False), bool):
            raise ConfigError("'relevant_only' muss ein Wahrheitswert sein.")

    def fetch_page(self, context: FetchContext, cursor: Mapping[str, Any] | None) -> PageResult:
        """One feed of the source."""
        profile = _profile(context.config)
        source = feeds.feed_source(profile, self.key)
        names = list(source.feeds)
        index = int((cursor or {}).get("feed", 0))
        if not 0 <= index < len(names):
            raise ParserError("Feed-Cursor außerhalb des Profils.")
        name = names[index]
        response = raise_for_status(
            context.transport.request("GET", source.feeds[name], timeout=context.timeout)
        )
        try:
            entries = feeds.parse_feed(response.text())
        except ParseError as exc:
            raise ParserError(str(exc)) from exc
        documents, errors = feeds.normalize_entries(entries, profile, self.key, name)
        if context.config.get("relevant_only", False):
            documents = feeds.select_relevant(documents, profile.keywords_de)
        records = [
            _record(
                self.source,
                context,
                d,
                {"title": d.title, "link": d.source_url},
                f"{name}/{d.external_id}",
            )
            for d in documents
        ]
        next_cursor = {"feed": index + 1} if index + 1 < len(names) else None
        return _page(records, _issues(errors), next_cursor)


class BaFinFeedAdapter(FeedAdapter):
    """BaFin RSS feeds of the profile."""

    key = "bafin"


class CuriaFeedAdapter(FeedAdapter):
    """CURIA RSS feeds of the profile."""

    key = "curia"


class EcaPublicationsAdapter:
    """ECA publication overview page; no placeholder documents when it cannot be read."""

    source = Source(
        source_id="legal.eca",
        title="Europäischer Rechnungshof – Publikationen",
        family=FAMILY,
        adapter_version=ADAPTER_VERSION,
        profile_version="2026.09.1",
        data_format="text/html",
        auth=AuthKind.NONE,
        capabilities=Capabilities(
            pagination=False, incremental=False, full_snapshot=False, deletions=False
        ),
        snapshot_semantics=SnapshotSemantics.APPEND_ONLY,
        filters=(),
    )

    def validate_config(self, config: Mapping[str, Any]) -> None:
        """Profile must contain the ECA page source."""
        try:
            feeds.feed_source(_profile(config), "eca")
        except ConfigurationError as exc:
            raise ConfigError(str(exc)) from exc

    def fetch_page(self, context: FetchContext, cursor: Mapping[str, Any] | None) -> PageResult:
        """The first profile publication URL (source order)."""
        profile = _profile(context.config)
        source = feeds.feed_source(profile, "eca")
        url = source.publication_urls[0]
        response = raise_for_status(context.transport.request("GET", url, timeout=context.timeout))
        text = response.text()
        if "<a" not in text.lower() and "<html" not in text.lower():
            raise ParserError("ECA-Seite enthält kein HTML.")
        documents = feeds.publication_links(text, profile)
        records = [
            _record(
                self.source,
                context,
                d,
                {"href": d.source_url, "text": d.title},
                f"page/{d.external_id}",
            )
            for d in documents
        ]
        return _page(records, [], None)


def register(registry: AdapterRegistry) -> AdapterRegistry:
    """Register all adapters of this family explicitly."""
    for factory in (
        DipDrucksachenAdapter,
        EurLexAdapter,
        BaFinFeedAdapter,
        CuriaFeedAdapter,
        EcaPublicationsAdapter,
    ):
        registry.register(factory().source.source_id, factory)
    return registry
