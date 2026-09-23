# auditcore_geo

Eigenständig installierbarer, **charakterisierter Geokern**: Großkreisentfernung
mit ausdrücklichem Erdmodell, Umkreissuche ohne falsch-negative Treffer, Punkt in
Fläche mit erkanntem Rand, Rand- und Stützpunktabstand, Flächenschwerpunkt,
UTM ↔ geographisch (Krüger), GeoPackage-Polygone und Douglas-Peucker. Laufzeit
nur Standardbibliothek. Der Nominatim-Geocoder ist ein Quellenadapter auf
`auditcore_harvest` im Extra `[geocoder]`. PostGIS, Kartenoberflächen und
Referenzdaten (PLZ, NUTS, Schutzgebiete) bleiben in den Anwendungen.

```python
from auditcore_geo import (
    ETRS89_UTM32N,
    KUGEL_MITTLERER_RADIUS,
    Lage,
    Punkt,
    flaeche_aus_geojson,
    grosskreis_km,
    lage,
    randabstand_m,
    umkreis,
    utm_nach_geographisch,
)

frankfurt, berlin = Punkt(lat=50.1106, lon=8.6821), Punkt.aus_lonlat([13.405, 52.52])
grosskreis_km(frankfurt, berlin, KUGEL_MITTLERER_RADIUS)  # 423.5505… (osint)
treffer = umkreis(frankfurt, [berlin, Punkt(50.14, 8.68)], 5_000, KUGEL_MITTLERER_RADIUS)

gebiet = flaeche_aus_geojson(
    {
        "type": "Polygon",
        "coordinates": [
            [[8.66, 50.10], [8.68, 50.10], [8.68, 50.11], [8.66, 50.11], [8.66, 50.10]]
        ],
    }
)
lage(Punkt(50.10, 8.67), gebiet) is Lage.RAND  # Rand ausdrücklich
randabstand_m(Punkt(50.12, 8.67), gebiet, KUGEL_MITTLERER_RADIUS)  # ≈ 1112 m
utm_nach_geographisch(477000.0, 5550000.0, ETRS89_UTM32N)  # ETRS89, keine Datumsumrechnung
```

| Modul | Inhalt |
|---|---|
| `koordinaten` | `Punkt(lat, lon)` mit Wertebereichsprüfung; Konstruktoren nur mit ausdrücklicher Achsenfolge; Bezugssysteme EPSG:4326/OGC:CRS84/EPSG:4258/EPSG:25832 als Beschreibung; `achsenfolge_erkennen` (→ `UNBEKANNT` statt still „nicht drehen“). |
| `distanz` | Profile `kugel.r1_6371008_8m` (osint, designer gis) und `kugel.6371000m` (designer register/company, flowsearch); `grosskreis_m/_km`; `umkreis` mit exaktem Kugel-Vorfilter (Pole, Datumsgrenze); `abstand_zur_strecke_lokal_m` (lokale Näherung wie designer). |
| `flaeche` | GeoJSON `Polygon`/`MultiPolygon` mit Löchern; `lage` (innen/außen/Rand, optional Meter-Toleranz), `enthaelt(..., rand_gilt_als_innen=...)`, `randabstand_m`, `naechster_stuetzpunkt_m`, `flaechenschwerpunkt`. Ungültige Geometrie ist ein Fehler, nie 0 m oder (0, 0). |
| `projektion` | UTM-Zonen 1–60, Nord/Süd, GRS80/WGS 84; bitgleich mit osint `utm_nach_wgs84` (Zone 32N), ≤ 0,71 mm zu PROJ. |
| `gpkg` | GeoPackageBinary + ISO-WKB (2D Polygon/MultiPolygon) mit `srs_id`; strikt. |
| `vereinfachung` | Douglas-Peucker iterativ, ergebnisgleich mit osint; `ring_vereinfachen(..., stellen=)`. |
| `legacy` | Verhaltensgleiche Nachbildungen der Quellfunktionen für Umstellung und Nachweis. |
| `nominatim` | `NominatimAdapter` (`geo.nominatim_search`), `pruefe_laufparameter`, `empfohlene_laufparameter` – erzwingen die prüfbaren OSMF-Bedingungen (≥ 1 s, regelmäßig ≥ 15 s, identifizierender User-Agent, Budget, https). |

Herkunft: `osint@d361ddb`, `audit_designer@1254591`, `flowsearch@10cb2a3`,
`flowworkshop@3d1cb40`; MIT-Freigabe für den extrahierten Bibliothekscode
(`NOTICE`, `provenance.json`). Abweichungen vom Original (GEO-C01–C14) und
offene fachliche Entscheidungen: [docs/behavior-changes.md](docs/behavior-changes.md).
Umstellung der Anwendungen: [docs/consumer-integration.md](docs/consumer-integration.md).
Consumer sind nach Nutzerentscheidung vom 23.09.2026 **geplant** („der mehrfache
Nutzen kommt noch“). Debian-Paket: `python3-auditcore-geo`.

Nominatim-Ergebnisse stehen unter ODbL; Anwendungen zeigen „© OpenStreetMap
contributors“ an und speichern Ergebnisse zwischen. Das Paket enthält keine
OSM- oder BKG-Daten.
