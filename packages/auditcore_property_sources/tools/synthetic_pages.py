"""Synthetic, structure-derived portal pages for the characterization.

Neither ``wohnungsmonitor`` nor ``versteigerung`` stores original portal
pages. The pages below are therefore **synthetic and derived from the
structures the original parsers document** (regular expressions, JSON-LD and
Livewire formats, docstrings and comments). Every name, address, identifier
and price is fictitious; no advertiser names, telephone numbers or other
personal data are included. They prove the behavior of the original code on
these inputs, not the current layout of the live portals.

``python tools/synthetic_pages.py <dir>`` writes every page to ``<dir>``.
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path


# --------------------------------------------------------------------------- #
# immobilien.de: schema.org JSON-LD plus the price type in the markup
# --------------------------------------------------------------------------- #
def _imde_listing(
    kennung: str,
    price: object,
    postal: str | None,
    size: object,
    rooms: object,
    posted: str | None,
    name: str | None = "2-Zimmer-Wohnung",
) -> dict[str, object]:
    listing: dict[str, object] = {
        "@type": "RealEstateListing",
        "url": f"https://www.immobilien.de/expose/{kennung}",
        "offers": {"@type": "Offer", "priceSpecification": {"price": price}},
    }
    if name is not None:
        listing["name"] = name
    if posted is not None:
        listing["datePosted"] = posted
    if postal is not None:
        listing["address"] = {"@type": "PostalAddress", "postalCode": postal}
    if size is not None:
        listing["floorSize"] = {"@type": "QuantitativeValue", "value": size}
    if rooms is not None:
        listing["numberOfRooms"] = rooms
    return listing


def immobilien_de_pages() -> dict[str, str]:
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebPage", "name": "Mietwohnungen Berlin"},
            {
                "@type": "ItemList",
                "itemListElement": [
                    _imde_listing("41000001", 593.67, "10245", 54.3, 2, "2026-09-15"),
                    _imde_listing("41000002", 640, "10961", 61, 2.5, "2026-09-14", "Altbau"),
                    _imde_listing("41000003", "702.5", "12043", 48.0, 1, "15.09.2026"),
                    _imde_listing("41000004", 1234.5, "13055", 88.25, 3, "2026-09-10"),
                    _imde_listing("41000005", None, None, None, None, None, None),
                    _imde_listing("41000006", "auf Anfrage", "10115", 40, "2", "2026-09-01"),
                    _imde_listing("41000007", 455.0, "99999", 30.5, 1, "2026-09-02"),
                    {
                        "@type": ["Product", "RealEstateListing"],
                        "url": "https://www.immobilien.de/expose/41000008/",
                        "name": "Liste als Typ",
                        "address": {"postalCode": "10245"},
                        "offers": {"priceSpecification": {"price": 510}},
                    },
                    {
                        "@type": "RealEstateListing",
                        "url": "https://www.immobilien.de/projekt/abc",
                        "name": "ohne numerische Kennung",
                    },
                ],
            },
        ],
    }
    markup = (
        '<div class="card"><span class="price">593,67 €</span> | <span>Kaltmiete</span></div>'
        '<div class="card"><span class="price">640,00 €</span><span>Warmmiete</span></div>'
        '<div class="card"><span>702,50 €</span><span>Nettokaltmiete</span></div>'
        '<div class="card"><span>1.234,50 €</span><span>Warmmiete</span></div>'
        '<div class="card"><span>455 €</span></div>'
        '<div class="card"><span>510 €</span><span>Kaltmiete</span></div>'
    )
    page = (
        '<!DOCTYPE html><html lang="de"><head><title>Mietwohnungen</title>'
        '<script type="application/ld+json">' + json.dumps(graph, ensure_ascii=False) + "</script>"
        '<script type="application/ld+json">{kaputt</script>'
        "</head><body>" + markup + "</body></html>"
    )
    empty = (
        '<!DOCTYPE html><html><head><script type="application/ld+json">'
        '{"@context":"https://schema.org","@type":"WebPage"}</script></head>'
        "<body><p>Keine Treffer</p></body></html>"
    )
    return {"immobilien_de/seite-1.html": page, "immobilien_de/leer.html": empty}


# --------------------------------------------------------------------------- #
# inberlinwohnen: Livewire snapshots (wire:snapshot) with nested [value, {"s": …}]
# --------------------------------------------------------------------------- #
def _wire(name: str, data: dict[str, object]) -> str:
    snapshot = {"data": data, "memo": {"name": name, "id": "x"}, "checksum": "0"}
    return html.escape(json.dumps(snapshot, ensure_ascii=False), quote=True)


def _ibw_item(ident: int, **fields: object) -> dict[str, object]:
    item: dict[str, object] = {"id": ident}
    item.update(fields)
    return item


def inberlinwohnen_pages() -> dict[str, str]:
    company = [{"name": "Beispiel Wohnungsbaugesellschaft mbH"}, {"s": "arr"}]
    first = _ibw_item(
        900001,
        title="<b>Helle 2-Zimmer-Wohnung</b> mit Balkon &amp; Aufzug",
        company=company,
        address=[
            {
                "street": "Musterstraße",
                "number": "12a",
                "zipCode": "10245",
                "district": "Friedrichshain-Kreuzberg",
                "lat": "52,5071",
                "lon": "13.4545",
            },
            {"s": "arr"},
        ],
        area="54,32 m²",
        rentNet="351,30 €",
        extraCosts="68,00",
        rentGross="419,30",
        details=[
            [
                [
                    {"label": "Gesamtmiete", "value": "489,30 €"},
                    {"label": "WBS", "value": "erforderlich"},
                    {"label": "Heizung", "value": "Fernwärme"},
                ],
                {"s": "arr"},
            ],
            [
                [
                    {"label": "Energieverbrauchskennwert", "value": "98,5 kWh"},
                    {"label": "Eingestellt am", "value": "04.09.2026"},
                ],
                {"s": "arr"},
            ],
        ],
        attributes=[
            [{"flat_attribute_id": 3}, {"flat_attribute_id": 7}, {"flat_attribute_id": 99}],
            {"s": "arr"},
        ],
        rooms="2",
        level=3,
        levelsTotal=5,
        constructionYear=1965,
        energyPassType="Verbrauch",
        bathrooms=1,
        occupationDate="01.11.2026",
        deeplink="https://www.inberlinwohnen.de/wohnung/900001",
        createdAt="2026-09-04T17:59:02.000000Z",
    )
    second = _ibw_item(
        900002,
        title="Wohnung",
        company=None,
        address={
            "street": "Beispielweg",
            "number": None,
            "zipCode": "",
            "district": None,
            "lat": "52.45117026",
            "lon": "52.45117026",
        },
        area=61.5,
        rentNet=512.0,
        extraCosts=None,
        rentGross="600,00",
        details=[],
        attributes=[],
        rooms=3,
        createdAt="2026-09-05 08:00:00",
    )
    third = _ibw_item(
        900003,
        title="Unbekannte Werte",
        address={},
        area="unbekannt",
        rentNet="400",
        extraCosts="100",
        details=[{"label": "WBS", "value": "nicht erforderlich"}],
        createdAt=None,
        rooms="2,5",
    )
    attributes = (
        '<div wire:snapshot="'
        + _wire(
            "apartment-finder.item.partials.attributes-list",
            {"itemAttributes": [[3, 7, 11], {"s": "arr"}]},
        )
        + '" wire:id="a"><span>Balkon</span><span>Aufzug</span><span></span></div>'
    )
    items = "".join(
        '<div wire:snapshot="'
        + _wire("apartment-finder.item.apartment-item", {"item": [i, {"s": "arr"}]})
        + '" wire:id="i">…</div>'
        for i in (first, second, third)
    )
    foreign = '<div wire:snapshot="' + _wire("other.component", {"item": {"id": 5}}) + '">x</div>'
    broken = '<div wire:snapshot="{kein json" >y</div>'
    page1 = (
        "<!DOCTYPE html><html><body><p>1 bis 3 von 1.203 Angeboten</p>"
        + attributes
        + items
        + foreign
        + broken
        + "</body></html>"
    )
    later = _ibw_item(
        900004,
        title="Seite zwei",
        address={"zipCode": "12043"},
        attributes=[{"flat_attribute_id": 11}],
        rentNet="300",
        area="30",
    )
    page2 = (
        "<!DOCTYPE html><html><body><p>4 bis 4 von 1.203 Angeboten</p>"
        '<div wire:snapshot="'
        + _wire("apartment-finder.item.apartment-item", {"item": later})
        + '">z</div></body></html>'
    )
    return {
        "inberlinwohnen/seite-1.html": page1,
        "inberlinwohnen/seite-2.html": page2,
        "inberlinwohnen/leer.html": "<html><body>keine Angebote</body></html>",
    }


# --------------------------------------------------------------------------- #
# Kleinanzeigen: result cards with data-adid/data-href and "m² · Zi." text
# --------------------------------------------------------------------------- #
def _ka_card(
    adid: str, slug: str, place: str, title: str, text: str, size: str, rooms: str, price: str
) -> str:
    return (
        f'<article class="aditem" data-adid="{adid}" data-href="/s-anzeige/{slug}/{adid}-203-3331">'
        f'<div class="aditem-main--top--left">{place}</div>'
        f'<h2><a href="/s-anzeige/{slug}/{adid}-203-3331">{title}</a></h2>'
        f'<p class="aditem-main--middle--description">{text}</p>'
        f'<p class="simpletag">{size} m² · {rooms} Zi.</p>'
        f'<p class="aditem-main--middle--price-shipping--price">{price}</p>'
        "</article>"
    )


def kleinanzeigen_pages() -> dict[str, str]:
    cards = [
        _ka_card(
            "3100000001",
            "helle-2-zimmer",
            "10245 Friedrichshain",
            "Helle 2-Zimmer-Wohnung",
            "Ruhige Lage, Nachmieter ab November",
            "54,5",
            "2",
            "650 €",
        ),
        _ka_card(
            "3100000002",
            "altbau",
            "10405 Prenzlauer Berg",
            "Altbau mit Dielen",
            "Kaltmiete zuzüglich Nebenkosten",
            "1.250",
            "4",
            "1.250 € VB",
        ),
        _ka_card(
            "3100000003",
            "tausch",
            "13086 Weissensee",
            "Wohnungstausch 2 gegen 3",
            "Tausche meine Wohnung",
            "60",
            "2",
            "500 €",
        ),
        _ka_card(
            "3100000004",
            "gesuch",
            "12043 Neukölln",
            "Suche eine Wohnung",
            "Paar sucht Wohnung",
            "50",
            "2",
            "600 €",
        ),
        _ka_card(
            "3100000005",
            "moebliert",
            "10115 Mitte",
            "Möbliertes Apartment",
            "Zwischenmiete befristet",
            "30",
            "1",
            "900 €",
        ),
        _ka_card(
            "3100000006",
            "ohne-ort",
            "Berlin",
            "Wohnung ohne Postleitzahl",
            "Beschreibung",
            "45,00",
            "1,5",
            "480 €",
        ),
        '<article data-adid="3100000007"><h2>Karte ohne Maße</h2>'
        "<p>10999 Kreuzberg | x</p></article>",
    ]
    page = "<!DOCTYPE html><html><body><ul>" + "".join(cards) + "</ul></body></html>"
    return {
        "kleinanzeigen/seite-1.html": page,
        "kleinanzeigen/leer.html": "<html><body>Keine Ergebnisse</body></html>",
    }


# --------------------------------------------------------------------------- #
# bienici: JSON search API (realEstateAds)
# --------------------------------------------------------------------------- #
def bienici_ads() -> list[dict[str, object]]:
    return [
        {
            "id": "ag-exemple-001",
            "title": " Appartement lumineux ",
            "accountType": "agency",
            "accountDisplayName": "Agence Exemple",
            "propertyType": "flat",
            "adTypeFR": "location",
            "city": "Hœrdt",
            "postalCode": "67720",
            "departmentCode": "67",
            "district": {"insee_code": "67202"},
            "blurInfo": {"position": {"lat": 48.69, "lon": 7.78}},
            "price": 880,
            "charges": 60,
            "rentWithoutCharges": 820,
            "surfaceArea": 58.02,
            "roomsQuantity": 3,
            "bedroomsQuantity": 2,
            "agencyRentalFee": 450.5,
            "safetyDeposit": 820,
            "isFurnished": False,
            "floor": 2,
            "floorQuantity": 4,
            "heating": "individuel gaz",
            "energyValue": 150,
            "energyClassification": "D",
            "bathroomsQuantity": 1,
            "publicationDate": "2026-09-08T11:54:43.211Z",
            "modificationDate": "2026-09-10T08:00:00.000Z",
            "hasElevator": True,
            "hasCellar": True,
            "hasBalcony": False,
            "parkingPlacesQuantity": 1,
            "photos": [{"url_photo": "https://file.bienici.com/photo/exemple.jpg"}],
        },
        {
            "id": "particulier-002",
            "title": "",
            "accountType": "individual",
            "accountDisplayName": "M. Exemple",
            "propertyType": "house",
            "city": "Raon-l'Étape",
            "postalCode": "88110",
            "departmentCode": "88",
            "district": {"code_insee": "88372"},
            "blurInfo": {"centroid": {"lat": 48.4, "lon": 6.84}},
            "price": 700,
            "charges": 50,
            "surfaceArea": 90,
            "roomsQuantity": 1,
            "isFurnished": True,
            "publicationDate": "1970-01-01T00:00:00.000Z",
            "showerRoomsQuantity": 1,
            "hasTerrace": True,
            "hasGarden": True,
        },
        {
            "id": "ohne-nebenkosten-003",
            "accountType": "agency",
            "propertyType": "loft",
            "city": "Châtenois",
            "departmentCode": "99",
            "price": 640.456,
            "surfaceArea": None,
            "roomsQuantity": 0,
            "publicationDate": None,
        },
        {"id": "", "title": "ohne Kennung"},
    ]


def bienici_pages() -> dict[str, str]:
    ads = bienici_ads()
    page1 = {"total": 3, "perPage": 2, "from": 0, "realEstateAds": ads[:2]}
    page2 = {"total": 3, "perPage": 2, "from": 2, "realEstateAds": ads[2:]}
    page3 = {"total": 3, "perPage": 2, "from": 4, "realEstateAds": []}
    return {
        "bienici/seite-1.json": json.dumps(page1, ensure_ascii=False),
        "bienici/seite-2.json": json.dumps(page2, ensure_ascii=False),
        "bienici/seite-3.json": json.dumps(page3, ensure_ascii=False),
    }


# --------------------------------------------------------------------------- #
# Citya: schema.org OfferCatalog in JSON-LD
# --------------------------------------------------------------------------- #
def citya_offers() -> list[dict[str, object]]:
    def offer(
        kennung: str,
        name: str,
        price: object,
        postal: str | None,
        place: str | None,
        url: str | None = None,
    ) -> dict[str, object]:
        return {
            "@type": "Offer",
            "url": url
            if url is not None
            else f"https://www.citya.com/annonces/location/appartement/exemple-{postal}/{kennung}",
            "price": price,
            "itemOffered": {
                "@type": "Accommodation",
                "name": name,
                "address": {"postalCode": postal, "addressLocality": place},
            },
        }

    return [
        offer(
            "100001",
            "Location appartement de 3 pièces de 58.02m² à Strasbourg",
            "650.5",
            "67000",
            "Strasbourg",
        ),
        offer("100002", "Location maison de 5 pieces de 120,5m² à Colmar", 1100, "68000", "Colmar"),
        offer("100003", "Location parking de 12m² à Metz", "65", "57000", "Metz"),
        offer("100004", "Location studio à Nancy", "n.c.", "54000", "Nancy"),
        offer("", "Location local commercial de 40m² à Épinal", 900, "88000", "Épinal", url=""),
    ]


def citya_pages() -> dict[str, str]:
    catalog = {"@context": "https://schema.org", "@type": "OfferCatalog", "offers": citya_offers()}
    page = (
        '<!DOCTYPE html><html><head><script type="application/ld+json">'
        '{"@type":"Organization","name":"Citya"}</script>'
        '<script type="application/ld+json">'
        + json.dumps(catalog, ensure_ascii=False)
        + "</script></head><body><h1>362 biens à louer</h1></body></html>"
    )
    empty = (
        '<html><head><script type="application/ld+json">{"@type":"OfferCatalog",'
        '"offers":[]}</script></head><body>0 biens</body></html>'
    )
    return {"citya/seite-1.html": page, "citya/leer.html": empty}


# --------------------------------------------------------------------------- #
# ParuVendu: result blocks class="blocAnnonce …"
# --------------------------------------------------------------------------- #
def _pv_block(ident: str, link: str, title: str, price: str, place: str, date: str) -> str:
    return (
        f'<div class="blocAnnonce annonce" data-id="{ident}">'
        f'<a href="{link}" title=" {title}">'
        f"<h3>{title}</h3></a>"
        f'<div class="ergov3-priceannonce">{price}</div>'
        f"<p>{place}</p><span>{date}</span></div>"
    )


def paruvendu_pages() -> dict[str, str]:
    blocks = [
        _pv_block(
            "1262000001",
            "/immobilier/location/appartement/huttenheim-67230/1262000001",
            "Appartement 3 pièces 65 m²",
            "780&euro; <sup>CC</sup>",
            "Huttenheim (67)",
            "12/09/2026",
        ),
        _pv_block(
            "1262000002",
            "/immobilier/location/maison/colmar-68000/1262000002",
            "Maison 5 pièces 120,5 m²",
            "1 100 &euro; HC",
            "Colmar (68)",
            "11/09/2026",
        ),
        _pv_block(
            "1262000003",
            "/immobilier/location/appartement/metz-57000/1262000003",
            "Studio 1 pièce 22 m²",
            "450&euro;",
            "Metz (57)",
            "",
        ),
        _pv_block(
            "1262000004",
            "/immobilier/location/appartement/nulle-part/1262000004",
            "Loft 2 pièces",
            "prix sur demande",
            "sans département",
            "01/09/2026",
        ),
        '<div class="blocAnnonce"><p>Werbung ohne Kennung</p></div>',
    ]
    page = (
        "<!DOCTYPE html>\n<html><head><script>var x = 'blocAnnonce';</script></head><body>\n"
        + "\n".join(blocks)
        + "\n</body></html>"
    )
    return {
        "paruvendu/seite-1.html": page,
        "paruvendu/leer.html": "<html><body>Aucune annonce</body></html>",
    }


# --------------------------------------------------------------------------- #
# ZVG-Portal: result list (Aktenzeichen links) and detail pages
# --------------------------------------------------------------------------- #
def zvg_listing(amp: str = "&amp;") -> str:
    rows = [
        ("880001", "5 K 12/24"),
        ("880002", "12 K 7/2025"),
        ("880003", "3 L 1/23"),
        ("880001", "5 K 12/24"),
        ("880004", "ohne Aktenzeichen"),
    ]
    links = "".join(
        f'<tr><td><a href="index.php?button=showZvg{amp}zvg_id={z}{amp}land_abk=he">'
        f"<b>{a}</b></a></td></tr>"
        for z, a in rows
    )
    other = '<a href="index.php?button=showZvg&amp;zvg_id=990001&amp;land_abk=rp">9 K 1/24</a>'
    return f"<html><body><table>{links}</table>{other}</body></html>"


def _zvg_detail(
    objekt: str,
    beschreibung: str | None,
    wert: str,
    termin: str,
    ort: str | None = "Amtsgericht Musterstadt, Saal 2",
    extra: str = "",
    aktenzeichen: str = "5 K 12/24",
    anhaenge: tuple[str, ...] = (),
) -> str:
    rows = [
        f"<tr><td>Aktenzeichen:</td><td><b>{aktenzeichen}</b></td></tr>",
        f"<tr><td>Objekt/Lage:</td><td>{objekt}</td></tr>",
    ]
    if beschreibung is not None:
        rows.append(f"<tr><td>Beschreibung:</td><td>{beschreibung}</td></tr>")
    rows.append(f"<tr><td>Verkehrswert in €:</td><td>{wert}</td></tr>")
    rows.append(f"<tr><td>Termin:</td><td>{termin}</td></tr>")
    if ort is not None:
        rows.append(f"<tr><td>Ort der Versteigerung:</td><td>{ort}</td></tr>")
    links = "".join(
        f'<a href="index.php?button=showAnhang&amp;land_abk=he&amp;file_id={f}&amp;zvg_id=880001">'
        f"Anhang {i}</a> "
        for i, f in enumerate(anhaenge, 1)
    )
    return (
        f"<html><body><table>{''.join(rows)}</table>{extra}<p>Gericht: Musterstadt</p>"
        f"{links}</body></html>"
    )


def zvg_detail_pages() -> dict[str, str]:
    return {
        "efh": _zvg_detail(
            "Einfamilienhaus, Musterstraße 12, 35390 Musterstadt",
            "Einfamilienhaus, Baujahr 1968, Wohnfläche ca. 120,5 m², Garage",
            "245.000,00",
            "Dienstag, 14. Oktober 2026, 09:00 Uhr",
            anhaenge=("101", "102", "101"),
        ),
        "etw-dual-address": _zvg_detail(
            "Eigentumswohnung, Beispielstr. 5, 60311 Frankfurt am Main",
            "Wohnungseigentum im 2. OG, Beispielstraße 5 a, 60311 Frankfurt am Main, "
            "Wohnfläche 64 m², Baujahr 1995",
            "Gesamtverkehrswert: 667.000,00 € Einzelwerte: 600.000,00 € 67.000,00 €",
            "Mittwoch, 3. März 2027, 13:30 Uhr",
        ),
        "tausender-komma": _zvg_detail(
            "Grundstück, unbebaut, Am Eichbühel 30, 61476 Kronberg",
            "Gartenland, Flurstück 12/3",
            "80,000,-€ Sicherheitsleistung: 8.000,00 € Kassenzeichen 12345",
            "Montag, 5. Januar 2026, 10:00 Uhr",
        ),
        "summe-ohne-gesamt": _zvg_detail(
            "Mehrfamilienhaus mit 6 Wohnungen, Hauptstr. 2 A, 2 B, 34369 Musterdorf",
            "Wohnhaus mit 6 Einheiten, Wohnfläche 465 m², Baujahr 1962",
            "Haus: 400.000,00 € Garage: 15.000,- €",
            "Freitag, 30. Oktober 2026, 8:30 Uhr",
        ),
        "ohne-beschreibung": _zvg_detail(
            "Tiefgaragenstellplatz, Parkstraße, 65307 Bad Schwalbach",
            None,
            "12.500,00 €",
            "Donnerstag, 1. Februar 2029, 11:00 Uhr",
        ),
        "mojibake": _zvg_detail(
            "Reihenhaus, GartenstraÃŸe 7, 36037 Fulda",
            "Reihenmittelhaus, WohnflÃ¤che 98 mÂ², Baujahr 2031",
            "310.000,00 €",
            "Dienstag, 30. Februar 2026, 09:00 Uhr",
        ),
        "flur-kein-strasse": _zvg_detail(
            "Landwirtschaftsfläche, Flur 3 Flurstück 17, Gemarkung Musterau, 00000 Musterau",
            "Ackerland, Grünland",
            "Verkehrswert laut Gutachten 9.800 EUR",
            "Termin folgt",
            ort=None,
        ),
        "gewerbe": _zvg_detail(
            "Wohn- und Geschäftshaus, Marktplatz 1, 63065 Offenbach am Main",
            "Laden im EG, Büro im 1. OG, Wohnung im DG. Gläubiger: Beispielbank AG",
            "1.480.000,00 €",
            "Dienstag, 11. März 2025, 01:00 Uhr",
            aktenzeichen="7 K 244/2024",
        ),
        "ohne-alles": "<html><body><p>Keine Daten</p></body></html>",
    }


ZVG_MONEY = [
    "667.000,00",
    "65.000,-",
    "80,000,-",
    "725,12",
    "725,1",
    "1.250.000",
    "12 500,00 €",
    "EUR 9.800",
    "",
    "-",
    "abc",
    "1,5",
    "100",
    "0,-",
    "3.000.000,00 EUR",
]
ZVG_NUMBERS = ["945,80", "2015", "1.234,5", "ca. 120,5 m²", "keine Angabe", "12.345.678,99"]
ZVG_VALUE_BLOCKS = [
    "Verkehrswert in €: 245.000,00 € Termin:",
    "Verkehrswert in €: Gesamtverkehrswert 1.200.000,- EUR, Einzelwert 200.000,00 €",
    "Verkehrswert in €: 50.000,00 € 25.000,00 € Sicherheitsleistung 7.500,00 €",
    "Verkehrswert in €: laut Gutachten ohne Betrag",
    "Verkehrswert in €: 80,000,-€ IBAN siehe Bekanntmachung 12.345,00 €",
    "",
]
ZVG_ADDRESSES = [
    "Einfamilienhaus, Musterstraße 12, 35390 Musterstadt",
    "Am Eichbühel 30, 61476 Kronberg im Taunus",
    "Oberdorf 1, 34369 Musterdorf",
    "Mehrfamilienhaus, Hauptstr. 2 A, 2 B, 34369 Musterdorf",
    "Doppelhaus, Beispielweg 16 + 16 B, 35578 Wetzlar",
    "Reihenhaus, Lindenallee 16-18, 64283 Darmstadt",
    "Grundstück, Parkstraße, 65307 Bad Schwalbach",
    "Garage, Am Wasser, 35287 Amöneburg",
    "Waldfläche, Der Schillersberg, 36037 Fulda",
    "Flur 3 Flurstück 17, Gemarkung Musterau, 00000 Musterau",
    "Wohnung Nr. 5, 60311 Frankfurt am Main",
    "Gebäude, Str. 3, 12345 Ort",
    "ohne jede Adresse",
    "",
    "Grundbuch von Musterau Blatt 123, 35390 Musterstadt",
]
ZVG_TYPES = [
    "Wohn- und Geschäftshaus",
    "Mehrfamilienhaus mit 6 Wohnungen",
    "Reihenendhaus",
    "Doppelhaushälfte",
    "Eigentumswohnung mit Tiefgaragenstellplatz",
    "Einfamilienhaus",
    "Ladenlokal",
    "Hotel mit Restaurant",
    "Arztpraxis",
    "Lagerhalle",
    "Betriebsgrundstück",
    "unbebautes Grundstück",
    "Tiefgaragenstellplatz",
    "Schloss",
    "Wohnhaus mit 3 Wohnungen",
]
ZVG_MOJIBAKE = [
    "StraÃŸe",
    "GrÃ¼nland",
    "MÃ¤rz",
    "WohnflÃ¤che 98 mÂ²",
    "Ã¼ber",
    "ok",
    "",
    "\u009fx",
    "Caf�",
]
ZVG_STREETS = ["Graubergerstr.", "Hauptstr", "Marktpl.", "Str. 3", "Am Markt", None, "Lindenstr, 5"]


def all_pages() -> dict[str, str]:
    pages: dict[str, str] = {}
    for part in (
        immobilien_de_pages(),
        inberlinwohnen_pages(),
        kleinanzeigen_pages(),
        bienici_pages(),
        citya_pages(),
        paruvendu_pages(),
    ):
        pages.update(part)
    pages["zvg/liste.html"] = zvg_listing()
    pages["zvg/liste-roh.html"] = zvg_listing("&")
    for name, page in zvg_detail_pages().items():
        pages[f"zvg/detail-{name}.html"] = page
    return pages


def main() -> None:
    target = Path(sys.argv[1])
    for name, content in all_pages().items():
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print(f"{len(all_pages())} synthetische Seiten nach {target} geschrieben.")


if __name__ == "__main__":
    main()
