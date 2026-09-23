"""Consumer integration check against the installed wheel (no pushes, no production data).

Applies the shims of ``docs/consumer-migration.md`` to *copies* of the
consumer modules, then runs the consumers' own entry points on the synthetic
pages and compares with the recorded original results::

    python tools/consumer_integration.py <wohnungsmonitor copy> <versteigerung copy> \
        tests/fixtures/legacy_observed.json

The shims rebind the consumer functions to the library (same names, same
signatures). Paging (``hole_bestand``), network, scheduling, persistence and
notifications stay in the consumers.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
import synthetic_pages as sp  # noqa: E402

SHIMS = {
    "immobilien_export.py": """
from auditcore_property_sources import immobilien_de as _ps


def parse_page(doc):
    return _ps.parse_page(doc)[0]


def normalise(a):
    return _ps.normalise(a, plz_bezirke())
""",
    "inberlinwohnen_export.py": """
from auditcore_property_sources import inberlinwohnen as _ps

total_count = _ps.total_count
parse_page = _ps.parse_page


def learn_attributes(doc):
    MERKMALE.update(_ps.learn_attributes(doc, MERKMALE))
    return MERKMALE


def normalise(eintrag):
    return _ps.normalise(eintrag, MERKMALE)
""",
    "kleinanzeigen_export.py": """
from auditcore_property_sources import kleinanzeigen as _ps

parse_page = _ps.parse_page
brauchbar = _ps.usable


def normalise(roh):
    return _ps.normalise(roh, bezirke_laden())
""",
    "bienici_export.py": """
from auditcore_property_sources import bienici as _ps


def normalise(a):
    return _ps.normalise(a, advertiser_names="legacy")
""",
    "citya_export.py": """
from auditcore_property_sources import citya as _ps

katalog = _ps.catalog
gesamtzahl = _ps.total
ist_wohnraum = _ps.is_residential
normalise = _ps.normalise
""",
    "paruvendu_export.py": """
from auditcore_property_sources import paruvendu as _ps

_karten = _ps.cards
normalise = _ps.normalise
""",
    "backend/app/crawler/zvg_crawler.py": """
from auditcore_property_sources import zvg as _ps

fix_mojibake = _ps.fix_mojibake
clean = _ps.clean
parse_de_number = _ps.parse_de_number
parse_money_amount = _ps.parse_money_amount
extract_market_value = _ps.extract_market_value
classify_type = _ps.classify_type
extract_address = _ps.extract_address
expand_street = _ps.expand_street
_norm_street = _ps.normalized_street
parse_listing_akten = _ps.parse_listing_akten


def decode_portal_response(response):
    return _ps.decode_portal_bytes(response.content)


def parse_detail(html, v):
    notice = _ps.parse_detail(
        html,
        _ps.ZvgNotice(zvg_id=v.zvg_id, land=v.land, court_id=v.court_id,
                      file_number=v.file_number, court_name=v.court_name,
                      detail_url=v.detail_url),
        reference_year=datetime.now().year,
    )
    for name, value in vars(notice).items():
        setattr(v, name, value)
    return v
