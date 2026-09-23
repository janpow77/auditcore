# auditcore_risk 0.1.0 — Bericht

Stand: 23. September 2026. Teil 1 (riskanalysis, Flowstat) gemergt als PR #17
(`85c6fba`); Teil 2 (flowinvoice-Rechnungsindikatoren und Betrugsprüfungen)
auf Branch `feat/auditcore-risk-flowinvoice`. Nicht veröffentlicht; der
zentrale Release v0.3.0 folgt nach allen Paketen. Mit diesem Paket steigen
`auditcore_entity_matching` auf 0.2.0 (Profil `riskanalysis.payee`,
`pair_score`) und `auditcore_statistics` auf 0.2.0 (Legacyvariante
`legacy_flowinvoice_benford`), jeweils additiv.

## Umfang

Eigenständige Distribution `auditcore_risk` (Debian `python3-auditcore-risk`).
Laufzeitabhängigkeit nur `auditcore_entity_matching==0.2.0` (reine
Standardbibliothek). Extras: `fuzzy` (rapidfuzz über
`auditcore_entity_matching[fuzzy]`), `pandas` (DataFrame-Adapter),
`procurement` (`auditcore_procurement==0.1.0`, jahresbezogene EU-Schwellen).
Keine Laufzeitabhängigkeit auf `auditcore`.

| Fähigkeit | Umsetzung |
|---|---|
| Mechanik | 16 Regelarten (u. a. Schwellennähe, runde Beträge, fehlende Vergabekennung, Selbstbeauftragung per Namensabgleich, Konzentration, Versionshistorie, Leave-one-out-Kürzungsquote, Dubletten, Datums-/Saldenprüfungen, Anteil des größten Rechnungsstellers) |
| Regelprofile | JSON mit Schema, Fingerabdruck, Quelle, Fundstelle je Regel, offene Entscheidungen; `riskanalysis.legacy b5c523bf7eaa`, `audit_designer.flowstat_belegliste 1254591156d3` (Legacy), `riskanalysis.year_bound 2026.09.1` (Kandidat) |
| Ergebnis | je Beleg Flags (auch „unbestimmt“), Treffer mit Code, Bezeichnung, Begründung, Belegwerten, Interpretation (`indicator`/`descriptive_prior`) und Quellfundstelle; Profilidentität; Zusammenfassung im Format der Quelle; **kein Gesamtscore** |
| Schwellennähe | Legacy statisch; Kandidat mit EU-Schwelle je Geltungszeitraum aus `auditcore_procurement` (nicht dupliziert), ohne Rückfallschwelle |
| Entitätsabgleich | RF09 über `auditcore_entity_matching` (Profil `riskanalysis.payee`, `pair_score`) |
| pandas-Adapter | `compute_red_flags`/`red_flag_summary` als Drop-in für riskanalysis und flowinvoice |
| Rechnungsindikatoren (Teil 2) | Profil `flowinvoice.risk_checker`: 9 Indikatoren mit Schweregrad, Texten und dem Legacy-Score **dieses** Profils (Summe der Schweregewichte / 5) |
| Betrugsprüfungen (Teil 2) | `flowinvoice.fraud_signals` (Blocker/Warnungen/Score aus Teilprüfungen; Sanktionen/PEP/Firma nur als Signale), `flowinvoice.ted_contractor` (über `notice/1`-Datensätze aus `auditcore_procurement`), `flowinvoice.duplicates`; Benford in `auditcore_statistics` |

## Quellen, Rechte

Gegen GitHub geprüft (23.09.2026): riskanalysis `main` =
`b5c523bf7eaa326153778d9751f176f03d4d56ed` (`red_flags.py` Blob `b6196a7`,
`payee_normalizer.py` Blob `fceae5b`); audit_designer `main` =
`1254591156d3bdf6ccdf4050dec7713a61ad4a20` und audit-portal `main` =
`ac1ccc779db69492db0c2c154b6ec84fdd1794b1` (`belegliste_analysis_service.py`
identischer Blob `d03738c`); flowinvoice `main` = `fb2d185…` (inhaltsgleiche
Kopie von `red_flags.py`). Alle privat, ohne Lizenzdatei. Nutzerentscheidung
22.09.2026 „die Bibliotheken sollen MIT sein, die anderen Repos nicht“:
`USER_AUTHORIZED_MIT` für den extrahierten Bibliothekscode, keine
Umlizenzierung der Quellen. Testdaten synthetisch.

