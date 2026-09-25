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
