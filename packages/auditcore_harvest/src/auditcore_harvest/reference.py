"""Executable reference adapters used by the adapter guide and the contract tests.

* :class:`JsonApiAdapter` – paged JSON API with a continuation token.
* :class:`FeedAdapter` – RSS 2.0 or Atom feed, one page, no DTDs accepted.

Both use only the standard library and the injected transport.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ElementTree
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from .adapter import FetchContext, require
from .errors import ConfigError, ParserError
from .model import (
    AuthKind,
    Capabilities,
    HarvestRecord,
    PageResult,
    PageStatus,
    RecordIssue,
    SnapshotSemantics,
    Source,
)
from .transport import raise_for_status

Normalizer = Callable[[Mapping[str, Any]], Mapping[str, Any]]


def _identity(item: Mapping[str, Any]) -> Mapping[str, Any]:
    return dict(item)


@dataclass
class JsonApiAdapter:
    """Generic paged JSON API: ``{items_key: [...], next_key: token|null}``.

    Config: ``url`` (str, required); optional ``page_size`` (int). With
    ``api_key_param`` set, the key is read from the credential provider under
    the name ``"api_key"`` and sent as a query parameter; it never appears in
    records, locators or events.
    """

    source: Source
    items_key: str = "items"
    id_field: str = "id"
    next_key: str = "next"
    token_param: str = "cursor"
    size_param: str = "size"
    api_key_param: str | None = None
    normalize: Normalizer = _identity

    def validate_config(self, config: Mapping[str, Any]) -> None:
        """``url`` must be an http(s) address; ``page_size`` a positive int."""
        url = require(config, "url", str)
        if not url.startswith(("http://", "https://")):
            raise ConfigError("'url' muss eine http(s)-Adresse sein.")
        size = config.get("page_size")
        if size is not None and (isinstance(size, bool) or not isinstance(size, int) or size < 1):
            raise ConfigError("'page_size' muss eine positive ganze Zahl sein.")

    def fetch_page(self, context: FetchContext, cursor: Mapping[str, Any] | None) -> PageResult:
        """Fetch one page and map every item to a record."""
        params: dict[str, str] = {}
        size = context.request.page_size or context.config.get("page_size")
        if size:
            params[self.size_param] = str(size)
        if cursor and cursor.get("token"):
            params[self.token_param] = str(cursor["token"])
        for name, value in context.request.filters.items():
            if name in self.source.filters:
                params[name] = str(value)
        secret_params = dict(params)
        if self.api_key_param:
            secret_params[self.api_key_param] = context.secret(self.source.source_id, "api_key")
        url = str(context.config["url"])
        response = raise_for_status(
            context.transport.request("GET", url, params=secret_params, timeout=context.timeout)
        )
        try:
            payload = json.loads(response.body)
        except ValueError as exc:
            raise ParserError("Antwort ist kein JSON.") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get(self.items_key), list):
            raise ParserError(f"Antwort enthält keine Liste '{self.items_key}'.")
        records: list[HarvestRecord] = []
        issues: list[RecordIssue] = []
        locator = f"{url}?{'&'.join(f'{k}={v}' for k, v in sorted(params.items()))}"
        for index, item in enumerate(payload[self.items_key]):
            where = f"{locator}#{index}"
            if not isinstance(item, dict) or item.get(self.id_field) in (None, ""):
                issues.append(RecordIssue(where, f"Eintrag ohne '{self.id_field}'."))
                continue
            try:
                normalized = self.normalize(item)
            except (KeyError, TypeError, ValueError) as exc:
                issues.append(RecordIssue(where, f"Normalisierung fehlgeschlagen: {exc}"))
                continue
            records.append(
                HarvestRecord(
                    source_id=self.source.source_id,
                    record_id=str(item[self.id_field]),
                    raw=item,
                    normalized=normalized,
                    provenance=context.provenance(self.source, where, item),
                    deleted=bool(item.get("deleted") is True),
                )
            )
        token = payload.get(self.next_key)
        complete = token in (None, "")
        return PageResult(
            records=tuple(records),
            next_cursor=None if complete else {"token": str(token)},
            complete=complete,
            status=PageStatus.PARTIAL if issues else PageStatus.OK,
            issues=tuple(issues),
            total_hint=payload.get("total") if isinstance(payload.get("total"), int) else None,
        )


_ATOM = "{http://www.w3.org/2005/Atom}"


def _text(element: ElementTree.Element | None) -> str:
    return "" if element is None or element.text is None else element.text.strip()


@dataclass
class FeedAdapter:
    """RSS 2.0 / Atom feed as one complete page; ``guid``/``id`` or link is the record id.

    Documents with a DOCTYPE are rejected (no entity expansion). An empty but
    well-formed feed is a legitimate empty result; anything else that cannot
    be parsed is a :class:`ParserError`.
    """

    source: Source

    def validate_config(self, config: Mapping[str, Any]) -> None:
        """``url`` required (http(s) or ``file:``)."""
        url = require(config, "url", str)
        if not url.startswith(("http://", "https://", "file:")):
            raise ConfigError("'url' muss http(s) oder file: sein.")

    def fetch_page(self, context: FetchContext, cursor: Mapping[str, Any] | None) -> PageResult:
        """Fetch and parse the whole feed."""
        url = str(context.config["url"])
        response = raise_for_status(context.transport.request("GET", url, timeout=context.timeout))
        text = response.text()
        if "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
            raise ParserError("Feed mit DOCTYPE/ENTITY wird aus Sicherheitsgründen abgelehnt.")
        try:
            root = ElementTree.fromstring(text)
        except ElementTree.ParseError as exc:
            raise ParserError(f"Feed ist kein wohlgeformtes XML: {exc}") from exc
        if root.tag == "rss":
            channel = root.find("channel")
            if channel is None:
                raise ParserError("RSS ohne channel.")
            items = [
                (
                    item,
                    _text(item.find("guid")) or _text(item.find("link")),
                    {
                        "title": _text(item.find("title")),
                        "link": _text(item.find("link")),
                        "published": _text(item.find("pubDate")),
                        "summary": _text(item.find("description")),
                    },
                )
                for item in channel.findall("item")
            ]
        elif root.tag == f"{_ATOM}feed":
            items = []
            for entry in root.findall(f"{_ATOM}entry"):
                link = entry.find(f"{_ATOM}link")
                href = "" if link is None else link.get("href", "")
                items.append(
                    (
                        entry,
                        _text(entry.find(f"{_ATOM}id")) or href,
                        {
                            "title": _text(entry.find(f"{_ATOM}title")),
                            "link": href,
                            "published": _text(entry.find(f"{_ATOM}updated")),
                            "summary": _text(entry.find(f"{_ATOM}summary")),
                        },
                    )
                )
        else:
            raise ParserError(f"Unbekanntes Feedformat '{root.tag}'.")
        records: list[HarvestRecord] = []
        issues: list[RecordIssue] = []
        for index, (_, identifier, normalized) in enumerate(items):
            where = f"{url}#{index}"
            if not identifier:
                issues.append(RecordIssue(where, "Eintrag ohne guid/id/link."))
                continue
            records.append(
                HarvestRecord(
                    source_id=self.source.source_id,
                    record_id=identifier,
                    raw=normalized,
                    normalized=normalized,
                    provenance=context.provenance(self.source, where, normalized),
                )
            )
        return PageResult(
            records=tuple(records),
            next_cursor=None,
            complete=True,
            status=PageStatus.PARTIAL if issues else PageStatus.OK,
            issues=tuple(issues),
        )


def example_json_source() -> Source:
    """Source declaration of the guide's JSON example (synthetic, not a real service)."""
    return Source(
        source_id="example.json_api",
        title="Beispiel-JSON-API (synthetisch)",
        family="example",
        adapter_version="1.0.0",
        profile_version="2026.09.1",
        data_format="application/json",
        auth=AuthKind.API_KEY,
        capabilities=Capabilities(
            pagination=True, incremental=False, full_snapshot=True, deletions=True
        ),
        snapshot_semantics=SnapshotSemantics.FULL_SNAPSHOT_REPLACE,
        filters=("land",),
    )


def example_feed_source() -> Source:
    """Source declaration of the guide's feed example (synthetic)."""
    return Source(
        source_id="example.feed",
        title="Beispiel-Feed (synthetisch)",
        family="example",
        adapter_version="1.0.0",
        profile_version="2026.09.1",
        data_format="application/rss+xml",
        auth=AuthKind.NONE,
        capabilities=Capabilities(
            pagination=False, incremental=False, full_snapshot=False, deletions=False
        ),
        snapshot_semantics=SnapshotSemantics.APPEND_ONLY,
    )
