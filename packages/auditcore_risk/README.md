# auditcore_risk

## Zweck

Risiko-Merkmale (Red Flags) aus ausdrücklich gewählten, versionierten und quellengebundenen Regelprofilen, jedes Merkmal mit Code, Begründung, Belegwerten und Quellfundstelle.

Für Anwendungen, die Belege, Rechnungen oder Mittelabrufe für Stichproben und
Verwaltungskontrollen (VerwK) priorisieren – riskanalysis, Flowstat in
audit_designer und audit-portal, flowinvoice. Die Mechanik wertet genau ein
Profil aus; es gibt **keinen gemeinsamen oder vereinheitlichten
Risikoscore** und keine stillen Gewichts- oder Schwellenänderungen. Ein
Merkmal ist ein Prüfhinweis, keine Feststellung und keine Fehlerquote.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install 'auditcore_risk[fuzzy,procurement]' \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (zuletzt veröffentlicht: 0.3.4 im
Release v0.4.2; weitere Versionen und Hashes unter
`https://janpow77.github.io/auditcore/simple/auditcore-risk/`):

```text
auditcore_risk @ https://github.com/janpow77/auditcore/releases/download/v0.4.2/auditcore_risk-0.3.4-py3-none-any.whl#sha256=811970b803f1609e3e0810d18170428c97d15b9361f0e0cd3487b1c2916c5b69
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-risk
```

Extras: `[fuzzy]` – Namensabgleich (RF09) über
`auditcore_entity_matching[fuzzy]` (rapidfuzz); ohne Extra löst der
Namensabgleich `DependencyError` aus. `[pandas]` – DataFrame-Adapter
`auditcore_risk.frame`. `[procurement]` – jahresbezogene EU-Schwellen aus
`auditcore_procurement`. `[web]` – REST-Schnittstelle `auditcore_risk.web`
als Starlette-Anwendung; `[fastapi]` – dieselben Endpunkte als FastAPI-Router.
`[dev]` – Test- und Prüfwerkzeuge.

## Schnellstart

Das Profil der Flowstat-Belegliste braucht nur den Kern (kein Namensabgleich):

```python
from auditcore_risk import evaluate, load_profile

profil = load_profile("audit_designer.flowstat_belegliste", "1254591156d3")
belege = [
    {"projektbetrag": 40_000.0, "vergabe": None, "rechnungssteller": "Alpha GmbH",
     "rechnungsnummer": "R-1", "rechnungsdatum": "2026-03-01"},
    {"projektbetrag": 1_234.5, "vergabe": "V-7", "rechnungssteller": "Beta KG",
     "rechnungsnummer": "R-2", "rechnungsdatum": "2026-03-02"},
]
ergebnis = evaluate(belege, profil)

codes = [merkmal.code for merkmal in ergebnis.records[0].hits]
assert codes == ["BL_RF01_ROUND_AMOUNT", "BL_RF08_PROCUREMENT_MISSING"]
assert ergebnis.records[1].hits == ()
# Regeln ohne Eingabespalten werden ausgewiesen, nicht still übergangen
assert ergebnis.skipped["BL_RF09_DIRECT_AWARD_HIGH_AMOUNT"] == "Spalten fehlen: direktvergabe"
assert ergebnis.profile["status"] == "LEGACY_CHARACTERIZED"
```

