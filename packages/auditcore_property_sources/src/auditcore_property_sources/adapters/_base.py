"""Shared adapter pieces: source description, config checks, robots handling, pages."""

from __future__ import annotations

from collections.abc import Mapping

from .._types import JSON
from ..robots import RobotsRules, is_allowed, parse_robots, robots_url
from ._harvest import (
    AuthKind,
    Capabilities,
    ConfigError,
    FetchContext,
    HarvestError,
    HarvestRecord,
    PageResult,
    PageStatus,
    ParserError,
    RecordIssue,
    SnapshotSemantics,
    Source,
    raise_for_status,
)

ADAPTER_VERSION = "1.1.0"
ROBOTS_POLICIES = ("ignore", "respect")
DEFAULT_ROBOTS_POLICY = "ignore"
Cursor = Mapping[str, JSON] | None


class AccessNotPermittedError(HarvestError):
    """robots.txt disallows the address; never retried."""

    code = "access_not_permitted"


def _source(source_id: str, title: str, data_format: str, filters: tuple[str, ...] = ()) -> Source:
    return Source(
        source_id=source_id,
        title=title,
        family="property",
        adapter_version=ADAPTER_VERSION,
        profile_version="2026.09.1",
        data_format=data_format,
        auth=AuthKind.NONE,
        capabilities=Capabilities(
            pagination=True, incremental=False, full_snapshot=True, deletions=False
        ),
        snapshot_semantics=SnapshotSemantics.FULL_SNAPSHOT_REPLACE,
        filters=filters,
    )


def _robots_policy(config: Mapping[str, JSON]) -> str:
    value = config.get("robots_policy", DEFAULT_ROBOTS_POLICY)
    if value not in ROBOTS_POLICIES:
        raise ConfigError("'robots_policy' ist 'ignore' oder 'respect'.")
    return str(value)


def _positive(config: Mapping[str, JSON], name: str, default: int) -> int:
    value = config.get(name, default)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ConfigError(f"'{name}' muss eine positive ganze Zahl sein.")
    return value


def _template(config: Mapping[str, JSON], name: str, default: str, *fields: str) -> str:
    value = config.get(name, default)
    if not isinstance(value, str) or not value.startswith(("https://", "http://", "file:")):
        raise ConfigError(f"'{name}' muss eine http(s)- oder file:-Adresse sein.")
    for placeholder in fields:
        if "{" + placeholder + "}" not in value:
            raise ConfigError(f"'{name}' braucht den Platzhalter {{{placeholder}}}.")
    return value


class _Portal:
    """Shared request, robots and record helpers."""

    source: Source
    token: str = "*"

    def _rules(self, context: FetchContext, cursor: Cursor, url: str) -> RobotsRules | None:
        if _robots_policy(context.config) == "ignore":
            return None
        if not url.startswith(("http://", "https://")):
            return None
        if cursor and cursor.get("robots") is not None:
            return RobotsRules.from_list(cursor["robots"])
        response = context.transport.request("GET", robots_url(url), timeout=context.timeout)
        if 500 <= response.status < 600:
            raise_for_status(response)  # retryable transport error
        if not 200 <= response.status < 300:
            return RobotsRules((), "*")  # RFC 9309: unavailable robots.txt → no rules
        return parse_robots(response.text(), self.token)

    @staticmethod
    def _check(rules: RobotsRules | None, url: str) -> None:
        if rules is not None and not is_allowed(rules, url):
            raise AccessNotPermittedError(
                f"robots.txt ({rules.group}) untersagt den Abruf von {url}.",
                detail={"url": url, "group": rules.group},
            )

    def _get_text(self, context: FetchContext, rules: RobotsRules | None, url: str) -> str:
        self._check(rules, url)
        response = raise_for_status(context.transport.request("GET", url, timeout=context.timeout))
        body = response.body.decode("utf-8", errors="replace")
        if "<html" not in body[:4096].lower() and "<!doctype" not in body[:4096].lower():
            raise ParserError(f"Antwort von {url} ist kein HTML-Dokument.")
        return body

    def _record(
        self,
        context: FetchContext,
        record_id: str,
        raw: JSON,
        normalized: Mapping[str, JSON],
        locator: str,
    ) -> HarvestRecord:
        return HarvestRecord(
            source_id=self.source.source_id,
            record_id=record_id,
            raw=raw,
            normalized=dict(normalized),
            provenance=context.provenance(self.source, locator, raw),
        )

    @staticmethod
    def _cursor(rules: RobotsRules | None, **state: JSON) -> dict[str, JSON]:
        return {**state, "robots": None if rules is None else rules.to_list()}

    @staticmethod
    def _page(
        records: list[HarvestRecord],
        issues: list[RecordIssue],
        next_cursor: Cursor,
        total: int | None = None,
    ) -> PageResult:
        return PageResult(
            records=tuple(records),
            next_cursor=next_cursor,
            complete=next_cursor is None,
            status=PageStatus.PARTIAL if issues else PageStatus.OK,
            issues=tuple(issues),
            total_hint=total,
        )