Teil 2: flowinvoice `main` = `fb2d18568d2eaf64574d131ceae51a936b9aac02`
(gegen GitHub geprüft): `services/risk_checker.py` (Blob `b799e85`, audit-portal
nur formatverschieden), `services/fraud_detection/{manager,ted_checker,duplicate_detector,benfords_law}.py`
(Blobs `0a48b36`, `5618a2e`, `ad6c7ff`, `77bf2b1`).

Geprüft und nicht übernommen: `vp_ai` `ScorecardService`
(Bearbeitungsstands-Score über ORM) und `RuleValidationService`
(Checklistenregeln); KPAnG-Tatbildung (bleibt in regulierung).

## Characterization

| Quelle | Werkzeug | Umgebung | Umfang | Ergebnis |
|---|---|---|---|---|
| riskanalysis `red_flags.py` | `tools/capture_riskanalysis.py` (Blob-geprüft, unverändert importiert) | pandas 3.0.5, NumPy 2.5.1, rapidfuzz 3.14.5 | 173 Frames (Frames der 26 Originaltests, Grenzfälle je Regel, 120 zufällige), > 2.500 Belege | exakt reproduziert (Flags, `name_match`, Codes, Zusammenfassung inkl. Volumen) |
| Flowstat `_red_flags` (Designer + Portal) | `tools/capture_flowstat.py` (AST, Blob-geprüft, beide Kopien verglichen) | pandas 2.1.4, NumPy 1.26.2 | 112 Frames | Codes und Zähler exakt; Konzentrationsanteil in 2 Frames letzte Binärstelle (RK-C06) |
| riskanalysis `normalize_name`, `_name_match` | `auditcore_entity_matching/tools/capture_riskanalysis_payee.py` | rapidfuzz 3.14.5 | 55 Namen, 25 Paare | exakt |

| flowinvoice `RiskChecker.assess` | `tools/capture_flowinvoice_risk_checker.py` (unverändert importiert) | flowinvoice-Umgebung (`requirements-production.txt`) | 338 Anfragen | exakt (Indikatoren, Schwere, Texte, Score, Zusammenfassung) |
| flowinvoice Manager, TED, Dubletten | `tools/capture_flowinvoice_fraud.py` (Teilprüfungen durch Stellvertreter ersetzt; SQL NOT_EXECUTED) | dito | 268 / 129 / 250 Fälle | exakt; 23 Originalabbrüche (`TypeError`) als `InputError` (RK-C09) |
| flowinvoice `BenfordsLawAnalyzer` | `auditcore_statistics/tools/capture_flowinvoice_benford.py` | Standardbibliothek | 65 Fälle | exakt |

Alle Capture-Läufe sind reproduzierbar (Wiederholung bytegleich).
Bewusste Abweichungen RK-C01 … RK-C07 und erhaltene Eigenheiten RK-L03:
`packages/auditcore_risk/docs/behavior-changes.md`.

## Tests und Gates (tatsächlich ausgeführt)

| Prüfung | Ergebnis |
|---|---|
| Paket-pytest (Python 3.12, pandas 3.0.6, rapidfuzz 3.10.1) | Teil 1: 573 passed; mit Teil 2: **1.573 passed** (zusätzlich Replay RiskChecker 340, Replay Betrugsprüfungen 648, Betrugsvertrag 12; Fixtures unter Python 3.11 wie die Produktionsimages erzeugt, RK-L07) |
| `auditcore_statistics` 0.2.0 | 159 passed (davon 68 neu) |
| `auditcore_entity_matching` 0.2.0 | 543 passed (davon 84 neu für `riskanalysis.payee`) |
| ruff, ruff format, mypy strict (src und gesamtes Paket), bandit -ll | PASS |
| Plattform (`pytest`, `ruff check .`, `mypy src`, CLI-Hilfen) | Teil 1: 281 passed; mit Teil 2 und main-Stand: 284 passed, PASS |
| auditcore-quality strict (`--framework` verwaltung-app-framework@15f5338, Kontext, SBOM) | Syntax, Lint, Typen, bandit, pip-audit, Tests, Supply Chain PASS; API-Vergleich NOT_EXECUTED (erste Version, keine Basis); 2 × AC-OSS-001 REVIEW_REQUIRED (Regex-Platzhaltermuster in Profil/Fixture, kein Kennzeichen); Gesamt REVIEW_REQUIRED wegen Policy ([risk-quality.json](risk-quality.json)) |
| Policy (`tools/policy_proof.py`) | F-09, F-15, F-17 VERIFIED und artefaktgebunden (T-11, T-14, T-31, T-38, Profilprüfungen); F-05 REVIEW_REQUIRED (Namen können natürliche Personen bezeichnen, Bewertung beim Consumer), F-07/F-07.ASSESS offen (Schutzbedarf UNKNOWN) |

