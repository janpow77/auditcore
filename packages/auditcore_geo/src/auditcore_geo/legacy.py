"""Verhaltensgleiche Nachbildungen der Quellfunktionen (für Umstellung und Nachweis).

Jede Funktion reproduziert das in ``tests/fixtures/legacy_observed.json``
aufgezeichnete Verhalten des Originals exakt – einschließlich der dort
dokumentierten Mängel (GEO-C01 bis GEO-C12 in ``docs/behavior-changes.md``).
Neue Aufrufer verwenden die Funktionen der übrigen Module.

Die Nachbildungen liegen je Quelle in ``_legacy_osint``, ``_legacy_designer``
und ``_legacy_flowsearch``; alle Namen bleiben hier importierbar.
"""

from ._legacy_designer import (
    _designer_im_ring,
    _designer_ringe,
    _register_im_ring,
    designer_company_abstand_zur_geometrie_m,
    designer_company_haversine_m,
    designer_gis_haversine_m,
    designer_gis_punkt_in_geometrie,
    designer_gis_randabstand_m,
    designer_gis_schwerpunkt,
    designer_gis_strecke_m,
    designer_register_entfernung_km,
    designer_register_naechster_stuetzpunkt_km,
    designer_register_punkt_in_gebiet,
)
from ._legacy_flowsearch import (
    flowsearch_calculate_distance_km,
    flowsearch_geometriezentrum,
    flowsearch_natura_distance_m,
)
from ._legacy_osint import (
    OSINT_ERDRADIUS_KM,
    OSINT_STELLEN,
    OSINT_TOLERANZ_GRAD,
    osint_achsen_drehen,
    osint_douglas_peucker,
    osint_haversine_km,
    osint_im_ring,
    osint_ring_vereinfachen,
    osint_umkreis,
    osint_utm_nach_wgs84,
    osint_wkb_polygone,
)

__all__ = [
    "OSINT_ERDRADIUS_KM",
    "OSINT_STELLEN",
    "OSINT_TOLERANZ_GRAD",
    "_designer_im_ring",
    "_designer_ringe",
    "_register_im_ring",
    "designer_company_abstand_zur_geometrie_m",
    "designer_company_haversine_m",
    "designer_gis_haversine_m",
    "designer_gis_punkt_in_geometrie",
    "designer_gis_randabstand_m",
    "designer_gis_schwerpunkt",
    "designer_gis_strecke_m",
    "designer_register_entfernung_km",
    "designer_register_naechster_stuetzpunkt_km",
    "designer_register_punkt_in_gebiet",
    "flowsearch_calculate_distance_km",
    "flowsearch_geometriezentrum",
    "flowsearch_natura_distance_m",
    "osint_achsen_drehen",
    "osint_douglas_peucker",
    "osint_haversine_km",
    "osint_im_ring",
    "osint_ring_vereinfachen",
    "osint_umkreis",
    "osint_utm_nach_wgs84",
    "osint_wkb_polygone",
]
