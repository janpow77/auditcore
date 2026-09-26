# Paritätsinventur Geo-Karte

Stand 25.09.2026. Vorbilder: audit_designer (`main` @ `fce6b26f`: GIS-Arbeitsplatz
`frontend/src/components/gis/*`, `composables/useLeafletMap.ts`, Backend
`api/vpai_notebook/gis/*`, `core/shared/research/register/geocoding.py`), flowsearch
(`master` @ `10cb2a3`: `frontend/src/components/NaturaMap.vue`, `api/eu_beneficiaries.py:calculate_distance`,
`services/natura2000_service.py`), wohnungsmonitor (`main` @ `76571bf`: `index.html`,
`index-fr.html`, `frankreich_gebiet.py:entfernung`). Ziel: gemeinsame Komponente
`<flowaudit-geo-map>` in `@auditcore/ui` auf Basis von `auditcore_geo.web`
([Vertrag](geo-rest.md)). Alle drei Vorbilder nutzen Leaflet 1.9.

Legende: **übernommen** = gleiche Fachlogik über die Bibliothek; **ergänzt** = neu gegenüber
den Vorbildern; **abweichend** = bewusst anders (Begründung); **offen** = nicht umgesetzt.

| Funktion | Vorbild | Gemeinsame Komponente | Stand |
|---|---|---|---|
| Kartenbibliothek | alle: Leaflet 1.9.4 (audit_designer zusätzlich leaflet-draw, markercluster, heat, minimap, fullscreen) | Leaflet 1.9.4 (BSD-2-Clause), dynamisch geladen; keine Plugins | übernommen (Kern), Plugins offen |
| Kachelquelle | audit_designer: fest OSM, OSM.de, Esri, OpenTopoMap, CARTO, `/offline-tiles`; flowsearch: `localhost:8080`; wohnungsmonitor: `tile.openstreetmap.org` | nur über Eigenschaft `tiles` der Anwendung, Standard: keine | abweichend (kein fester Fremdserver, Datenschutz, OSMF-Kachelrichtlinie) |
| Namensnennung | Leaflet-Attribution je Grundkarte | Leaflet-Hinweis plus sichtbare Zeile unter der Karte, als Text | übernommen, ergänzt |
| Punkte anzeigen | wohnungsmonitor `circleMarker`, audit_designer Layer | `circleMarker` mit Tooltip, Treffer hervorgehoben | übernommen |
| Flächen anzeigen | audit_designer/flowsearch `L.geoJSON` (NUTS, Natura 2000) | GeoJSON Polygon/MultiPolygon, gewählte Fläche hervorgehoben | übernommen |
| WMS-Ebenen (BfN Schutzgebiete) | flowsearch `L.tileLayer.wms` (BfN) | – | offen (Anwendung kann Flächen per GeoPackage-Quelle liefern) |
| Umkreis auf der Karte | flowsearch/wohnungsmonitor `L.circle` | `L.circle` um den Bezugspunkt nach der Suche | übernommen |
| Umkreissuche | flowsearch `/natura2000/search?radius=` (Server, 6 371 000 m); wohnungsmonitor `entfernung` (6 371,0088 km); audit_designer register `_entfernung_km` (6 371 km) | `POST /umkreis` mit ausdrücklichem Erdmodell, Vorauswahl der Empfehlung D1 (R1) | übernommen; Erdmodell sichtbar statt fest |
| Ergebnisliste mit Entfernung | flowsearch (m, gerundet), wohnungsmonitor (km) | Tabelle unter 1 km in m, sonst km mit zwei Stellen, Treffer auf der Karte grün | übernommen |
| Punkt in Fläche | audit_designer `_point_in_geometry` (Strahl, Rand zufällig) | `POST /lage`: innen/außen/Rand, Randregel ausdrücklich (D2), Randtoleranz, Randfall-Hinweis | ergänzt (Rand erkannt) |
| Randabstand | audit_designer `_geometry_edge_distance_m`; company `_distance_to_geometry_m` (nächster Stützpunkt) | Kantenabstand der Bibliothek (`abstand_m`) | übernommen (Bibliotheksvertrag GEO-C11) |
| Zusammengefallene Ringe | audit_designer PR #382 (Workaround) | Hinweise GEO-C16 in der Ergebnisanzeige | übernommen |
| GeoPackage laden | audit_designer: Datei-Explorer erkennt `.gpkg`, Lesen im Backend (Fiona/GDAL) | `POST /gpkg` (Upload) und benannte Serverquellen; nur Polygone; stdlib `sqlite3` | übernommen (ohne GDAL); Punkte/Linien offen |
| Bezugssysteme GeoPackage | audit_designer: beliebig über GDAL/PROJ | 4326/4258 direkt, ETRS89- und WGS-84-UTM zurückgerechnet, sonst Fehler | abweichend (kein PROJ; unbekanntes SRS nie still) |
| UTM-Anzeige | audit_designer Statusleiste: nur Grad | Zone, Rechts-/Hochwert, EPSG für den Bezugspunkt, Ellipsoid wählbar | ergänzt |
| UTM-Eingabe | – | Bezugspunkt aus Zone, Halbkugel, Ost- und Nordwert über `POST /utm/geographisch` (Komma oder Punkt, Wertebereich je Feld geprüft); nur wenn der Port `fromUtm` anbietet | ergänzt |
| Douglas-Peucker | osint `bundeslaender_holen.py` (Skript, Grad) | `POST /vereinfachung`, Toleranzregler in Metern (über UTM) oder Grad, Vorher/Nachher-Zahl, Überlagerung gestrichelt | ergänzt (Oberfläche), Grad ergebnisgleich |
| Adresssuche | audit_designer `_geocode_address` (Nominatim direkt, immer an); flowsearch `geocoding_service`; wohnungsmonitor Offline-Koordinaten | nur serverseitig über `Geocoder` (`NominatimGeocoder` auf auditcore_harvest), abschaltbar (Standard aus), clientseitig nur mit `geocoding: true` | abweichend (Datenschutz, OSMF-Bedingungen, D5) |
| Koordinateneingabe | audit_designer Omnibar (Suche) | Breite/Länge mit Komma oder Punkt, Punkt aus Liste übernehmen | ergänzt (Tastaturbedienung) |
| Zeichnen/Messen | audit_designer leaflet-draw, Messwerkzeug (lokal geplanar) | – | offen |
| Clustering, Heatmap, Minikarte | audit_designer Plugins | – | offen |
| Klassifikation, Attributtabelle, Export | audit_designer GIS-Arbeitsplatz | – | offen (Anwendungsfunktion, nicht Kern) |
| Dunkelmodus | audit_designer CARTO dark | Token `--fa-*` für Objekte und Oberfläche; Kacheln bestimmt die Anwendung | übernommen (Oberfläche) |
| Unscharfe Anzeige von Koordinaten | wohnungsmonitor 50 m | – | offen (Sache der Anwendung vor Übergabe) |

Hinweis zur Kreisdarstellung: `L.circle` zeichnet mit Leaflets eigenem Erdradius;
maßgeblich für die Trefferliste ist allein die Berechnung der Bibliothek.

Bildschirmfotos (Demo mit synthetischen Koordinaten und Kacheln):
[Umkreis](screenshots/geo/geo-umkreis.png),
[Randfall](screenshots/geo/geo-randfall.png),
[Vereinfachung](screenshots/geo/geo-vereinfachung.png),
[GeoPackage](screenshots/geo/geo-geopackage.png),
[dunkel](screenshots/geo/geo-dunkel.png).
