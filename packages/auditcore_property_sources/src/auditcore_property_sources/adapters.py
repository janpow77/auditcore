"""Harvest adapters (extra ``auditcore_property_sources[sources]``) on ``auditcore_harvest``.

One adapter per source profile; each translates exactly one page into
:class:`auditcore_harvest.HarvestRecord` objects, reproducing the paging and
stop rules of the original ``hole_bestand`` functions. Timeouts, bounded
retries, rate limiting, checkpoints and partial failures belong to the
``HarvestEngine``; transport (including user agent, cookies and sessions) is
injected by the consumer. Nothing here sleeps, stores or schedules.

**Access rules.** Before the first request to an ``http(s)`` address the
adapter reads the portal's robots.txt through the injected transport and
refuses every disallowed address with :class:`AccessNotPermittedError`
(non-retryable). The rules travel in the cursor, so a resumed run keeps the
decision of its first page. ``file:`` addresses (archived pages served by a
consumer ``FileTransport``) are not checked.
"""

from __future__ import annotations

import json
import urllib.parse
from collections.abc import Mapping, Sequence
from typing import Any

try:
    from auditcore_harvest import (
        AuthKind,
        Capabilities,
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
    from auditcore_harvest.adapter import require
    from auditcore_harvest.errors import ConfigError
except ImportError as exc:  # pragma: no cover - exercised without the extra
    from .errors import DependencyError

    raise DependencyError(
        "auditcore_harvest fehlt: auditcore_property_sources[sources] installieren."
    ) from exc

from . import bienici, citya, immobilien_de, inberlinwohnen, kleinanzeigen, paruvendu, zvg
from .robots import RobotsRules, is_allowed, parse_robots, robots_url

ADAPTER_VERSION = "1.0.0"
Cursor = Mapping[str, Any] | None


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


def _positive(config: Mapping[str, Any], name: str, default: int) -> int:
    value = config.get(name, default)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ConfigError(f"'{name}' muss eine positive ganze Zahl sein.")
    return value


def _template(config: Mapping[str, Any], name: str, default: str, *fields: str) -> str:
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
        raw: Any,
        normalized: Mapping[str, Any],
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
    def _cursor(rules: RobotsRules | None, **state: Any) -> dict[str, Any]:
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


# --------------------------------------------------------------------------- #
# Berlin (wohnungsmonitor profile "berlin")
# --------------------------------------------------------------------------- #
class ImmobilienDeAdapter(_Portal):
    """immobilien.de result pages up to ``max_price`` (config ``max_price``, ``pages``)."""

    def __init__(self, plz_bezirke: Mapping[str, Sequence[str]]) -> None:
        self.source = _source(immobilien_de.SOURCE_ID, "immobilien.de (Berlin, Miete)", "text/html")
        self.plz_bezirke = dict(plz_bezirke)

    def validate_config(self, config: Mapping[str, Any]) -> None:
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
    """Kleinanzeigen result pages; the original address is disallowed by robots.txt."""

    def __init__(self, ortsteile_bezirke: Mapping[str, str]) -> None:
        self.source = _source(
            kleinanzeigen.SOURCE_ID, "Kleinanzeigen (Berlin, Mietwohnungen)", "text/html"
        )
        self.districts = kleinanzeigen.district_index(ortsteile_bezirke)

    def validate_config(self, config: Mapping[str, Any]) -> None:
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


# --------------------------------------------------------------------------- #
# Alsace/Lorraine (wohnungsmonitor profile "frankreich")
# --------------------------------------------------------------------------- #
class BieniciAdapter(_Portal):
    """bienici.com JSON search per zone list (config ``zones`` required)."""

    def __init__(self) -> None:
        self.source = _source(bienici.SOURCE_ID, "bien'ici (Frankreich, Miete)", "application/json")

    def validate_config(self, config: Mapping[str, Any]) -> None:
        zones = require(config, "zones", list)
        if not zones or not all(isinstance(z, str) and z for z in zones):
            raise ConfigError("'zones' muss eine nicht leere Liste von Zonenkennungen sein.")
        _positive(config, "max_price", 1100)
        _positive(config, "page_size", 200)
        _positive(config, "max_pages", 20)
        if config.get("advertiser_names", "minimal") not in ("minimal", "legacy"):
            raise ConfigError("'advertiser_names' ist 'minimal' oder 'legacy'.")

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
        response = raise_for_status(context.transport.request("GET", url, timeout=context.timeout))
        try:
            payload = json.loads(response.body)
        except ValueError as exc:
            raise ParserError("bienici-Antwort ist kein JSON.") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("realEstateAds"), list):
            raise ParserError("bienici-Antwort enthält keine Liste 'realEstateAds'.")
        ads = payload["realEstateAds"]
        seen = set((cursor or {}).get("seen", []))
        mode = config.get("advertiser_names", "minimal")
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


# --------------------------------------------------------------------------- #
# ZVG-Portal (versteigerung)
# --------------------------------------------------------------------------- #
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
    """Detail pages of given notices (config ``notices``); disallowed live by robots.txt.

    Usable with archived detail pages (``detail_url_template`` with ``file:``)
    that the consumer obtained lawfully. ``reference_year`` for the plausible
    *Baujahr* comes from the injected clock.
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
        response = raise_for_status(context.transport.request("GET", url, timeout=context.timeout))
        doc = zvg.decode_portal_bytes(response.body)
        if "<html" not in doc[:4096].lower():
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
        following = self._cursor(rules, notice=index + 1) if index + 1 < len(notices) else None
        return self._page([record], [], following, len(notices))


__all__ = [
    "ADAPTER_VERSION",
    "AccessNotPermittedError",
    "BieniciAdapter",
    "CityaAdapter",
    "ImmobilienDeAdapter",
    "InBerlinWohnenAdapter",
    "KleinanzeigenAdapter",
    "ParuvenduAdapter",
    "ZvgDetailAdapter",
    "ZvgListingAdapter",
]
