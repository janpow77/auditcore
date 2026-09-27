# Spezifikation auditcore_geo

Stand: 26.09.2026, Paketversion 0.3.1. Charakterisierung: 290 aufgezeichnete
Fälle der Quellanwendungen (`tests/fixtures/legacy_observed.json`, Replay in
`tests/test_legacy_replay.py`), 168 Fälle zu zusammengefallenen Ringen
(`tests/test_entartete_ringe.py`), Vergleich mit shapely/pyproj in
`docs/behavior-changes.md`. Eigenschaftstests: `tests/test_spezifikation.py`.

## Zweck

Kleiner Geokern ohne Fremdabhängigkeiten für Prüfanwendungen: Entfernungen und
Umkreissuche auf der Kugel mit ausdrücklich gewähltem Erdmodell, Lage eines
Punktes zu Flächen (etwa Vorhabenstandort zu Schutzgebiet) mit erkanntem Rand,
Randabstand, Flächenschwerpunkt, UTM-Umrechnung, Lesen von
GeoPackage-Polygonen und Linienvereinfachung. Die Ergebnisse sind
deterministisch und fondsneutral; Referenzdaten (Gebiete, Verzeichnisse)
liefert die Anwendung.

## Verträge

| Bereich | Funktion/Klasse | Eingabe | Ausgabe | Nebenwirkungen |
|---|---|---|---|---|
| Koordinaten | `Punkt(lat, lon)`, `Punkt.aus_lonlat`, `Punkt.aus_latlon`, `Punkt.aus_folge` | Grad; Breite −90..90, Länge −180..180, endlich; Zahlenpaare nur mit genannter Achsenfolge | unveränderlicher Punkt | keine |
| Achsenfolge | `achsenfolge_erkennen(ringe, bereich)` | Ringe aus Zahlenpaaren, bekanntes Gebiet | `LON_LAT`, `LAT_LON` oder `UNBEKANNT` (kein Paar passt oder Widerspruch) | keine |
| Erdmodell | `Kugelprofil`, `KUGELPROFILE`, `kugelprofil(id)` | `kugel.r1_6371008_8m` (empfohlen, `EMPFOHLENES_ERDMODELL`) oder `kugel.6371000m` | Profil; kein stiller Standard | keine |
| Entfernung | `grosskreis_m`, `grosskreis_km` | zwei Punkte, Profil | Haversine-Entfernung, geklemmt | keine |
| Strecke | `abstand_zur_strecke_lokal_m` | Punkt, Strecke, Profil | Meter, lokale abstandstreue Näherung (Strecken bis wenige km) | keine |
| Umkreis | `umkreis(zentrum, punkte, radius_m, profil)` | Radius ≥ 0 oder `None` (alle) | `Treffer(index, abstand_m)`, Grenze eingeschlossen, sortiert nach (Abstand, Index) | keine |
| Flächen | `flaeche_aus_geojson`, `flaeche_aus_ringen`, `flaeche_aus_gpkg` (`strikt=`) | GeoJSON `Polygon`/`MultiPolygon` in (lon, lat); GeoPackage nur geographisch oder mit Umrechnung | `Flaeche` mit Teilflächen und zusammengefallenen Ringen (GEO-C16, `hinweise`) | keine |
| Lage | `lage(punkt, flaeche, rand_toleranz_m=0, profil=None)` | Randtoleranz in Metern verlangt ein Profil | `Lage.INNEN`/`AUSSEN`/`RAND` | keine |
| Enthaltensein | `enthaelt(flaeche, punkt, rand_gilt_als_innen=)` | Randregel ist Pflichtangabe (Empfehlung `EMPFOHLEN_RAND_GILT_ALS_INNEN = True`) | bool | keine |
| Abstände | `randabstand_m`, `randbefund`, `flaechen_im_umkreis`, `naechster_stuetzpunkt_m` | Punkt, Fläche(n), Profil | Kantenabstand (0 innen/auf dem Rand) bzw. getrennt benannter Stützpunktabstand | keine |
| Schwerpunkt | `flaechenschwerpunkt(flaeche)` | Fläche | flächengewichteter Schwerpunkt, Löcher abgezogen | keine |
| UTM | `UtmZone(zone, nordhalbkugel, ellipsoid)`, `geographisch_nach_utm`, `utm_nach_geographisch(_lonlat)`, `ETRS89_UTM32N` | Zonen 1–60, beide Halbkugeln, GRS80/WGS 84 | (Ost, Nord) in m bzw. Punkt; keine Datumstransformation | keine |
| GeoPackage | `lies_gpkg_polygone(blob)` | GeoPackage-Binärgeometrie, 2D-Polygon/MultiPolygon | `GpkgGeometrie` mit `srs_id` | keine |
| Vereinfachung | `douglas_peucker(punkte, toleranz)`, `ring_vereinfachen(ring, toleranz, stellen=)` | Toleranz in Koordinateneinheiten, endlich, ≥ 0 | Teilfolge bzw. geschlossener Ring oder `None` (< 4 Punkte) | keine |
| Adresssuche | `nominatim.NominatimAdapter`, `pruefe_laufparameter`, `empfohlene_laufparameter` (Extra `geocoder`) | Konfiguration mit User-Agent, Budget, Takt | Treffer mit Rang, ohne erfundene Konfidenz | Netz, nur über `auditcore_harvest` |
| REST | `auditcore_geo.web` (Extras `web`/`fastapi`), Vertrag `docs/ui/geo-rest.md` | JSON-Objekte mit Pfadangaben | JSON; Fehler `{"error": {"code", "message"}}` | keine außer Geocoder |

