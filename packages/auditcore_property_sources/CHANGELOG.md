# Changelog auditcore_property_sources

Aus der Git-Historie rekonstruiert (`git log -- packages/auditcore_property_sources`).

## 0.1.2 – 2026-09-25

Verhaltensänderung (PS-C10, Nutzerauftrag vom 25.09.2026).

### Behoben
- `zvg.parse_de_number` liest deutsche Zahlen nach dem gemeinsamen Vertrag
  `contracts/common-cases/parse-number` (Modus `de`) über
  `auditcore_common.numbers_de`: „1234,56“ → 1234,56 (bisher 123,0),
  „2015“ → 2015,0 (bisher 201,0). Mehrdeutiges („1.234“, „1.5“, „1,234“) und
  Text um die Zahl ergeben `None` statt einer geratenen Zahl. Damit stimmen
  auch die Wohnflächen aus `parse_detail` („Wohnfläche 1234,56 m²“).

### Hinzugefügt
- `zvg.legacy_parse_de_number`: das charakterisierte Original, unverändert
  (Replay und Paritätsnachweise der Consumer).
- Pflichtabhängigkeit `auditcore_common==0.1.1`.

## 0.1.1 – 2026-09-25

Refaktorierung ohne Verhaltensänderung; Datensätze, Issues, Cursor,
robots.txt-Entscheidungen und Fehlertexte unverändert. Extra `sources`
benötigt `auditcore_harvest==0.1.1`.

### Geändert (intern)
- `adapters` ist ein Unterpaket: `_harvest` (einziger Importort von
  `auditcore_harvest`), `_base` (gemeinsame Portal-Hilfen), `berlin`, `france`,
  `zvg`. Alle bisherigen Namen bleiben aus `auditcore_property_sources.adapters`
  importierbar (Strukturtest).
- `zvg.py` in `_zvg_text` (Text/Zahlen) und `_zvg_address` (Adressen) sowie kurze
  Detailschritte geschnitten; öffentliche Namen weiter aus `zvg` importierbar.
- `parse_robots` über eine Gruppenhilfe; `normalise` von bienici, paruvendu und
  inberlinwohnen sowie `ZvgListingAdapter.fetch_page` in Teilschritte zerlegt
  (Auswertungsreihenfolge unverändert).
- `Any` nur noch im dokumentierten Alias `_types.JSON` für Portal-JSON; die
  Parser bleiben ohne Abhängigkeit von `auditcore_harvest`.

### Messung (Code-Qualitäts-Gate)
| Kennzahl | 0.1.0 | 0.1.1 |
|---|---|---|
| McCabe > 10 | 4 | 0 |
| Funktionen > 60 Zeilen | 5 | 0 |
| Module > 400 Zeilen | 2 | 0 |
| `Any`-Verwendungen | 66 | 1 |
| mypy --strict | 0 | 0 |

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
