# Changelog auditcore_geo

Rekonstruiert aus der Git-Historie (Pull Requests #13, #16, #38, #73).

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
