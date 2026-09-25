# auditcore_common

## Zweck

Gemeinsame Hilfsfunktionen der auditcore-Fachpakete und Anwendungen (JSON, Hashing, Profile, sicheres XML, HTML-Links, Numerik, Dateinamen, Event-Loop), nur zusammengeführt, wenn die Gleichheit mit jeder Paketkopie bewiesen ist.

Für die Fachpakete dieses Repositorys und – mit den App-Hilfen – für die
Anwendungen, aus denen die Kopien stammen; keine allgemeine Werkzeugkiste. Unterschiede zwischen den früheren Paketkopien sind benannte
Parameter, nie stille Vereinheitlichung; Fehler bleiben paketeigen. Neue
Module kommen nur nach Thema hinzu (keine Sammeldatei `utils`).

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install auditcore_common \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Version 0.1.0 ist noch nicht veröffentlicht; nach dem nächsten Release steht
sie mit Direkt-URL und Hash unter
`https://janpow77.github.io/auditcore/simple/auditcore-common/`. Muster für eine
hashgebundene `requirements.txt`:

```text
auditcore_common @ https://github.com/janpow77/auditcore/releases/download/v<release>/auditcore_common-0.1.0-py3-none-any.whl#sha256=<sha256 aus dem Index>
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-common
```

Extras: `[xml]` – `defusedxml` für `safe_xml` (verzögert importiert);
`[dev]` – Test- und Prüfwerkzeuge.

## Schnellstart

```python
from datetime import date

from auditcore_common.hashing import canonical_sha256
from auditcore_common.json_values import jsonable
from auditcore_common.text import group_thousands_de

# Schlüsselreihenfolge ändert den kanonischen Hash nicht.
assert canonical_sha256({"b": 1, "a": "ä"}) == canonical_sha256({"a": "ä", "b": 1})
assert jsonable({"am": date(2026, 9, 25)}) == {"am": "2026-09-25"}
```

```pycon
>>> group_thousands_de(1234567)
'1.234.567'
```

## API-Überblick

Der Paketstamm exportiert nur `__version__`; eingebunden wird je Thema über
das Modul:

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

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_common.__all__` (1):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `__version__` | Wert | – | `(Paketstamm)` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_common.aio` | Run coroutines from synchronous code (Celery tasks, thread pools). |
| `auditcore_common.clock` | Timezone-aware time. |
| `auditcore_common.filenames` | File names for downloads and exports; each function is one characterized variant. |
| `auditcore_common.frozen` | Read-only copies of JSON data and their mutable counterparts. |
| `auditcore_common.hashing` | Canonical JSON and SHA-256 digests. |
| `auditcore_common.html_text` | Anchor links of HTML pages and HTML marker detection (standard library only). |
| `auditcore_common.ids` | Random identifiers. |
| `auditcore_common.json_values` | JSON value types and conversions to JSON-compatible values. |
| `auditcore_common.numeric` | Floating-point helpers with documented, NumPy-compatible results without NumPy. |
| `auditcore_common.optional` | Lazy import of optional extras with the caller's own error type and message. |
| `auditcore_common.profiles` | Packaged, versioned JSON profiles: list, recommend and load them explicitly. |
| `auditcore_common.safe_xml` | XML parsing only through ``defusedxml`` (extra ``xml``), imported lazily. |
| `auditcore_common.text` | Small text normalisations shared by several packages. |
<!-- api-overview:end -->

## Profile und Konfiguration

Keine eigenen Profile oder Einstellungen. `profiles` ist der gemeinsame Lader
für die paketierten, versionierten JSON-Profile der Fachpakete; welche
Variante (Parameter) ein Paket braucht, steht in
[docs/quality/duplikate.md](../../docs/quality/duplikate.md) (Tabelle A).
Anbindung eines Fachpakets (Pin, Architekturtest, paketeigene Fehler,
Deprecation-Aliase): [docs/consumer-integration.md](docs/consumer-integration.md).

## Herkunft und Charakterisierung

Konsolidierung innerhalb von auditcore (Stand `40ce8f71`) sowie App-Hilfen aus
den Anwendungsrepositories (siehe unten). Auswahl per AST-Inventur
(`scripts/inventory_duplicate_functions.py`, `docs/quality/duplikate.md`).
`tests/legacy_reference.py` enthält die wörtlichen Kopien aller
zusammengeführten Funktionen, Quelle und Git-Blob stehen in
`provenance.json`. Die Differenztests vergleichen alt gegen neu mit seeded
Zufallsstichproben (je Gruppe mehrere tausend Eingaben) und Randfällen:
Ergebnis einschließlich Typen, Float-Bitmuster und Schlüsselreihenfolge oder
Fehler einschließlich Typ, Meldung und Ursache. `numpy_pairwise_sum` und
`numpy_round` werden zusätzlich gegen NumPy geprüft, wenn es installiert ist.

Die App-Hilfen (`share_percent`, `as_float`, `as_float_comma`, `filenames`,
`aio`) stammen aus der Inventur `docs/reports/app-helfer-python.md` (Klasse b:
audit_designer, audit-portal, flowinvoice, riskanalysis, regulierung,
versteigerung, flowaudit) und sind gegen die wörtlichen App-Kopien in
`tests/legacy_apps.py` differenziell geprüft (Quellcommits in
`provenance.json`, `sources`).

## Bewusste Verhaltensabweichungen

Keine. Jede Funktion verhält sich wie die jeweilige Paketkopie; wo sich die
Kopien unterschieden, wählt der Aufrufer die Variante über einen benannten
Parameter.

## Abhängigkeiten

Python ≥ 3.11, zur Laufzeit nur die Standardbibliothek. Optional
`defusedxml>=0.7.1` über `[xml]`. Keine Abhängigkeit von der Plattform
`auditcore` oder anderen Fachpaketen; umgekehrt pinnen Fachpakete
`auditcore_common` exakt (z. B. `auditcore_procurement`).

## Sicherheit und Datenschutz

Kein Netzwerk, keine Speicherung. XML wird ausschließlich über `defusedxml`
gelesen (`safe_xml`, optional `forbid_dtd`); fehlt das Extra, meldet
`require_module` den Fehler des aufrufenden Pakets. `sha256_file` liest die
übergebene Datei nur lesend.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Freigabe des Rechteinhabers vom 22.09.2026 für die
Bibliotheken in auditcore (`USER_AUTHORIZED_MIT`). Zusammengeführte Dateien
mit Git-Blobs: `provenance.json`; Zuschreibung: `NOTICE`.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
