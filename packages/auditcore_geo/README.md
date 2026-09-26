# auditcore_geo

## Zweck

Charakterisierter Geokern ohne Fremdabhängigkeiten: Großkreisentfernung mit ausdrücklichem Erdmodell, Umkreissuche, Punkt in Fläche mit erkanntem Rand, UTM, GeoPackage-Polygone und Douglas-Peucker.

Für Anwendungen, die Vorhaben, Begünstigte oder Schutzgebiete räumlich
zuordnen (osint, audit_designer, flowsearch, flowworkshop). Der
Nominatim-Geocoder ist ein Quellenadapter auf `auditcore_harvest` im Extra
`[geocoder]`. PostGIS, Kartenoberflächen und Referenzdaten (PLZ, NUTS,
Schutzgebiete) bleiben in den Anwendungen. Die öffentliche API ist bewusst
deutsch benannt (Entscheidungen D1–D6).

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install auditcore_geo \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (zuletzt veröffentlicht: 0.2.1 im
Release v0.4.0; weitere Versionen und Hashes unter
`https://janpow77.github.io/auditcore/simple/auditcore-geo/`):

```text
auditcore_geo @ https://github.com/janpow77/auditcore/releases/download/v0.4.0/auditcore_geo-0.2.1-py3-none-any.whl#sha256=3433bd595e51d8d08b8c7ba98fdf667f7158cd0c07fe822af7ed92ab39acf963
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-geo
```

Extras: `[geocoder]` – Nominatim-Adapter (`auditcore_geo.nominatim`) auf
`auditcore_harvest`; `[web]` – REST-Routen `auditcore_geo.web` auf Starlette
(Debian: `python3-starlette`); `[fastapi]` – zusätzlich FastAPI-Router
(`python3-fastapi`); `[dev]` – Test- und Prüfwerkzeuge.

## Schnellstart

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
assert round(grosskreis_km(frankfurt, berlin, KUGEL_MITTLERER_RADIUS), 4) == 423.5505  # wie osint

treffer = umkreis(frankfurt, [berlin, Punkt(50.14, 8.68)], 5_000, KUGEL_MITTLERER_RADIUS)
assert [t.index for t in treffer] == [1]  # nur der zweite Punkt liegt im 5-km-Umkreis

gebiet = flaeche_aus_geojson(
    {
        "type": "Polygon",
        "coordinates": [
            [[8.66, 50.10], [8.68, 50.10], [8.68, 50.11], [8.66, 50.11], [8.66, 50.10]]
        ],
    }
)
assert lage(Punkt(50.10, 8.67), gebiet) is Lage.RAND  # Rand wird ausdrücklich erkannt
assert lage(Punkt(50.105, 8.67), gebiet) is Lage.INNEN
assert round(randabstand_m(Punkt(50.12, 8.67), gebiet, KUGEL_MITTLERER_RADIUS)) == 1112

