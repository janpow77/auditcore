# REST-Vertrag Geo-Karte (`auditcore_geo.web`)

Stand 2026-09-25. Vertrag zwischen `auditcore_geo.web` (ab 0.3.0) und der
Oberflächenkomponente `<flowaudit-geo-map>` aus `@auditcore/ui` (Vue
`FaGeoMap`, React `FlowauditGeoMap`). Alle Berechnungen laufen in der
Bibliothek; die Oberfläche rechnet selbst keine Entfernungen, Lagen oder
Projektionen. Kein Erdmodell und keine Randregel wird still angenommen
(Entscheidungen D1, D2): Die Oberfläche übernimmt die Empfehlung aus
`GET /profile` sichtbar als Vorauswahl und sendet sie ausdrücklich mit.

## Einbinden

| Extra | Paket (pip) | Debian (optional, „Suggests“) |
|---|---|---|
| `auditcore_geo[web]` | `starlette>=0.26.1` | `python3-starlette (>= 0.26.1)` |
| `auditcore_geo[fastapi]` | `fastapi>=0.92` | `python3-fastapi (>= 0.92.0)` |
| `auditcore_geo[geocoder]` | `auditcore_harvest==0.1.1` | `python3-auditcore-harvest` |

```python
from pathlib import Path
from starlette.routing import Mount
from auditcore_geo.web import Settings, create_app, create_router, routes

settings = Settings(
    gpkg_sources={"schutzgebiete": Path("/srv/geo/schutzgebiete.gpkg")},  # nur Namen sichtbar
    max_points=20_000,
)
app = create_app("/api/geo", settings=settings)              # eigenständig (Starlette)
fastapi_app.include_router(create_router("/api/geo", settings=settings))  # FastAPI
starlette_app.router.routes.append(Mount("/api/geo", routes=routes(settings=settings)))
```

Die Vertragsfunktionen `catalogue`, `radius_search`, `locate`, `to_utm`,
`from_utm`, `simplify`, `read_geopackage` und `read_source` sind ohne
Web-Framework aufrufbar. Die FastAPI-Variante hängt die Starlette-Endpunkte
unverändert ein (Antworten byteidentisch, nicht im OpenAPI-Schema).
Authentisierung, CORS und Ratenbegrenzung sind Sache der Anwendung.

`Settings`: `max_body_bytes` (16 MiB), `max_points` (50 000),
`max_vertices` (250 000), `max_gpkg_bytes` (64 MiB), `max_gpkg_areas`
(5 000), `gpkg_sources` (Name → Pfad), `geocoder` (Standard `None`).

## Endpunkte

Pfade relativ zum Einhängepunkt. Punkte sind immer
`{"lat": Breite, "lon": Länge}` in Dezimalgrad (benannte Achsen, keine
Achsenfolge-Raterei); Flächen sind GeoJSON `Polygon`/`MultiPolygon` in
RFC-7946-Folge (Länge, Breite).

| Methode | Pfad | Zweck |
|---|---|---|
| GET | `/profile` | Erdmodelle, Empfehlungen, Ellipsoide, Grenzen, aktive Anschlüsse |
| POST | `/umkreis` | Punkte bis einschließlich Radius, nach Entfernung sortiert |
| POST | `/lage` | Punkt in Fläche: innen/außen/Rand, Randregel, Randabstand |
| POST | `/utm` | Rechts-/Hochwert eines Punktes |
| POST | `/utm/geographisch` | Punkt aus Rechts-/Hochwert |
| POST | `/vereinfachung` | Douglas-Peucker je Ring |
| POST | `/gpkg` | GeoPackage-Datei (Anfragekörper = Datei) lesen; `?tabelle=` optional |
| GET | `/gpkg/quellen` | Namen der Serverquellen |
| GET | `/gpkg/quellen/{name}` | Serverquelle lesen; `?tabelle=` optional |
| POST | `/geocode` | Adresssuche – nur mit angeschlossenem Geocoder, sonst 404 |