""",
}


def apply(root: Path) -> list[str]:
    """Append the shim block to every module present in ``root``."""
    done = []
    for relative, shim in SHIMS.items():
        path = root / relative
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            if "auditcore_property_sources" not in text:
                path.write_text(
                    text + "\n\n# --- auditcore_property_sources ---" + shim, encoding="utf-8"
                )
            done.append(relative)
    return done


def load(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wohnungsmonitor", type=Path)
    parser.add_argument("versteigerung", type=Path)
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()
    import auditcore_property_sources

    library = Path(auditcore_property_sources.__file__).resolve()
    patched = apply(args.wohnungsmonitor) + apply(args.versteigerung)
    observed = json.loads(args.fixture.read_text(encoding="utf-8"))
    by = {}
    for case in observed["cases"]:
        by.setdefault((case["group"], case["function"]), []).append(case)
    pages = sp.all_pages()
    checks: dict[str, str] = {}

    def verdict(name: str, ok: bool) -> None:
        checks[name] = "PASS" if ok else "FAIL"

    def web_fetch(module: ModuleType, attr: str, web: dict[str, Any]) -> None:
        setattr(module, attr, lambda url, *a, **k: web[url])
        module.time.sleep = lambda s: None  # type: ignore[attr-defined]

    mods = {
        n: load(args.wohnungsmonitor / f"{n}.py", f"shim_{n}")
        for n in (
            "immobilien_export",
            "inberlinwohnen_export",
            "kleinanzeigen_export",
            "bienici_export",
            "citya_export",
            "paruvendu_export",
        )
    }
    mapping = observed["synthetic_mappings"]

    imde = mods["immobilien_export"]
    imde._PLZ_BEZIRKE = mapping["plz_bezirke"]
    web_fetch(
        imde,
        "fetch",
        {
            imde.SUCHE.format(hoechstpreis=700, seite=n): pages[f]
            for n, f in (
                (1, "immobilien_de/seite-1.html"),
                (2, "immobilien_de/seite-1.html"),
                (3, "immobilien_de/leer.html"),
            )
        },
    )
    got = json.loads(json.dumps(imde.hole_bestand(700, 3), ensure_ascii=False))
    verdict(
        "wohnungsmonitor.immobilien_export.hole_bestand",
        got == by[("immobilien_de", "hole_bestand")][0]["output"],
    )

    ibw = mods["inberlinwohnen_export"]
    ibw.MERKMALE.clear()
    web_fetch(
        ibw,
        "fetch",
        {
            ibw.BASE: pages["inberlinwohnen/seite-1.html"],
            f"{ibw.BASE}?page=2": pages["inberlinwohnen/seite-2.html"],
            f"{ibw.BASE}?page=3": pages["inberlinwohnen/leer.html"],
        },
    )
    got = json.loads(json.dumps(ibw.hole_bestand(0.0), ensure_ascii=False))
    verdict(
        "wohnungsmonitor.inberlinwohnen_export.hole_bestand",
        got == by[("inberlinwohnen", "hole_bestand")][0]["output"],
    )

    kle = mods["kleinanzeigen_export"]
    kle._ZUORDNUNG = {kle._schluessel(k): v for k, v in mapping["ortsteile_bezirke"].items()}
    web_fetch(
        kle,
        "fetch",
        {
            kle.SUCHE.format(seite="", hoechstpreis=700): pages["kleinanzeigen/seite-1.html"],
            kle.SUCHE.format(seite="seite:2/", hoechstpreis=700): pages["kleinanzeigen/leer.html"],
        },
    )
    got = json.loads(json.dumps(kle.hole_bestand(700, 3, 0.0), ensure_ascii=False))
    verdict(
        "wohnungsmonitor.kleinanzeigen_export.hole_bestand",
        got == by[("kleinanzeigen", "hole_bestand")][0]["output"],
    )

    bic = mods["bienici_export"]
    recorded = by[("bienici", "hole_bestand")][0]
    web_fetch(
        bic,
        "_hole",
        {
            u: json.loads(pages[f"bienici/seite-{i}.json"])
            for i, u in enumerate(recorded["args"]["requested"], 1)
        },
    )
    got = json.loads(
        json.dumps(bic.hole_bestand(["-7415"], seitengroesse=2, wartezeit=0), ensure_ascii=False)
    )
    verdict("wohnungsmonitor.bienici_export.hole_bestand", got == recorded["output"])

    cya = mods["citya_export"]
    web_fetch(
        cya,
        "_hole",
        {cya.SUCHE.format(dep="bas-rhin-67", seite=n): pages["citya/seite-1.html"] for n in (1, 2)},
    )
    got = json.loads(json.dumps(cya.hole_bestand(["bas-rhin-67"], wartezeit=0), ensure_ascii=False))
    verdict(
        "wohnungsmonitor.citya_export.hole_bestand",
        got == by[("citya", "hole_bestand")][0]["output"],
    )

    pvd = mods["paruvendu_export"]
    web_fetch(
        pvd,
        "_hole",
        {
            pvd.SUCHE.format(
                art="appartement", dep="bas-rhin-67", hoechstpreis=1100, seite=1
            ): pages["paruvendu/seite-1.html"]
        },
    )
    got = json.loads(
        json.dumps(
            pvd.hole_bestand(["bas-rhin-67"], arten=("appartement",), wartezeit=0),
            ensure_ascii=False,
        )
    )
    verdict(
        "wohnungsmonitor.paruvendu_export.hole_bestand",
        got == by[("paruvendu", "hole_bestand")][0]["output"],
    )

    backend = args.versteigerung / "backend"
    sys.path.insert(0, str(backend))
    zvg = load(backend / "app/crawler/zvg_crawler.py", "app.crawler.zvg_crawler")
    ok = True
    for case in by[("zvg", "parse_detail")]:
        v = zvg.Verfahren(
            zvg_id="880001",
            land="he",
            court_id="M1201",
            court_name=zvg.COURT_NAMES["M1201"],
            file_number="",
            detail_url=f"{zvg.BASE}?button=showZvg&zvg_id=880001&land_abk=he",
        )
        zvg.parse_detail(pages[case["args"]["page"].removeprefix("")], v)
        data = dict(vars(v))
        data["termin"] = v.termin.isoformat() if v.termin else None
        ok &= json.loads(json.dumps(data, ensure_ascii=False)) == case["output"]
    for case in by[("zvg", "parse_listing_akten")]:
        ok &= (
            zvg.parse_listing_akten(pages[case["args"]["page"]], case["args"]["land"])
            == case["output"]
        )
    for case in by[("zvg", "extract_address")]:
        ok &= list(zvg.extract_address(case["args"]["value"])) == case["output"]
    verdict("versteigerung.zvg_crawler.parse_detail/listing/address", ok)
    reparse = load(backend / "app/crawler/reparse_addresses.py", "shim_reparse")
    merged = reparse.merge_address(
        "Eigentumswohnung, Beispielstr. 5, 60311 Frankfurt am Main",
        "Wohnung, Beispielstraße 5 a, 60311 Frankfurt am Main",
    )
    verdict(
        "versteigerung.reparse_addresses.merge_address",
        merged[:4] == ("Beispielstr.", "5", "60311", "Frankfurt am Main"),
    )
    result = {
        "status": "PASS" if all(v == "PASS" for v in checks.values()) else "FAIL",
        "library": str(library),
        "patched": patched,
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
