"""Every recorded original call is reproduced exactly or covered by a documented change.

Fixture: ``tests/fixtures/legacy_observed.json`` (``tools/capture_property_sources.py``)
— the original wohnungsmonitor and versteigerung functions executed on the
synthetic, structure-derived pages in ``tests/fixtures/pages``.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import pytest
from support import cases, normalized, observed, page, replay, run

from auditcore_property_sources import (
    adapters,
    bienici,
    citya,
    immobilien_de,
    inberlinwohnen,
    kleinanzeigen,
    paruvendu,
    zvg,
    zvg_lifecycle,
)

MAPPINGS = observed()["synthetic_mappings"]


def plain(value: Any) -> Any:
    """JSON round trip as in the capture (tuples → lists, int keys → text)."""
    return json.loads(json.dumps(value, ensure_ascii=False))


def ids(recorded: list[dict[str, Any]]) -> list[str]:
    return [f"{c['function']}-{i}" for i, c in enumerate(recorded)]


# --------------------------------------------------------------------------- #
# Pure functions: exact replay
# --------------------------------------------------------------------------- #
def _call(group: str, function: str, args: dict[str, Any]) -> Any:
    if group == "immobilien_de":
        if function == "parse_page":
            return immobilien_de.parse_page(page(args["page"]))[0]
        if function == "_mietarten":
            return immobilien_de.rent_types(page(args["page"]))
        if function == "_mietart_zu":
            return immobilien_de.rent_type_for(args["price"], args["arten"])
        if function == "normalise":
            return immobilien_de.normalise(args["raw"], args["plz_bezirke"])
    if group == "inberlinwohnen":
        if function == "total_count":
            return inberlinwohnen.total_count(page(args["page"]))
        if function == "learn_attributes":
            return inberlinwohnen.learn_attributes(page(args["page"]), {})
        if function == "parse_page":
            return inberlinwohnen.parse_page(page(args["page"]))
        if function == "normalise":
            names = {int(k): v for k, v in args["merkmale"].items()}
            return inberlinwohnen.normalise(args["raw"], names)
        if function == "_zahl":
            return inberlinwohnen.number(args["value"])
        if function == "_utc":
            return inberlinwohnen.utc(args["value"])
    if group == "kleinanzeigen":
        if function == "parse_page":
            return kleinanzeigen.parse_page(page(args["page"]))
        if function == "brauchbar":
            return kleinanzeigen.usable(args["raw"])
        if function == "normalise":
            index = kleinanzeigen.district_index(args["ortsteile_bezirke"])
            return kleinanzeigen.normalise(args["raw"], index)
        if function == "_zahl":
            return kleinanzeigen.number(args["value"])
        if function == "_schluessel":
            return kleinanzeigen.place_key(args["value"])
        if function == "suche_url":
            return kleinanzeigen.search_url(args["hoechstpreis"], 1 if not args["seite"] else 2)
    if group == "bienici":
        if function == "normalise":
            return bienici.normalise(args["raw"], advertiser_names="legacy")
        if function == "_datum":
            return bienici.date(args["value"])
        if function == "_ortsform":
            return bienici.place_form(args["value"])
    if group == "citya":
        if function == "katalog":
            return citya.catalog(page(args["page"]))
        if function == "gesamtzahl":
            return citya.total(page(args["page"]))
        if function == "ist_wohnraum":
            return citya.is_residential(args["name"])
        if function == "normalise":
            return citya.normalise(args["raw"], args["dep_name"], args["dep_code"])
    if group == "paruvendu":
        if function == "_karten":
            return paruvendu.cards(page(args["page"]))
        if function == "normalise":
            return paruvendu.normalise(args["block"], args["dep_name"], args["art_vorgabe"])
        if function == "_zahl":
            return paruvendu.number(args["value"])
    if group == "zvg":
        simple = {
            "parse_money_amount": zvg.parse_money_amount,
            "parse_de_number": zvg.parse_de_number,
            "extract_market_value": zvg.extract_market_value,
            "extract_address": zvg.extract_address,
            "classify_type": zvg.classify_type,
            "fix_mojibake": zvg.fix_mojibake,
            "clean": zvg.clean,
            "expand_street": zvg.expand_street,
            "_norm_street": zvg.normalized_street,
        }
        if function in simple:
            return simple[function](args["value"])
        if function == "decode_portal_response":
            return zvg.decode_portal_bytes(bytes.fromhex(args["body_hex"]))
        if function == "parse_listing_akten":
            return zvg.parse_listing_akten(page(args["page"]), args["land"])
        if function == "parse_detail":
            notice = zvg.ZvgNotice(
                zvg_id="880001",
                land="he",
                court_id="M1201",
                court_name=zvg.COURT_NAMES["M1201"],
                detail_url=zvg.detail_url("880001", "he"),
            )
            return zvg.parse_detail(
                page(args["page"]), notice, reference_year=args["reference_year"]
            ).to_dict()
        if function == "resolve_courts":
            return zvg.resolve_courts(args["arg"])
        if function == "courts":
            return {"he": zvg.COURTS_HE, "rp": zvg.COURTS_RP, "kern": zvg.KERN_COURTS}
    raise LookupError(f"{group}.{function}")


PURE = [
    json.loads(json.dumps(c))
    for c in observed()["cases"]
    if c["function"]
    not in {"hole_bestand", "ZvgPortal.search_court", "ZvgPortal.detail", "portal_requests"}
]


@pytest.mark.parametrize(
    "case", PURE, ids=[f"{c['group']}.{c['function']}-{i}" for i, c in enumerate(PURE)]
)
def test_pure_function_reproduces_the_original_exactly(case: dict[str, Any]) -> None:
    assert case["exception"] is None
    expected = case["output"]
    if case["function"] == "parse_detail":
        # PS-C05: coordinates come from geocoding, which stays with the consumer.
        assert (expected.pop("lat"), expected.pop("lon")) == (None, None)
    assert plain(_call(case["group"], case["function"], case["args"])) == expected


def test_bienici_minimal_mode_only_hides_private_advertiser_names() -> None:
    """PS-C02: the only difference to the original is the name of private advertisers."""
    for case in cases("bienici", "normalise"):
        legacy, minimal = case["output"], bienici.normalise(case["args"]["raw"])
        if case["args"]["raw"].get("accountType") == "individual":
            assert legacy["gesellschaft"] == "M. Exemple"
            assert minimal["gesellschaft"] == "Privatangebot"
            legacy = {**legacy, "gesellschaft": "Privatangebot"}
        assert plain(minimal) == legacy


def test_search_court_misses_escaped_links_while_the_parsed_listing_does_not() -> None:
    """PS-L05: ``ZvgPortal.search_court`` reads raw HTML and misses ``&amp;`` links."""
    escaped, raw = cases("zvg", "ZvgPortal.search_court")
    assert escaped["output"] == [] and raw["output"] == ["880001", "880002", "880003", "880004"]
    assert zvg.listing_ids(page("zvg/liste.html"), "he") == raw["output"]
    assert zvg.listing_ids(page("zvg/liste-roh.html"), "he") == raw["output"]


def test_portal_requests_equal_the_adapter_request_pattern() -> None:
    recorded = cases("zvg", "portal_requests")[0]["output"]
    post = recorded[0]
    assert post["method"] == "POST" and post["params"] == {"button": "Suchen"}
    assert post["data"] == {
        "button": "Suchen",
        "land_abk": "he",
        "ger_id": "M1201",
        "order_by": "2",
        "art": "",
        "gbuch": "",
    }
    detail = cases("zvg", "ZvgPortal.detail")[0]
    assert detail["output"] == "<html>detail</html>"
    assert recorded[-1]["params"] == {"button": "showZvg", "zvg_id": "880001", "land_abk": "he"}


# --------------------------------------------------------------------------- #
# Paging (original hole_bestand) versus the harvest adapters on the same pages
# --------------------------------------------------------------------------- #
def _web(case: dict[str, Any], pages: dict[str, str]) -> dict[str, str]:
    requested = case["args"]["requested"]
    return {url: page(pages[url]) for url in requested if url in pages}


def _legacy(case: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(case["output"][0], key=lambda d: str(d["id"]))


def test_immobilien_de_paging() -> None:
    case = cases("immobilien_de", "hole_bestand")[0]
    web = {
        immobilien_de.search_url(700, 1): page("immobilien_de/seite-1.html"),
        immobilien_de.search_url(700, 2): page("immobilien_de/seite-1.html"),
        immobilien_de.search_url(700, 3): page("immobilien_de/leer.html"),
    }
    adapter = adapters.ImmobilienDeAdapter(MAPPINGS["plz_bezirke"])
    result, sink = run(adapter, replay(web, robots=None), {"max_price": 700, "pages": 3})
    assert result.pages == 2 and len(case["args"]["requested"]) == 2
    assert plain(normalized(sink)) == _legacy(case)
    assert result.status.value == "partial" and "JSON-LD" in result.issues[0].message  # PS-C06


def test_inberlinwohnen_paging() -> None:
    case = cases("inberlinwohnen", "hole_bestand")[0]
    web = {
        inberlinwohnen.page_url(1): page("inberlinwohnen/seite-1.html"),
        inberlinwohnen.page_url(2): page("inberlinwohnen/seite-2.html"),
        inberlinwohnen.page_url(3): page("inberlinwohnen/leer.html"),
    }
    result, sink = run(adapters.InBerlinWohnenAdapter(), replay(web, robots=None), {})
    assert result.pages == 3 == len(case["args"]["requested"])
    assert plain(normalized(sink)) == _legacy(case) and case["output"][1] == 1203


def test_kleinanzeigen_paging() -> None:
    case = cases("kleinanzeigen", "hole_bestand")[0]
    web = {
        kleinanzeigen.search_url(700, 1): page("kleinanzeigen/seite-1.html"),
        kleinanzeigen.search_url(700, 2): page("kleinanzeigen/leer.html"),
    }
    adapter = adapters.KleinanzeigenAdapter(MAPPINGS["ortsteile_bezirke"])
    result, sink = run(adapter, replay(web, robots=None), {"max_price": 700, "pages": 3})
    assert result.pages == 2 == len(case["args"]["requested"])
    assert plain(normalized(sink)) == _legacy(case)


def test_bienici_paging() -> None:
    case = cases("bienici", "hole_bestand")[0]
    web = dict(
        zip(
            case["args"]["requested"],
            (page(f"bienici/seite-{n}.json") for n in (1, 2, 3)),
            strict=True,
        )
    )
    config = {"zones": ["-7415"], "page_size": 2, "advertiser_names": "legacy"}
    result, sink = run(adapters.BieniciAdapter(), replay(web, robots=None), config)
    assert result.pages == 3 and plain(normalized(sink)) == _legacy(case)
    assert result.issues[0].message == "Anzeige ohne Kennung."  # PS-C06


def test_citya_paging() -> None:
    case = cases("citya", "hole_bestand")[0]
    web = {citya.search_url("bas-rhin-67", n): page("citya/seite-1.html") for n in (1, 2)}
    result, sink = run(
        adapters.CityaAdapter(), replay(web, robots=None), {"departements": ["bas-rhin-67"]}
    )
    assert result.pages == 2 == len(case["args"]["requested"])
    assert plain(normalized(sink)) == _legacy(case)
    assert result.issues and "ohne Adresse" in result.issues[0].message  # PS-C06


def test_paruvendu_paging() -> None:
    case = cases("paruvendu", "hole_bestand")[0]
    web = {
        paruvendu.search_url("appartement", "bas-rhin-67", 1100, 1): page("paruvendu/seite-1.html")
    }
    result, sink = run(
        adapters.ParuvenduAdapter(),
        replay(web, robots=None),
        {"departements": ["bas-rhin-67"], "kinds": ["appartement"]},
    )
    assert result.pages == 1 and plain(normalized(sink)) == _legacy(case)


# --------------------------------------------------------------------------- #
# ZVG lifecycle: original SQL on PostgreSQL versus the pure functions
# --------------------------------------------------------------------------- #
def _state(entry: dict[str, Any], name: str) -> zvg_lifecycle.CaseState:
    def when(text: str | None) -> datetime | None:
        return None if text is None else datetime.fromisoformat(text)

    return zvg_lifecycle.CaseState(
        file_number=name,
        status=entry["status"],
        last_seen_at=when(entry["last_seen_at"]),
        closed_at=when(entry["closed_at"]),
        deleted=entry["deleted"],
        dates=tuple(datetime.fromisoformat(d) for d in entry["dates"]),
    )


def test_lifecycle_steps_reproduce_the_original_sql() -> None:
    lifecycle = observed()["lifecycle"]
    assert lifecycle["status"] == "OBSERVED" and lifecycle["database"].startswith("PostgreSQL")
    steps = lifecycle["steps"]
    courts = {"M1201": "Frankfurt am Main", "M1906": "Wiesbaden"}
    state = {n: _state(e, n) for n, e in steps[0]["state"].items()}
    court_of = {n: e["court"] for n, e in steps[0]["state"].items()}
    for step in steps[1:]:
        court = courts[step["court"]]
        mine = [c for n, c in state.items() if court_of[n] == court]
        now = datetime.fromisoformat(step.get("now_before") or step_now(steps, step))
        if step["step"] == "mark_seen":
            updated = zvg_lifecycle.mark_seen(mine, step["listed"], now)
        elif step["step"] == "close_vanished":
            updated, closed = zvg_lifecycle.close_vanished(mine, now, step["grace_days"])
            assert closed == step["closed"]
        else:
            name = step["file_number"]
            termin = None if step["termin"] is None else datetime.fromisoformat(step["termin"])
            updated = [
                zvg_lifecycle.reappear(c, termin, now) if c.file_number == name else c for c in mine
            ]
        for case in updated:
            state[case.file_number] = case
        for name, expected in step["state"].items():
            got = state[name]
            assert got.status == expected["status"], (step["step"], name)
            assert (got.closed_at is not None) == (expected["closed_at"] is not None), name
            seen_changed = expected["last_seen_at"] != steps[0]["state"][name]["last_seen_at"]
            if seen_changed and step["step"] in {"mark_seen", "upsert"}:
                assert got.last_seen_at is not None


def step_now(steps: list[dict[str, Any]], step: dict[str, Any]) -> str:
    """Steps without an own clock reading use the previous one (mark_seen with empty list)."""
    before = [s.get("now_before") for s in steps[: steps.index(step)] if s.get("now_before")]
    return str(before[-1])


def test_lifecycle_fixture_covers_the_documented_transitions() -> None:
    steps = observed()["lifecycle"]["steps"]
    closed = {s["court"]: s["state"] for s in steps if s["step"] == "close_vanished"}
    after = closed["M1201"]
    assert after["verschwunden-termin-vorbei"]["status"] == "abgehalten"
    assert after["verschwunden-termin-zukunft"]["status"] == "aufgehoben"
    assert after["verschwunden-gemischt"]["status"] == "aufgehoben"
    assert after["verschwunden-ohne-termin"]["status"] == "aufgehoben"
    assert after["karenz-nicht-abgelaufen"]["status"] == "terminiert"
    assert after["nie-gesehen"]["closed_at"] is None and after["geloescht"]["closed_at"] is None
    assert after["anderes-gericht"]["closed_at"] is None
    assert closed["M1906"]["anderes-gericht"]["status"] == "abgehalten"
    upserts = [s for s in steps if s["step"] == "upsert"]
    assert [u["state"][u["file_number"]]["status"] for u in upserts] == [
        "terminiert",
        "erfasst",
        "erfasst",
    ]