### `GET /profile`

```json
{"bibliothek": "auditcore_geo 0.3.1",
 "erdmodelle": [{"id": "kugel.r1_6371008_8m", "radius_m": 6371008.8, "beschreibung": "…", "empfohlen": true},
                {"id": "kugel.6371000m", "radius_m": 6371000.0, "beschreibung": "…", "empfohlen": false}],
 "empfohlenes_erdmodell": "kugel.r1_6371008_8m", "rand_gilt_als_innen_empfohlen": true,
 "ellipsoide": ["GRS80", "WGS84"], "vereinfachung_einheiten": ["meter", "grad"],
 "grenzen": {"max_body_bytes": 16777216, "max_punkte": 50000, "max_stuetzpunkte": 250000,
             "max_gpkg_bytes": 67108864, "max_gpkg_flaechen": 5000},
 "geocoder": {"aktiv": false, "namensnennung": null}, "gpkg_quellen": []}
```

### `POST /umkreis`

Anfrage: `zentrum` (Punkt), `punkte` (Liste von Punkten mit optionaler `id`,
Text oder ganze Zahl; ohne `id` gilt der Index), `radius_m` (≥ 0),
`erdmodell` (Pflicht). Antwort: `erdmodell`, `radius_m`, `geprueft`,
`treffer[]` mit `index`, `id`, `abstand_m` (Großkreis, Haversine), sortiert
nach (Abstand, Index). Der Vorfilter ist exakt (Pole, Datumsgrenze).

### `POST /lage`

Anfrage: `punkt`, `flaeche`, `erdmodell`, `rand_gilt_als_innen` (Pflicht,
Empfehlung D2 `true`), `rand_toleranz_m` (optional, Standard 0).
Antwort:

| Feld | Inhalt |
|---|---|
| `lage` | exakte Lage `innen`, `aussen`, `rand` (Punkt genau auf Kante/Ecke) |
| `lage_mit_toleranz` | Lage mit Randtoleranz (Punkte näher als `rand_toleranz_m` an einer Kante zählen als Rand) – maßgeblich für `enthaelt` |
| `enthaelt` | `innen`, oder `rand` bei `rand_gilt_als_innen` |
| `abstand_m` | Abstand zum nächsten Rand (0 innen/auf dem Rand) |
| `entarteter_ring`, `hinweise` | zusammengefallene Ringe (GEO-C16) mit lesbarem Hinweis |

### `POST /utm`, `POST /utm/geographisch`

`/utm`: `punkt`, `ellipsoid` (`GRS80` = ETRS89 oder `WGS84`, Pflicht),
`zone` (optional 1–60; sonst Standardzone aus der Länge ohne Sonderzonen
Norwegen/Spitzbergen). Antwort: `zone`, `nordhalbkugel`, `ellipsoid`,
`epsg` (258zz für ETRS89 Zonen 28–38 Nord, 326zz/327zz für WGS 84, sonst
`null`), `mittelmeridian`, `ost`, `nord`. `/utm/geographisch`: `ost`,
`nord`, `zone`, `nordhalbkugel`, `ellipsoid` → `{"punkt": {...}, "zone"}`.
Keine Datumstransformation. Die Oberfläche nutzt `/utm/geographisch` für
die UTM-Eingabe des Bezugspunkts („UTM-Koordinaten eingeben“: Zone 1–60,
Halbkugel, Ostwert über 0 und unter 1 000 000 m, Nordwert 0–10 000 000 m,
Ellipsoid aus der Auswahl); der Port-Eintrag `fromUtm` ist optional, ohne
ihn blendet die Karte die Eingabe aus. Nach jeder Umrechnung füllt die
Karte die Felder mit dem Rechts-/Hochwert des Bezugspunkts.

### `POST /vereinfachung`

