"""Capture actual RSS/HTML behavior of auditdatabase ``app/harvester/rss.py`` (BaFin, CURIA, ECA).

Run with an interpreter that provides httpx, feedparser, BeautifulSoup and SQLAlchemy::

    python -I tools/capture_legacy_feeds.py <auditdatabase>/backend \
        tests/fixtures/legacy_feeds_observed.json

Synthetic RSS/Atom/HTML documents are parsed by the real feedparser and
BeautifulSoup versions pinned by the application; ``httpx.AsyncClient`` is
replaced, so no request leaves the process. ``PYTHONHASHSEED`` is recorded
because the source derives identifiers from ``hash()``.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from capture_legacy_harvesters import (  # noqa: E402
    SOURCES,
    FakeClientFactory,
    FakeResponse,
    error,
    jsonable,
    load,
)

RSS_BLOB = "0918dfd90aca1804df8b30c9190ebc3b8282a54a"

BAFIN_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Synthetisch</title><link>https://example.invalid</link>
<description>Synthetischer Feed</description>
<item><title>Allgemeinverfügung zur Vergabe von Fördermitteln</title>
<link>https://example.invalid/DE/Meldung/2024/meldung_2024_03_15.html</link>
<description>Kurzfassung mit &lt;b&gt;Markup&lt;/b&gt;</description>
<pubDate>Fri, 15 Mar 2024 10:20:30 +0100</pubDate><category>Aufsicht</category></item>
<item><title>Eintrag ohne Link</title><description>Nur Text</description>
<pubDate>kein Datum</pubDate></item>
<item><title>Allgemeinverfügung zur Vergabe von Fördermitteln</title>
<link>https://example.invalid/DE/Meldung/2024/meldung_2024_03_15.html</link></item>
</channel></rss>"""

CURIA_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>CURIA synthetisch</title><link>https://example.invalid</link>
<description>x</description>
<item><title>Urteil in der Rechtssache C-123/22 zur EFRE-Förderung</title>
<link>https://example.invalid/juris/document/document.jsf?docid=1</link>
<description>Zusammenfassung zur Kohäsionspolitik</description>
<pubDate>Tue, 05 Mar 2024 09:00:00 +0100</pubDate></item>
<item><title>Pressemitteilung ohne Förderbezug</title>
<link>https://example.invalid/press/cp240001de.pdf</link>
<description>Allgemeines Thema</description></item>
</channel></rss>"""

ATOM = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>Atom synthetisch</title>
<entry><title>Atom-Eintrag Vergabe</title><link href="https://example.invalid/a/1"/>
<id>urn:uuid:1</id><updated>2024-02-01T10:00:00Z</updated><summary>Text</summary></entry>
</feed>"""

ECA_HTML = """<html><body>
<a href="/de/publications/SR-2024-01">Sonderbericht 01/2024: Synthetischer Titel zur Prüfung</a>
<a href="https://example.invalid/report/annual-2023">Jahresbericht 2023 synthetisch lang genug</a>
<a href="/de/other">Kurz</a><a href="/de/report/x">kurz</a>
</body></html>"""