```pycon
>>> print(ergebnis.records[0].hits[1].reason)
Betrag 40.000,00 über 25.000,00; Vergabekennung fehlt; Kostenart vergaberelevant.
```

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_risk.__all__` (30):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `DuplicateMatch` | Datenklasse | One candidate document considered a duplicate. | `fraud_duplicates` |
| `FraudProfile` | Datenklasse | Immutable fraud-check profile (one mechanic, one source variant). | `fraud_profile` |
| `SignalAssessment` | Datenklasse | Blockers, warnings, score components, score and level of one invoice. | `fraud_signals` |
| `TedAssessment` | Datenklasse | Statistics, red flags and legitimacy of one contractor (legacy structure). | `fraud_ted` |
| `assess_contractor` | Funktion | Legacy TED statistics, red flags and legitimacy over ``notice/1`` records. | `fraud_ted` |
| `available_fraud_profiles` | Funktion | Packaged ``(id, version)`` pairs of fraud-check profiles. | `fraud` |
| `find_duplicates` | Funktion | Exact matches first; fuzzy matches only if there is no exact match (as the source). | `fraud_duplicates` |
| `load_fraud_profile` | Funktion | Load an explicitly named packaged fraud-check profile (optionally of one kind). | `fraud` |
| `score_signals` | Funktion | Legacy blocker/warning derivation and score of the fraud-check manager. | `fraud_signals` |
| `select_contracts` | Funktion | Contracts of one contractor like the source SQL (not executed against Postgres). | `fraud_ted` |
| `KINDS` | Konstante | – | `rules` |
| `DatasetFinding` | Datenklasse | Result of a dataset-wide rule (for example a concentration share). | `results` |
| `DependencyError` | Ausnahme | An optional extra needed by the selected profile is not installed. | `errors` |
| `Evaluation` | Datenklasse | Complete, profile-bound result; ``summary`` follows the profile's format. | `results` |
| `FlagHit` | Datenklasse | One raised flag with its justification. | `results` |
| `InputError` | Ausnahme | Records violate the column/value contract of the selected profile. | `errors` |
| `ProfileError` | Ausnahme | A rule profile is missing, malformed or not explicitly selected. | `errors` |
| `RecordResult` | Datenklasse | Flags of one record in profile order (``None`` = not decidable). | `results` |
| `RiskError` | Ausnahme | Base class of all library errors. | `errors` |
| `RiskProfile` | Datenklasse | Immutable rule profile with identity, source and fingerprint. | `profiles` |
| `Rule` | Datenklasse | One flag rule; ``params`` hold every fachliche setting explicitly. | `profiles` |
| `__version__` | Wert | – | `(Paketstamm)` |
| `available_profiles` | Funktion | Packaged ``(id, version)`` pairs; none of them is an implicit default. | `profiles` |
| `evaluate` | Funktion | Evaluate ``profile`` over ``records``. | `engine` |
| `flatten_record` | Funktion | One level of nested mappings as ``parent.child`` fields (lists stay values). | `engine` |
| `identifier_missing` | Funktion | Whether ``value`` counts as a missing procurement identifier under ``rule``. | `engine` |
| `load_profile` | Funktion | Load an explicitly named packaged profile version. | `profiles` |
| `missing_columns` | Funktion | Per rule, required columns absent from ``columns`` (planning aid for consumers). | `engine` |
| `name_similarity` | Funktion | Similarity of one name pair under a ``name_similarity`` rule (for example RF09). | `engine` |
| `profile_from_dict` | Funktion | Validate a profile document; nothing is defaulted silently. | `profiles` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_risk.amount_rules` | Amount rule kinds: round amounts, threshold proximity, procurement identifiers. |
| `auditcore_risk.assessment` | Profile-local legacy aggregation of one record: message texts, points and weights. |
| `auditcore_risk.assessment_schema` | Checks of a profile's own legacy aggregation block (``assessment``). |
| `auditcore_risk.base` | Shared building blocks of the rule kinds (records, context, outcomes, helpers). |
| `auditcore_risk.engine` | Evaluate one explicitly selected profile over records. |
| `auditcore_risk.errors` | Error contract of the risk library; ``code`` is stable and machine readable. |
| `auditcore_risk.field_rules` | Field rule kinds: comparisons, missing values, dates and duplicate keys per record. |
| `auditcore_risk.frame` | pandas adapter (extra ``pandas``): drop-in functions for frame-based consumers. |
| `auditcore_risk.fraud` | Fraud-check mechanics of flowinvoice ``fraud_detection`` as profile-driven functions. |
| `auditcore_risk.fraud_duplicates` | ``duplicates``: exact and fuzzy invoice duplicates among pre-selected candidates. |
| `auditcore_risk.fraud_profile` | The fraud-check profile type shared by the three fraud mechanics. |
| `auditcore_risk.fraud_profiles` | – |
| `auditcore_risk.fraud_signals` | ``signal_score``: blockers, warnings, score and level from the sub-check results. |
| `auditcore_risk.fraud_ted` | ``ted_contractor``: statistics, red flags and legitimacy over one contractor's contracts. |
| `auditcore_risk.group_rules` | Group rule kinds: repeated awards, leave-one-out deduction rates, top shares. |
| `auditcore_risk.invoice_checks` | Parameter checks of the single-invoice rule kinds (``Kind.validate``). |
| `auditcore_risk.invoice_rules` | Rule kinds for single-invoice risk indicators (flowinvoice/audit-portal ``RiskChecker``). |
| `auditcore_risk.profile_data` | – |
| `auditcore_risk.profiles` | Versioned, source-bound rule profiles. |
| `auditcore_risk.results` | Result types of an evaluation: flag hits, record results, dataset findings. |
| `auditcore_risk.rule_checks` | Parameter value checks of the rule kinds that have no own ``Kind.validate``. |
| `auditcore_risk.rules` | Rule kinds: the reusable mechanics behind every profile rule. |
| `auditcore_risk.score_rules` | Predicate kinds for point scores (WIBANK-RBVK criteria, ex-ante indicators). |
| `auditcore_risk.summary` | Overview of an evaluation in the summary format the profile names. |
| `auditcore_risk.templates` | Message templates of profiles: only plain placeholders, no attribute or index access. |
| `auditcore_risk.values` | Value semantics of the characterized sources, expressed without pandas. |
| `auditcore_risk.web` | REST interface and display data for risk flags (extras ``web`` / ``fastapi``). |
<!-- api-overview:end -->

