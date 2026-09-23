"""Write the ``auditcore_harvest`` replay fixtures of this package.

Responses are synthetic, in the documented formats of the sources (DIP API
``{"numFound", "cursor", "documents"}``, W3C SPARQL JSON results, RSS 2.0 /
Atom, ECA overview HTML). They contain no retrieved third-party content and
no credentials. Run from the package directory:
``python tools/build_replay_fixtures.py tests/fixtures/replay``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from capture_routes import drucksache  # noqa: E402

from auditcore_legal_sources import eurlex  # noqa: E402
from auditcore_legal_sources.profile import load_profile  # noqa: E402

DIP_URL = "https://search.dip.bundestag.de/api/v1/drucksache"
PROFILE = load_profile("auditdatabase.esi", "2026.09.1")


def dip_page(term: str, cursor: str | None, docs: list[dict[str, Any]], nxt: str) -> dict[str, Any]:
    params = {"format": "json", "num": "30", "f.titel": term}
    if cursor:
        params["cursor"] = cursor
    return {
        "request": {"method": "GET", "url": DIP_URL, "params": params},
        "response": {
            "status": 200,
            "headers": {"content-type": "application/json"},
            "body_json": {"numFound": 4, "cursor": nxt, "documents": docs},
        },
    }


def sparql(query: str, rows: list[dict[str, str]]) -> dict[str, Any]:
    bindings = [{k: {"type": "literal", "value": v} for k, v in row.items()} for row in rows]
    return {
        "request": {
            "method": "GET",
            "url": PROFILE.eurlex_endpoint,
            "params": eurlex.sparql_form(query),
        },
        "response": {
            "status": 200,
            "headers": {"content-type": eurlex.RESULTS_MEDIA_TYPE},
            "body_json": {
                "head": {"vars": sorted({k for r in rows for k in r})},
                "results": {"bindings": bindings},
            },
        },
    }


def rss(items: list[tuple[str, str, str]]) -> str:
    body = "".join(
        f"<item><title>{t}</title><link>{link}</link><description>{d}</description>"
        f"<pubDate>Fri, 15 Mar 2024 10:20:30 +0100</pubDate></item>"
        for t, link, d in items
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
        "<title>Synthetisch</title><link>https://example.invalid</link>"
        f"<description>Synthetischer Feed</description>{body}</channel></rss>"
    )


def feed(url: str, text: str, status: int = 200) -> dict[str, Any]:
    return {
        "request": {"method": "GET", "url": url, "params": {}},
        "response": {
            "status": status,
            "headers": {"content-type": "application/rss+xml"},
            "body_text": text,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    fixtures: dict[str, list[dict[str, Any]]] = {
        "dip.json": [
            dip_page("EFRE", None, [drucksache(1), drucksache(2)], "AoE1"),
            dip_page("EFRE", "AoE1", [drucksache(3, datum="2019-06-01")], "AoE2"),
            dip_page("EFRE", "AoE2", [], "AoE2"),
            dip_page("Strukturfonds", None, [drucksache(2), drucksache(4)], "B1"),
            dip_page("Strukturfonds", "B1", [], "B1"),
        ],
        "dip_partial.json": [
            dip_page(
                "EFRE", None, [drucksache(1), {"titel": "ohne ID"}, drucksache(5, titel="")], "C1"
            ),
            dip_page("EFRE", "C1", [], "C1"),
        ],
    }
    names = list(PROFILE.eurlex_queries)
    fixtures["eurlex.json"] = [
        sparql(
            PROFILE.eurlex_queries[names[0]],
            [
                {"celex": "32021R1060", "title": "Dublette Dachverordnung", "date": "2021-06-24"},
                {
                    "celex": "32022R0001",
                    "title": "Delegierte VO zu 2021/1060 EFRE",
                    "date": "2022-05-04",
                },
            ],
        ),
        sparql(
            PROFILE.eurlex_queries[names[1]],
            [
                {
                    "celex": "32022R0001",
                    "title": "Doppelt aus zweiter Abfrage",
                    "date": "2022-05-04",
                },
                {"celex": "32023R0100", "title": "Delegierte VO Kohäsion", "date": "2023-01-15"},
            ],
        ),
        sparql(PROFILE.eurlex_queries[names[2]], []),
        sparql(
            PROFILE.eurlex_queries[names[3]],
            [
                {
                    "celex": "52023DC0010",
                    "title": "Mitteilung Kohäsion 2021-2027",
                    "date": "2023-02",
                },
            ],
        ),
    ]
    from datetime import date

    fixtures["eurlex_update.json"] = [
        sparql(
            eurlex.update_query(PROFILE, date(2024, 1, 31)),
            [
                {"celex": "32024R0500", "title": "Neue Durchführungs-VO ESF", "date": "2024-02-10"},
            ],
        )
    ]
    bafin = PROFILE.feeds["bafin"].feeds
    fixtures["bafin.json"] = [
        feed(
            bafin["aufsicht"],
            rss(
                [
                    ("Allgemeinverfügung zur Vergabe", "https://example.invalid/bafin/a1", "Text"),
                    ("Aufsichtsmitteilung", "https://example.invalid/bafin/a2", "Mehr Text"),
                ]
            ),
        ),
        feed(
            bafin["massnahmen"],
            rss(
                [
                    ("Maßnahme gegen Institut", "https://example.invalid/bafin/m1", "Text"),
                ]
            ),
        ),
        feed(bafin["presse"], rss([])),
    ]
    curia = PROFILE.feeds["curia"].feeds
    fixtures["curia.json"] = [
        feed(
            curia["gerichtshof"],
            rss(
                [
                    (
                        "Urteil C-123/22 zur EFRE-Förderung",
                        "https://example.invalid/curia/1",
                        "Kohäsionspolitik",
                    ),
                    ("Urteil ohne Bezug", "https://example.invalid/curia/2", "Zollrecht"),
                ]
            ),
        ),
        feed(
            curia["gericht"],
            rss(
                [
                    ("Urteil T-45/21 Beihilfe", "https://example.invalid/curia/3", "Beihilferecht"),
                ]
            ),
        ),
        feed(curia["pressemitteilungen"], rss([])),
    ]
    eca_url = PROFILE.feeds["eca"].publication_urls[0]
    fixtures["eca.json"] = [
        {
            "request": {"method": "GET", "url": eca_url, "params": {}},
            "response": {
                "status": 200,
                "headers": {"content-type": "text/html"},
                "body_text": "<html><body>"
                '<a href="/de/publications/SR-2024-01">Sonderbericht 01/2024: '
                "Synthetischer Titel zur Prüfung</a>"
                '<a href="/de/report/annual-2023">Jahresbericht 2023 synthetisch lang</a>'
                '<a href="/de/other">Kontakt und Impressum der Seite</a>'
                "</body></html>",
            },
        },
    ]
    fixtures["eca_unavailable.json"] = [
        {
            "request": {"method": "GET", "url": eca_url, "params": {}},
            "response": {"status": 503, "headers": {}, "body_text": ""},
        },
    ]
    for name, exchanges in fixtures.items():
        path = args.output / name
        path.write_text(
            json.dumps({"exchanges": exchanges}, indent=1, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(path)


if __name__ == "__main__":
    main()
