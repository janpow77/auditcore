# auditcore_geo 0.1.0 — Bericht

Stand: 23. September 2026. Branch `feat/auditcore-geo` (Worktree, Basis
`main@886a53a`). Grundlage: REPOSITORY_PACKAGE_COVERAGE.md H4 (letzter Absatz),
FUNCTIONS_OSINT_MAP.md, FUNCTIONS_DESIGNER_FLOWSTAT_MCP.md („Geocoding“).

## Entscheidung über das Paket

**Nutzerentscheidung 23.09.2026:** auditcore_geo wird gebaut, auch ohne bereits
umgestellten Consumer – „der mehrfache Nutzen kommt noch“. Consumer sind daher
**geplant**, nicht umgestellt. Unabhängig davon ist die Mechanik mehrfach
implementiert (inventarisiert, ausgeführt):

| Mechanik | Implementierungen |
|---|---|
| Haversine | osint `haversine_km`; audit_designer `_haversine_distance_m`, `_entfernung_km`, `_NaturaClient._haversine_m`; flowsearch `calculate_distance`, `Natura2000Service._calculate_distance` (sechs Varianten, zwei Radien, zwei Einheiten, zwei Achsenfolgen) |
| Punkt in Fläche / Randabstand | osint `_im_ring`; audit_designer `_point_in_geometry`, `_punkt_in_gebiet`, `_geometry_edge_distance_m`, `naechste_nuts3`, `_distance_to_geometry_m` |
| Nominatim | osint `vorhaben_verorten.abfragen`; flowworkshop `geocode_single`; audit_designer `_geocode_address` (+ `company_records`) |

Nicht aufgenommen (Begründung in `docs/behavior-changes.md`): Offline-PLZ/NUTS-
Verortung (datengebunden), flowworkshop `lookup_nuts`, PostGIS, WFS/Overpass,
Kartenoberflächen.

## Umfang

Distribution `auditcore_geo` (Debian `python3-auditcore-geo`), Laufzeit nur
Standardbibliothek; Extra `geocoder` = `auditcore_harvest==0.1.0`
(`python3-auditcore-harvest`). Keine Laufzeitabhängigkeit auf `auditcore`.

| Modul | Funktionen |
|---|---|
| `koordinaten` | `Punkt`, `Achsenfolge`, Bezugssysteme, `achsenfolge_erkennen` |
| `distanz` | Profile `kugel.r1_6371008_8m`, `kugel.6371000m`; `grosskreis_m/_km`, `umkreis`, `abstand_zur_strecke_lokal_m` |
| `flaeche` | `flaeche_aus_geojson`, `lage` (innen/außen/Rand), `enthaelt`, `randabstand_m`, `naechster_stuetzpunkt_m`, `flaechenschwerpunkt` |
| `projektion` | `UtmZone`, `utm_nach_geographisch(_lonlat)`, `geographisch_nach_utm` |
| `gpkg` | `lies_gpkg_polygone` (mit `srs_id`) |
| `vereinfachung` | `douglas_peucker`, `ring_vereinfachen` |
| `legacy` | exakte Nachbildungen aller charakterisierten Quellfunktionen |
| `nominatim` | `NominatimAdapter` (`geo.nominatim_search`), `pruefe_laufparameter`, `empfohlene_laufparameter` |

## Quellen und Rechte

GitHub-HEADs verifiziert (`gh api`): osint `d361ddb` (main), audit_designer
`1254591` (main), flowsearch `10cb2a3` (master), flowworkshop `3d1cb40` (main);
Blobs in `provenance.json`/`NOTICE`. Rechte: `USER_AUTHORIZED_MIT` (22.09.2026),
keine Umlizenzierung der Quellrepositories. Keine OSM- (ODbL) oder BKG-Daten
im Paket; Nominatim-Fixtures synthetisch. OSMF-Nutzungsbedingungen am
23.09.2026 gelesen und im Adapter umgesetzt.

## Characterization

