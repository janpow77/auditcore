# auditcore_common

Gemeinsame Hilfsfunktionen der auditcore-Fachpakete – **nur zusammengeführt,
wenn die Gleichheit mit jeder Paketkopie bewiesen ist**. Kern ohne
Laufzeitabhängigkeiten; `defusedxml` nur über das Extra `[xml]`, verzögert
importiert. Unterschiede zwischen den Paketkopien sind benannte Parameter,
nie stille Vereinheitlichung.

```python
from datetime import date

from auditcore_common.hashing import canonical_sha256
from auditcore_common.json_values import jsonable

assert canonical_sha256({"b": 1, "a": "ä"}) == canonical_sha256({"a": "ä", "b": 1})
assert jsonable({"am": date(2026, 9, 25)}) == {"am": "2026-09-25"}
```

| Modul | Inhalt | Varianten (Parameter) |
|---|---|---|
| `json_values` | `JsonValue`/`JsonObject`, `jsonable`, `decode_json` | `enums`, `dataclasses`, `sets` (dataprotection), `decimals`, `nan_as_none` (funding) |
| `hashing` | `canonical_json`, `canonical_sha256`, `sha256_text`, `sha256_file` | `compact=False` (documents-Profile), `ensure_ascii=True, default=str` (documents-Pipeline) |
| `profiles` | `packaged_profile_ids`, `packaged_profile_entries`, `recommended_profile_id`, `load_packaged_profile` | `require_text`, `invalid_name` = `missing`/`invalid`/`invalid_or_hidden` |
| `frozen` | `freeze`, `thaw` | – |
| `safe_xml` | `parse_xml`, `defused_fromstring` (Extra `xml`) | `forbid_dtd` |
| `html_text` | `LinkCollector`, `anchor_links`, `has_html_marker` | `markers`, `window` |
| `numeric` | `numpy_pairwise_sum`, `numpy_round`, `require_finite`, `parse_percent_rate`, `share_percent`, `as_float`, `as_float_comma` | Fehlermeldungen als Fabriken; `digits`, `multiply_first`; `blank_as_none`, `bool_as_none`, `catch_type_error` |
| `filenames` | `path_component`, `unicode_filename`, `replace_reserved`, `underscore_slug`, `dashed_slug`, `export_filename` | je Funktion eine charakterisierte App-Variante; Fallback und Länge als Parameter |
| `aio` | `ThreadLoopRunner`, `run_sync`, `run_on_current_loop` | ein Loop je Thread und Runner (fork-sicher) bzw. Legacy-Variante |
| `clock`, `ids` | `utc_now`, `require_aware`, `new_uuid` | – |
| `text` | `group_thousands_de`, `compact_upper` | – |
| `optional` | `require_module` – verzögerter Import eines Extras mit paketeigenem Fehler | – |

Fehler bleiben paketeigen: Die Funktionen nehmen die Fehlerklasse
(oder -fabrik) des aufrufenden Pakets entgegen, damit Typen und Meldungen
der charakterisierten Pakete unverändert bleiben.

**Gleichheitsnachweis.** `tests/legacy_reference.py` enthält die wörtlichen
Kopien aller zusammengeführten Funktionen (Quelle und Git-Blob in
`provenance.json`). Die Differenztests vergleichen alt gegen neu mit
seeded Zufallsstichproben (je Gruppe mehrere tausend Eingaben) und
Randfällen: Ergebnis einschließlich Typen, Float-Bitmuster und
Schlüsselreihenfolge oder Fehler einschließlich Typ, Meldung und Ursache.
`numpy_pairwise_sum`/`numpy_round` werden zusätzlich gegen NumPy selbst
geprüft, wenn NumPy installiert ist.

Die App-Hilfen (`share_percent`, `as_float`, `filenames`, `aio`) stammen aus der
Inventur `docs/reports/app-helfer-python.md` (Klasse b) und sind gegen die
wörtlichen App-Kopien in `tests/legacy_apps.py` differenziell geprüft
(Quellcommits in `provenance.json`, `sources`).

Neue Module kommen nur nach Thema hinzu (keine Sammeldatei `utils`); die
Auswahl steht in [docs/quality/duplikate.md](../../docs/quality/duplikate.md).
Debian-Paket: `python3-auditcore-common`.
