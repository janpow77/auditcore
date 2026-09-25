"""RSS/Atom feed entries and publication pages (BaFin, CURIA, ECA).

Entries are feedparser-style mappings (``title``, ``link``, ``id``,
``summary``/``description``, ``published``/``updated`` and their
``*_parsed`` UTC tuples, ``tags``). :func:`parse_feed` produces them with the
optional ``feeds`` extra; any other parser with the same shape works.
Publication pages are read with the standard library ``html.parser``.

Identities are derived from the entry ``id`` or ``link`` with SHA-256; the
source used ``hash()``, which changes per process (LS-C10). No placeholder
documents are produced when a page cannot be read (LS-C13).
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, date, datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.parse import urljoin

from auditcore_harvest import JSON

from .errors import ConfigurationError, ParseError
from .model import LegalDocument
from .normalize import is_relevant, parse_publication_date
from .profile import FeedSource, SourceProfile


def feed_source(profile: SourceProfile, key: str) -> FeedSource:
    """Feed source ``bafin``, ``curia`` or ``eca`` of the profile."""
    try:
        return profile.feeds[key]
    except KeyError as exc:
        raise ConfigurationError(f"Profil {profile.id} enthält keine Quelle '{key}'.") from exc


def parse_feed(text: str) -> list[Mapping[str, JSON]]:
    """Parse RSS/Atom with feedparser (extra ``feeds``); malformed feeds raise ``ParseError``."""
    try:
        import feedparser
    except ImportError as exc:  # pragma: no cover - depends on the installed extra
        raise ConfigurationError("Feed-Parsing benötigt auditcore_legal_sources[feeds].") from exc
    parsed = feedparser.parse(text)
    if getattr(parsed, "bozo", False) and not parsed.entries:
        raise ParseError(f"Feed nicht lesbar: {parsed.get('bozo_exception')!r}")
    return [dict(entry) for entry in parsed.entries]


def _stable_id(prefix: str, value: str) -> str:
    return f"{prefix}_{hashlib.sha256(value.encode('utf-8')).hexdigest()[:16]}"


def _published(entry: Mapping[str, JSON]) -> tuple[date | None, str | None, str | None]:
    """Date from the parsed UTC tuple, else the RFC 822/ISO text; returns (date, precision, iso)."""
    for key in ("published_parsed", "updated_parsed"):
        value = entry.get(key)
        if isinstance(value, (list, tuple)) and len(value) >= 6:
            year, month, day, hour, minute, second = (int(v) for v in value[:6])
            moment = datetime(year, month, day, hour, minute, second, tzinfo=UTC)
            return moment.date(), "day", moment.isoformat()
    raw = entry.get("published") or entry.get("updated")
    if isinstance(raw, str) and raw.strip():
        try:
            moment = parsedate_to_datetime(raw)
        except (TypeError, ValueError):
            parsed_day, precision = parse_publication_date(raw)
            return parsed_day, precision, None
        return moment.date(), "day", moment.isoformat()
    return None, None, None


def normalize_entry(
    entry: Mapping[str, JSON], profile: SourceProfile, key: str, feed: str
) -> LegalDocument:
    """Normalize one feed entry of feed ``feed`` of source ``key``.

    Raises:
        ParseError: no title, or neither ``id`` nor ``link`` to derive a stable identity.
    """
    source = feed_source(profile, key)
    if feed not in source.feeds and feed not in source.alternative_feeds:
        raise ConfigurationError(f"Feed '{feed}' gehört nicht zur Quelle {key}.")
    title = entry.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ParseError(f"{key}: Feedeintrag ohne Titel.", source_id=key, location="title")
    link = entry.get("link") if isinstance(entry.get("link"), str) else ""
    guid = entry.get("id") if isinstance(entry.get("id"), str) else ""
    anchor = guid or link
    if not anchor:
        raise ParseError(f"{key}: Feedeintrag ohne id und link.", source_id=key, location="id")
    summary = entry.get("summary", entry.get("description", ""))
    summary = summary if isinstance(summary, str) else ""
    published, precision, iso = _published(entry)
    raw_date = entry.get("published", entry.get("updated"))
    cases = sorted({m for p in source.case_patterns for m in re.findall(p, title + " " + summary)})
    metadata: dict[str, JSON] = {
        "feed": feed,
        "guid": guid or None,
        "published_at": iso,
        "categories": [t.get("term") for t in entry.get("tags", []) if isinstance(t, Mapping)],
    }
    if cases:
        metadata["case_numbers"] = cases
    return LegalDocument(
        source_id=key,
        external_id=_stable_id(key, anchor),
        title=title.strip(),
        publication_date=published,
        date_precision=precision,
        raw_date=raw_date if isinstance(raw_date, str) and raw_date else None,
        source_url=link or None,
        document_type=source.document_types.get(feed),
        content=f"{title}\n\n{summary}",
        abstract=summary or None,
        metadata=metadata,
        profile=profile.reference,
        adapter=f"feeds.{key}",
    )


def normalize_entries(
    entries: Iterable[Mapping[str, JSON]], profile: SourceProfile, key: str, feed: str
) -> tuple[list[LegalDocument], list[ParseError]]:
    """Normalize a feed; defective entries are reported with their index."""
    documents: list[LegalDocument] = []
    errors: list[ParseError] = []
    for index, entry in enumerate(entries):
        try:
            documents.append(normalize_entry(entry, profile, key, feed))
        except ParseError as exc:
            exc.location = f"entries[{index}].{exc.location}"
            errors.append(exc)
    return documents, errors


def select_relevant(
    documents: Sequence[LegalDocument], keywords: Iterable[str]
) -> list[LegalDocument]:
    """Explicit keyword filter over title and content; no fallback to unrelated documents."""
    words = tuple(keywords)
    return [d for d in documents if is_relevant(f"{d.title} {d.content or ''}", words)]


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Start collecting the text of an anchor with ``href``."""
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self._href, self._text = href, []

    def handle_data(self, data: str) -> None:
        """Collect anchor text."""
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        """Finish the current anchor."""
        if tag == "a" and self._href is not None:
            self.links.append((self._href, " ".join("".join(self._text).split())))
            self._href = None


def publication_links(html: str, profile: SourceProfile, key: str = "eca") -> list[LegalDocument]:
    """Publication links of an ECA overview page (source rule: marker in href, title > 10)."""
    source = feed_source(profile, key)
    parser = _Links()
    parser.feed(html)
    documents = []
    for href, text in parser.links:
        if not any(marker in href.lower() for marker in source.link_markers):
            continue
        if len(text) < source.min_title_length:
            continue
        url = href if href.startswith("http") else urljoin(source.base_url, href)
        documents.append(
            LegalDocument(
                source_id=key,
                external_id=_stable_id(key, url),
                title=text,
                publication_date=None,
                date_precision=None,
                raw_date=None,
                source_url=url,
                document_type="Bericht",
                content=text,
                profile=profile.reference,
                adapter=f"page.{key}",
            )
        )
    return documents