## Invarianten

| Nr. | Invariante | Test |
|---|---|---|
| I1 | `grosskreis_m` ist symmetrisch, nicht negativ, 0 für gleiche Punkte und höchstens π · Radius. | `test_i1_entfernung_symmetrisch_nichtnegativ_beschraenkt` |
| I2 | Die Großkreisentfernung erfüllt die Dreiecksungleichung (Rundungsspielraum 1 mm). | `test_i2_dreiecksungleichung` |
| I3 | `grosskreis_km` = `grosskreis_m` / 1000; zwei Profile unterscheiden sich nur um das Verhältnis ihrer Radien. | `test_i3_einheit_und_profil_skalieren_linear` |
| I4 | `umkreis` liefert genau die Punkte mit Entfernung ≤ Radius (kein Treffer geht durch den Vorfilter verloren, auch an Polen und Datumsgrenze), sortiert nach (Abstand, Index). | `test_i4_umkreis_vollstaendig_und_sortiert` |
| I5 | UTM-Rundlauf geographisch → UTM → geographisch innerhalb ±3° um den Mittelmeridian weicht höchstens 1 mm ab, in allen Zonen und auf beiden Halbkugeln; `ETRS89_UTM32N` rechnet auf GRS80. | `test_i5_utm_rundlauf_unter_einem_millimeter`, `test_i5_zone_32n_ist_grs80` |
| I6 | `douglas_peucker` liefert eine Teilfolge der Eingabe mit erstem und letztem Punkt; jeder weggelassene Punkt liegt höchstens `toleranz` von der Geraden durch die Endpunkte seines Abschnitts entfernt. | `test_i6_douglas_peucker_teilfolge_mit_endpunkten_und_toleranz` |
| I7 | `lage` ist dreiwertig und hängt nicht von Umlaufsinn oder Startpunkt des Rings ab; Punkte genau auf Kante oder Ecke sind `RAND`. | `test_i7_lage_dreiwertig_unabhaengig_von_umlaufsinn_und_start` |
| I8 | `enthaelt` folgt `lage` und der ausdrücklich übergebenen Randregel; `randabstand_m` ist 0 genau für Punkte innen oder auf dem Rand und sonst positiv. | `test_i8_randregel_ausdruecklich_und_randabstand_null_genau_bei_nicht_aussen` |
| I9 | Der Flächenschwerpunkt eines Rechtecks ist seine Mitte (flächengewichtet, nicht Stützpunktmittel). | `test_i9_schwerpunkt_rechteck_ist_mitte` |
| I10 | `aus_lonlat` und `aus_latlon` sind spiegelbildlich; nicht endliche oder außerhalb des Wertebereichs liegende Koordinaten werden mit `KoordinatenFehler` abgewiesen, nie geklemmt. | `test_i10_achsenfolge_benannt_ungueltiges_wird_abgewiesen` |

## Fehlerfälle

Alle Fehler sind Unterklassen von `GeoError` (`ValueError`) mit stabilem `code`:

- `KoordinatenFehler` (`koordinaten_fehler`): Koordinate keine Zahl, nicht
  endlich, außerhalb des Wertebereichs; Zahlenpaar zu kurz; Achsenfolge
  `UNBEKANNT` beim Bilden eines Punktes.
- `GeometrieFehler` (`geometrie_fehler`): nicht unterstützter Geometrietyp,
  fehlende Ringliste, leerer Ring, Positionen ohne Zahlen oder nicht endlich,
  mit `strikt=True` jeder zusammengefallene Ring; fehlerhafte
  GeoPackage-Blobs (Z/M-Geometrien, Leerflag, Restbytes, abgeschnittene Daten,
  unbekannte Hüllrechtecke); negative oder nicht endliche Toleranz; negative
  Randtoleranz. Eine unbrauchbare Geometrie ergibt nie einen Ersatzwert wie
  (0, 0) oder 0 m.
