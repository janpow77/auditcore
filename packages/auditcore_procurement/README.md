# auditcore_procurement

## Zweck

Vergabebekanntmachungen (TED, HAD) als kanonischer Datensatz mit verhaltensgleicher TED-Normalisierung und Dateiimport sowie deterministische, versionierte Vergabe-Vorprüfungen mit EU-Schwellenwerten je Geltungszeitraum.

Für Prüf- und Analyseanwendungen (audit-portal, Flowinvoice, audit_designer),
die Vergabedaten einlesen und vorprüfen. Ein Precheck-Ergebnis ist keine
Prüfentscheidung. Feature-Flag, Offline-Sperren, Zugriffsrechte, Importjobs,
Datenbank und die LLM-gestützte Vergabeanalyse bleiben in der Anwendung.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install auditcore_procurement \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (zuletzt veröffentlicht: 0.2.3 im
Release v0.4.1; weitere Versionen und Hashes unter
`https://janpow77.github.io/auditcore/simple/auditcore-procurement/`):

```text
auditcore_procurement @ https://github.com/janpow77/auditcore/releases/download/v0.4.1/auditcore_procurement-0.2.3-py3-none-any.whl#sha256=aaee40807b3284f6f4f3302e4f19ee8ceafabba221ffd1b6dd07138b6e97c12e
```

Ab 0.2.2 gehört `auditcore_common` als eigene Zeile dazu. Debian/Ubuntu über
die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)); Suggests
`python3-lxml`, `python3-auditcore-harvest`:

```bash
sudo apt-get install python3-auditcore-procurement
```

Extras: `[html]` – HAD-Ergebnisseiten parsen (`lxml`); `[sources]` –
Harvest-Adapter `procurement.ted_awards` und `procurement.had_search` auf
`auditcore_harvest`; `[dev]` – Test- und Prüfwerkzeuge.

## Schnellstart

```python
from datetime import date
from decimal import Decimal

from auditcore_procurement import load_profile, normalize_notice, run_prechecks, validate_record

datensatz = normalize_notice({"publication-number": "1-2024", "winner-name": "Beispiel GmbH"})
assert validate_record(datensatz) == []

profil = load_profile("procurement.hvtg", "2026.09.3")
bericht = run_prechecks(
    profil, Decimal("50000"), None, None, "Liefer-/Dienstleistungen",
    "Oeffentliche Ausschreibung", "BELOW_EU", [], mode="strict",
    reference_date=date(2026, 3, 1), authority_type="sub_central",
)
schwelle = bericht["checks"][0]["eu_threshold"]
assert schwelle["value"] == 216000 and schwelle["valid_from"] == "2026-01-01"
```

```pycon
>>> datensatz["contractor_name"]
'Beispiel GmbH'
>>> [c["status"] for c in bericht["checks"]], bericht["overall_status"]
(['PASS', 'PASS', 'FAIL', 'FAIL'], 'FAIL')
```

Die beiden `FAIL` entstehen, weil im Beispiel keine Pflichtdokumente und keine
Angebote übergeben werden.

## API-Überblick

- **Datensatz** `auditcore_procurement.notice/1` (`records.NOTICE_FIELDS`):
  Online-Abruf und Dateiimport liefern dieselben Felder; `validate_record`
  prüft Typen, ISO-Daten und Auftragnehmer.
- **TED** (`ted`, `ted_values`): `normalize_notice`, `inspect_notice`,
  Abfragebau, Werteextraktion.
- **Unternehmenssuche** (`company_sources`): Flowinvoice- und
  Designer-Variante für TED und HAD getrennt; `legacy_*` exakt wie das
  Original, `ted_company_result`/`had_result` mit Status
  `ok`/`no_hit`/`rate_limited`/`failed`.
- **Prechecks** (`prechecks`): `run_prechecks`, `load_profile`,
  `eu_period`/`ThresholdUnavailable`.
