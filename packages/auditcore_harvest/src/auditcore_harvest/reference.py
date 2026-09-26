"""Executable reference adapters used by the adapter guide and the contract tests.

* :class:`JsonApiAdapter` – paged JSON API with a continuation token.
* :class:`FeedAdapter` – RSS 2.0 or Atom feed, one page, no DTDs accepted;
  parsed only through ``defusedxml`` (extra ``xml``).

Both use the injected transport; the JSON adapter needs only the standard library.
"""

from __future__ import annotations

# Types and ParseError only; parsing goes through defusedxml (auditcore_common.safe_xml).
import xml.etree.ElementTree as ElementTree  # nosec B405
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from auditcore_common.safe_xml import parse_xml

from .adapter import FetchContext, require
from .errors import ConfigError, ParserError
from .model import (
    JSON,
    AuthKind,
    Capabilities,
    Cursor,
    HarvestRecord,
    PageResult,
    RecordIssue,
    SnapshotSemantics,
    Source,
    page_result,
)
from .transport import decode_json, raise_for_status

Normalizer = Callable[[Mapping[str, JSON]], Mapping[str, JSON]]
FeedItem = tuple[str, dict[str, str]]


def _identity(item: Mapping[str, JSON]) -> Mapping[str, JSON]:
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

    def validate_config(self, config: Mapping[str, JSON]) -> None:
        """``url`` must be an http(s) address; ``page_size`` a positive int."""
        url = require(config, "url", str)
        if not url.startswith(("http://", "https://")):
            raise ConfigError("'url' muss eine http(s)-Adresse sein.")
        size = config.get("page_size")
        if size is not None and (isinstance(size, bool) or not isinstance(size, int) or size < 1):
            raise ConfigError("'page_size' muss eine positive ganze Zahl sein.")

    def fetch_page(self, context: FetchContext, cursor: Cursor | None) -> PageResult:
        """Fetch one page and map every item to a record."""
        params = self._params(context, cursor)
        secret_params = dict(params)
        if self.api_key_param:
            secret_params[self.api_key_param] = context.secret(self.source.source_id, "api_key")
        url = str(context.config["url"])
        response = raise_for_status(
            context.transport.request("GET", url, params=secret_params, timeout=context.timeout)
        )
        payload = decode_json(response.body)
        if not isinstance(payload, dict) or not isinstance(payload.get(self.items_key), list):
            raise ParserError(f"Antwort enthält keine Liste '{self.items_key}'.")
        locator = f"{url}?{'&'.join(f'{k}={v}' for k, v in sorted(params.items()))}"
        records, issues = self._records(context, payload[self.items_key], locator)
        token = payload.get(self.next_key)
        total = payload.get("total")
        return page_result(
            records,
            issues,
            None if token in (None, "") else {"token": str(token)},
            total_hint=total if isinstance(total, int) else None,
        )

    def _params(self, context: FetchContext, cursor: Cursor | None) -> dict[str, str]:
        """Secret-free query parameters: page size, continuation token, declared filters."""
        params: dict[str, str] = {}
        size = context.request.page_size or context.config.get("page_size")
        if size:
            params[self.size_param] = str(size)
        if cursor and cursor.get("token"):
            params[self.token_param] = str(cursor["token"])
        for name, value in context.request.filters.items():
            if name in self.source.filters:
                params[name] = str(value)
        return params

    def _records(
        self, context: FetchContext, items: list[JSON], locator: str
    ) -> tuple[list[HarvestRecord], list[RecordIssue]]:
        """Map items to records; items without id or with a failing normalizer are issues."""
        records: list[HarvestRecord] = []
        issues: list[RecordIssue] = []
        for index, item in enumerate(items):
            where = f"{locator}#{index}"
            if not isinstance(item, dict) or item.get(self.id_field) in (None, ""):
                issues.append(RecordIssue(where, f"Eintrag ohne '{self.id_field}'."))
                continue
            try:
                normalized = self.normalize(item)
            except (KeyError, TypeError, ValueError) as exc:
                issues.append(RecordIssue(where, f"Normalisierung fehlgeschlagen: {exc}"))
                continue
            record_id = str(item[self.id_field])
            deleted = bool(item.get("deleted") is True)
            records.append(
                context.record(self.source, record_id, item, normalized, where, deleted=deleted)
            )
        return records, issues