# ETRS89/UTM 32N → geographisch (keine Datumsumrechnung)
ort = utm_nach_geographisch(477000.0, 5550000.0, ETRS89_UTM32N)
```

```pycon
>>> round(ort.lat, 6), round(ort.lon, 6)
(50.10181, 8.678392)
```

## API-Überblick

| Modul | Inhalt |
|---|---|
| `koordinaten` | `Punkt(lat, lon)` mit Wertebereichsprüfung; Konstruktoren nur mit ausdrücklicher Achsenfolge; Bezugssysteme EPSG:4326/OGC:CRS84/EPSG:4258/EPSG:25832 als Beschreibung; `achsenfolge_erkennen` (→ `UNBEKANNT` statt still „nicht drehen“). |
| `distanz` | Profile `kugel.r1_6371008_8m` (osint, designer gis) und `kugel.6371000m` (designer register/company, flowsearch); `grosskreis_m/_km`; `umkreis` mit exaktem Kugel-Vorfilter (Pole, Datumsgrenze); `abstand_zur_strecke_lokal_m` (lokale Näherung wie designer). |
| `flaeche` | GeoJSON `Polygon`/`MultiPolygon` mit Löchern (`flaeche_aus_geojson`, `flaeche_aus_ringen`, `flaeche_aus_gpkg`); `lage` (innen/außen/Rand, optional Meter-Toleranz), `enthaelt(..., rand_gilt_als_innen=...)`, `randabstand_m`, `randbefund`, `flaechen_im_umkreis`, `naechster_stuetzpunkt_m`, `flaechenschwerpunkt`. Zu Punkt/Linie zusammengefallene Ringe (0.2.0, GEO-C16) verwerfen die Fläche nicht: Außenringe zählen als Objekt ohne Fläche mit Abstand, Löcher entfallen, jeder Fall steht in `Flaeche.hinweise` (`strikt=True` weist ab). Unlesbare Geometrie ist ein Fehler, nie 0 m oder (0, 0). |
| `projektion` | UTM-Zonen 1–60, Nord/Süd, GRS80/WGS 84; bitgleich mit osint `utm_nach_wgs84` (Zone 32N), ≤ 0,71 mm zu PROJ. |
| `gpkg` | GeoPackageBinary + ISO-WKB (2D Polygon/MultiPolygon) mit `srs_id`; strikt. |
| `vereinfachung` | Douglas-Peucker iterativ, ergebnisgleich mit osint; `ring_vereinfachen(..., stellen=)`. |
| `legacy` | Verhaltensgleiche Nachbildungen der Quellfunktionen für Umstellung und Nachweis. |
| `nominatim` | `NominatimAdapter` (`geo.nominatim_search`), `pruefe_laufparameter`, `empfohlene_laufparameter` – erzwingen die prüfbaren OSMF-Bedingungen (≥ 1 s, regelmäßig ≥ 15 s, höchstens 1 000 Anfragen je Tag und Consumer, identifizierender User-Agent, Budget, https). |

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_geo.__all__` (57):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `BEREICH_DEUTSCHLAND_OSINT` | Konstante | Bereich, an dem ``osint`` (``werkzeuge/betroffenheit.py:_achsen_drehen``) die Achsenfolge deutscher GML-Antworten erkennt: Breite 47–56, Länge 5–16 Grad. | `koordinaten` |
| `EMPFOHLENES_ERDMODELL` | Konstante | Empfohlenes Profil für neue gemeinsame Bestände (Entscheidung vom 23.09.2026, vom Nutzer delegiert). Keine Funktion verwendet es still; es wird ausdrücklich übergeben. | `distanz` |
| `EMPFOHLEN_RAND_GILT_ALS_INNEN` | Konstante | Empfohlene Randregel (Entscheidung vom 23.09.2026, vom Nutzer delegiert): Randpunkte zählen als innen – ein möglicher Schutzgebietsbezug wird eher gemeldet als übersehen. | `_flaechenmodell` |
| `EPSG_25832` | Konstante | ETRS89 / UTM Zone 32N (Rechtswert, Hochwert in Metern), z. B. BKG VG2500. | `koordinaten` |
| `EPSG_4258` | Konstante | ETRS89 geographisch (Bezugssystem der amtlichen deutschen Geobasisdaten). | `koordinaten` |
| `EPSG_4326` | Konstante | WGS 84 geographisch; Achsenfolge der EPSG-Registrierung ist Breite, Länge. | `koordinaten` |
| `ETRS89_UTM32N` | Konstante | ETRS89 / UTM Zone 32N (EPSG:25832). | `projektion` |
| `GRS80` | Konstante | GRS80 (ETRS89); Wert der Quelle ``osint``. | `projektion` |
| `KUGELPROFILE` | Konstante | – | `distanz` |
| `KUGEL_6371_KM` | Konstante | Gerundeter Radius 6 371 000 m. | `distanz` |
| `KUGEL_MITTLERER_RADIUS` | Konstante | Mittlerer Erdradius R1 = (2a + b) / 3 des GRS80/WGS 84 (6 371 008,8 m). | `distanz` |
| `OGC_CRS84` | Konstante | OGC CRS84 = WGS 84 in der Reihenfolge Länge, Breite (GeoJSON, RFC 7946). | `koordinaten` |
| `VERTRAG_ENTARTETE_RINGE` | Konstante | Vertragsnummer der Behandlung zusammengefallener Ringe. | `_flaechenmodell` |
| `WGS84` | Konstante | WGS 84. | `projektion` |
| `Achsenfolge` | Aufzählung | Reihenfolge eines Zahlenpaares. | `koordinaten` |
| `Bereich` | Datenklasse | Achsparalleles Rechteck in Grad; dient nur Plausibilitäts- und Vorfilterzwecken. | `koordinaten` |
| `Ellipsoid` | Datenklasse | Rotationsellipsoid mit großer Halbachse ``a`` (m) und Abplattung ``f``. | `projektion` |
| `EntarteterRing` | Datenklasse | Ein auf Punkt oder Linie zusammengefallener Ring (GEO-C16). | `_flaechenmodell` |
| `Entartung` | Aufzählung | Worauf ein Ring zusammengefallen ist. | `_flaechenmodell` |
| `Flaeche` | Datenklasse | Echte Teilflächen und zusammengefallene Ringe (GeoJSON ``Polygon``/``MultiPolygon``). | `_flaechenmodell` |
| `GeoError` | Ausnahme | Basisklasse; ``code`` ist stabil und maschinenlesbar. | `errors` |
| `GeometrieFehler` | Ausnahme | Geometrie unlesbar, unvollständig oder von einem nicht unterstützten Typ. | `errors` |
| `GpkgGeometrie` | Datenklasse | Polygone (je Liste von Ringen mit Punkten in Quellkoordinaten) und ``srs_id``. | `gpkg` |
| `KoordinatenFehler` | Ausnahme | Koordinate nicht endlich, außerhalb des Wertebereichs oder Achsenfolge unbekannt. | `errors` |
| `Koordinatenreferenzsystem` | Datenklasse | Beschreibung eines Bezugssystems; die Bibliothek transformiert keine Datumsangaben. | `koordinaten` |
| `Kugelprofil` | Datenklasse | Kugelförmiges Erdmodell mit Radius in Metern und Herkunft der Variante. | `distanz` |
| `Lage` | Aufzählung | Lage eines Punktes zu einer Fläche. | `_flaechenmodell` |
| `Polygon` | Datenklasse | Außenring und Löcher; Ringe ohne wiederholten Schlusspunkt. | `_flaechenmodell` |
| `ProfilFehler` | Ausnahme | Unbekanntes oder ungültiges Profil (Erdmodell, Projektion). | `errors` |
| `Punkt` | Datenklasse | Geographische Koordinate in Grad (Breite ``lat``, Länge ``lon``). | `koordinaten` |
| `Randbefund` | Datenklasse | Lage und Randabstand samt Hinweisen der Fläche. | `flaeche` |
| `RingRolle` | Aufzählung | Außenring oder Loch. | `_flaechenmodell` |
| `Treffer` | Datenklasse | Ein Punkt im Umkreis: Index in der Eingabefolge und Entfernung in Metern. | `distanz` |
| `UtmZone` | Datenklasse | UTM-Zone (1–60), Halbkugel und Ellipsoid; Maßstab 0,9996, Rechtswert-Offset 500 km. | `projektion` |
| `__version__` | Wert | – | `(Paketstamm)` |
| `abstand_zur_strecke_lokal_m` | Funktion | Kürzester Abstand von ``p`` zur Strecke ``a``–``b`` in Metern. | `distanz` |
| `achsenfolge_erkennen` | Funktion | Achsenfolge von Zahlenpaaren anhand eines bekannten Gebiets bestimmen. | `koordinaten` |
| `douglas_peucker` | Funktion | Vereinfachte Punktfolge; Anfangs- und Endpunkt bleiben stets erhalten. | `vereinfachung` |
| `enthaelt` | Funktion | Punkt in Fläche; wie der Rand zählt, muss der Aufrufer ausdrücklich sagen. | `flaeche` |
| `flaeche_aus_geojson` | Funktion | ``Polygon``/``MultiPolygon`` in GeoJSON-Achsenfolge; alles andere ist ein Fehler. | `_flaechenmodell` |
| `flaeche_aus_gpkg` | Funktion | Fläche aus :func:`lies_gpkg_polygone`; zusammengefallene Ringe nach GEO-C16. | `_flaechenmodell` |
| `flaeche_aus_ringen` | Funktion | Fläche aus Polygonen (je Ringe aus ``(lon, lat)``-Paaren, Ring 0 außen). | `_flaechenmodell` |
| `flaechen_im_umkreis` | Funktion | Alle Flächen mit :func:`randabstand_m` bis einschließlich ``radius_m``. | `flaeche` |
| `flaechenschwerpunkt` | Funktion | Flächengewichteter Schwerpunkt, eben in Grad gerechnet (Löcher abgezogen). | `flaeche` |
| `geographisch_nach_utm` | Funktion | ``(ost, nord)`` in Metern; Hinrechnung nach Krüger (n³). | `projektion` |
| `grosskreis_km` | Funktion | Großkreisentfernung in Kilometern. | `distanz` |
| `grosskreis_m` | Funktion | Großkreisentfernung in Metern (Haversine, numerisch geklemmt). | `distanz` |
| `kugelprofil` | Funktion | Profil nach Kennung oder :class:`ProfilFehler`. | `distanz` |
| `lage` | Funktion | Lage des Punktes: innen, außen oder auf dem Rand. | `flaeche` |
| `lies_gpkg_polygone` | Funktion | Polygone eines GeoPackage-Blobs samt ``srs_id``. | `gpkg` |
| `naechster_stuetzpunkt_m` | Funktion | Großkreisabstand zum nächsten Stützpunkt (nicht zur Kante!) in Metern. | `flaeche` |
| `randabstand_m` | Funktion | Abstand zum nächsten Rand in Metern; 0 für Punkte innen oder auf dem Rand. | `flaeche` |
| `randbefund` | Funktion | :func:`lage` und :func:`randabstand_m` in einem, mit Herkunft des Abstands. | `flaeche` |
| `ring_vereinfachen` | Funktion | Geschlossenen Ring vereinfachen; ``None``, wenn weniger als vier Punkte bleiben. | `vereinfachung` |
| `umkreis` | Funktion | Alle Punkte bis einschließlich ``radius_m``, nach (Entfernung, Index) sortiert. | `distanz` |
| `utm_nach_geographisch` | Funktion | Geographischer :class:`Punkt` aus UTM; Länge auf -180..180 normiert. | `projektion` |
| `utm_nach_geographisch_lonlat` | Funktion | ``(lon, lat)`` in Grad aus Rechts-/Hochwert in Metern (Achsenfolge der Quelle). | `projektion` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_geo.distanz` | Entfernungen auf der Kugel mit ausdrücklichem Erdmodell. |
| `auditcore_geo.errors` | Fehlervertrag der Geobibliothek. |
| `auditcore_geo.flaeche` | Flächen aus GeoJSON: Punkt in Fläche mit Rand, Randabstand, Schwerpunkt. |
| `auditcore_geo.gpkg` | Flächengeometrien aus GeoPackage-Blobs (GeoPackageBinary + ISO-WKB) lesen. |
| `auditcore_geo.koordinaten` | Punkte, Koordinatenreferenzsysteme und Achsenfolge. |
| `auditcore_geo.legacy` | Verhaltensgleiche Nachbildungen der Quellfunktionen (für Umstellung und Nachweis). |
| `auditcore_geo.nominatim` | Nominatim-Geocoder als Quellenadapter auf ``auditcore_harvest`` (Extra ``[geocoder]``). |
| `auditcore_geo.projektion` | Transversale Mercatorprojektion (UTM) nach Krüger, Reihe bis n³. |
| `auditcore_geo.vereinfachung` | Linien- und Ringvereinfachung nach Douglas-Peucker. |
| `auditcore_geo.web` | REST-Vertrag und Routen für Geo-Oberflächen (Extras ``web`` und ``fastapi``). |
<!-- api-overview:end -->

## Profile und Konfiguration

- **Erdmodelle** (`Kugelprofil`, kein stiller Standardwert):
  `kugel.r1_6371008_8m` (`KUGEL_MITTLERER_RADIUS`, osint, designer gis) und
  `kugel.6371000m` (`KUGEL_6371_KM`, designer register/company, flowsearch).
  Empfohlen für neue gemeinsame Bestände: `EMPFOHLENES_ERDMODELL` (R1,
  Entscheidung D1); `kugel.6371000m` bleibt für Replay und Altbestände.
- **Randpunkte**: `EMPFOHLEN_RAND_GILT_ALS_INNEN = True` (D2), wird an
  `enthaelt(..., rand_gilt_als_innen=...)` ausdrücklich übergeben.
- **Zusammengefallene Ringe** (0.2.0): `strikt=True` weist sie ab, sonst
  werden sie als `EntarteterRing` in `Flaeche.entartet`/`Flaeche.hinweise`
  geführt (`VERTRAG_ENTARTETE_RINGE`).
- **Nominatim** (`[geocoder]`): `pruefe_laufparameter` und
  `empfohlene_laufparameter` erzwingen am öffentlichen Endpunkt ≥ 1 s Abstand,
  bei regelmäßigen Läufen ≥ 15 s, höchstens 1 000 Anfragen je Tag und Consumer
  (`OEFFENTLICH_TAGESGRENZE`, D5), identifizierenden `user_agent`, Budget und
  https. Eigene Instanzen sind nicht begrenzt.

## Web-Schnittstelle (0.3.0)

`auditcore_geo.web` stellt den REST-Vertrag für die Oberflächenkomponente
`<flowaudit-geo-map>` aus `@flowaudit/ui` bereit
([`docs/ui/geo-rest.md`](../../docs/ui/geo-rest.md)): Katalog der Erdmodelle
und Empfehlungen D1/D2, Umkreissuche, Punkt in Fläche mit ausdrücklicher
Randregel und Randtoleranz, UTM hin und zurück, Douglas-Peucker in Metern
oder Grad, GeoPackage-Dateien (Upload oder benannte Serverquellen, UTM wird
zurückgerechnet). Die Vertragsfunktionen sind framework-frei; die Web-Schicht
trägt wie alle auditcore-Web-Module englische Namen, die JSON-Felder folgen
den deutschen Begriffen der Bibliothek.

```python
from auditcore_geo.web import Settings, create_app, create_router

