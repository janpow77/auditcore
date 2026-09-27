# Changelog auditcore_common

## Unreleased

- `rest.decode_body` nimmt `too_large_code` und `invalid_json_code` (Vorgabe
  `too_large`/`invalid_json`, bisheriges Verhalten unverändert), damit
  Verträge mit eigenen Fehlercodes (geo: `zu_gross`/`ungueltiges_json`) die
  Funktion nutzen können.
- Duplikatgruppe A16 abgeschlossen: `rest.json_object` ersetzt jetzt auch
  sampling `web._validate.as_object`, geo `web._contract.Body.of` und
  extrapolation `web._contract.Reader`; dazu geo `web._http.Reply`, `_json`
  und `decode`. Differenztests gegen die wörtlichen Kopien
  (`tests/legacy_rest.py`, `tests/test_rest.py`).

## 0.2.0 – 2026-09-26 – Paketstand für Release v0.4.2

- Neues Modul `rest`: rahmenwerkfreier Teil der JSON-REST-Verträge von
  `auditcore_sampling` und `auditcore_statistics` (Duplikatgruppe B1) –
  `ContractError` (Status, Code, `to_dict`), `Reply`, `json_reply`,
  `decode_body` (Größengrenze 413 `too_large`, 400 `invalid_json`,
  `parse_float`), `guarded` (Vertragsfehler → JSON-Antwort), `choice` und
  `bounded_list` mit paketeigener Fehlerklasse (`error`). Meldungen und
  Statuscodes unverändert; Differenztests gegen die wörtlichen Kopien
  (`tests/legacy_rest.py`, `tests/test_rest.py`).
- `rest.json_object(value, path, *, error=...)`: JSON-Objekt mit Text-Schlüsseln
  oder `422` „'<path>' muss ein JSON-Objekt sein.“ – ersetzt die wörtlich
  gleichen `_object`-Prüfungen in `auditcore_identifiers.web` und
  `auditcore_reporting.web` (Differenztest gegen beide Kopien in
  `tests/legacy_rest.py`, `tests/test_rest.py`).
- Eigenschaftstests mit Hypothesis (`tests/test_properties.py`, Extra `dev`):
  paarweise Summe, `numpy_round`, `require_finite`, `canonical_sha256`,
  `decode_body` und `choice` gegen die früheren Kopien aus sampling,
  statistics und market_indicators.

## 0.1.1 – Deutsche Zahleneingabe nach dem gemeinsamen Vertrag

- Neues Modul `numbers_de`: `parse_number(text, mode)`, `parse_de_number(text)`
  und `parse_number_result(text, mode)` (Ergebnis `ParsedNumber` mit Wert oder
  Hinweis `leer`/`mehrdeutig`/`ungültig`, `message` als deutscher Text).
  Umsetzung des Vertrags `contracts/common-cases/parse-number.json` (Modi
  `de`, `en`, `auto`) mit den Festlegungen des Nutzers vom 25.09.2026:
  „1.5“ und „1.234“ sind in Beträgen mehrdeutig und werden mit Hinweis
  abgelehnt, höchstens zwei Nachkommastellen (`max_fraction_digits`, `None`
  hebt die Grenze für Mengen und Sätze auf). Im Modus `auto` gilt ein
  einzelner Trenner vor genau drei Ziffern nur dann als mehrdeutig, wenn der
  ganzzahlige Teil eine gültige Tausendergruppe sein kann (`"0.345"` und
  `"1234.567"` sind eindeutig).
- Alle Python-Fälle des Vertrags laufen als Tests (`tests/test_numbers_de.py`).
- Pins `auditcore_common==0.1.1` in den abhängigen Paketen.

## 0.1.0 – Erstausgabe

**Nachtrag vor der ersten Veröffentlichung** (0.1.0 war noch in keinem Release;
die exakten Pins der migrierten Pakete bleiben dadurch gültig): generische
App-Hilfen aus `docs/reports/app-helfer-python.md`, je gegen die wörtlichen
App-Kopien geprüft (`tests/legacy_apps.py`):

- `numeric.share_percent` (audit_designer, flowinvoice, riskanalysis,
  regulierung; Varianten `digits`, `multiply_first`), `numeric.as_float`
  (audit_designer ×3, audit-portal, flowinvoice, regulierung, versteigerung ×2;
  Varianten `blank_as_none`, `catch_type_error`, `bool_as_none`),
  `numeric.as_float_comma` (audit_designer beneficiaries).
- `filenames`: sechs benannte Varianten (audit_designer ×3, audit-portal ×2,
  regulierung).
- `aio.ThreadLoopRunner`/`run_sync` (flowinvoice, fork-sicher, ein Loop je
  Thread und Runner) und `run_on_current_loop` (audit_designer, flowaudit).

Erstausgabe:

Zusammenführung der doppelten Hilfsfunktionen der auditcore-Fachpakete nach
der AST-Inventur `docs/quality/duplikate.md` (Stand main 40ce8f7):

- `json_values`: `jsonable` (risk `plain`, dataprotection `plain`, funding
  `json_safe` als benannte Varianten), `decode_json` (legal/registry `_json`),
  `JsonValue`/`JsonObject` (bisher registry `_types`).
- `hashing`: `canonical_sha256` (Profil-Fingerprints in neun Paketen,
  dataprotection `canonical_sha256`, harvest `canonical_hash`), Varianten der
  documents-Profile und der documents-Pipeline, `sha256_text`, `sha256_file`
  (vier Kopien in documents/invoicesynth).
- `profiles`: Auflisten, Empfehlen und explizites Laden paketierter Profile
  (sieben Lader mit drei Namensprüfungen und optionaler Typprüfung).
- `frozen`: `freeze`/`thaw` (documents, registry, risk).
- `safe_xml`: `defusedxml`-Laden (registry zweimal, reporting).
- `html_text`: Linksammler (legal) und HTML-Erkennung (property dreimal, legal).
- `numeric`: `numpy_pairwise_sum` (statistics, sampling, market),
  `numpy_round` (statistics, sampling), `require_finite` (geo, market),
  `parse_percent_rate` (documents, invoicesynth).
- `clock`, `ids`, `text`, `optional`.

Nachweis: 135 Tests, davon Differenztests je Gruppe gegen die wörtlichen
Paketkopien; Code-Gate-Baseline 0 in allen Metriken.
