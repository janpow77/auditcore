# Changelog auditcore_geo

Rekonstruiert aus der Git-Historie (Pull Requests #13, #16, #38, #54, #73).

## Unreleased

Keine Verhaltensänderung. Die Endlichkeitsprüfung der Koordinaten nutzt
`auditcore_common.numeric.require_finite`; Fehlerklasse `KoordinatenFehler`
und Meldungen unverändert (`tests/test_common_parity.py`). Neue
Pflichtabhängigkeit `auditcore_common==0.1.1` (APT `python3-auditcore-common`,
nur Standardbibliothek).

## 0.3.0 – 2026-09-25 – REST-Vertrag für Geo-Oberflächen

- Neues Unterpaket `auditcore_geo.web` (Extras `web`, `fastapi`): Katalog
  (`GET /profile`), Umkreis, Lage mit Randregel und Toleranz, UTM hin und
  zurück, Douglas-Peucker in Metern (über UTM) oder Grad, GeoPackage-Dateien
  als SQLite lesen (Upload oder benannte Serverquelle; EPSG:4326/4258,
  ETRS89- und WGS-84-UTM-Zonen), Adresssuche nur mit angeschlossenem
  `Geocoder` (`NominatimGeocoder` auf `auditcore_harvest`). Starlette-Routen
  und FastAPI-Router mit byteidentischen Antworten.
- Bestehende Module unverändert (nur Versionskennung).

## 0.2.1 – 2026-09-25 – Refaktorierung ohne Verhaltensänderung

- `flaeche` nach Verantwortung geschnitten: Flächenmodell und Leser
  (Ringe, Polygone, zusammengefallene Ringe, `flaeche_aus_*`) liegen in
  `_flaechenmodell`; `flaeche` enthält Lage, Abstände und Schwerpunkt und
  gibt alle bisherigen Namen weiter aus.
- `legacy` nach Quellen geschnitten (`_legacy_osint`, `_legacy_designer`,
  `_legacy_flowsearch`); alle Namen bleiben unter `auditcore_geo.legacy`.
- `nominatim`: Konfigurationsprüfung in kurze Einzelprüfungen zerlegt
  (Reihenfolge und Meldungen unverändert), neue öffentliche Funktion
  `check_config`; Bedingungen, Anfragemodell und Trefferdaten ohne
  Harvest-Import in `_nominatim_daten` (der Architekturtest „nur
  `nominatim` importiert `auditcore_harvest`“ gilt weiter).
- `lies_gpkg_polygone`: Kopfprüfung und MultiPolygon-Leser als Hilfen.
- Typen: Geometrie-Eingaben als `object` mit `TypeGuard`-Prüfungen statt
  `Any`; `Any` bleibt an Roh-GeoJSON-Grenzen der Legacy-Nachbildungen und
  am Harvest-Cursor.
- Keine Umbenennung öffentlicher Namen, keine Aliase nötig. Die öffentliche
  API bleibt bewusst deutsch (Entscheidungen D1–D6); neu hinzugekommene
  interne Hilfen und `check_config` tragen englische Bezeichner.

Messung mit `auditcore-codegate check --package auditcore_geo`:

| Messung | 0.2.0 | 0.2.1 |
|---|---|---|
| Funktionen mit McCabe > 10 | 2 | 0 |
| Funktionen > 60 Zeilen | 0 | 0 |
| Module > 400 Zeilen | 2 | 0 |
| `Any`-Verwendungen | 27 | 12 |
| nicht-englische Bezeichner | 20 | 20 (öffentliche deutsche API) |
| mypy --strict | sauber | sauber |
| Tests / Abdeckung | 994 / 97,6 % | 1020 / 98,6 % |

## 0.2.0 – 2026-09-23

- Zu Punkt oder Linie zusammengefallene Ringe verwerfen die Fläche nicht mehr
  (GEO-C16, Entscheidung D6): zusammengefallene Außenringe bleiben als Objekt
  ohne Fläche mit Abstand (`lage`/`enthaelt`, `randabstand_m`, `randbefund`,
  `flaechen_im_umkreis`, `naechster_stuetzpunkt_m`), zusammengefallene Löcher
  entfallen, echte Teilflächen bleiben Fläche. Jeder Fall steht als
  `EntarteterRing` in `Flaeche.entartet` und in `Flaeche.hinweise`;
  `strikt=True` weist ab.
- Neu: `flaeche_aus_ringen`, `flaeche_aus_gpkg` (projizierte Daten nur mit
  Umrechnung).
- Charakterisierung gegen designer gis/company, flowsearch, auditcore_geo 0.1.0
  und shapely/pyproj (`tools/capture_entartet.py`, 12 Geometrien × 14 Punkte).
- 0.1.0 (Release v0.3.0) bleibt unverändert.
- 2026-09-25: Pin des Extras `[geocoder]` auf `auditcore_harvest==0.1.1`
  angehoben (#73), ohne Versionsänderung dieses Pakets.

## 0.1.0 – 2026-09-23

- Charakterisierter Geokern (nur Standardbibliothek): Erdmodell-Profile,
  Großkreisentfernung, Umkreissuche mit exaktem Vorfilter, Punkt in Fläche
  mit Rand, Randabstand, Schwerpunkt, UTM ↔ geographisch, GeoPackage-Polygone,
  iteratives Douglas-Peucker, Legacy-Nachbildungen (`legacy`) und
  Nominatim-Adapter auf `auditcore_harvest` im Extra `[geocoder]` (#13).
- 290 an den Originalen ausgeführte Fälle aus osint, audit_designer,
  flowsearch und flowworkshop; Verhaltensänderungen GEO-C01–C14.
- Entscheidungen D1–D5 umgesetzt (#16): `EMPFOHLENES_ERDMODELL`,
  `EMPFOHLEN_RAND_GILT_ALS_INNEN`, öffentliches Nominatim höchstens 1 000
  Anfragen je Tag und Consumer (GEO-C15).
