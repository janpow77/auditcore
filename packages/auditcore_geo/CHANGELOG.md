# Changelog – auditcore_geo

## 0.2.1 – Refaktorierung ohne Verhaltensänderung

- `flaeche` nach Verantwortung geschnitten: Flächenmodell und Leser
  (Ringe, Polygone, zusammengefallene Ringe, `flaeche_aus_*`) liegen in
  `_flaechenmodell`; `flaeche` enthält Lage, Abstände und Schwerpunkt und
  gibt alle bisherigen Namen weiter aus.
- `legacy` nach Quellen geschnitten (`_legacy_osint`, `_legacy_designer`,
  `_legacy_flowsearch`); alle Namen bleiben unter `auditcore_geo.legacy`.
- `nominatim`: Konfigurationsprüfung in kurze Einzelprüfungen zerlegt
  (Reihenfolge und Meldungen unverändert), neue öffentliche Funktion
  `pruefe_konfiguration`; Bedingungen, Anfragemodell und Trefferdaten ohne
  Harvest-Import in `_nominatim_daten` (der Architekturtest „nur
  `nominatim` importiert `auditcore_harvest`“ gilt weiter).
- `lies_gpkg_polygone`: Kopfprüfung und MultiPolygon-Leser als Hilfen.
- Typen: Geometrie-Eingaben als `object` mit `TypeGuard`-Prüfungen statt
  `Any`; `Any` bleibt an Roh-GeoJSON-Grenzen der Legacy-Nachbildungen und
  am Harvest-Cursor.
- Keine Umbenennung öffentlicher Namen, keine Aliase nötig.

| Messung | 0.2.0 | 0.2.1 |
|---|---|---|
| Funktionen mit McCabe > 10 | 2 | 0 |
| Module > 400 Zeilen | 2 | 0 |
| `Any`-Vorkommen | 30 | 15 |
| mypy --strict | sauber | sauber |
| Tests / Abdeckung | 994 / 97,6 % | 1020 / 98,6 % |
