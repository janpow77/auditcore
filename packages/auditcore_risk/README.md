# auditcore_risk

Eigenständig installierbare Bibliothek für **Risiko-Merkmale (Red Flags) aus
ausdrücklich gewählten, versionierten und quellengebundenen Regelprofilen**.
Die Mechanik wertet genau ein Profil aus; jedes Merkmal trägt Code,
Bezeichnung, Begründung, Belegwerte und die Fundstelle in der Quelle.
Es gibt **keinen gemeinsamen oder vereinheitlichten Risikoscore** und keine
stillen Gewichts- oder Schwellenänderungen.

```python
from auditcore_risk import evaluate, load_profile

profil = load_profile("riskanalysis.legacy", "b5c523bf7eaa")
ergebnis = evaluate(
    [
        {
            "bruttobetrag": 40_000.0,
            "vergabenummer": "0=ni",
            "Name": "Alpha GmbH",
            "zahlungsempfaenger": "Beta KG",
        }
    ],
    profil,
)
for merkmal in ergebnis.records[0].hits:
    print(merkmal.code, merkmal.reason)
# RF01 Betrag 40.000,00 ist ein glattes Vielfaches von 1.000,00.
# RF08 Betrag 40.000,00 über 25.000,00; Vergabekennung ist ein Platzhalter ('0=ni'); …
```

## Profile

| Profil | Version | Status | Quelle |
|---|---|---|---|
| `riskanalysis.legacy` | `b5c523bf7eaa` | `LEGACY_CHARACTERIZED` | riskanalysis `red_flags.py` (RF01, RF02, RF08–RF15), exakt reproduziert |
| `audit_designer.flowstat_belegliste` | `1254591156d3` | `LEGACY_CHARACTERIZED` | Flowstat `_red_flags` (BL_RF01–BL_RF10) in audit_designer und audit-portal |
| `riskanalysis.year_bound` | `2026.09.1` | `CANDIDATE_HUMAN_DECISION_REQUIRED` | abgelöst durch 2026.09.2 |
| `riskanalysis.year_bound` | `2026.09.2` | `APPROVED` | abgelöst durch 2026.09.3 |
| `riskanalysis.year_bound` | `2026.09.3` | `APPROVED` (empfohlen) | Entscheidung 23.09.2026: netto, EU-Schwelle des Jahres, RF12 gruppenintern, RF09 mit Umschrift „mueller“ |
| `flowinvoice.risk_checker` | `2026.09.2` | `APPROVED` (nicht aktiviert) | Splitting mit EU-Schwelle des Jahres |
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

## Module und Extras

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
| Jahresbezogene Schwellen | EU-Schwellen je Geltungszeitraum aus `auditcore_procurement` (`procurement.hvtg 2026.09.2`), nicht dupliziert | Extra `procurement` |

Ein Beleg, dessen Jahr keinen belegten Schwellenzeitraum hat, bleibt
**unbestimmt** (`None`, mit Grund), statt still als unauffällig zu gelten.

Herkunft, Rechte und Charakterisierung: [`provenance.json`](provenance.json),
[`NOTICE`](NOTICE). Unterschiede zum Original und offene fachliche
Entscheidungen: [docs/behavior-changes.md](docs/behavior-changes.md).
Consumer-Umstellung: [docs/consumer-integration.md](docs/consumer-integration.md).
Debian-Paket: `python3-auditcore-risk`.