Module und Regelarten:

| Modul | Inhalt | Abhängigkeit |
|---|---|---|
| `profiles` | Laden und strenge Prüfung der Profile | – |
| `rules` | Regelarten (Mechanik): `round_multiple`, `near_threshold`, `missing_procurement`, `name_similarity`, `counterparty_concentration`, `ratio_history`, `leave_one_out_rate`, `numeric_compare`, `text_equals`, `missing_value`, `date_before`, `duplicate_key`, `nonzero_without_text`, `balance_mismatch`, `amount_with_marker`, `top_share` | – |
| `engine` | `evaluate`, `flatten_record`, `name_similarity`, `identifier_missing`, `missing_columns` | – |
| `invoice_rules` | Regelarten je Rechnung (`amount_or_statistic`, `share_above`, `all_missing`, `round_amount_terms`, `date_outside_range`, `text_patterns`, `names_differ`, `identifier_equal`, `split_window`) | – |
| `fraud` | Signalscore, TED-Auftragnehmerprofil, Dubletten | – |
| `score_rules` | Kriterien für Punkte-Scores (`truthy_all`, `text_in_set`, `number_range`, `set_overlap`) mit Bewertung `points_stages` | – |
| `frame` | pandas-Adapter: `compute_red_flags`, `red_flag_summary`, `evaluate_frame`, `annotate` | Extra `pandas` |
| Namensabgleich (RF09) | Normalisierung über `auditcore_entity_matching` (Profil `riskanalysis.payee`) | Extra `fuzzy` (rapidfuzz) |
| `web` | REST-Schnittstelle: `create_app` (Starlette), `routes`, `build_fastapi_router`; framework-freie Handler und Profilbeschreibung mit Eingabefeldern (`field_catalog.json`) | Extra `web` (starlette), für den Router Extra `fastapi` |
| Jahresbezogene Schwellen | EU-Schwellen je Geltungszeitraum aus `auditcore_procurement` 0.2.0 (`procurement.hvtg 2026.09.3`: 2014–2027; abgelöste Profilfassungen: 2026.09.2), nicht dupliziert | Extra `procurement` |

