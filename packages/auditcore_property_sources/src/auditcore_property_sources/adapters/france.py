"""Alsace/Lorraine rental portals (wohnungsmonitor profile "frankreich")."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from .. import bienici, citya, paruvendu
from ._base import (
    Cursor,
    _Portal,
    _positive,
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


class BieniciAdapter(_Portal):
    """bienici.com JSON search per zone list (config ``zones`` required).

    Sends the original request headers (browser user agent, ``Accept-Language``,
    ``Referer``); ``user_agent=None`` leaves the user agent to the transport.
    """

    def __init__(self) -> None:
        self.source = _source(bienici.SOURCE_ID, "bien'ici (Frankreich, Miete)", "application/json")

    def validate_config(self, config: Mapping[str, Any]) -> None:
        _robots_policy(config)
        zones = require(config, "zones", list)
        if not zones or not all(isinstance(z, str) and z for z in zones):
            raise ConfigError("'zones' muss eine nicht leere Liste von Zonenkennungen sein.")
        _positive(config, "max_price", 1100)
        _positive(config, "page_size", 200)
        _positive(config, "max_pages", 20)
        if config.get("advertiser_names", bienici.DEFAULT_ADVERTISER_NAMES) not in (
            "minimal",
            "legacy",
        ):
            raise ConfigError("'advertiser_names' ist 'minimal' oder 'legacy'.")
        agent = config.get("user_agent", bienici.BROWSER_USER_AGENT)
        if agent is not None and (not isinstance(agent, str) or not agent.strip()):
            raise ConfigError("'user_agent' ist eine Zeichenkette oder None.")

    def fetch_page(self, context: FetchContext, cursor: Cursor) -> PageResult:
        config = context.config
        page = int((cursor or {}).get("page", 1))
        size = _positive(config, "page_size", 200)
        filters = bienici.search_filter(
            list(config["zones"]),
            max_price=_positive(config, "max_price", 1100),
            page=page,
            page_size=size,
            min_rooms=config.get("min_rooms", 1),
            max_rooms=config.get("max_rooms", 3),
            property_types=tuple(config.get("property_types", ("flat", "house"))),
        )
        url = bienici.search_url(filters)
        rules = self._rules(context, cursor, url)
        self._check(rules, url)
        response = raise_for_status(
            context.transport.request(
                "GET",
                url,
                headers=bienici.request_headers(
                    config.get("user_agent", bienici.BROWSER_USER_AGENT)
                ),
                timeout=context.timeout,
            )
        )
        try:
            payload = json.loads(response.body)
        except ValueError as exc:
            raise ParserError("bienici-Antwort ist kein JSON.") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("realEstateAds"), list):
            raise ParserError("bienici-Antwort enthält keine Liste 'realEstateAds'.")
        ads = payload["realEstateAds"]
        seen = set((cursor or {}).get("seen", []))
        mode = config.get("advertiser_names", bienici.DEFAULT_ADVERTISER_NAMES)
        records, issues, new = [], [], []
        for index, ad in enumerate(ads):
            ident = ad.get("id") if isinstance(ad, dict) else None
            if not ident:
                issues.append(RecordIssue(f"{url}#{index}", "Anzeige ohne Kennung."))
                continue
            if ident in seen or ident in new:
                continue
            new.append(ident)
            normalized = bienici.normalise(ad, advertiser_names=mode)
            records.append(
                self._record(context, str(normalized["id"]), ad, normalized, f"{url}#{ident}")
            )
        total = payload.get("total") if isinstance(payload.get("total"), int) else None
        done = len(ads) < size or not new or page >= _positive(config, "max_pages", 20)
        following = (
            None if done else self._cursor(rules, page=page + 1, seen=sorted(seen | set(new)))
        )
        return self._page(records, issues, following, total)


class CityaAdapter(_Portal):
    """Citya result pages per département (config ``departements``: address forms)."""

    def __init__(self) -> None:
        self.source = _source(citya.SOURCE_ID, "Citya (Frankreich, Miete)", "text/html")

    def _departements(self, config: Mapping[str, Any]) -> list[str]:
        value = config.get("departements", [p for p, _ in citya.DEPARTEMENTS.values()])
        if not isinstance(value, list) or not value or not all(isinstance(v, str) for v in value):
            raise ConfigError("'departements' muss eine nicht leere Liste sein.")
        return value

    def validate_config(self, config: Mapping[str, Any]) -> None:
        _robots_policy(config)
        self._departements(config)
        _positive(config, "max_pages", 8)
        _template(config, "url_template", citya.SEARCH, "dep", "seite")

    def fetch_page(self, context: FetchContext, cursor: Cursor) -> PageResult:
        config = context.config
        state = dict(cursor or {})
        deps = self._departements(config)
        dep_index, page = int(state.get("dep", 0)), int(state.get("page", 1))
        dep = deps[dep_index]
        names = {p: n for p, n in citya.DEPARTEMENTS.values()}
        codes = {p: c for c, (p, _) in citya.DEPARTEMENTS.items()}
        url = _template(config, "url_template", citya.SEARCH, "dep", "seite").format(
            dep=dep, seite=page
        )
        rules = self._rules(context, cursor, url)
        doc = self._get_text(context, rules, url)
        seen = set(state.get("seen", []))
        target = int(state.get("sollzahl", 0))
        dep_total = state.get("dep_total")
        if dep_total is None:
            dep_total = citya.total(doc)
            target += dep_total
        offers = citya.catalog(doc)
        records, issues, new = [], [], 0
        for index, offer in enumerate(offers):
            link = offer.get("url") if isinstance(offer, dict) else None
            if not link:
                issues.append(RecordIssue(f"{url}#{index}", "Angebot ohne Adresse (url)."))
                continue
            if link in seen:
                continue
            seen.add(link)
            new += 1
            title = (offer.get("itemOffered") or {}).get("name")
            if not citya.is_residential(title):
                continue
            normalized = citya.normalise(offer, names.get(dep, dep), codes.get(dep))
            records.append(
                self._record(context, str(normalized["id"]), offer, normalized, f"{url}#{link}")
            )
        stop = (
            not offers
            or new == 0
            or page >= _positive(config, "max_pages", 8)
            or (len(seen) >= target and dep_total)
        )
        if not stop:
            following: Cursor = self._cursor(
                rules,
                dep=dep_index,
                page=page + 1,
                seen=sorted(seen),
                sollzahl=target,
                dep_total=dep_total,
            )
        elif dep_index + 1 < len(deps):
            following = self._cursor(
                rules, dep=dep_index + 1, page=1, seen=sorted(seen), sollzahl=target, dep_total=None
            )
        else:
            following = None
        return self._page(records, issues, following, target or None)


class ParuvenduAdapter(_Portal):
    """ParuVendu result pages per département and property kind (30 cards per page)."""

    def __init__(self) -> None:
        self.source = _source(paruvendu.SOURCE_ID, "ParuVendu (Frankreich, Miete)", "text/html")

    def _lists(self, config: Mapping[str, Any]) -> tuple[list[str], list[str]]:
        deps = config.get("departements", [p for p, _ in paruvendu.DEPARTEMENTS.values()])
        kinds = config.get("kinds", ["appartement", "maison"])
        for name, value in (("departements", deps), ("kinds", kinds)):
            if (
                not isinstance(value, list)
                or not value
                or not all(isinstance(v, str) for v in value)
            ):
                raise ConfigError(f"'{name}' muss eine nicht leere Liste sein.")
        return deps, kinds

    def validate_config(self, config: Mapping[str, Any]) -> None:
        _robots_policy(config)
        self._lists(config)
        _positive(config, "max_price", 1100)
        _positive(config, "max_pages", 3)
        _template(config, "url_template", paruvendu.SEARCH, "art", "dep", "hoechstpreis", "seite")

    def fetch_page(self, context: FetchContext, cursor: Cursor) -> PageResult:
        config = context.config
        state = dict(cursor or {})
        deps, kinds = self._lists(config)
        d, k, page = int(state.get("dep", 0)), int(state.get("kind", 0)), int(state.get("page", 1))
        names = {p: n for p, n in paruvendu.DEPARTEMENTS.values()}
        url = _template(
            config, "url_template", paruvendu.SEARCH, "art", "dep", "hoechstpreis", "seite"
        ).format(
            art=kinds[k], dep=deps[d], hoechstpreis=_positive(config, "max_price", 1100), seite=page
        )
        rules = self._rules(context, cursor, url)
        blocks = paruvendu.cards(self._get_text(context, rules, url))
        seen = set(state.get("seen", []))
        records, new = [], 0
        for block in blocks:
            normalized = paruvendu.normalise(block, names.get(deps[d], deps[d]), kinds[k])
            if normalized is None or normalized["id"] in seen:
                continue
            seen.add(normalized["id"])
            new += 1
            records.append(
                self._record(
                    context, str(normalized["id"]), block, normalized, f"{url}#{normalized['id']}"
                )
            )
        stop = (
            len(blocks) < paruvendu.PAGE_SIZE
            or new == 0
            or page >= _positive(config, "max_pages", 3)
        )
        position: tuple[int, int, int] | None = (d, k, page + 1)
        if stop:
            position = (
                (d, k + 1, 1)
                if k + 1 < len(kinds)
                else ((d + 1, 0, 1) if d + 1 < len(deps) else None)
            )
        following = (
            None
            if position is None
            else self._cursor(
                rules, dep=position[0], kind=position[1], page=position[2], seen=sorted(seen)
            )
        )
        return self._page(records, [], following)
