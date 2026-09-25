"""ZVG-Portal adapters (versteigerung): result lists per court and detail pages."""

from __future__ import annotations

import urllib.parse
from collections.abc import Mapping
from typing import Any

from .. import zvg
from ._base import (
    Cursor,
    _Portal,
    _robots_policy,
    _source,
    _template,
)
from ._harvest import (
    ConfigError,
    FetchContext,
    PageResult,
    ParserError,
    RecordIssue,
    raise_for_status,
    require,
)


def _zvg_url(params: Mapping[str, str]) -> str:
    return f"{zvg.BASE}?{urllib.parse.urlencode(params)}"


class ZvgListingAdapter(_Portal):
    """Result list of each court (POST ``button=Suchen``); one court per page.

    Records carry ``zvg_id``, land, court and Aktenzeichen — enough for the
    lifecycle (:mod:`auditcore_property_sources.zvg_lifecycle`). Notices
    without an Aktenzeichen are reported as issues (the original drops them).
    """

    def __init__(self) -> None:
        self.source = _source(
            zvg.SOURCE_ID, "ZVG-Portal (Zwangsversteigerungen)", "text/html", filters=("courts",)
        )

    def _courts(self, config: Mapping[str, Any]) -> list[str]:
        value = config.get("courts", "kern")
        courts = zvg.resolve_courts(value) if isinstance(value, str) else value
        if not isinstance(courts, list) or not courts:
            raise ConfigError("'courts' ist 'kern', 'he', 'all' oder eine Liste von ger_id.")
        unknown = [c for c in courts if c not in zvg.LAND_BY_COURT]
        if unknown:
            raise ConfigError(f"Unbekannte Gerichte: {', '.join(map(str, unknown))}.")
        return list(courts)

    def validate_config(self, config: Mapping[str, Any]) -> None:
        _robots_policy(config)
        self._courts(config)

    def fetch_page(self, context: FetchContext, cursor: Cursor) -> PageResult:
        courts = self._courts(context.config)
        index = int((cursor or {}).get("court", 0))
        court = courts[index]
        land = zvg.LAND_BY_COURT[court]
        session = {"button": "Termine suchen"}
        search = {"button": "Suchen"}
        rules = self._rules(context, cursor, zvg.BASE)
        for params in (session, search):
            self._check(rules, _zvg_url(params))
        raise_for_status(
            context.transport.request(
                "GET",
                zvg.BASE,
                params=session,
                headers={"Accept-Language": "de"},
                timeout=context.timeout,
            )
        )
        form = {
            "button": "Suchen",
            "land_abk": land,
            "ger_id": court,
            "order_by": "2",
            "art": "",
            "gbuch": "",
        }
        response = raise_for_status(
            context.transport.request(
                "POST",
                zvg.BASE,
                params=search,
                data=urllib.parse.urlencode(form).encode(),
                headers={
                    "Referer": _zvg_url(session),
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                timeout=context.timeout,
            )
        )
        doc = zvg.decode_portal_bytes(response.body)
        if "<html" not in doc[:4096].lower() and "<!doctype" not in doc[:4096].lower():
            raise ParserError("ZVG-Trefferliste ist kein HTML-Dokument.")
        files = zvg.parse_listing_akten(doc, land)
        issues = [
            RecordIssue(f"{zvg.detail_url(z, land)}", "Bekanntmachung ohne Aktenzeichen.")
            for z in zvg.listing_ids(doc, land)
            if z not in files
        ]
        records = []
        for zvg_id, file_number in files.items():
            normalized = {
                "zvg_id": zvg_id,
                "land": land,
                "court_id": court,
                "court_name": zvg.COURT_NAMES[court],
                "file_number": file_number,
                "detail_url": zvg.detail_url(zvg_id, land),
            }
            records.append(
                self._record(
                    context,
                    f"{land}:{zvg_id}",
                    {"zvg_id": zvg_id, "text": file_number},
                    normalized,
                    f"{zvg.BASE}?button=Suchen&ger_id={court}#{zvg_id}",
                )
            )
        following = self._cursor(rules, court=index + 1) if index + 1 < len(courts) else None
        return self._page(records, issues, following, None)


class ZvgDetailAdapter(_Portal):
    """Detail pages of given notices (config ``notices``).

    robots.txt of the portal disallows ``showZvg``; the default
    ``robots_policy="ignore"`` fetches them like the original. Archived detail
    pages (``detail_url_template`` with ``file:``) work as well.
    ``reference_year`` for the plausible *Baujahr* comes from the injected clock.
    """

    def __init__(self) -> None:
        self.source = _source("property.zvg_detail", "ZVG-Portal (Detailseiten)", "text/html")

    def _notices(self, config: Mapping[str, Any]) -> list[Mapping[str, str]]:
        notices: list[Mapping[str, str]] = require(config, "notices", list)
        for n in notices:
            if not (
                isinstance(n, Mapping)
                and str(n.get("court_id")) in zvg.LAND_BY_COURT
                and str(n.get("zvg_id", "")).isdigit()
            ):
                raise ConfigError("Jede Bekanntmachung braucht zvg_id (Ziffern) und court_id.")
        if not notices:
            raise ConfigError("'notices' ist leer.")
        return notices

    def validate_config(self, config: Mapping[str, Any]) -> None:
        _robots_policy(config)
        self._notices(config)
        _template(
            config,
            "detail_url_template",
            zvg.BASE + "?button=showZvg&zvg_id={zvg_id}&land_abk={land}",
            "zvg_id",
        )

    def fetch_page(self, context: FetchContext, cursor: Cursor) -> PageResult:
        notices = self._notices(context.config)
        index = int((cursor or {}).get("notice", 0))
        notice = notices[index]
        court = str(notice["court_id"])
        land = zvg.LAND_BY_COURT[court]
        zvg_id = str(notice["zvg_id"])
        template = _template(
            context.config,
            "detail_url_template",
            zvg.BASE + "?button=showZvg&zvg_id={zvg_id}&land_abk={land}",
            "zvg_id",
        )
        url = template.format(zvg_id=zvg_id, land=land)
        rules = self._rules(context, cursor, url)
        self._check(rules, url)
        headers: dict[str, str] = {}
        if url.startswith(("http://", "https://")):
            # Wie ZvgPortal.__init__/detail: Sitzung über "Termine suchen", dann
            # Detailabruf mit Referer der Trefferliste (PS-C09).
            if not (cursor or {}).get("session"):
                raise_for_status(
                    context.transport.request(
                        "GET",
                        zvg.BASE,
                        params={"button": "Termine suchen"},
                        headers={"Accept-Language": "de"},
                        timeout=context.timeout,
                    )
                )
            headers = {"Accept-Language": "de", "Referer": _zvg_url({"button": "Suchen"})}
        response = raise_for_status(
            context.transport.request("GET", url, headers=headers, timeout=context.timeout)
        )
        doc = zvg.decode_portal_bytes(response.body)
        head = doc[:4096].lower()
        if "<html" not in head and "<!doctype" not in head:
            raise ParserError(f"Detailseite {url} ist kein HTML-Dokument.")
        parsed = zvg.parse_detail(
            doc,
            zvg.ZvgNotice(
                zvg_id=zvg_id,
                land=land,
                court_id=court,
                court_name=zvg.COURT_NAMES[court],
                file_number=str(notice.get("file_number", "")),
                detail_url=zvg.detail_url(zvg_id, land),
            ),
            reference_year=context.clock.now().year,
        )
        record = self._record(
            context, f"{land}:{zvg_id}", {"url": url, "length": len(doc)}, parsed.to_dict(), url
        )
        following = (
            self._cursor(rules, notice=index + 1, session=bool(headers))
            if index + 1 < len(notices)
            else None
        )
        return self._page([record], [], following, len(notices))