## Installation

`scripts/verify_domain_packages.py` mit installierter Plattform (Wheel aus
diesem Branch) für harvest, entity_matching 0.2.0, procurement und risk mit
`--apt`: **PASS** — Build + SBOM, hashgebundene Requirements-Installation,
`pip check`, Importherkunft, Smoke aus dem installierten Wheel, selektive
Installation/Entfernung je Paket, Debian-Pakete Revision 1/2, signierte
APT-Quelle, Installation, Upgrade 1→2 und Entfernung im netzlosen Container.
Wheel-SHA256 `auditcore_risk-0.1.0` (Teil 1):
`49581f4f998c45ad16a12813da04ccc3ffe25e7c63d3a57f2b3a0b5392d032cd`
(`auditcore_entity_matching-0.2.0`: `34730c6f…`). Teil 2 erneut mit
harvest, entity_matching 0.2.0, procurement, statistics 0.2.0 und risk:
**PASS 49/49 Prüfungen** inkl. APT-Lebenszyklus (statistics 0.2.0
`5a01b4f5…`). Anschließend alle Quelltestsuiten gegen die installierten
Wheels: PASS.

## Consumer

| Consumer | Stelle | Nachweis | Status |
|---|---|---|---|
| riskanalysis | `backend/app/pipeline/red_flags.py` | Testsuite vorher/nachher identisch (178 passed, 9 failed ohne `Database.mdb`, 9 skipped); Frame-Vergleich 453 Frames / 8.583 Belege identisch | getestet, Umstellung nach v0.3.0 |
| flowinvoice | `backend/app/verwk/pipeline/red_flags.py` | `tests/verwk` vorher/nachher 564 passed, 8 skipped; mit synthetischem Demobestand (3.789 Belege) `build_levels` identisch, Pipeline-Integrationstests 34 passed | getestet, Umstellung nach v0.3.0 |
| audit_designer, audit-portal (Flowstat) | `belegliste_analysis_service.py:_red_flags` | Replay 112 Originalfälle; Anwendungstests NOT_EXECUTED | geplant |
| flowinvoice Betrugsprüfung | `services/fraud_detection/{manager,ted_checker,duplicate_detector,benfords_law}.py` (API `/api/fraud/*`, Pipeline-Regel) | Replay aller Originalfälle; flowinvoice hat keine Tests dieser Module (NOT_EXECUTED) | geplant |
| flowinvoice/audit-portal RiskChecker | `services/risk_checker.py` | kein Laufzeitaufrufer in beiden Anwendungen | geplant |

Umstellungsanleitung und Vorlage: `packages/auditcore_risk/docs/consumer-integration.md`,
`packages/auditcore_risk/docs/consumers/riskanalysis_red_flags.py`.

## HUMAN_DECISION_REQUIRED

1. Kein gemeinsamer/vereinheitlichter Risikoscore ohne fachliche Entscheidung.
2. RF02: netto kommentierte Schwellen gegen Bruttobeträge.
3. RF02 jahresbezogen: Freigabe `riskanalysis.year_bound` (Stichtag, Auftraggebertyp,
   Leistungskategorie; nationale Wertgrenzen jahresbezogen?). 221.000 ist die
   EU-Schwelle 2024–2025, seit 2026 gilt 216.000.
4. RF09: Umlautzerlegung (`Müller → mu ller`) vs. empfohlene Transliteration.
5. RF12: Merkmalsübertragung über gleiche Vorhabenkennung aus fremden Gruppen.
6. BL_RF08/BL_RF09 gegenüber RF08: unterschiedliche Vergaberegeln bleiben getrennt.
7. flowinvoice RiskChecker: Aktivierung/Anbindung der gespeicherten Konfiguration; Bezugsgröße der Lieferantenhäufung.
8. Betrugs-Signalscore: Skala der TED-Legitimität (0–1 oder 0–100), Zählung der Warnungen vor/nach Deduplizierung.
9. Rechnungssplitting-Schwellen (1.000–50.000, 80 %) vs. RF02 und jahresbezogene EU-Schwellen.
10. Benford der Betrugsprüfung: Umstellung auf `benford_test` (exakte Erwartungswerte, echter p-Wert).