Anfrage: `flaeche`, `toleranz` (≥ 0), `einheit` (`meter` oder `grad`),
`stellen` (optional 0–12, nur bei `grad`). `grad` rechnet wie die Quelle
osint in Koordinateneinheiten; `meter` projiziert jeden Ring in die
UTM-Zone des Flächenschwerpunkts (WGS 84), vereinfacht dort und rechnet
zurück. Antwort: `geometrie` (MultiPolygon oder `null`, wenn nichts übrig
bleibt), `stuetzpunkte_vorher`, `stuetzpunkte_nachher`, `entfallene_ringe`
(`polygon`, `ring`; ein entfallener Außenring nimmt seine Löcher mit),
`einheit`, `toleranz`, `utm_zone`.

### `POST /gpkg`, `GET /gpkg/quellen/{name}`

Die Datei wird im Speicher geöffnet (`sqlite3` `deserialize`, `query_only`,
`trusted_schema=OFF`, Fortschrittswächter gegen lange Abfragen). Gelesen
werden Tabellen aus `gpkg_geometry_columns` mit Flächentyp; Bezeichnung aus
der ersten passenden Textspalte (`name`, `bezeichnung`, `gebietsname`, `gen`,
`label`, `titel`, `title`, sonst erste Textspalte). Bezugssysteme: 4326 und
4258 direkt, ETRS89/UTM 25828–25838 und WGS 84/UTM 326xx/327xx werden
zurückgerechnet, alles andere ist ein Fehler (`profil_fehler`). Antwort:
`tabellen`, `tabelle`, `srs_id`, `umgerechnet`, `flaechen[]` (`id`,
`bezeichnung`, `geometrie` als MultiPolygon mit 7 Nachkommastellen,
`hinweise`), `fehler[]` (`id`, `meldung` – unlesbare Einzelgeometrien, nie
still verworfen), `abgeschnitten`; bei Serverquellen zusätzlich `quelle`.

### `POST /geocode`

Nur wenn der Server `Settings(geocoder=…)` setzt; sonst
404 `geocoder_abgeschaltet`. Anfrage `{"anfrage": "…"}` (≤ 300 Zeichen).
Antwort `{"treffer": [{"rang", "lat", "lon", "anzeigename"}],
"namensnennung": "…"}`. `NominatimGeocoder` (Extra `[geocoder]`) führt jede
Suche als Lauf des `HarvestEngine` mit Nominatim-Adapter aus: Takt ≥ 1 s,
höchstens 1 000 Anfragen je Tag am öffentlichen Dienst (429
`geocoder_grenze`), Zwischenspeicher je Anfragetext, ein Lauf zur Zeit;
Dienstfehler sind 502 `geocoder_fehler`, nie „kein Treffer“. Die Oberfläche
bietet die Suche zusätzlich nur mit `createGeoRestPort({ geocoding: true })`
an und sendet erst auf ausdrücklichen Klick (keine Autovervollständigung).

## Fehler

`{"error": {"code": "…", "message": "…"}}` mit deutscher Meldung:
400 `ungueltiges_json`, 404 `unbekannt`/`geocoder_abgeschaltet`,
413 `zu_gross`, 422 `ungueltige_eingabe`, `profil_fehler`,
`koordinaten_fehler`, `geometrie_fehler`, `kein_geopackage`,
`keine_flaechen`, 429 `geocoder_grenze`, 502 `geocoder_fehler`.

## Kacheln und Datenschutz

Die Komponente lädt Kacheln ausschließlich von der Anwendung übergebenen
Quelle (`tiles: { url, attribution, maxZoom?, subdomains? }`); ohne sie gibt
es keinen Kartenhintergrund und keine Anfrage an fremde Server. Die
Namensnennung wird unter der Karte und im Leaflet-Hinweis angezeigt (als
Text, nicht HTML). Punkte und Flächen gehen nur an den eigenen Server
(Port). Kartenbibliothek: Leaflet 1.9 (BSD-2-Clause), dynamisch geladen.