`tools/capture_legacy.py` führt die Originale tatsächlich aus (Blob-Prüfung;
osint unverändert importiert, audit_designer/flowsearch per AST, flowworkshop
mit Stellvertretern): **290 Fälle** (Distanz 47, Umkreis 5, Punkt in Fläche 125,
Abstände 13, Schwerpunkte 8, Achsenfolge 6, UTM 29, WKB 15, Douglas-Peucker 30,
Nominatim-Anfragebildung 12). Zweimal ausgeführt, identisch. Referenzen
pyproj 3.8.0/PROJ 9.8.1 und shapely 2.1.2 nur zum Vergleich. Befunde
GEO-C01–C15, u. a.: Umkreis-Vorfilter verliert Treffer (995 km bei 60° N,
Datumsgrenze), MultiPolygon-Fehler in designer gis (Punkt in zweiter Teilfläche
277,99 m „außerhalb“), ungültige Geometrie → 0,0 m bzw. (0, 0), EWKB-Z still
falsch gelesen, erfundene Geocoder-Konfidenz, Netzfehler = kein Treffer.

## Tests und Gates (tatsächlich ausgeführt, Python 3.12.3)

| Prüfung | Ergebnis |
|---|---|
| Paket-pytest | **607 passed** (Vertrag 297, Legacy-Replay 279, Nominatim 26, Policy-Fälle 3, Architektur 2) |
| ruff / ruff format / mypy strict / bandit -ll | PASS |
| auditcore-quality strict (Framework `15f5338`) | Syntax, Lint, Typen, bandit, pip-audit, Tests, Supply Chain PASS; API-Baseline neu (NOT_EXECUTED beim ersten Lauf, Vergleich danach); Gesamt REVIEW_REQUIRED wegen Policy |
| Policy (verwaltung-app-framework@15f5338, frischer Klon) | F-07, F-09, F-15 VERIFIED (T-11, T-14, T-37, T-38, Profile); offen F-05, F-07.ASSESS, T-12 (Schutzbedarf/DSFA UNKNOWN) |
| Live-Smoke Nominatim | PASS, 2 Anfragen, Takt 1 s, nur Status/Anzahl/Hash aufgezeichnet |
| Plattform-pytest / ruff / mypy / CLI-Hilfen | 281 passed / PASS / PASS / PASS |
| `scripts/verify_domain_packages.py` harvest+geo `--apt` | alle 28 Schritte PASS: Build, SBOM, Hash-Requirements, `pip check`, Importherkunft, Smoke, selektive Installation (geo ohne harvest), Entfernung, Debian-Pakete, signierte APT-Quelle, Install/Upgrade 1→2/Remove im netzlosen Container |

Wheel `auditcore_geo-0.1.0-py3-none-any.whl` SHA-256
`2b74f9e7731a6d59f47cdc9bd9624cf359d60ac66c548e1cc74c6588ac76c3f6` (Erstfassung, reproduzierbar); nach Umsetzung der Entscheidungen `efeab5924e7598d55e783a7092b15608bab8eb4a4a2e570e0607908e84f973a0` (verify_domain_packages harvest+geo `--apt` erneut 28/28 PASS).

## Consumer (geplant)

Getestete Integrationsvariante osint `ortsdienst/dienst.py` (Wegwerf-Kopie,
isolierte venv nur mit dem Wheel): `tests/test_ortsdienst.py` 13/13 vorher und
nachher PASS; 60/60 identische Umkreisantworten auf 5 000 synthetischen
Vorhaben. Patch und Umstellungsanleitung für osint, audit_designer, flowsearch,
flowworkshop: `packages/auditcore_geo/docs/consumer-integration.md`.
Browser-Tests von osint (Playwright) NOT_EXECUTED. **MIGRATION_BLOCKED** bis
zum zentralen Release v0.3.0.

## Entscheidungen (DECIDED, 23.09.2026, vom Nutzer delegiert)

Die fünf zuvor offenen Fragen hat der Nutzer delegiert („entscheide du bitte“);
Umsetzung auf Branch `feat/auditcore-geo-entscheidungen`, Version bleibt 0.1.0:

1. **Erdradius (D1):** R1 = 6 371 008,8 m empfohlen für neue gemeinsame Bestände
   (`EMPFOHLENES_ERDMODELL`); 6 371 000 m bleibt für Replay/Altbestände; kein stiller Standard.
2. **Randpunkte (D2):** zählen als innen (`EMPFOHLEN_RAND_GILT_ALS_INNEN`); Parameter bleibt ausdrücklich.
3. **designer-Natura-Analyse (D3):** Umstellung auf korrekte Multipolygone (bewusste Korrektur GEO-C04/C05).
4. **company (D4):** Kantenabstand statt Stützpunktabstand (GEO-C09).
5. **Öffentliches Nominatim (D5):** ≤ 1 Anfrage/s, Zeitplanläufe 15 s, ≤ 1 000 Anfragen je Tag
   und Consumer, cachen; darüber eigene Instanz oder Import. Durchgesetzt in
   `validate_config`, `pruefe_laufparameter` und `empfohlene_laufparameter`
   (`heute_bereits_gesendet`, GEO-C15).