- **Harvest-Adapter** (Extra `sources`) holen genau eine Seite; Seitenfolge,
  Wiederholung, Rate-Limit, Checkpoint und Senke steuert `auditcore_harvest`.
  Beide bestehen dessen Contract-Suite.

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_procurement.__all__` (19):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `COVERAGE_ALL_NOTICES` | Konstante | – | `records` |
| `COVERAGE_AWARDS_WITH_WINNER` | Konstante | Coverage labels. Award-only results must not be presented as full coverage. | `records` |
| `NOTICE_FIELDS` | Konstante | – | `records` |
| `RECORD_CONTRACT` | Konstante | – | `records` |
| `Issue` | Datenklasse | Validation or plausibility note; ``blocking`` means the value is unreliable. | `records` |
| `PrecheckProfile` | Datenklasse | Versioned, source-bound rules of the deterministic prechecks. | `precheck_profile` |
| `SearchResult` | Datenklasse | Explicit outcome of one company search; ``notices`` is complete only if ``ok``. | `company_sources` |
| `ThresholdUnavailable` | Ausnahme | No verified EU threshold is recorded for the requested date/year. | `precheck_profile` |
| `__version__` | Wert | – | `(Paketstamm)` |
| `build_ted_query` | Funktion | TED expert query. An explicit ``query`` wins; otherwise filters are AND-combined and always restricted to award notices with a winner (:data:`AWARD_FILTER`). | `ted` |
| `had_result` | Funktion | Corrected contract. HTTP 404 is ``no_hit`` only in the ``designer`` variant (source semantics); in ``flowinvoice`` it is a failure. 403 is rate limiting. | `company_sources` |
| `inspect_notice` | Funktion | Visible warnings the legacy normalisation does not report (never alters records). | `ted` |
| `load_profile` | Funktion | Load an explicitly named packaged profile version. | `precheck_profile` |
| `normalize_notice` | Funktion | Flat canonical record of one TED notice. | `ted` |
| `normalize_notices` | Funktion | Normalise a list of notices; ``None`` results are skipped. | `ted` |
| `parse_ted_file` | Funktion | Parse a TED JSON upload (raw v3 notices or already normalised records). | `ted` |
| `run_prechecks` | Funktion | All prechecks in source order; overall status is the worst of FAIL > REVIEW_REQUIRED > WARNING > PASS (REVIEW_REQUIRED only in strict mode). | `prechecks` |
| `ted_company_result` | Funktion | Corrected contract: HTTP errors, invalid JSON and parser errors are explicit failures. | `company_sources` |
| `validate_record` | Funktion | Check a canonical record: known fields, value types, ISO dates, required contractor. | `records` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_procurement.company_sources` | TED company search (mnemonic fields) and HAD (Hessische Ausschreibungsdatenbank). |
| `auditcore_procurement.precheck_common` | Result statuses and shared helpers of the procurement prechecks. |
| `auditcore_procurement.precheck_profile` | Versioned precheck profiles: validation, packaged profiles and EU threshold periods. |
| `auditcore_procurement.precheck_threshold` | Threshold classification of the prechecks (legacy table and strict EU periods). |
| `auditcore_procurement.prechecks` | Deterministic procurement prechecks over an explicitly selected, versioned profile. |
| `auditcore_procurement.profiles` | – |
| `auditcore_procurement.records` | Canonical procurement notice record contract shared by online harvest and file import. |
| `auditcore_procurement.sources` | TED and HAD source adapters on ``auditcore_harvest`` (extra ``sources``). |
| `auditcore_procurement.ted` | TED notice normalisation, file import and query building (pure, no network). |
| `auditcore_procurement.ted_values` | Value extraction for TED notice fields (text, lists, amounts, dates). |
<!-- api-overview:end -->

## Profile und Konfiguration

Mitgelieferte Precheck-Profile (versioniert, mit Herkunft und Fingerprint):

- `procurement.hvtg-legacy 2026.09.1` – Code-Konstanten des Originals.
- `procurement.hvtg 2026.09.2` – freigegeben, EU-Schwellen 2024–2027.
- `procurement.hvtg 2026.09.3` – EU-Schwellen 2014–2027 in
  Zweijahreszeiträumen, je Wert mit amtlicher Fundstelle (VO (EU) Nr. 1336/2013,
  2015/2170 und 2015/2342, 2017/2365, 2019/1828, 2021/1952, 2023/2495,
  2025/2152).

