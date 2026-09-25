# Changelog

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
