# Changelog auditcore_common

## 0.1.0 – Erstausgabe

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
