"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

from datetime import UTC, datetime, timedelta
from importlib.metadata import distribution
from importlib.util import find_spec

from auditcore_property_sources import (
    catalog,
    immobilien_de,
    is_allowed,
    kleinanzeigen,
    parse_robots,
    zvg,
    zvg_lifecycle,
)


def main() -> None:
    """Parsers, lifecycle, robots and catalog from the installed package."""
    package = distribution("auditcore_property_sources")
    assert package.version == "0.1.0"
    assert not [r for r in package.requires or [] if "extra ==" not in r]
    assert zvg.parse_money_amount("80,000,-") == 80000.0
    assert zvg.extract_address("Am Eichbühel 30, 61476 Kronberg") == (
        "Am Eichbühel",
        "30",
        "61476",
        "Kronberg",
    )
    doc = (
        '<html><script type="application/ld+json">{"@type":"RealEstateListing",'
        '"url":"https://www.immobilien.de/expose/1","offers":{"priceSpecification":'
        '{"price":500}}}</script><span>500 €</span><span>Warmmiete</span></html>'
    )
    listings, _ = immobilien_de.parse_page(doc)
    assert immobilien_de.normalise(listings["1"], {})["gesamtmiete"] == 500.0
    now = datetime(2026, 9, 23, tzinfo=UTC)
    case = zvg_lifecycle.CaseState(
        "5 K 1/26", "terminiert", now - timedelta(days=5), dates=(now - timedelta(days=1),)
    )
    closed, count = zvg_lifecycle.close_vanished([case], now)
    assert count == 1 and closed[0].status == "abgehalten"
    rules = parse_robots("User-agent: *\nDisallow: /*/preis:*\n")
    assert not is_allowed(rules, kleinanzeigen.search_url(700, 1))
    assert len(catalog()["sources"]) == 7
    if find_spec("auditcore_harvest") is not None:
        from auditcore_property_sources.adapters import ZvgListingAdapter

        assert ZvgListingAdapter().source.source_id == "property.zvg"
    print("PASS: installed auditcore_property_sources parsers, lifecycle, robots and catalog")


if __name__ == "__main__":
    main()
