"""robots.txt evaluation and the access findings recorded in the catalog."""

from __future__ import annotations

import pytest
from support import robots_text

from auditcore_property_sources import (
    catalog,
    immobilien_de,
    is_allowed,
    kleinanzeigen,
    parse_robots,
    zvg,
)
from auditcore_property_sources.errors import AccessNotPermitted
from auditcore_property_sources.robots import RobotsRules, require_allowed, robots_url

RULES = """
User-agent: special
Disallow: /

User-agent: *
Allow: /a/frei$
Disallow: /a/
Disallow : /b-*
Disallow: /*?mode=*
Disallow:
# Kommentar
Sitemap: https://example.invalid/sitemap.xml
"""


@pytest.mark.parametrize(
    ("url", "allowed"),
    [
        ("https://x.invalid/", True),
        ("https://x.invalid/a/frei", True),
        ("https://x.invalid/a/frei2", False),
        ("https://x.invalid/a/x", False),
        ("https://x.invalid/b-test", False),
        ("https://x.invalid/c?mode=list", False),
        ("https://x.invalid/c?other=1", True),
    ],
)
def test_wildcards_anchors_and_longest_match(url: str, allowed: bool) -> None:
    assert is_allowed(parse_robots(RULES), url) is allowed


def test_group_selection_and_round_trip() -> None:
    special = parse_robots(RULES, "Special-Bot/1.0")
    assert special.group == "special-bot/1.0" and not is_allowed(special, "/x")
    rules = parse_robots(RULES, "unknown")
    assert rules.group == "*" and RobotsRules.from_list(rules.to_list()) == rules
    assert parse_robots("").rules == ()
    with pytest.raises(AccessNotPermitted):
        require_allowed(rules, "https://x.invalid/a/x")
    assert robots_url("https://www.zvg-portal.de/index.php?x=1") == (
        "https://www.zvg-portal.de/robots.txt"
    )


def test_catalog_access_findings_equal_the_robots_snapshots() -> None:
    zvg_rules = parse_robots(robots_text("zvg-portal.de"))
    assert is_allowed(zvg_rules, zvg.BASE + "?button=Suchen")
    assert not is_allowed(zvg_rules, zvg.detail_url("1", "he"))
    assert not is_allowed(zvg_rules, zvg.BASE + "?button=showAnhang&file_id=1")
    ka = parse_robots(robots_text("kleinanzeigen.de"))
    assert not is_allowed(ka, kleinanzeigen.search_url(700, 1))
    assert not is_allowed(ka, kleinanzeigen.search_url(700, 2))
    assert is_allowed(ka, "https://www.kleinanzeigen.de/s-wohnung-mieten/berlin/c203l3331")
    assert is_allowed(parse_robots(robots_text("immobilien.de")), immobilien_de.search_url(700, 1))
    for entry in catalog()["sources"]:
        addresses = entry["access"]["robots"]["addresses"]
        blocked = any(a["allowed"] is False for a in addresses)
        assert blocked == (entry["source_id"] in {"property.kleinanzeigen", "property.zvg"})
        assert robots_text(entry["robots_snapshot"].removesuffix(".txt"))
