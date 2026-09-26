"""Harvest contract of every adapter plus the robots.txt enforcement."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from auditcore_harvest import FileTransport, ReplayTransport, RunStatus
from auditcore_harvest.testing import assert_adapter
from support import exchange, observed, page, replay, robots_text, run

from auditcore_property_sources import (
    bienici,
    citya,
    immobilien_de,
    inberlinwohnen,
    kleinanzeigen,
    paruvendu,
    zvg,
)
from auditcore_property_sources.adapters import (
    BieniciAdapter,
    CityaAdapter,
    ImmobilienDeAdapter,
    InBerlinWohnenAdapter,
    KleinanzeigenAdapter,
    ParuvenduAdapter,
    ZvgDetailAdapter,
    ZvgListingAdapter,
)

MAPPINGS = observed()["synthetic_mappings"]
ROBOTS = {
    "www.immobilien.de": "immobilien.de",
    "www.inberlinwohnen.de": "inberlinwohnen.de",
    "www.kleinanzeigen.de": "kleinanzeigen.de",
    "www.bienici.com": "bienici.com",
    "www.citya.com": "citya.com",
    "www.paruvendu.fr": "paruvendu.fr",
    "www.zvg-portal.de": "zvg-portal.de",
}


def with_robots(
    pages: dict[str, str],
    host: str,
    extra: list[dict[str, Any]] | None = None,
) -> Callable[[], ReplayTransport]:
    text = robots_text(ROBOTS[host])
    return lambda: replay(pages, robots=(f"https://{host}/robots.txt", text), extra=extra)


def clean(name: str) -> str:
    """Synthetic page without its deliberately broken parts (the contract needs ``complete``)."""
    text = page(name)
    for broken in (
        '<script type="application/ld+json">{kaputt</script>',
        '<div wire:snapshot="{kein json" >y</div>',
        '<tr><td><a href="index.php?button=showZvg&amp;zvg_id=880004&amp;land_abk=he">'
        "<b>ohne Aktenzeichen</b></a></td></tr>",
    ):
        text = text.replace(broken, "")
    if name.startswith("bienici/"):
        data = json.loads(text)
        data["realEstateAds"] = [a for a in data["realEstateAds"] if a.get("id")]
        text = json.dumps(data)
    if name.startswith("citya/"):
        text = text.replace(
            '"url": ""', '"url": "https://www.citya.com/annonces/location/x/100005"'
        )
    return text


def zvg_listing_exchanges(listing: str = "zvg/liste.html") -> list[dict[str, Any]]:
    return [
        exchange(zvg.BASE, "<html>Termine suchen</html>", params={"button": "Termine suchen"}),
        exchange(
            zvg.BASE,
            page(listing) if listing == "zvg/liste.html" else listing,
            method="POST",
            params={"button": "Suchen"},
        ),
        exchange("https://www.zvg-portal.de/robots.txt", robots_text("zvg-portal.de")),
    ]


CONTRACT: list[tuple[str, Callable[[], Any], dict[str, Any], Callable[[], ReplayTransport]]] = [
    (
        "immobilien_de",
        lambda: ImmobilienDeAdapter(MAPPINGS["plz_bezirke"]),
        {"max_price": 700, "pages": 2},
        with_robots(
            {
                immobilien_de.search_url(700, 1): clean("immobilien_de/seite-1.html"),
                immobilien_de.search_url(700, 2): page("immobilien_de/leer.html"),
            },
            "www.immobilien.de",
        ),
    ),
    (
        "inberlinwohnen",
        InBerlinWohnenAdapter,
        {},
        with_robots(
            {
                inberlinwohnen.page_url(1): clean("inberlinwohnen/seite-1.html"),
                inberlinwohnen.page_url(2): page("inberlinwohnen/seite-2.html"),
                inberlinwohnen.page_url(3): page("inberlinwohnen/leer.html"),
            },
            "www.inberlinwohnen.de",
        ),
    ),
    (
        "kleinanzeigen-archiv",
        lambda: KleinanzeigenAdapter(MAPPINGS["ortsteile_bezirke"]),
        {"pages": 2, "url_template": "https://archiv.invalid/ka/{seite}{hoechstpreis}.html"},
        lambda: replay(
            {
                "https://archiv.invalid/ka/700.html": page("kleinanzeigen/seite-1.html"),
                "https://archiv.invalid/ka/seite:2/700.html": page("kleinanzeigen/leer.html"),
            },
            robots=None,
        ),
    ),
    (
        "bienici",
        BieniciAdapter,
        {"zones": ["-7415"], "page_size": 2},
        with_robots(
            {
                bienici.search_url(
                    bienici.search_filter(["-7415"], max_price=1100, page=n, page_size=2)
                ): clean(f"bienici/seite-{n}.json")
                for n in (1, 2, 3)
            },
            "www.bienici.com",
        ),
    ),
    (
        "citya",
        CityaAdapter,
        {"departements": ["bas-rhin-67"]},
        with_robots(
            {citya.search_url("bas-rhin-67", n): clean("citya/seite-1.html") for n in (1, 2)},
            "www.citya.com",
        ),
    ),
    (
        "paruvendu",
        ParuvenduAdapter,
        {"departements": ["bas-rhin-67"], "kinds": ["appartement"]},
        with_robots(
            {
                paruvendu.search_url("appartement", "bas-rhin-67", 1100, 1): page(
                    "paruvendu/seite-1.html"
                )
            },
            "www.paruvendu.fr",
        ),
    ),
    (
        "zvg-liste",
        ZvgListingAdapter,
        {"courts": ["M1201"]},
        lambda: ReplayTransport(tuple(zvg_listing_exchanges(clean("zvg/liste.html")))),
    ),
]


@pytest.mark.parametrize(
    ("name", "factory", "config", "transport"), CONTRACT, ids=[c[0] for c in CONTRACT]
)
def test_adapter_fulfils_the_harvest_contract(
    name: str,
    factory: Callable[[], Any],
    config: dict[str, Any],
    transport: Callable[[], ReplayTransport],
) -> None:
    report = assert_adapter(factory, config=config, transport_factory=transport, min_records=1)
    assert report.cases["missing_credentials"].startswith("SKIPPED")


def test_kleinanzeigen_original_address_is_fetched_by_default_without_robots() -> None:
    """PS-D01 (DECIDED 2026-09-23): default ``robots_policy="ignore"`` fetches like the original."""
    adapter = KleinanzeigenAdapter(MAPPINGS["ortsteile_bezirke"])
    transport = with_robots(
        {kleinanzeigen.search_url(700, 1): page("kleinanzeigen/seite-1.html")},
        "www.kleinanzeigen.de",
    )()
    result, sink = run(adapter, transport, {"max_price": 700, "pages": 1})
    assert result.status is RunStatus.COMPLETE and sink.records
    urls = [c["url"] for c in transport.calls]
    assert "https://www.kleinanzeigen.de/robots.txt" not in urls
    assert urls == [kleinanzeigen.search_url(700, 1)]


def test_kleinanzeigen_original_address_is_refused_when_robots_are_respected() -> None:
    """The original search path matches ``Disallow: /*/preis:*``."""
    adapter = KleinanzeigenAdapter(MAPPINGS["ortsteile_bezirke"])
    transport = with_robots(
        {kleinanzeigen.search_url(700, 1): page("kleinanzeigen/seite-1.html")},
        "www.kleinanzeigen.de",
    )()
    result, sink = run(adapter, transport, {"max_price": 700, "robots_policy": "respect"})
    assert result.status is RunStatus.FAILED and not sink.records
    assert result.errors[0]["code"] == "access_not_permitted"
    assert result.errors[0]["retryable"] is False and result.attempts == 1
    assert [c["url"] for c in transport.calls] == ["https://www.kleinanzeigen.de/robots.txt"]


def test_zvg_detail_pages_are_fetched_live_by_default() -> None:
    """PS-D01 (DECIDED 2026-09-23): ``showZvg`` is fetched like the original."""
    notices = {"notices": [{"zvg_id": "880001", "court_id": "M1201"}]}
    url = zvg.BASE + "?button=showZvg&zvg_id=880001&land_abk=he"
    session = exchange(zvg.BASE, "<html>x</html>", params={"button": "Termine suchen"})
    live = replay({url: page("zvg/detail-efh.html")}, robots=None, extra=[session])
    result, sink = run(ZvgDetailAdapter(), live, notices)
    assert result.status is RunStatus.COMPLETE and len(sink.records) == 1
    # PS-C09: session first, then the detail page with the result list as referer
    assert [(c["url"], c["params"]) for c in live.calls] == [
        (zvg.BASE, {"button": "Termine suchen"}),
        (url, {}),
    ]
    assert "referer" in live.calls[1]["header_names"]


def test_zvg_detail_pages_are_refused_when_respected_but_work_from_an_archive(
    tmp_path: Path,
) -> None:
    notices = {"notices": [{"zvg_id": "880001", "court_id": "M1201"}]}
    live = replay(
        {},
        robots=None,
        extra=[exchange("https://www.zvg-portal.de/robots.txt", robots_text("zvg-portal.de"))],
    )
    result, _ = run(ZvgDetailAdapter(), live, {**notices, "robots_policy": "respect"})
    assert result.errors[0]["code"] == "access_not_permitted"
    assert "showZvg" in result.errors[0]["message"]

    archive = tmp_path / "zvg"
    archive.mkdir()
    (archive / "880001.html").write_text(page("zvg/detail-efh.html"), encoding="utf-8")
    config = {**notices, "detail_url_template": "file:zvg/{zvg_id}.html"}
    result, sink = run(ZvgDetailAdapter(), FileTransport(tmp_path), config)
    assert result.status is RunStatus.COMPLETE, result.errors
    record = next(iter(sink.records.values()))
    assert record.normalized["file_number"] == "5 K 12/24"
    assert record.normalized["market_value"] is None  # PS-L03: amount without currency sign
    assert record.normalized["build_year"] == 1968


def test_zvg_listing_request_shape_and_issues() -> None:
    transport = ReplayTransport(tuple(zvg_listing_exchanges()))
    result, sink = run(ZvgListingAdapter(), transport, {"courts": ["M1201"]})
    assert result.status is RunStatus.PARTIAL
    assert [i.message for i in result.issues] == ["Bekanntmachung ohne Aktenzeichen."]
    assert sorted(r.normalized["file_number"] for r in sink.records.values()) == [
        "12 K 7/2025",
        "3 L 1/23",
        "5 K 12/24",
    ]
    post = [c for c in transport.calls if c["method"] == "POST"]
    assert post and post[0]["params"] == {"button": "Suchen"}
    assert "content-type" in post[0]["header_names"]


@pytest.mark.parametrize(
    ("factory", "config"),
    [
        (lambda: ImmobilienDeAdapter({}), {"pages": 0}),
        (lambda: ImmobilienDeAdapter({}), {"url_template": "ftp://x/{hoechstpreis}{seite}"}),
        (lambda: ImmobilienDeAdapter({}), {"url_template": "https://x/{seite}"}),
        (BieniciAdapter, {}),
        (BieniciAdapter, {"zones": []}),
        (BieniciAdapter, {"zones": ["1"], "advertiser_names": "alle"}),
        (BieniciAdapter, {"zones": ["1"], "user_agent": ""}),
        (BieniciAdapter, {"zones": ["1"], "robots_policy": "manchmal"}),
        (InBerlinWohnenAdapter, {"robots_policy": True}),
        (CityaAdapter, {"departements": "bas-rhin-67"}),
        (ParuvenduAdapter, {"kinds": []}),
        (ZvgListingAdapter, {"courts": ["X9999"]}),
        (ZvgListingAdapter, {"courts": []}),
        (ZvgDetailAdapter, {"notices": []}),
        (ZvgDetailAdapter, {"notices": [{"zvg_id": "abc", "court_id": "M1201"}]}),
    ],
)
def test_invalid_configuration_is_rejected(
    factory: Callable[[], Any], config: dict[str, Any]
) -> None:
    from auditcore_harvest import ConfigError

    with pytest.raises(ConfigError):
        factory().validate_config(config)


def test_unavailable_robots_txt_means_no_rules_and_server_errors_are_retried() -> None:
    web = {inberlinwohnen.page_url(1): page("inberlinwohnen/leer.html")}
    result, _ = run(InBerlinWohnenAdapter(), replay(web, robots=None), {"robots_policy": "respect"})
    assert result.status is RunStatus.COMPLETE
    broken = ReplayTransport(
        (
            exchange(inberlinwohnen.page_url(1), page("inberlinwohnen/leer.html")),
            exchange("https://www.inberlinwohnen.de/robots.txt", "", status=503),
        )
    )
    result, _ = run(InBerlinWohnenAdapter(), broken, {"robots_policy": "respect"})
    assert result.status is RunStatus.FAILED and result.errors[0]["retryable"] is True


def test_zvg_listing_pages_through_the_courts_in_order() -> None:
    second = clean("zvg/liste.html").replace("8800", "7700").replace("5 K 12/24", "6 K 3/25")
    session = exchange(zvg.BASE, "<html>x</html>", params={"button": "Termine suchen"})
    transport = ReplayTransport(
        (
            exchange("https://www.zvg-portal.de/robots.txt", robots_text("zvg-portal.de")),
            session,
            exchange(zvg.BASE, clean("zvg/liste.html"), method="POST", params={"button": "Suchen"}),
            dict(session),
            exchange(zvg.BASE, second, method="POST", params={"button": "Suchen"}),
        ),
        ordered=True,
    )
    result, sink = run(
        ZvgListingAdapter(), transport, {"courts": ["M1201", "M1406"], "robots_policy": "respect"}
    )
    assert result.status is RunStatus.COMPLETE and result.pages == 2
    courts = {r.normalized["zvg_id"]: r.normalized["court_id"] for r in sink.records.values()}
    assert courts["880001"] == "M1201" and courts["770001"] == "M1406"
    assert [c["method"] for c in transport.calls] == ["GET", "GET", "POST", "GET", "POST"]


def _bienici_transport() -> ReplayTransport:
    url = bienici.search_url(
        bienici.search_filter(["-7415"], max_price=1100, page=1, page_size=200)
    )
    return replay({url: clean("bienici/seite-3.json")}, robots=None)


def test_bienici_sends_the_original_browser_headers_by_default() -> None:
    """PS-D02 (DECIDED 2026-09-23): browser user agent like the original ``_hole``."""
    transport = _bienici_transport()
    run(BieniciAdapter(), transport, {"zones": ["-7415"], "max_pages": 1})
    assert transport.calls[0]["header_names"] == [
        "accept",
        "accept-language",
        "referer",
        "user-agent",
    ]
    assert bienici.request_headers()["User-Agent"].startswith("Mozilla/5.0 (X11; Linux x86_64)")


def test_bienici_user_agent_none_leaves_the_agent_to_the_transport() -> None:
    transport = _bienici_transport()
    run(BieniciAdapter(), transport, {"zones": ["-7415"], "max_pages": 1, "user_agent": None})
    assert "user-agent" not in transport.calls[0]["header_names"]
    assert "User-Agent" not in bienici.request_headers(None)