app = create_app("/api/geo")                       # Starlette ([web])
router = create_router("/api/geo", settings=Settings(max_points=20_000))  # FastAPI
```

Adresssuche gibt es nur, wenn der Server ausdrücklich einen `Geocoder`
übergibt (`Settings(geocoder=NominatimGeocoder(...))`, Extra `[geocoder]`,
Transport/Uhr/Warten injiziert, Zwischenspeicher und Tagesgrenze D5); ohne
ihn antwortet `/geocode` mit 404 `geocoder_abgeschaltet`.

## Herkunft und Charakterisierung

Extrahiert aus `osint@d361ddb`, `audit_designer@1254591`, `flowsearch@10cb2a3`
und `flowworkshop@3d1cb40` (Blobs in `NOTICE`). Vor der Übernahme wurden
290 Fälle an den Originalen tatsächlich ausgeführt (`tools/capture_legacy.py`,
`tests/fixtures/legacy_observed.json`; pyproj/PROJ und shapely nur als
Vergleichsreferenz). `auditcore_geo.legacy` reproduziert alle Fälle exakt,
`utm_nach_wgs84` bitgleich; der Bibliotheksvertrag weicht nur in den
dokumentierten Punkten ab. Für 0.2.0 kamen 168 Fälle zu zusammengefallenen
Ringen hinzu (`tools/capture_entartet.py`; Lage gegen shapely 168/168 gleich).
Live-Rauchtest gegen Nominatim am 23.09.2026 bestanden (`tools/live_smoke.py`).
Consumer: audit_designer nutzt 0.1.0 (Release v0.3.0); weitere Umstellungen sind
geplant ([Umstellung](docs/consumer-integration.md)).

## Bewusste Verhaltensabweichungen

GEO-C01–C16 und die Entscheidungen D1–D6 (23.09.2026):
[docs/behavior-changes.md](docs/behavior-changes.md). Kurzfassung:
benannte Erdmodelle statt sechs Haversine-Varianten, exakter Umkreis-Vorfilter
ohne falsch-negative Treffer (Pole, Datumsgrenze), dreiwertige Lage mit Rand,
Multipolygone je Teilfläche mit eigenen Löchern, Fehler statt Ersatzwerten
(nie 0 m oder (0, 0)), strikte GeoPackage-Lesung, `UNBEKANNT` bei unklarer
Achsenfolge, flächengewichteter Schwerpunkt und getrennte Abstandsmaße,
Netzfehler ≠ „kein Treffer“, keine erfundene Konfidenz beim Geocoding,
Nominatim-Tagesgrenze, zusammengefallene Ringe als Punkt/Linie statt Verwerfen
der Fläche.

## Abhängigkeiten

Python ≥ 3.11, zur Laufzeit nur die Standardbibliothek. Optional
`auditcore_harvest==0.1.1` über `[geocoder]`; `auditcore_geo` importiert den
Adapter nicht selbst. pyproj, shapely und PostGIS sind keine Abhängigkeiten.

## Sicherheit und Datenschutz

Der Kern rechnet nur mit übergebenen Koordinaten, ohne Netzwerk oder Dateien
(außer dem ausdrücklich übergebenen GeoPackage-Blob). Der Nominatim-Adapter
sendet Adressen über den vom Consumer injizierten Transport an den Endpunkt;
Adressen können personenbezogen sein – Zweck, Zwischenspeicherung und
Auftragsverarbeitung klärt die Anwendung. Unlesbare Geometrie ist immer ein
`GeometrieFehler`, damit fehlende Daten weder Betroffenheit noch
Nichtbetroffenheit vortäuschen. Nominatim-Ergebnisse stehen unter ODbL;
Anwendungen zeigen „© OpenStreetMap contributors“ an. Das Paket enthält keine
OSM- oder BKG-Daten; die Nominatim-Fixtures sind synthetisch.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`) für den extrahierten Bibliothekscode, Freigabe des
Rechteinhabers vom 22.09.2026 (`USER_AUTHORIZED_MIT`); die Quellrepositories
werden nicht umlizenziert, Datenrechte der Dienste bleiben gesondert. Quellen
und Blobs: `NOTICE` und `provenance.json`.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
