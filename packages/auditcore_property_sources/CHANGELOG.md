# Changelog auditcore_property_sources

Aus der Git-Historie rekonstruiert (`git log -- packages/auditcore_property_sources`).

## 0.1.0 – 2026-09-23

Erste Fassung (#20): getrennte Quellprofile für Immobiliendaten aus
`janpow77/wohnungsmonitor@76571bf` (immobilien.de, inberlinwohnen,
Kleinanzeigen, bien'ici, Citya, ParuVendu) und `janpow77/versteigerung@e4ad7af`
(ZVG-Portal), 238 aufgezeichnete Originalfälle.

- Parser je Portal nur mit der Standardbibliothek, keine Vereinheitlichung der
  Preissemantik; ZVG-Parser und reiner Lebenszyklus (`zvg_lifecycle`).
- Harvest-Adapter im Extra `sources` (Contract-Suite von `auditcore_harvest`
  bestanden), Zugangskatalog `catalog()` mit robots.txt-Befund,
  Nutzungsbedingungen und Live-Status.
- Korrekturen PS-C01 bis PS-C08 (`docs/behavior-changes.md`).

### Nachträge ohne Versionsänderung

- 2026-09-23 (#34): Nutzerentscheidungen PS-D01 bis PS-D03 – Einstellung
  `robots_policy` (Standard `"ignore"`, `"respect"` wählbar), bien'ici sendet
  die Kopfzeilen des Originals, `advertiser_names="legacy"` als Standard;
  PS-C09: `ZvgDetailAdapter` baut wie das Original zuerst eine Sitzung auf.
  Live-Smoke für Kleinanzeigen und ZVG.
- 2026-09-25 (#73): Extra `sources` verlangt `auditcore_harvest==0.1.1`. Das im
  Release v0.3.0 veröffentlichte Wheel 0.1.0 verlangt noch
  `auditcore_harvest==0.1.0`.