## Profile und Konfiguration

| Profil | Version | Status | Quelle |
|---|---|---|---|
| `riskanalysis.legacy` | `b5c523bf7eaa` | `LEGACY_CHARACTERIZED` | riskanalysis `red_flags.py` (RF01, RF02, RF08–RF15), exakt reproduziert |
| `audit_designer.flowstat_belegliste` | `1254591156d3` | `LEGACY_CHARACTERIZED` | Flowstat `_red_flags` (BL_RF01–BL_RF10) in audit_designer und audit-portal |
| `riskanalysis.year_bound` | `2026.09.1` | `CANDIDATE_HUMAN_DECISION_REQUIRED` | abgelöst durch 2026.09.2 |
| `riskanalysis.year_bound` | `2026.09.2` | `APPROVED` | abgelöst durch 2026.09.3 |
| `riskanalysis.year_bound` | `2026.09.3` | `APPROVED` | abgelöst durch 2026.09.4 (EU-Schwellen nur 2024–2027) |
| `riskanalysis.year_bound` | `2026.09.4` | `APPROVED` | abgelöst durch 2026.09.5 (ohne Nettobetrag Abbruch bzw. Ersatzbetrag 0) |
| `riskanalysis.year_bound` | `2026.09.5` | `APPROVED` (empfohlen) | Entscheidungen 23.09.2026: netto, EU-Schwelle des Jahres (2014–2027, `procurement.hvtg 2026.09.3`), RF12 gruppenintern, RF09 mit Umschrift „mueller“; 24.09.2026: ohne Nettobetrag RF02/RF08 je Beleg unbestimmt („Nettobetrag fehlt in der Quelle“), kein Rückfall auf brutto |
| `flowinvoice.risk_checker` | `2026.09.2` | `APPROVED` | abgelöst durch 2026.09.3 (EU-Schwellen nur 2024–2027) |
| `flowinvoice.risk_checker` | `2026.09.3` | `APPROVED` (nicht aktiviert) | Splitting mit EU-Schwelle des Jahres (2014–2027) |
| `flowinvoice.rbvk_wibank` | `2026.09.2` | `APPROVED` (empfohlen) | nach Profildatei V1.21 |
| `flowinvoice.risk_checker` | `fb2d18568d2e` | `LEGACY_CHARACTERIZED` | flowinvoice/audit-portal `RiskChecker` (9 Rechnungsindikatoren, Texte und Legacy-Score dieses Profils) |
| `flowinvoice.rbvk_wibank` | `fb2d18568d2e` | `LEGACY_CHARACTERIZED` | WIBANK-RBVK-Punkte je Mittelabruf (Codeverhalten), Stufen 8/19 |
| `flowinvoice.exante_basis` | `fb2d18568d2e` | `LEGACY_CHARACTERIZED` | 7 Ex-ante-Indikatoren, Basisgewichte, Klassen 30/55; kalibrierte Gewichte ausdrücklich über `points` |
| `flowinvoice.exante_heuristik` | `fb2d18568d2e` | `LEGACY_CHARACTERIZED` | Vergleichsheuristik des Ex-ante-Scores (Deckel 100) |

Betrugsprüfungen aus flowinvoice `fraud_detection` haben eigene Profile
(Schema `auditcore_risk.fraud-profile/1`, `load_fraud_profile`):