`mode="legacy"` ist ergebnisgleich zum Original, `mode="strict"` korrigiert
die Befunde P-C01 bis P-C04 und P-C10 bis P-C12 und nennt Profil, Fingerprint
und den angewandten EU-Schwellenwert samt Fundstelle. Der Zeitraum wird über
`reference_date` (Datum der Maßnahme/Bekanntmachung) oder `year` gewählt;
fehlt er, lautet der Befund `REVIEW_REQUIRED`. `authority_type`
(`central`/`sub_central`) wählt den Wert für Liefer-/Dienstleistungen. Der
Standardabruf enthält nur Zuschlagsbekanntmachungen mit Auftragnehmer
(`award_notices_with_winner`); `require_contractor=False` behält alle Typen.
Quellenkatalog: `sources_catalog.json` (Format `auditcore_harvest.catalog/1`).

## Herkunft und Charakterisierung

Aus `janpow77/audit-portal@d8eefa4` (TED-Harvester, `audit_prep.ted_normalize`,
Prechecks, Regelwerk), `janpow77/flowinvoice@fb2d185` und
`janpow77/audit_designer@030a71e` (`company_records.py`). Das Original wurde
mit `tools/capture_procurement_legacy.py` ausgeführt: 57 Normalisierungs-,
Datei- und Query-Fälle, 13 Abrufszenarien, 27 Precheck-Fälle und 30 Fälle der
TED-/HAD-Clients (`tests/fixtures/procurement_legacy_observed.json`);
zusätzlich bestehen die 28 Originaltests am fixierten audit-portal-Commit. Der
Legacy-Vertrag (Standard der reinen Funktionen, `mode="legacy"`, `legacy_*`)
ist **legacy-exakt**, einschließlich der ASCII-Umschreibungen in den
Meldungstexten der Quelle. `audit_prep` ist Teil des Portal-Wheels; sein
TED-Kern wird dort künftig aus dieser Bibliothek re-exportiert.

## Bewusste Verhaltensabweichungen

Nur im korrigierten Vertrag (`mode="strict"`, `*_result`, Harvest-Adapter),
Einzelheiten P-C01 bis P-C12 in [docs/behavior-changes.md](docs/behavior-changes.md):
unbekannte Schwellenstufe und fehlende Werte ergeben `NOT_CHECKED` statt
PASS, Wert 0 ist ein Wert, exakte Zuordnung der Vergabeart statt Teilstring,
EU-Schwellen je Zeitraum und Auftraggeberart statt fester Zahlen, EU-Recht ab
Erreichen des Schwellenwerts (§ 106 GWB), Client-Fehler als Status statt
leerer Liste, nicht auswertbare TED-Antworten als `ParserError`.
Mehrdeutige Textbeträge (`"1.234,56"`) bleiben aus Kompatibilitätsgründen
gleich, `inspect_notice` meldet sie als `ambiguous_amount`.

## Abhängigkeiten

Python ≥ 3.11. Pflicht: `auditcore_common==0.1.0`. Optional `lxml>=4.9.2`
(`[html]`) und `auditcore_harvest==0.1.3` (`[sources]`). Keine Abhängigkeit
von der Plattform `auditcore`, Webframeworks oder Datenbanken.

## Sicherheit und Datenschutz

Der Kern arbeitet ohne Netzwerk. Online-Abruf nur über die Harvest-Adapter und
den Transport der Anwendung. Bekanntmachungen enthalten Namen von
Auftragnehmern (Unternehmen, ggf. Einzelunternehmer); Speicherung und
Zweckbindung verantwortet die Anwendung. Nutzungsbedingungen von TED und HAD
sind nicht geprüft (`REVIEW_REQUIRED`); Fixtures sind synthetisch im
Originalformat. Die nationalen Wertstufen sind Anwendungsregeln
(`REVIEW_REQUIRED`), eine rechtliche Validierung ist nicht erfolgt.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`) für den extrahierten Bibliothekscode laut Entscheidung des
Rechteinhabers vom 22.09.2026; die Quellrepositories werden nicht
umlizenziert (audit-portal trägt eine proprietäre Lizenz). Quelldateien mit
Git-Blobs: `NOTICE` und `provenance.json`.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