def entry_data(entry: Any) -> dict[str, Any]:
    """feedparser entry as plain JSON (struct_time as 9-item list)."""
    data: dict[str, Any] = {}
    for key, value in dict(entry).items():
        if key.endswith("_parsed") and value is not None:
            data[key] = list(value)
        else:
            data[key] = json.loads(json.dumps(value, default=str))
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backend", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    SOURCES["auditdatabase"]["blobs"]["rss.py"] = RSS_BLOB  # type: ignore[index]
    modules = load("auditdatabase", args.backend.resolve())
    rss = modules["rss"]
    import feedparser

    cases: list[dict[str, Any]] = []

    def record(name: str, operation: str, inputs: Any, call: Any) -> None:
        try:
            output, exception = jsonable(call()), None
        except Exception as exc:  # noqa: BLE001
            output, exception = None, error(exc)
        cases.append({"name": name, "operation": operation, "inputs": inputs,
                      "output": output, "exception": exception})

    bafin, curia, eca = rss.BaFinHarvester(), rss.CURIAHarvester(), rss.ECAHarvester()
    for feed_name, xml in (("aufsicht", BAFIN_RSS), ("atom", ATOM)):
        parsed = feedparser.parse(xml)
        for index, entry in enumerate(parsed.entries):
            record(f"bafin-entry-{feed_name}-{index}", "bafin_entry",
                   {"feed": feed_name, "entry": entry_data(entry), "index": index},
                   lambda e=entry, f=feed_name: bafin._normalize_entry(e, f))
    for feed_name in ("gerichtshof", "urteile"):
        parsed = feedparser.parse(CURIA_RSS)
        for index, entry in enumerate(parsed.entries):
            record(f"curia-entry-{feed_name}-{index}", "curia_entry",
                   {"feed": feed_name, "entry": entry_data(entry), "index": index},
                   lambda e=entry, f=feed_name: curia._normalize_entry(e, f))
    record("eca-core-reports", "eca_core", {}, eca._get_core_reports)

    def feed_route(call: dict[str, Any]) -> Any:
        url = call["url"]
        if "bafin" in url and "Aufsicht" in url:
            return FakeResponse(200, text=BAFIN_RSS)
        if "curia" in url and "jur=C" in url:
            return FakeResponse(200, text=CURIA_RSS)
        if "eca.europa.eu/de/publications" in url:
            return FakeResponse(200, text=ECA_HTML)
        return FakeResponse(404, text="")

    factory = FakeClientFactory(feed_route)
    rss.httpx.AsyncClient = factory
    rss.RSSHarvester._working_feeds.clear()
    bafin_result = asyncio.run(rss.BaFinHarvester().harvest())
    bafin_calls = [c["url"] for c in factory.calls]
    factory.calls.clear()
    curia_result = asyncio.run(rss.CURIAHarvester().harvest())
    curia_calls = [c["url"] for c in factory.calls]
    cases.append({"name": "rss-shared-feed-cache", "operation": "rss_flow", "inputs": {},
                  "output": {"bafin": jsonable(bafin_result), "bafin_calls": bafin_calls,
                             "curia": jsonable(curia_result), "curia_calls": curia_calls,
                             "cache_shared": rss.BaFinHarvester._working_feeds
                             is rss.CURIAHarvester._working_feeds},
                  "exception": None})
    rss.RSSHarvester._working_feeds.clear()
    factory.calls.clear()
    curia_alone = asyncio.run(rss.CURIAHarvester().harvest())
    cases.append({"name": "curia-harvest-fresh-cache", "operation": "rss_flow", "inputs": {},
                  "output": {"result": jsonable(curia_alone),
                             "calls": [c["url"] for c in factory.calls]}, "exception": None})
    rss.ECAHarvester._working_url = None
    eca_scraped = asyncio.run(rss.ECAHarvester().harvest())
    rss.ECAHarvester._working_url = None
    rss.httpx.AsyncClient = FakeClientFactory(lambda call: FakeResponse(503, text=""))
    eca_fallback = asyncio.run(rss.ECAHarvester().harvest())
    cases.append({"name": "eca-harvest", "operation": "eca_flow", "inputs": {"html": ECA_HTML},
                  "output": {"scraped": jsonable(eca_scraped), "fallback": jsonable(eca_fallback)},
                  "exception": None})
    report = {
        "status": "OBSERVED",
        "scope": "LOCAL_LEGACY_CHARACTERIZATION_SYNTHETIC_FEEDS_NO_NETWORK",
        "source": {"repository": "janpow77/auditdatabase",
                   "commit": SOURCES["auditdatabase"]["commit"],
                   "files": [{"path": "backend/app/harvester/rss.py", "git_blob": RSS_BLOB}]},
        "environment": {"feedparser": feedparser.__version__,
                        "PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED", "random")},
        "documents": {"bafin_rss": BAFIN_RSS, "curia_rss": CURIA_RSS, "atom": ATOM,
                      "eca_html": ECA_HTML},
        "profile": {
            "bafin_feeds": dict(rss.BaFinHarvester.FEEDS),
            "bafin_alternative_feeds": dict(rss.BaFinHarvester.ALTERNATIVE_FEEDS),
            "curia_feeds": dict(rss.CURIAHarvester.FEEDS),
            "curia_alternative_feeds": dict(rss.CURIAHarvester.ALTERNATIVE_FEEDS),
            "eca_publication_urls": list(rss.ECAHarvester.PUBLICATION_URLS),
            "eca_feeds": dict(rss.ECAHarvester.FEEDS),
        },
        "cases": cases,
    }
    args.output.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({"status": "OBSERVED", "cases": len(cases),
                      "exceptions": sum(c["exception"] is not None for c in cases)}))


if __name__ == "__main__":
    main()