| Profil | Funktion | Inhalt |
|---|---|---|
| `flowinvoice.fraud_signals` | `score_signals` | Blocker, Warnungen, Score und Stufe aus den Ergebnissen der Teilprüfungen (Sanktions-, PEP- und Firmenprüfung werden nur als Signale konsumiert) |
| `flowinvoice.ted_contractor` | `select_contracts`, `assess_contractor` | Statistik, Merkmale und Legitimitätswert öffentlicher Aufträge (TED-Datensätze im `notice/1`-Vertrag von `auditcore_procurement`) |
| `flowinvoice.fraud_signals`, `flowinvoice.ted_contractor` 2026.09.2 | wie oben | empfohlen: Legitimität 0–1, Warnungen nach Dublettenentfernung |
| `flowinvoice.duplicates` | `find_duplicates` | exakte und unscharfe Rechnungsdubletten unter vorausgewählten Kandidaten |

Die Benford-Prüfung derselben Quelle liegt als `legacy_flowinvoice_benford`
in `auditcore_statistics` 0.2.0 (methodisch nicht gleich `benford_test`).

`load_profile(id, version)` verlangt beides ausdrücklich; es gibt kein
Standardprofil. Profile sind JSON-Dokumente mit Fingerabdruck (SHA-256); das
Ergebnis nennt Profil, Version, Fingerabdruck und Status.

Ein Beleg, dessen Jahr keinen belegten Schwellenzeitraum hat (mit 2026.09.3:
vor 2014 oder ab 2028), bleibt **unbestimmt** (`None`, mit Grund), statt still als unauffällig zu gelten.

Eingabefelder je Profil (Feld, Regeln, Bedeutung mit Beleg, Pflicht/optional,
Verhalten bei fehlender Spalte oder leerem Wert):
[docs/eingabefelder.md](docs/eingabefelder.md), erzeugt mit
`python tools/document_fields.py`; `tests/test_eingabefelder.py` hält die
Datei aktuell.

### Web-Schnittstelle (Extras `web`, `fastapi`)

```python no-run
from auditcore_risk.web import create_app          # Starlette, Pfade unter /risk
from auditcore_risk.web import build_fastapi_router  # app.include_router(...)
```

`GET /profiles`, `GET /profiles/{id}/{version}` (Regeln, Schwellen, Eingabefelder),
`POST /profiles/{id}/{version}/check-columns`, `POST /evaluate` (Merkmale je
Datensatz mit Begründung, verwendeten Eingabewerten, unbestimmten und
übersprungenen Regeln). Vertrag: [docs/ui/risk-rest.md](../../docs/ui/risk-rest.md).
Die Eingabefelder je Profil liefert `src/auditcore_risk/web/field_catalog.json`,
erzeugt mit `python tools/export_field_catalog.py` aus derselben Ableitung wie
`docs/eingabefelder.md`; `tests/test_web_field_catalog.py` hält die Datei aktuell.

### Fehlender Betrag: „unbestimmt“ statt Ersatzwert (ab 0.3.0)

Die Regelarten `near_threshold` und `missing_procurement` kennen den optionalen
Parameter `missing_amount_reason` (verlangt `missing_value: null`): Ein leerer
Betrag ergibt dann `None` (unbestimmt) mit dieser Begründung statt eines
Ersatzbetrags. `missing_procurement` bleibt `False`, wo der Betrag nicht
entscheidet (echte Vergabekennung oder nicht vergaberelevante Kostenart).
`when_missing_columns: "undetermined"` behandelt eine fehlende Betragsspalte wie
leere Werte; zulässig nur für diese beiden Regelarten mit `missing_amount_reason`
und nur, wenn die Betragsspalte die einzige Pflichtspalte ist. Bestehende
Profile nutzen beides nicht und verhalten sich unverändert.

## Herkunft und Charakterisierung

