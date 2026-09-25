# Changelog auditcore_funding_sources

## 0.1.2 – Englische Namen der designer-Parser

Keine fachliche Änderung: Die Replays gegen die aufgezeichneten Originalausgaben
von audit_designer laufen unverändert grün.

- `designer.parse_betrag` → `designer.parse_amount`,
  `designer.parse_satz` → `designer.parse_rate`,
  `designer.parse_datum` → `designer.parse_date`.
  Die Namen kollidieren nicht mit `workshop.parse_amount`/`workshop.parse_date`,
  weil beide Varianten in getrennten Modulen liegen.
- Die alten Namen bleiben als Aliase erreichbar (Attributzugriff und
  `from … import`); sie liefern dieselbe Funktion und geben eine
  `DeprecationWarning` aus. Möglich, seit die Architekturtests das Modul
  `warnings` ausschließlich für solche Aliase zulassen.
- Code-Gate: `non_english_identifiers` 1 → 0.

## 0.1.1 – Refaktorierung ohne Verhaltensänderung

Keine fachliche Änderung: alle 865 bestehenden Tests (Replays gegen die
aufgezeichneten Originalausgaben von flowworkshop, audit_designer und
flowsearch, Adapter-, Snapshot- und Architekturtests) laufen unverändert grün;
Profildaten und Fingerprints sind bytegleich.

- Betragsparser der Varianten flowworkshop, designer und state aid als
  explizite Grammatiken (`_parsing.AmountGrammar`) statt dreier kopierter
  Funktionen; die Unterschiede (Bereichswörter, Leer-Token, Punkt-Tausender)
  stehen als Daten nebeneinander. `detect_sa_reference` und die
  Rechtsform-Filterung existieren nur noch einmal.
- `workshop.py` geteilt: `workshop_state_aid.py` (Quelle `state_aid_service`);
  `deminimis.py` geteilt: `deminimis_inventory.py` (Satzkennung,
  Bestandsabgleich). Alle Namen bleiben über die bisherigen Module erreichbar.
- `cumulation.calculate`, `workshop.validate_rows` und der
  De-minimis-Adapter in kurze Schritte zerlegt; Harvest-Felder der
  flowworkshop-Zeile (`workshop.harvest_values`) und das Einlesen einer
  flowsearch-Datei (`flowsearch.read_items`) liegen beim Quellprofil statt im
  Adapter.
- Eingabeparameter von `Any` auf `object` bzw. `Mapping[str, object]`
  verengt, wo die Funktion jeden Wert annimmt.

| Messung | 0.1.0 | 0.1.1 |
|---|---|---|
| Funktionen mit McCabe > 10 | 5 | 0 |
| Module > 400 Zeilen | 3 | 0 |
| `Any`-Vorkommen | 115 | 75 |
| mypy --strict | sauber | sauber |

Keine Umbenennungen öffentlicher Namen. Die deutschen Quellsymbole des
designer-Profils (`parse_betrag`, `parse_satz`, `parse_datum`) bleiben
unverändert: Ein Alias mit `DeprecationWarning` bräuchte das Modul `warnings`,
das der Architekturtest des Pakets nicht zulässt.
