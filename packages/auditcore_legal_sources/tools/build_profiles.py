"""Derive the packaged source profiles from the recorded legacy snapshot.

The data is taken unchanged from the fixture; institution names are already
neutralised there (2026.09.2 replaced 2026.09.2, which carried them).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

VERSION = "2026.09.2"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    parser.add_argument("feeds_fixture", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    data = json.loads(args.fixture.read_text(encoding="utf-8"))
    p, sources = data["profile"], data["sources"]
    feeds = json.loads(args.feeds_fixture.read_text(encoding="utf-8"))["profile"]
    update = next(c for c in data["cases"] if c["name"] == "eurlex-update-query")
    template = update["output"].replace(update["inputs"]["since"], "{since}")
    common = {
        "schema": "auditcore_legal_sources.profile/1",
        "version": VERSION,
        "status": "SOURCE_CHARACTERIZED",
    }
    profiles = {
        "auditdatabase.esi": {
            **common,
            "id": "auditdatabase.esi",
            "source": sources["auditdatabase"],
            "keywords": {"de": p["global_keywords_de"], "en": p["global_keywords_en"]},
            "dip": {
                "api_url": "https://search.dip.bundestag.de/api/v1",
                "portal_url": p["dip_base_url"].replace("search.", "").replace("/api/v1", ""),
                "keywords": p["dip_keywords"],
                "page_size": 30,
                "classification": "auditdatabase.dip",
            },
            "eurlex": {
                "endpoint": p["eurlex_endpoint"],
                "document_url": p["eurlex_base_url"],
                "queries": p["eurlex_queries"],
                "core_documents": p["eurlex_core_documents"],
                "update_query_template": template,
                "funding_period_rule": "auditdatabase",
            },
            "feeds": {
                "bafin": {
                    "feeds": feeds["bafin_feeds"],
                    "alternative_feeds": feeds["bafin_alternative_feeds"],
                    "document_types": {n: f"BaFin {n.title()}" for n in feeds["bafin_feeds"]},
                },
                "curia": {
                    "feeds": feeds["curia_feeds"],
                    "alternative_feeds": feeds["curia_alternative_feeds"],
                    "document_types": {
                        "gerichtshof": "Rechtsprechung Gerichtshof",
                        "gericht": "Rechtsprechung Gericht",
                        "pressemitteilungen": "Pressemitteilung",
                    },
                    "case_patterns": [r"[CT]-\d+/\d+"],
                },
                "eca": {
                    "publication_urls": feeds["eca_publication_urls"],
                    "base_url": "https://www.eca.europa.eu",
                    "link_markers": ["report", "publication"],
                    "min_title_length": 11,
                },
            },
        },
        "audit_designer.vp_ai": {
            **common,
            "id": "audit_designer.vp_ai",
            "source": sources["designer"],
            "keywords": {"de": p["designer_global_keywords_de"], "en": []},
            "dip": {
                "api_url": p["designer_dip_api_url"],
                "portal_url": p["designer_dip_base_url"],
                "keywords": p["designer_dip_queries"],
                "relevance_keywords": p["designer_dip_keywords"],
                "page_size": 50,
                "classification": "none",
            },
            "eurlex": {
                "endpoint": p["eurlex_endpoint"],
                "document_url": p["eurlex_base_url"],
                "queries": p["designer_eurlex_queries"],
                "core_documents": p["designer_eurlex_core_documents"],
                "update_query_template": None,
                "funding_period_rule": "designer",
            },
            "feeds": {},
        },
    }
    for key, profile in profiles.items():
        path = args.output / f"{key}-{VERSION}.json"
        path.write_text(json.dumps(profile, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()