Merge des Erstpakets: PR #13 (`253aed9`); KIRA `6aae35b9-1c5c-45be-baa4-ff414da11dff`.

## 0.2.0: zusammengefallene Ringe (GEO-C16, Nutzerentscheidung „c3. ja“, 23.09.2026)

Anlass: Bei der Umstellung von audit_designer (PR janpow77/audit_designer#382)
verwarf `flaeche_aus_geojson` 0.1.0 jede Geometrie mit einem auf Punkt oder
Linie zusammengefallenen Ring als Ganzes – 10 von 1 051 hessischen
Natura-2000-Gebieten fielen still aus der Prüfung (15 enthalten solche Ringe).
0.1.0 ist in v0.3.0 veröffentlicht und bleibt unverändert; die Korrektur ist
Version **0.2.0** (Branch `feat/auditcore-geo-ringe`, Basis `main@6560370`).

Umfang: Zusammengefallene Außenringe bleiben als Punkt-/Linienobjekt mit
Abstand erhalten (`lage`/`enthaelt`, `randabstand_m`, neu `randbefund`,
`flaechen_im_umkreis`, `naechster_stuetzpunkt_m`, `flaechenschwerpunkt`),
zusammengefallene Löcher entfallen, gültige Teilflächen bleiben Fläche; jeder
Fall steht als `EntarteterRing` in `Flaeche.entartet` und als Hinweis in
`Flaeche.hinweise`. Neu `flaeche_aus_ringen` und `flaeche_aus_gpkg`
(projizierte GeoPackages nur mit ausdrücklicher Umrechnung); `strikt=True`
weist ab. Semantik des designer-Workarounds `geo_flaeche.py` (`82e1ca5`)
übernommen, Code nicht. Legacy-Replay unverändert.

| Prüfung (tatsächlich ausgeführt, Python 3.12.3) | Ergebnis |
|---|---|
| Characterization `tools/capture_entartet.py` | 12 Geometrien × 14 Punkte = 168 Fälle; designer gis/company, flowsearch, `auditcore_geo` 0.1.0 (Tag v0.3.0), Referenz shapely 2.1.2/pyproj 3.8.0 |
| Paket-pytest | **994 passed** (neu 387 in `test_entartete_ringe.py`; Vertrag 297, Legacy-Replay 279 unverändert, Nominatim 26, Policy 3, Architektur 2) |
| Lage gegen shapely / Abstand gegen EPSG:25832 | 168/168 gleich / ≤ 0,5 % |
| Abstand gegen designer gis (wo es Ringe ab drei Positionen behielt) | 9 Geometrien, rel. 1e-9 gleich |
| ruff / ruff format / mypy strict (`src`) / bandit -ll | PASS |
| `scripts/verify_domain_packages.py` harvest+geo `--apt` | **28/28 PASS** (Build, Hash-Requirements, `pip check`, Smoke inkl. GEO-C16, selektive Installation, Debian-Pakete, signierte APT-Quelle, Install/Upgrade 1→2/Remove) |

Wheel `auditcore_geo-0.2.0-py3-none-any.whl` SHA-256
`6a460f39bb1a41ce3c547a6c09eb23ea5a9b43348e3cdd8baad1e058e12d4ee5`
(reproduzierbar, `SOURCE_DATE_EPOCH=1700000000`); harvest unverändert
`bc6cf59f…` (= Release v0.3.0).

Consumer audit_designer (`main@7226382`, Wegwerf-Kopie, isolierte venv, keine
Datenbank, kein Push): `test_geo_auditcore.py` + `test_vpai_gis_helpers.py`
53 passed mit 0.1.0, mit 0.2.0 und nach Umstellung ohne `geo_flaeche.py`.
Vergleich Workaround/Umstellung auf 168 Fällen: Abstände identisch; bewusst
anders nur Punkte genau auf einem zusammengefallenen Außenring (jetzt Rand =
innen nach D2) und der Schwerpunkt reiner Punkt-/Liniengebiete (wie shapely).
Anleitung und Patch: `packages/auditcore_geo/docs/consumer-integration.md`.
`test_flowstat_geo_handler.py` (PostgreSQL) NOT_EXECUTED. Requirements-Umstellung
im designer auf `auditcore_geo==0.2.0` erst nach einem Release, das 0.2.0 enthält.