_ATOM = "{http://www.w3.org/2005/Atom}"


def _text(element: ElementTree.Element | None) -> str:
    return "" if element is None or element.text is None else element.text.strip()


_XML_EXTRA = (
    "Der Feed-Adapter braucht defusedxml: pip install 'auditcore_harvest[xml]' "
    "(Debian: python3-defusedxml)."
)


def _parse_feed(text: str) -> ElementTree.Element:
    """Well-formed XML without DOCTYPE/ENTITY, else a :class:`ParserError`.

    Parsed with ``defusedxml`` and ``forbid_dtd``; without the extra ``xml`` a
    :class:`ConfigError` names the missing dependency (never a stdlib fallback).
    """
    if "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
        raise ParserError("Feed mit DOCTYPE/ENTITY wird aus Sicherheitsgründen abgelehnt.")
    try:
        return parse_xml(text, error=ConfigError, message=_XML_EXTRA, forbid_dtd=True)
    except ElementTree.ParseError as exc:
        raise ParserError(f"Feed ist kein wohlgeformtes XML: {exc}") from exc
    except ValueError as exc:  # defusedxml: DTD, entity or external reference forbidden
        raise ParserError("Feed mit DOCTYPE/ENTITY wird aus Sicherheitsgründen abgelehnt.") from exc


def _rss_items(root: ElementTree.Element) -> list[FeedItem]:
    channel = root.find("channel")
    if channel is None:
        raise ParserError("RSS ohne channel.")
    return [
        (
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


def _atom_items(root: ElementTree.Element) -> list[FeedItem]:
    items: list[FeedItem] = []
    for entry in root.findall(f"{_ATOM}entry"):
        link = entry.find(f"{_ATOM}link")
        href = "" if link is None else link.get("href", "")
        items.append(
            (
                _text(entry.find(f"{_ATOM}id")) or href,
                {
                    "title": _text(entry.find(f"{_ATOM}title")),
                    "link": href,
                    "published": _text(entry.find(f"{_ATOM}updated")),
                    "summary": _text(entry.find(f"{_ATOM}summary")),
                },
            )
        )
    return items


def _feed_items(root: ElementTree.Element) -> list[FeedItem]:
    """``(identifier, fields)`` per RSS item or Atom entry; other roots are parser errors."""
    if root.tag == "rss":
        return _rss_items(root)
    if root.tag == f"{_ATOM}feed":
        return _atom_items(root)
    raise ParserError(f"Unbekanntes Feedformat '{root.tag}'.")


@dataclass
class FeedAdapter:
    """RSS 2.0 / Atom feed as one complete page; ``guid``/``id`` or link is the record id.

    Documents with a DOCTYPE are rejected (no entity expansion). An empty but
    well-formed feed is a legitimate empty result; anything else that cannot
    be parsed is a :class:`ParserError`.
    """

    source: Source

    def validate_config(self, config: Mapping[str, JSON]) -> None:
        """``url`` required (http(s) or ``file:``)."""
        url = require(config, "url", str)
        if not url.startswith(("http://", "https://", "file:")):
            raise ConfigError("'url' muss http(s) oder file: sein.")

    def fetch_page(self, context: FetchContext, cursor: Cursor | None) -> PageResult:
        """Fetch and parse the whole feed."""
        url = str(context.config["url"])
        response = raise_for_status(context.transport.request("GET", url, timeout=context.timeout))
        items = _feed_items(_parse_feed(response.text()))
        records: list[HarvestRecord] = []
        issues: list[RecordIssue] = []
        for index, (identifier, normalized) in enumerate(items):
            where = f"{url}#{index}"
            if not identifier:
                issues.append(RecordIssue(where, "Eintrag ohne guid/id/link."))
                continue
            records.append(context.record(self.source, identifier, normalized, normalized, where))
        return page_result(records, issues)


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


def _feed_example() -> FeedAdapter:
    """Factory of the synthetic feed example for ``auditcore-harvest replay``."""
    return FeedAdapter(example_feed_source())