Quellen (Git-Blobs geprüft am 23.09.2026): `riskanalysis@b5c523b`
(`red_flags.py`), `audit_designer@1254591` und `audit-portal@ac1ccc7`
(identische `belegliste_analysis_service.py`), `flowinvoice@fb2d185`
(`risk_checker.py`, `fraud_detection`). Vor der Übernahme tatsächlich
ausgeführt und aufgezeichnet: riskanalysis 173 Frames
(`tools/capture_riskanalysis.py`), Flowstat 112 Frames
(`tools/capture_flowstat.py`), flowinvoice `RiskChecker` 338 Fälle sowie die
Betrugsprüfungen (Manager 268, TED 129, Dubletten 250 Fälle). Die Profile mit
Status `LEGACY_CHARACTERIZED` reproduzieren die Originale **legacy-exakt**;
die Profile `riskanalysis.year_bound` ab 2026.09.2, `flowinvoice.risk_checker` 2026.09.x und
`flowinvoice.rbvk_wibank` 2026.09.2 setzen Nutzerentscheidungen um
(`APPROVED`). Umstellung der Consumer:
[docs/consumer-integration.md](docs/consumer-integration.md).

## Bewusste Verhaltensabweichungen

Details und alle Entscheidungen: [docs/behavior-changes.md](docs/behavior-changes.md).

- RK-C01/RK-C07: Nicht numerische Beträge und Wahrheitswerte ergeben
  `InputError` mit Feldname; gleiche Skalarregel wie `pd.to_numeric`, aber
  ohne pandas im Kern.
- RK-C02: Fehlende Pflichtspalten ergeben `InputError`; übersprungene Regeln
  stehen in `Evaluation.skipped`.
- RK-C03: Kein stiller Rückfall auf `difflib`, wenn rapidfuzz fehlt.
- RK-C04: Jahresbezogene Schwellen nur in `riskanalysis.year_bound`; ohne
  belegten Zeitraum ist RF02 unbestimmt.
- RK-C05: Jedes Merkmal mit Begründung, Belegwerten und Quellfundstelle.
- RK-C06: Summen mit `math.fsum` (in 2 von 112 Flowstat-Frames weicht ein
  Konzentrationsanteil in der letzten Binärstelle ab; Entscheidungen gleich).
- RK-C08 bis RK-C11: deterministische Reihenfolge von Warnungen,
  Fehlervertrag statt Absturz bei TED und Dubletten, Merkmalsaufbereitung der
  VerwK-Punkte-Scores bleibt in der Anwendung.

## Abhängigkeiten

Python ≥ 3.11, `auditcore_common==0.2.0` (gemeinsame Hilfsfunktionen, nur
Standardbibliothek) und `auditcore_entity_matching==0.2.4` (Normalisierung für
RF09). Optional: `auditcore_entity_matching[fuzzy]==0.2.4` über `[fuzzy]`,
`pandas>=2.1` über `[pandas]`, `auditcore_procurement==0.2.4` über
`[procurement]`, `starlette>=0.26.1` über `[web]`, `fastapi>=0.92` über
`[fastapi]`. Die Benford-Prüfung aus flowinvoice liegt in
`auditcore_statistics` (keine Abhängigkeit).

## Sicherheit und Datenschutz

Verarbeitet Beleg- und Rechnungsdaten mit Namen von Rechnungsstellern und
Zahlungsempfängern, die der Aufrufer übergibt; das Paket speichert nichts und
nutzt im Kern kein Netzwerk (die SQL-Auswahl der TED-Kandidaten bleibt in der
Anwendung). Die REST-Schnittstelle aus `[web]` authentifiziert nicht;
Anmeldung und Rechte liefert die einbindende Anwendung. Regelprofile sind charakterisiertes Softwareverhalten zur
Priorisierung von Stichproben, keine rechtliche Bewertung und keine
Fehlerquote (TER/RER). Testdaten sind synthetisch.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Der Rechteinhaber hat am 22.09.2026 den extrahierten
Bibliothekscode und die Regelprofile freigegeben (`USER_AUTHORIZED_MIT`); die
Quellrepositories selbst werden nicht umlizenziert. Quellen mit Git-Blobs:
`NOTICE` und `provenance.json`.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
