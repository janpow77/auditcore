"""Kleiner, charakterisierter Geokern: Entfernung, Umkreis, Fläche, UTM, GeoPackage, Vereinfachung.

Laufzeit nur Standardbibliothek. Der Nominatim-Adapter liegt in
:mod:`auditcore_geo.nominatim` und benötigt das Extra ``[geocoder]``
(``auditcore_harvest``); dieses Paket importiert ihn nicht selbst.
"""

from .distanz import (
    KUGEL_6371_KM,
    KUGEL_MITTLERER_RADIUS,
    KUGELPROFILE,
    Kugelprofil,
    Treffer,
    abstand_zur_strecke_lokal_m,
    grosskreis_km,
    grosskreis_m,
    kugelprofil,
    umkreis,
)
from .errors import GeoError, GeometrieFehler, KoordinatenFehler, ProfilFehler
from .flaeche import (
    Flaeche,
    Lage,
    Polygon,
    enthaelt,
    flaeche_aus_geojson,
    flaechenschwerpunkt,
    lage,
    naechster_stuetzpunkt_m,
    randabstand_m,
)
from .gpkg import GpkgGeometrie, lies_gpkg_polygone
from .koordinaten import (
    BEREICH_DEUTSCHLAND_OSINT,
    EPSG_4258,
    EPSG_4326,
    EPSG_25832,
    OGC_CRS84,
    Achsenfolge,
    Bereich,
    Koordinatenreferenzsystem,
    Punkt,
    achsenfolge_erkennen,
)
from .projektion import (
    ETRS89_UTM32N,
    GRS80,
    WGS84,
    Ellipsoid,
    UtmZone,
    geographisch_nach_utm,
    utm_nach_geographisch,
    utm_nach_geographisch_lonlat,
)
from .vereinfachung import douglas_peucker, ring_vereinfachen

__version__ = "0.1.0"

__all__ = [
    "BEREICH_DEUTSCHLAND_OSINT",
    "EPSG_4258",
    "EPSG_4326",
    "EPSG_25832",
    "ETRS89_UTM32N",
    "GRS80",
    "KUGEL_6371_KM",
    "KUGEL_MITTLERER_RADIUS",
    "KUGELPROFILE",
    "OGC_CRS84",
    "WGS84",
    "Achsenfolge",
    "Bereich",
    "Ellipsoid",
    "Flaeche",
    "GeoError",
    "GeometrieFehler",
    "GpkgGeometrie",
    "KoordinatenFehler",
    "Koordinatenreferenzsystem",
    "Kugelprofil",
    "Lage",
    "Polygon",
    "ProfilFehler",
    "Punkt",
    "Treffer",
    "UtmZone",
    "__version__",
    "abstand_zur_strecke_lokal_m",
    "achsenfolge_erkennen",
    "douglas_peucker",
    "enthaelt",
    "flaeche_aus_geojson",
    "flaechenschwerpunkt",
    "geographisch_nach_utm",
    "grosskreis_km",
    "grosskreis_m",
    "kugelprofil",
    "lage",
    "lies_gpkg_polygone",
    "naechster_stuetzpunkt_m",
    "randabstand_m",
    "ring_vereinfachen",
    "umkreis",
    "utm_nach_geographisch",
    "utm_nach_geographisch_lonlat",
]
