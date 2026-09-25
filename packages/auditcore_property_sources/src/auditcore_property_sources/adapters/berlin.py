"""Berlin rental portals (wohnungsmonitor profile "berlin")."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .. import immobilien_de, inberlinwohnen, kleinanzeigen
from ._base import (
    Cursor,
    _Portal,
    _positive,
    _robots_policy,
    _source,
    _template,
)
from ._harvest import (
    FetchContext,
    PageResult,
    RecordIssue,
)


class ImmobilienDeAdapter(_Portal):
    """immobilien.de result pages up to ``max_price`` (config ``max_price``, ``pages``)."""

    def __init__(self, plz_bezirke: Mapping[str, Sequence[str]]) -> None:
        self.source = _source(immobilien_de.SOURCE_ID, "immobilien.de (Berlin, Miete)", "text/html")
        self.plz_bezirke = dict(plz_bezirke)

    def validate_config(self, config: Mapping[str, Any]) -> None:
        _robots_policy(config)
        _positive(config, "max_price", 700)
        _positive(config, "pages", 3)
        _template(config, "url_template", immobilien_de.SEARCH, "hoechstpreis", "seite")

    def fetch_page(self, context: FetchContext, cursor: Cursor) -> PageResult:
        config = context.config
        page = int((cursor or {}).get("page", 1))
        pages = _positive(config, "pages", 3)
        template = _template(config, "url_template", immobilien_de.SEARCH, "hoechstpreis", "seite")
        url = template.format(hoechstpreis=_positive(config, "max_price", 700), seite=page)
        rules = self._rules(context, cursor, url)
        listings, unreadable = immobilien_de.parse_page(self._get_text(context, rules, url))
        seen = set((cursor or {}).get("seen", []))
        new = {k: v for k, v in listings.items() if k not in seen}
        issues = [
            RecordIssue(f"{url}#ld+json[{i}]", "JSON-LD-Block nicht lesbar.") for i in unreadable
        ]
        records = []
        for key, listing in new.items():
            normalized = immobilien_de.normalise(listing, self.plz_bezirke)
            records.append(
                self._record(context, str(normalized["id"]), listing, normalized, f"{url}#{key}")
            )
        done = not new or page >= pages
        following = (
            None if done else self._cursor(rules, page=page + 1, seen=sorted(seen | set(new)))
        )
        return self._page(records, issues, following)


class InBerlinWohnenAdapter(_Portal):
    """inberlinwohnen.de finder: all pages, page count from the stated total."""

    def __init__(self) -> None:
        self.source = _source(
            inberlinwohnen.SOURCE_ID, "inberlinwohnen (landeseigene Gesellschaften)", "text/html"
        )

    def validate_config(self, config: Mapping[str, Any]) -> None:
        _robots_policy(config)
        _template(config, "first_url", inberlinwohnen.BASE)
        _template(config, "page_url_template", inberlinwohnen.BASE + "?page={seite}", "seite")

    def fetch_page(self, context: FetchContext, cursor: Cursor) -> PageResult:
        config = context.config
        state = dict(cursor or {})
        page = int(state.get("page", 1))
        url = (
            _template(config, "first_url", inberlinwohnen.BASE)
            if page == 1
            else _template(
                config, "page_url_template", inberlinwohnen.BASE + "?page={seite}", "seite"
            ).format(seite=page)
        )
        rules = self._rules(context, cursor, url)
        doc = self._get_text(context, rules, url)
        known = {int(k): v for k, v in (state.get("attributes") or {}).items()}
        attributes = inberlinwohnen.learn_attributes(doc, known)
        offers = inberlinwohnen.parse_page(doc)
        broken = inberlinwohnen.unreadable_snapshots(doc)
        issues = (
            [RecordIssue(url, f"{broken} Livewire-Snapshot(s) nicht lesbar.")] if broken else []
        )
        total = int(state.get("total", 0))
        pages = int(state.get("pages", 1))
        if page == 1:
            total = inberlinwohnen.total_count(doc)
            per_page = max(len(offers), 1)
            pages = -(-total // per_page) if total else 1
        records = []
        for ident, item in offers.items():
            normalized = inberlinwohnen.normalise(item, attributes)
            records.append(self._record(context, str(ident), item, normalized, f"{url}#{ident}"))
        done = (page > 1 and not offers) or page >= pages
        following = (
            None
            if done
            else self._cursor(
                rules,
                page=page + 1,
                pages=pages,
                total=total,
                attributes={str(k): v for k, v in sorted(attributes.items())},
            )
        )
        return self._page(records, issues, following, total or None)


class KleinanzeigenAdapter(_Portal):
    """Kleinanzeigen result pages (the original address is disallowed by robots.txt;
    fetched anyway under the default ``robots_policy="ignore"``)."""

    def __init__(self, ortsteile_bezirke: Mapping[str, str]) -> None:
        self.source = _source(
            kleinanzeigen.SOURCE_ID, "Kleinanzeigen (Berlin, Mietwohnungen)", "text/html"
        )
        self.districts = kleinanzeigen.district_index(ortsteile_bezirke)

    def validate_config(self, config: Mapping[str, Any]) -> None:
        _robots_policy(config)
        _positive(config, "max_price", 700)
        _positive(config, "pages", 5)
        _template(config, "url_template", kleinanzeigen.SEARCH, "seite", "hoechstpreis")

    def fetch_page(self, context: FetchContext, cursor: Cursor) -> PageResult:
        config = context.config
        page = int((cursor or {}).get("page", 1))
        template = _template(config, "url_template", kleinanzeigen.SEARCH, "seite", "hoechstpreis")
        url = template.format(
            seite="" if page == 1 else f"seite:{page}/",
            hoechstpreis=_positive(config, "max_price", 700),
        )
        rules = self._rules(context, cursor, url)
        ads = kleinanzeigen.parse_page(self._get_text(context, rules, url))
        records = []
        for ident, raw in ads.items():
            if kleinanzeigen.usable(raw):
                normalized = kleinanzeigen.normalise(raw, self.districts)
                records.append(
                    self._record(context, str(normalized["id"]), raw, normalized, f"{url}#{ident}")
                )
        done = not ads or page >= _positive(config, "pages", 5)
        return self._page(records, [], None if done else self._cursor(rules, page=page + 1))