- `ProfilFehler` (`profil_fehler`): unbekanntes Kugelprofil, Radius nicht
  positiv/endlich, UTM-Zone außerhalb 1–60, UTM-Koordinate nicht endlich,
  Randtoleranz ohne Profil.
- `GeoError` direkt: Umkreisradius negativ oder nicht endlich.
- Zusammengefallene Ringe (Punkt, Linie) sind ohne `strikt` kein Fehler,
  sondern werden als `EntarteterRing` mit Hinweis geführt (GEO-C16).

## Abgrenzung

- Keine Datumstransformation (ETRS89 ↔ WGS 84), keine Ellipsoid-Geodäsie für
  Entfernungen; die Kugel-Näherung ist für Nähe- und Umkreisprüfungen gedacht.
- Keine Referenzdaten (Schutzgebiete, PLZ-, NUTS-Verzeichnisse) und keine
  Offline-Verortung; die Anwendung lädt und hält sie.
- Keine räumliche Datenbank (PostGIS-Abfragen bleiben in der Anwendung).
- Die Adresssuche fragt nur mit ausdrücklich übergebenem Geocoder; Takt,
  Tagesgrenze und Zwischenspeicher verantwortet die Anwendung im Rahmen von
  `pruefe_laufparameter`.
- Authentifizierung, CORS und Speicherung liegen beim Host der REST-Schicht.

## Bewusste Abweichungen vom Altverhalten

Einzelheiten und Nachweise: `docs/behavior-changes.md` (GEO-C01 bis GEO-C16).
Die Nachbildungen im Modul `auditcore_geo.legacy` reproduzieren das
aufgezeichnete Altverhalten exakt, einschließlich der Mängel; sie dienen
Umstellung und Nachweis und sind nicht für neue Aufrufer gedacht.

| Altverhalten | Gewolltes Verhalten | Legacy-Variante | Nachweis |
|---|---|---|---|
| Sechs Haversine-Varianten mit verschiedenen Radien, Einheiten und Achsenfolgen (GEO-C01) | zwei benannte Profile ohne Standardwert, benannte Achsen | `legacy.osint_haversine_km`, `legacy.designer_gis_haversine_m`, Profil `kugel.6371000m` | `test_legacy_replay.py`, I3 |
| Rechteckvorfilter verliert Treffer an Polen und Datumsgrenze (GEO-C02) | exakter Kugel-Vorfilter | `legacy.osint_umkreis` | I4 |
| Randpunkte je nach Kantenrichtung innen oder außen (GEO-C03) | `RAND` erkannt, Randregel ausdrücklich | `legacy.osint_im_ring` | I7, I8 |
| Multipolygon: weitere Teile als Löcher, Randabstand > 0 im zweiten Teil (GEO-C04/05) | je Teilfläche eigener Außenring | `legacy.designer_gis_punkt_in_geometrie`, `legacy.designer_gis_randabstand_m` | `test_legacy_replay.py`, `test_entartete_ringe.py`, I8 |
| Ungültige Geometrie → 0 m bzw. (0, 0) (GEO-C06) | `GeometrieFehler` | `legacy.designer_company_abstand_zur_geometrie_m`, `legacy.flowsearch_geometriezentrum` | `test_contract.py` |
| EWKB-Z als 2D gelesen, Restbytes ignoriert (GEO-C07) | nur 2D, sonst Fehler | `legacy.osint_wkb_polygone` | `test_contract.py` |
| Achsenfolge: erstes Paar entscheidet, sonst „nicht drehen“ (GEO-C08) | `UNBEKANNT` bei Widerspruch | `legacy.osint_achsen_drehen` | `test_contract.py` |
| Schwerpunkt als Stützpunktmittel, Abstand zum nächsten Stützpunkt (GEO-C09) | flächengewichtet; Kanten- und Stützpunktabstand getrennt benannt | `legacy.designer_gis_schwerpunkt` | I9 |
| Douglas-Peucker rekursiv, negative Toleranz behält alles (GEO-C13) | iterativ, Eingaben geprüft | `legacy.osint_douglas_peucker` | I6 |
| `utm_nach_wgs84` rechnet GRS80, nur Zone 32N (GEO-C14) | Zonen 1–60, beide Halbkugeln, Bezugssystem benannt | `legacy.osint_utm_nach_wgs84` | I5 |
| Zusammengefallene Ringe fielen still weg bzw. verwarfen die Fläche (GEO-C16) | als Objekt ohne Fläche geführt, mit Hinweis | – | `test_entartete_ringe.py` |
