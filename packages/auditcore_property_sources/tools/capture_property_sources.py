"""Capture the actual behavior of the wohnungsmonitor and versteigerung parsers.

Run with an interpreter providing the versteigerung pins (beautifulsoup4
4.12.3, httpx 0.28.1, psycopg 3.2.3)::

    python -I tools/capture_property_sources.py <wohnungsmonitor> <versteigerung> \
        tests/fixtures/legacy_observed.json [--dsn postgresql://…]

Every source module is loaded unchanged from its file after verifying the
pinned Git blob. Inputs are the synthetic, structure-derived pages of
``tools/synthetic_pages.py``; network access is replaced by an in-memory page
map (``fetch``/``_hole``/``time.sleep`` are patched on the loaded module), so
no portal is contacted. With ``--dsn`` the original ``Ingest.mark_seen``,
``Ingest.close_vanished`` and ``Ingest.upsert`` run against a throwaway
PostgreSQL/PostGIS database migrated with the original Alembic migrations;
the lifecycle scenarios set ``last_seen_at`` and dates explicitly and record
the resulting status transitions.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
import synthetic_pages as sp  # noqa: E402

WOHNUNGSMONITOR = ("janpow77/wohnungsmonitor", "76571bfaa3435bfc6858b3cbaae8c4ea3969ef91")
VERSTEIGERUNG = ("janpow77/versteigerung", "e4ad7af0eaee0b151cc5e3358f95b961d7f3a448")
FILES = {
    "immobilien_export": ("immobilien_export.py", "44233aea7651855d51b26c3d173f624ca96a389b"),
    "inberlinwohnen_export": (
        "inberlinwohnen_export.py",
        "c044ed39271412c20978c41ec51e7f382def7336",
    ),
    "kleinanzeigen_export": (
        "kleinanzeigen_export.py",
        "8a7c8cba46e15b424f48ae95be43989a10c1b39f",
    ),
    "bienici_export": ("bienici_export.py", "5a8cc85e222193c505b6fd4dec43394ffd5fb015"),
    "citya_export": ("citya_export.py", "d5cc5d625bf19dca6f1c6a918069df6f35ae8509"),
    "paruvendu_export": ("paruvendu_export.py", "22f98c9f36d0299fe220743f40234b7119c7e62d"),
}
ZVG = ("backend/app/crawler/zvg_crawler.py", "b10ad2a63725246d3867bf9dd66329fc71e986cb")
#: Synthetic Berlin mappings (the real plz_bezirke.json/ortsteile_bezirke.json stay
#: consumer data of wohnungsmonitor and are not copied).
PLZ_BEZIRKE = {
    "10245": ["Friedrichshain-Kreuzberg"],
    "10961": ["Friedrichshain-Kreuzberg"],
    "12043": ["Neukölln"],
    "13055": ["Lichtenberg", "Marzahn-Hellersdorf"],
}
ORTSTEILE = {
    "Friedrichshain": "Friedrichshain-Kreuzberg",
    "Prenzlauer Berg": "Pankow",
    "Weißensee": "Pankow",
    "Neukölln": "Neukölln",
}


def git_blob(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def head(repo: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()


def load(path: Path, blob: str, name: str) -> ModuleType:
    if git_blob(path) != blob:
        raise SystemExit(f"{path} ist nicht der gepinnte Blob")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # dataclasses resolve annotations through sys.modules
    spec.loader.exec_module(module)
    return module


def plain(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        items = [plain(v) for v in value]
        return sorted(items, key=repr) if isinstance(value, (set, frozenset)) else items
    if isinstance(value, datetime):
        return {"$datetime": value.isoformat()}
    return value


class Recorder:
    def __init__(self) -> None:
        self.cases: list[dict[str, Any]] = []

    def call(self, group: str, function: str, args: dict[str, Any], run: Any) -> Any:
        try:
            output = run()
            error = None
        except Exception as exc:  # noqa: BLE001 - characterization records every error
            output = None
            error = {"type": type(exc).__name__, "message": str(exc)}
        self.cases.append(
            {
                "group": group,
                "function": function,
                "args": plain(args),
                "output": plain(output),
                "exception": error,
            }
        )
        return output


def patched_fetch(module: ModuleType, pages: dict[str, str], attr: str, log: list[str]) -> None:
    def fake(url: str, *args: Any, **kwargs: Any) -> Any:
        log.append(url)
        if url not in pages:
            raise RuntimeError(f"keine synthetische Seite für {url}")
        body = pages[url]
        return json.loads(body) if attr == "_hole" and module.__name__ == "bienici_export" else body

    setattr(module, attr, fake)
    module.time.sleep = lambda seconds: None  # type: ignore[attr-defined]


def capture_wohnungsmonitor(root: Path, rec: Recorder) -> dict[str, ModuleType]:
    mods = {k: load(root / p, b, k) for k, (p, b) in FILES.items()}
    pages = sp.all_pages()

    # immobilien.de ---------------------------------------------------------
    imde = mods["immobilien_export"]
    page = pages["immobilien_de/seite-1.html"]
    imde._PLZ_BEZIRKE = dict(PLZ_BEZIRKE)
    raw = rec.call(
        "immobilien_de",
        "parse_page",
        {"page": "immobilien_de/seite-1.html"},
        lambda: imde.parse_page(page),
    )
    rec.call(
        "immobilien_de",
        "_mietarten",
        {"page": "immobilien_de/seite-1.html"},
        lambda: imde._mietarten(page),
    )
    for item in (raw or {}).values():
        rec.call(
            "immobilien_de",
            "normalise",
            {"raw": item, "plz_bezirke": PLZ_BEZIRKE},
            lambda item=item: imde.normalise(item),
        )
    imde._PLZ_BEZIRKE = {}
    for item in list((raw or {}).values())[:2]:
        rec.call(
            "immobilien_de",
            "normalise",
            {"raw": item, "plz_bezirke": {}},
            lambda item=item: imde.normalise(item),
        )
    arten = imde._mietarten(page)
    for price in (593.67, 640, "640", 702.5, 1234.5, 455.0, None, "x", 0):
        rec.call(
            "immobilien_de",
            "_mietart_zu",
            {"price": price, "arten": arten},
            lambda price=price: imde._mietart_zu(price, arten),
        )
    rec.call(
        "immobilien_de",
        "parse_page",
        {"page": "immobilien_de/leer.html"},
        lambda: imde.parse_page(pages["immobilien_de/leer.html"]),
    )
    log: list[str] = []
    web = {
        imde.SUCHE.format(hoechstpreis=700, seite=1): page,
        imde.SUCHE.format(hoechstpreis=700, seite=2): page,
        imde.SUCHE.format(hoechstpreis=700, seite=3): pages["immobilien_de/leer.html"],
    }
    patched_fetch(imde, web, "fetch", log)
    imde._PLZ_BEZIRKE = dict(PLZ_BEZIRKE)
    rec.call(
        "immobilien_de",
        "hole_bestand",
        {"hoechstpreis": 700, "seiten": 3, "web": sorted(web), "requested": log},
        lambda: imde.hole_bestand(700, 3),
    )

    # inberlinwohnen --------------------------------------------------------
    ibw = mods["inberlinwohnen_export"]
    p1, p2 = pages["inberlinwohnen/seite-1.html"], pages["inberlinwohnen/seite-2.html"]
    rec.call(
        "inberlinwohnen",
        "total_count",
        {"page": "inberlinwohnen/seite-1.html"},
        lambda: ibw.total_count(p1),
    )
    rec.call(
        "inberlinwohnen",
        "total_count",
        {"page": "inberlinwohnen/leer.html"},
        lambda: ibw.total_count(pages["inberlinwohnen/leer.html"]),
    )
    ibw.MERKMALE.clear()
    rec.call(
        "inberlinwohnen",
        "learn_attributes",
        {"page": "inberlinwohnen/seite-1.html", "before": {}},
        lambda: dict(ibw.learn_attributes(p1)),
    )
    learned = dict(ibw.MERKMALE)
    items = rec.call(
        "inberlinwohnen",
        "parse_page",
        {"page": "inberlinwohnen/seite-1.html"},
        lambda: ibw.parse_page(p1),
    )
    for item in (items or {}).values():
        rec.call(
            "inberlinwohnen",
            "normalise",
            {"raw": item, "merkmale": learned},
            lambda item=item: ibw.normalise(item),
        )
    rec.call(
        "inberlinwohnen",
        "parse_page",
        {"page": "inberlinwohnen/seite-2.html"},
        lambda: ibw.parse_page(p2),
    )
    for value in (
        "52,5071",
        "52.45117026",
        "1.234,56 €",
        "54,32 m²",
        "unbekannt",
        "",
        None,
        7,
        "<b>12</b>",
        "-3,5",
        "ca. 60",
    ):
        rec.call("inberlinwohnen", "_zahl", {"value": value}, lambda value=value: ibw._zahl(value))
    for value in ("2026-09-04T17:59:02.000000Z", "2026-09-05 08:00:00", "2026-09-05", None, ""):
        rec.call("inberlinwohnen", "_utc", {"value": value}, lambda value=value: ibw._utc(value))
    log = []
    web = {
        ibw.BASE: p1,
        f"{ibw.BASE}?page=2": p2,
        f"{ibw.BASE}?page=3": pages["inberlinwohnen/leer.html"],
    }
    patched_fetch(ibw, web, "fetch", log)
    ibw.MERKMALE.clear()
    rec.call(
        "inberlinwohnen",
        "hole_bestand",
        {"web": sorted(web), "requested": log},
        lambda: ibw.hole_bestand(0.0),
    )

    # Kleinanzeigen ---------------------------------------------------------
    kle = mods["kleinanzeigen_export"]
    kle._ZUORDNUNG = {kle._schluessel(k): v for k, v in ORTSTEILE.items()}
    kp = pages["kleinanzeigen/seite-1.html"]
    rows = rec.call(
        "kleinanzeigen",
        "parse_page",
        {"page": "kleinanzeigen/seite-1.html"},
        lambda: kle.parse_page(kp),
    )
    for item in (rows or {}).values():
        rec.call("kleinanzeigen", "brauchbar", {"raw": item}, lambda item=item: kle.brauchbar(item))
        rec.call(
            "kleinanzeigen",
            "normalise",
            {"raw": item, "ortsteile_bezirke": ORTSTEILE},
            lambda item=item: kle.normalise(item),
        )
    for value in ("54,5", "1.250", "1.25", "1.2500", "650", "", None, "abc", "1.234,5"):
        rec.call("kleinanzeigen", "_zahl", {"value": value}, lambda value=value: kle._zahl(value))
    for value in ("Weissensee", "Weißensee", "Prenzlauer Berg", "", None):
        rec.call(
            "kleinanzeigen",
            "_schluessel",
            {"value": value},
            lambda value=value: kle._schluessel(value),
        )
    rec.call(
        "kleinanzeigen",
        "suche_url",
        {"seite": "", "hoechstpreis": 700},
        lambda: kle.SUCHE.format(seite="", hoechstpreis=700),
    )
    rec.call(
        "kleinanzeigen",
        "suche_url",
        {"seite": "seite:2/", "hoechstpreis": 700},
        lambda: kle.SUCHE.format(seite="seite:2/", hoechstpreis=700),
    )
    log = []
    web = {
        kle.SUCHE.format(seite="", hoechstpreis=700): kp,
        kle.SUCHE.format(seite="seite:2/", hoechstpreis=700): pages["kleinanzeigen/leer.html"],
    }
    patched_fetch(kle, web, "fetch", log)
    rec.call(
        "kleinanzeigen",
        "hole_bestand",
        {"hoechstpreis": 700, "seiten": 3, "web": sorted(web), "requested": log},
        lambda: kle.hole_bestand(700, 3, 0.0),
    )

    # bienici ---------------------------------------------------------------
    bic = mods["bienici_export"]
    for ad in sp.bienici_ads():
        rec.call("bienici", "normalise", {"raw": ad}, lambda ad=ad: bic.normalise(ad))
    for value in ("2026-09-08T11:54:43.211Z", "1970-01-01T00:00:00.000Z", "08.09.2026", None, 5):
        rec.call("bienici", "_datum", {"value": value}, lambda value=value: bic._datum(value))
    for value in ("Hœrdt", "Raon-l'Étape", "Châtenois", "  Saint Dié  ", "", None, "Æbeltoft"):
        rec.call("bienici", "_ortsform", {"value": value}, lambda value=value: bic._ortsform(value))
    log = []
    zonen = ["-7415"]

    def bienici_url(page_no: int, size: int) -> str:
        import urllib.parse as up

        grund = {
            "showAllModels": False,
            "filterType": "rent",
            "propertyType": ["flat", "house"],
            "maxPrice": 1100,
            "sortBy": "publicationDate",
            "sortOrder": "desc",
            "onTheMarket": [True],
            "zoneIdsByTypes": {"zoneIds": zonen},
            "minRooms": 1,
            "maxRooms": 3,
        }
        f = dict(grund, size=size, page=page_no)
        f["from"] = (page_no - 1) * size
        return str(bic.SUCHE.format(filter=up.quote(json.dumps(f))))

    web = {
        bienici_url(1, 2): pages["bienici/seite-1.json"],
        bienici_url(2, 2): pages["bienici/seite-2.json"],
        bienici_url(3, 2): pages["bienici/seite-3.json"],
    }
    patched_fetch(bic, web, "_hole", log)
    rec.call(
        "bienici",
        "hole_bestand",
        {"zonen": zonen, "seitengroesse": 2, "web": sorted(web), "requested": log},
        lambda: bic.hole_bestand(zonen, seitengroesse=2, wartezeit=0),
    )

    # Citya -----------------------------------------------------------------
    cya = mods["citya_export"]
    cp = pages["citya/seite-1.html"]
    offers = rec.call("citya", "katalog", {"page": "citya/seite-1.html"}, lambda: cya.katalog(cp))
    rec.call("citya", "gesamtzahl", {"page": "citya/seite-1.html"}, lambda: cya.gesamtzahl(cp))
    rec.call(
        "citya",
        "katalog",
        {"page": "citya/leer.html"},
        lambda: cya.katalog(pages["citya/leer.html"]),
    )
    for offer in offers or []:
        name = (offer.get("itemOffered") or {}).get("name")
        rec.call("citya", "ist_wohnraum", {"name": name}, lambda name=name: cya.ist_wohnraum(name))
        rec.call(
            "citya",
            "normalise",
            {"raw": offer, "dep_name": "Bas-Rhin", "dep_code": "67"},
            lambda offer=offer: cya.normalise(offer, "Bas-Rhin", "67"),
        )
    log = []
    web = {
        cya.SUCHE.format(dep="bas-rhin-67", seite=1): cp,
        cya.SUCHE.format(dep="bas-rhin-67", seite=2): cp,
    }
    patched_fetch(cya, web, "_hole", log)
    rec.call(
        "citya",
        "hole_bestand",
        {"departements": ["bas-rhin-67"], "web": sorted(web), "requested": log},
        lambda: cya.hole_bestand(["bas-rhin-67"], wartezeit=0),
    )

    # ParuVendu -------------------------------------------------------------
    pvd = mods["paruvendu_export"]
    pp = pages["paruvendu/seite-1.html"]
    blocks = rec.call(
        "paruvendu", "_karten", {"page": "paruvendu/seite-1.html"}, lambda: pvd._karten(pp)
    )
    for block in blocks or []:
        rec.call(
            "paruvendu",
            "normalise",
            {"block": block, "dep_name": "Bas-Rhin", "art_vorgabe": "appartement"},
            lambda block=block: pvd.normalise(block, "Bas-Rhin", "appartement"),
        )
    for value in ("1 100", "780", "1 250,50", "", None, "abc"):
        rec.call("paruvendu", "_zahl", {"value": value}, lambda value=value: pvd._zahl(value))
    log = []
    web = {pvd.SUCHE.format(art="appartement", dep="bas-rhin-67", hoechstpreis=1100, seite=1): pp}
    patched_fetch(pvd, web, "_hole", log)
    rec.call(
        "paruvendu",
        "hole_bestand",
        {
            "departements": ["bas-rhin-67"],
            "arten": ["appartement"],
            "web": sorted(web),
            "requested": log,
        },
        lambda: pvd.hole_bestand(["bas-rhin-67"], arten=("appartement",), wartezeit=0),
    )
    return mods


def capture_zvg(root: Path, rec: Recorder, dsn: str | None) -> dict[str, Any]:
    zvg = load(root / ZVG[0], ZVG[1], "zvg_crawler")
    import httpx

    pages = sp.all_pages()
    for text in sp.ZVG_MONEY:
        rec.call(
            "zvg",
            "parse_money_amount",
            {"value": text},
            lambda text=text: zvg.parse_money_amount(text),
        )
    for text in sp.ZVG_NUMBERS:
        rec.call(
            "zvg", "parse_de_number", {"value": text}, lambda text=text: zvg.parse_de_number(text)
        )
    for text in sp.ZVG_VALUE_BLOCKS:
        rec.call(
            "zvg",
            "extract_market_value",
            {"value": text},
            lambda text=text: zvg.extract_market_value(text),
        )
    for text in sp.ZVG_ADDRESSES:
        rec.call(
            "zvg", "extract_address", {"value": text}, lambda text=text: zvg.extract_address(text)
        )
    for text in sp.ZVG_TYPES:
        rec.call("zvg", "classify_type", {"value": text}, lambda text=text: zvg.classify_type(text))
    for text in sp.ZVG_MOJIBAKE:
        rec.call("zvg", "fix_mojibake", {"value": text}, lambda text=text: zvg.fix_mojibake(text))
        rec.call("zvg", "clean", {"value": text}, lambda text=text: zvg.clean(text))
    for text in sp.ZVG_STREETS:
        rec.call("zvg", "expand_street", {"value": text}, lambda text=text: zvg.expand_street(text))
        rec.call("zvg", "_norm_street", {"value": text}, lambda text=text: zvg._norm_street(text))
    sample = "<p>Grünland an der Straße, Maß 12 m², Café</p>"
    encodings = {
        "utf-8": sample.encode("utf-8"),
        "cp1252": sample.encode("cp1252"),
        "iso-8859-1": sample.encode("iso-8859-1"),
        "utf-8-double": sample.encode("utf-8").decode("latin-1").encode("utf-8"),
        "invalid-bytes": b"\xff\xfe<p>\x81\x8d\x8f\x90\x9d</p>",
    }
    for label, body in encodings.items():
        rec.call(
            "zvg",
            "decode_portal_response",
            {"label": label, "body_hex": body.hex()},
            lambda body=body: zvg.decode_portal_response(httpx.Response(200, content=body)),
        )

    listing = pages["zvg/liste.html"]
    for land in ("he", "rp"):
        rec.call(
            "zvg",
            "parse_listing_akten",
            {"page": "zvg/liste.html", "land": land},
            lambda land=land: zvg.parse_listing_akten(listing, land),
        )
        rec.call(
            "zvg",
            "parse_listing_akten",
            {"page": "zvg/liste-roh.html", "land": land},
            lambda land=land: zvg.parse_listing_akten(pages["zvg/liste-roh.html"], land),
        )
    portal = object.__new__(zvg.ZvgPortal)
    requests: list[dict[str, Any]] = []

    def fake_post(params: dict[str, Any], data: dict[str, Any]) -> str:
        requests.append({"method": "POST", "params": params, "data": data})
        return str(portal_pages.pop(0))

    def fake_get(params: dict[str, Any], referer: str | None = None) -> str:
        requests.append({"method": "GET", "params": params, "referer": referer})
        return "<html>detail</html>"

    portal_pages = [listing, pages["zvg/liste-roh.html"]]
    portal._post = fake_post
    portal._get = fake_get
    rec.call(
        "zvg",
        "ZvgPortal.search_court",
        {"court_id": "M1201", "land": "he", "page": "zvg/liste.html"},
        lambda: portal.search_court("M1201", "he"),
    )
    rec.call(
        "zvg",
        "ZvgPortal.search_court",
        {"court_id": "M1201", "land": "he", "page": "zvg/liste-roh.html"},
        lambda: portal.search_court("M1201", "he"),
    )
    rec.call(
        "zvg",
        "ZvgPortal.detail",
        {"zvg_id": "880001", "land": "he"},
        lambda: portal.detail("880001", "he"),
    )
    rec.call("zvg", "portal_requests", {}, lambda: list(requests))

    for name in sp.zvg_detail_pages():
        page = pages[f"zvg/detail-{name}.html"]

        def run(page: str = page) -> dict[str, Any]:
            v = zvg.Verfahren(
                zvg_id="880001",
                land="he",
                court_id="M1201",
                court_name=zvg.COURT_NAMES["M1201"],
                file_number="",
                detail_url=f"{zvg.BASE}?button=showZvg&zvg_id=880001&land_abk=he",
            )
            zvg.parse_detail(page, v)
            data = dict(vars(v))
            data["termin"] = v.termin.isoformat() if v.termin else None
            return data

        rec.call(
            "zvg",
            "parse_detail",
            {"page": f"zvg/detail-{name}.html", "reference_year": datetime.now().year},
            run,
        )
    rec.call("zvg", "resolve_courts", {"arg": "kern"}, lambda: zvg.resolve_courts("kern"))
    rec.call(
        "zvg",
        "resolve_courts",
        {"arg": "M1201, T2304,"},
        lambda: zvg.resolve_courts("M1201, T2304,"),
    )
    rec.call(
        "zvg",
        "courts",
        {},
        lambda: {"he": zvg.COURTS_HE, "rp": zvg.COURTS_RP, "kern": zvg.KERN_COURTS},
    )
    lifecycle = capture_lifecycle(zvg, dsn) if dsn else {"status": "NOT_EXECUTED"}
    return lifecycle


def capture_lifecycle(zvg: ModuleType, dsn: str) -> dict[str, Any]:
    """Run the original Ingest lifecycle against a throwaway migrated database."""
    import psycopg

    backend = Path(zvg.__file__).resolve().parents[2]
    sys.path.insert(0, str(backend))
    conn = psycopg.connect(dsn, autocommit=True)
    conn.execute(
        "TRUNCATE auction_dates, market_values, source_snapshots, properties, "
        "auction_cases, courts, regions, property_types CASCADE"
    )
    conn.execute(
        "INSERT INTO property_types (code, name_de, name_en, nutzungsart, sort_order) "
        "VALUES ('sonstige', 'Sonstige', 'Other', 'sonstige', 99)"
    )
    ingest = zvg.Ingest(dsn)
    court = ingest.court_id_db("M1201", "he")
    other = ingest.court_id_db("M1906", "he")
    ingest.commit()
    now = conn.execute("SELECT now()").fetchone()[0]
    scenarios = [
        # name, court, status, last_seen days ago (None = NULL), date offsets (days), deleted
        ("gesehen-heute-zukunft", court, "terminiert", 0, [10], False),
        ("verschwunden-termin-vorbei", court, "terminiert", 5, [-2], False),
        ("verschwunden-termin-zukunft", court, "terminiert", 5, [7], False),
        ("verschwunden-ohne-termin", court, "erfasst", 5, [], False),
        ("verschwunden-gemischt", court, "terminiert", 5, [-30, 3], False),
        ("karenz-nicht-abgelaufen", court, "terminiert", 2, [-1], False),
        ("karenz-grenze-3-tage", court, "erfasst", 3, [-1], False),
        ("nie-gesehen", court, "erfasst", None, [-1], False),
        ("bereits-abgehalten", court, "abgehalten", 9, [-5], False),
        ("geloescht", court, "terminiert", 9, [-5], True),
        ("anderes-gericht", other, "terminiert", 9, [-5], False),
        ("wieder-gelistet", court, "terminiert", 9, [4], False),
    ]
    for name, court_id, status, seen, dates, deleted in scenarios:
        case_id = conn.execute(
            "INSERT INTO auction_cases (id, court_id, file_number, case_type, status, "
            "last_seen_at, deleted_at, created_at, updated_at) VALUES (gen_random_uuid(), %s, %s, "
            "'zwangsversteigerung', %s, %s, %s, now(), now()) RETURNING id",
            (
                court_id,
                name,
                status,
                None if seen is None else now - timedelta(days=seen),
                now if deleted else None,
            ),
        ).fetchone()[0]
        for offset in dates:
            conn.execute(
                "INSERT INTO auction_dates (id, auction_case_id, date_type, scheduled_at, "
                "created_at, updated_at) VALUES (gen_random_uuid(), %s, 'ersttermin', %s, now(), "
                "now())",
                (case_id, now + timedelta(days=offset)),
            )

    def snapshot() -> dict[str, Any]:
        rows = conn.execute(
            "SELECT ac.file_number, ac.status, ac.last_seen_at, ac.closed_at, "
            "ac.deleted_at IS NOT NULL, c.name, COALESCE(array_agg(d.scheduled_at "
            "ORDER BY d.scheduled_at) FILTER (WHERE d.id IS NOT NULL), '{}') "
            "FROM auction_cases ac JOIN courts c ON c.id = ac.court_id "
            "LEFT JOIN auction_dates d ON d.auction_case_id = ac.id "
            "GROUP BY ac.id, c.name ORDER BY ac.file_number"
        ).fetchall()
        return {
            r[0]: {
                "status": r[1],
                "last_seen_at": None if r[2] is None else r[2].isoformat(),
                "closed_at": None if r[3] is None else r[3].isoformat(),
                "deleted": r[4],
                "court": r[5],
                "dates": [d.isoformat() for d in r[6]],
            }
            for r in rows
        }

    def clock() -> str:
        return str(conn.execute("SELECT now()").fetchone()[0].isoformat())

    steps: list[dict[str, Any]] = [{"step": "initial", "state": snapshot()}]
    before = clock()
    ingest.mark_seen("M1201", "he", ["wieder-gelistet", "gesehen-heute-zukunft", "unbekannt"])
    ingest.commit()
    steps.append(
        {
            "step": "mark_seen",
            "court": "M1201",
            "now_before": before,
            "listed": ["wieder-gelistet", "gesehen-heute-zukunft", "unbekannt"],
            "state": snapshot(),
        }
    )
    before = clock()
    closed = ingest.close_vanished("M1201", "he")
    ingest.commit()
    steps.append(
        {
            "step": "close_vanished",
            "court": "M1201",
            "grace_days": 3,
            "now_before": before,
            "closed": closed,
            "state": snapshot(),
        }
    )
    ingest.mark_seen("M1201", "he", [])
    steps.append({"step": "mark_seen", "court": "M1201", "listed": [], "state": snapshot()})
    before = clock()
    closed = ingest.close_vanished("M1906", "he", grace_days=0)
    ingest.commit()
    steps.append(
        {
            "step": "close_vanished",
            "court": "M1906",
            "grace_days": 0,
            "now_before": before,
            "closed": closed,
            "state": snapshot(),
        }
    )
    # Reappearance: the original upsert reopens a closed case.
    for name, termin in (
        ("verschwunden-termin-vorbei", now + timedelta(days=20)),
        ("verschwunden-ohne-termin", None),
        ("verschwunden-termin-zukunft", now - timedelta(days=1)),
    ):
        v = zvg.Verfahren(
            zvg_id="1",
            land="he",
            court_id="M1201",
            file_number=name,
            title="Objekt",
            termin=termin,
            detail_url=f"{zvg.BASE}?button=showZvg&zvg_id=1&land_abk=he",
        )
        before = clock()
        ingest.upsert(v)
        ingest.commit()
        steps.append(
            {
                "step": "upsert",
                "court": "M1201",
                "file_number": name,
                "now_before": before,
                "termin": None if termin is None else termin.isoformat(),
                "state": snapshot(),
            }
        )
    ingest.close()
    version = conn.execute("SELECT version()").fetchone()[0]
    conn.close()
    return {"status": "OBSERVED", "database": version.split(",")[0], "steps": steps}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wohnungsmonitor", type=Path)
    parser.add_argument("versteigerung", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--dsn")
    args = parser.parse_args()
    if (
        head(args.wohnungsmonitor) != WOHNUNGSMONITOR[1]
        or head(args.versteigerung) != VERSTEIGERUNG[1]
    ):
        raise SystemExit("Quellen stehen nicht auf den gepinnten Commits")
    rec = Recorder()
    capture_wohnungsmonitor(args.wohnungsmonitor.resolve(), rec)
    lifecycle = capture_zvg(args.versteigerung.resolve(), rec, args.dsn)
    import bs4
    import httpx

    report = {
        "status": "OBSERVED",
        "scope": "LOCAL_LEGACY_CHARACTERIZATION_ON_SYNTHETIC_STRUCTURE_DERIVED_PAGES",
        "inputs": "synthetic, structure-derived (tools/synthetic_pages.py); no personal data",
        "sources": {
            "wohnungsmonitor": {
                "repository": WOHNUNGSMONITOR[0],
                "commit": WOHNUNGSMONITOR[1],
                "files": {p: b for p, b in FILES.values()},
            },
            "versteigerung": {
                "repository": VERSTEIGERUNG[0],
                "commit": VERSTEIGERUNG[1],
                "files": {ZVG[0]: ZVG[1]},
            },
        },
        "environment": {
            "python": platform.python_version(),
            "beautifulsoup4": bs4.__version__,
            "httpx": httpx.__version__,
            "captured_on": datetime.now(UTC).date().isoformat(),
        },
        "synthetic_mappings": {"plz_bezirke": PLZ_BEZIRKE, "ortsteile_bezirke": ORTSTEILE},
        "cases": rec.cases,
        "lifecycle": lifecycle,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    print(
        json.dumps(
            {
                "status": "OBSERVED",
                "cases": len(rec.cases),
                "exceptions": sum(c["exception"] is not None for c in rec.cases),
                "lifecycle": lifecycle["status"],
            }
        )
    )


if __name__ == "__main__":
    main()
