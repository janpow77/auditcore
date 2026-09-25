# Changelog @flowaudit/ui

## 0.1.0 – 2026-09-25

Erste Fassung.

- Gerüst (PR #80): Vue-3-Bibliothek mit Web-Component-Einstieg
  `@flowaudit/ui/elements` (Namen `flowaudit-<name>`, Light DOM),
  Designtoken `--fa-*` mit Hell-/Dunkelmodus, i18n (Deutsch vollständig,
  Englisch vorbereitet, Formatierer), Basiskomponenten `FaButton`, `FaIcon`,
  `FaDialog`, `FaTable` (`<flowaudit-table>`), `FaBadge`, `FaTextField`,
  REST-Hilfen `requestJson`, `requestFile`, `createRunner`, `saveFile`,
  Demo-App mit Playwright-Prüfung.
- Kanban (PR #84): `KanbanBoard`, `KanbanBoardList`, Karten, Spalten,
  Detailansicht, Einstellungen, Teilen; Web Components
  `<flowaudit-kanban-board>` und `<flowaudit-kanban-boards>`; Ziehen per
  Pointer Events, Tastaturbedienung mit Ansagen, optimistische Änderungen mit
  Rücknahme.
- Geo-Karte: `FaGeoMap` (`<flowaudit-geo-map>`) mit REST-Port
  `createGeoRestPort` auf `auditcore_geo.web` (docs/ui/geo-rest.md):
  Punkte und Flächen auf Leaflet 1.9 (BSD-2-Clause, dynamisch geladen),
  Kachelquelle nur über `tiles` samt Namensnennung (kein fester
  Kachelserver), Bezugspunkt per Klick, Koordinateneingabe oder Punktliste,
  UTM-Anzeige, Umkreissuche mit ausdrücklichem Erdmodell und
  Entfernungsliste, Punkt in Fläche mit Randregel (D2), Randtoleranz und
  Randfall-Anzeige, Douglas-Peucker mit Toleranzregler (Meter/Grad),
  GeoPackage per Datei-Upload oder Serverquelle, Adresssuche nur mit
  `geocoding: true` und aktivem Server-Geocoder. REST-Hilfe `requestUpload`.
