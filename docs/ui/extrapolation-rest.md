# REST-Vertrag Hochrechnung (`auditcore_extrapolation.web`)

Vertrag `auditcore_extrapolation.evaluation/1`. Stand: auditcore_extrapolation 0.1.0.
Oberfläche: `<flowaudit-extrapolation>` bzw. `ExtrapolationPanel` aus `@auditcore/ui`,
nativ in React `FlowauditExtrapolation` aus `@auditcore/ui-react`.

`catalogue`, `evaluate`, `residual` und `export_evaluation` sind framework-frei.
`create_app`/`routes` benötigen das Extra `web` (Starlette, Debian `python3-starlette`),
`create_router` zusätzlich FastAPI. Authentisierung, Mandantentrennung und Ablage der
Ergebnisse bleiben in der einbindenden Anwendung.

```python
from auditcore_extrapolation.web import create_app, create_router
app = create_app("/api/extrapolation")
fastapi_app.include_router(create_router("/api/extrapolation"))
```

## Grundsätze

- Gerechnet wird nur mit `auditcore_extrapolation.assess` bzw. `residual_error_rate`;
  jede Formel nennt ihre Fundstelle im KOM-Leitfaden EGESIF_16-0014-01 bzw. in der
  Vorlage CPRE_23-0013-01 Annex 3 (Feld `source` der Herleitungsschritte).
- **Keine Voreinstellung der Methode.** Statistische Methoden verlangen
  `confidence_level` und `factor_profile` (`kom_2017_tables` = Tabellenwerte des
  Leitfadens, nur dessen Konfidenzniveaus; `exact` = ungerundet).
- **TER und RER sind getrennte Endpunkte.** `/evaluate` liefert die Gesamtfehlerquote
  (Art. 2 Nr. 35 VO (EU) 2021/1060), `/residual` die Restfehlerquote nach
  Finanzkorrekturen (Art. 2 Nr. 36).
- Fehlerklassen je Einheit: zufällig (hochgerechnet), systemisch (nur abgegrenzt; mit
  dem abgegrenzten Betrag der Schicht in der TER, nicht hochgerechnet), anomal (nur mit
  Begründung; nicht korrigiert Teil der TER, korrigiert nicht).
- Das Ergebnis (`material`, `not_material`, `inconclusive`) gibt die Regeln aus
  Abschn. 4.12 bzw. 6.4.6 des Leitfadens wieder und ersetzt kein fachliches Urteil.
- Fehlerform wie bei den übrigen Verträgen: `{"error": {"code", "message"}}` mit
  `invalid_input` (422), `invalid_json` (400), `too_large` (413). Grenzen: 16 MiB je
  Anfrage, 100 000 Einheiten, 200 Schichten. Antworten mit `Cache-Control: no-store`.
- Jede Antwort trägt `contract`, `library` und `fingerprint` (SHA-256 über die Anfrage
  in kanonischem JSON).

## Endpunkte

| Methode | Pfad | Zweck |
|---|---|---|
| GET | `/profiles` | Methoden, Faktorprofile, Konfidenzniveaus, Wesentlichkeit, Fehlerklassen |
| POST | `/evaluate` | Hochrechnung, Präzision, TER, Fehlerobergrenze, Ergebnis, Herleitung |
| POST | `/evaluate/export` | dieselbe Auswertung als Datei (`format`: `csv` oder `json`) |
| POST | `/residual` | Restfehlerquote nach Annex 3 (Zeilen A–M) |
| POST | `/attributes` | Merkmals-, Discovery- und Stop-or-go-Stichprobe (Leitfaden 7.9) |
| POST | `/negative-units` | positive und negative Grundgesamtheit, Abstimmung (Leitfaden 4.6) |

### `POST /evaluate`

```json
{
  "method": "mus.standard",
  "confidence_level": 0.9,
  "factor_profile": "kom_2017_tables",
  "materiality_rate": 0.02,
  "strata": [{"name": "Programm", "book_value": 1000000, "systemic_error": 2000}],
  "units": [
    {"id": "V-01", "stratum": "Programm", "book_value": 20000, "random_error": 1000},
    {"id": "V-02", "stratum": "Programm", "book_value": 10000, "systemic_error": 500},
    {"id": "V-04", "stratum": "Programm", "book_value": 8000, "anomalous_error": 800,
     "anomalous_reason": "Einmaliger Übertragungsfehler", "anomalous_corrected": true},
    {"id": "V-05", "stratum": "Programm", "book_value": 200000, "random_error": 4000,
     "exhaustive": true}
  ]
}
```

Methoden: `srs.mean_per_unit`, `srs.ratio`, `difference`, `mus.standard`, `mus.ratio`,
`mus.conservative` (zusätzlich `sample_size`), `nonstatistical.mean_per_unit`,
`nonstatistical.ratio`, `nonstatistical.pps`. Verfahren mit gleicher
Auswahlwahrscheinlichkeit und alle nicht-statistischen Verfahren verlangen
`population_size` je Schicht. `book_value` und `population_size` einer Schicht
schließen die Einheiten der Vollerhebung (`exhaustive: true`) ein.

Antwort (gekürzt):

```json
{"contract": "auditcore_extrapolation.evaluation/1", "library": "auditcore_extrapolation 0.1.0",
 "fingerprint": "5aaa…", "method": {"id": "mus.standard", "label": "MUS – Standardansatz", "…": "…"},
 "projection": {"projected_random_error": 14000.0, "precision": 16450.0, "coefficient": 1.645,
   "strata": [{"name": "Programm", "projected_error": 14000.0, "exhaustive_error": 4000.0,
               "sample_size": 4, "sampling_book_value": 800000.0,
               "figures": {"interval": 200000.0, "tainting_sum": 0.05, "sd_rates": 0.025}}],
   "steps": [{"label": "…", "formula": "…", "value": 14000.0, "source": "EGESIF_16-0014-01, Abschn. 6.3.1.4"}],
   "warnings": ["1 Einheit(en) mit anomalem Fehler aus der Hochrechnung ausgenommen …"], "extra": {}},
 "total_error_rate": {"book_value": 1000000.0, "tolerable_error": 20000.0,
   "systemic_errors": 2000.0, "anomalous_uncorrected": 0.0, "anomalous_corrected_excluded": 800.0,
   "total_error": 16000.0, "rate": 0.016, "precision": 16450.0, "upper_limit": 32450.0,
   "upper_limit_rate": 0.03245, "conclusion": "inconclusive", "explanation": ["…"],
   "steps": ["…"], "difference": null}}
```

`extra` enthält je nach Methode `estimator_check` (Kovarianzregel, Abschn. 6.1.1.3),
`allowances` (konservativer Ansatz, Zuschläge je Fehler) oder `coverage`
(nicht-statistisch, Art. 79 Abs. 2 VO (EU) 2021/1060: unter 300 Einheiten, mindestens 10 %).
Bei `difference` enthält `difference` den korrigierten Buchwert, die Untergrenze und BV − TE.

### `POST /residual`

```json
{"audit_population": 1000, "total_error_rate": 0.025, "ongoing_assessment": 0,
 "other_negative_amounts": 0, "financial_corrections": 2.1, "materiality_rate": 0.02}
```

`total_error_rate` ist ein Anteil (0,025 = 2,5 %). Zahlen werden als Dezimalzahlen
gelesen; die Antwort enthält je Zeile A–M `value` (Zahl) und `exact` (Dezimaltext),
`rate`, `rate_rounded` (ROUND(K; 4)), `exceeds_materiality`, bei Überschreitung
`extrapolated_correction` (L) und `rate_after_correction` (M), sonst `not_applicable`.

### `POST /evaluate/export`

Wie `/evaluate` plus `format`. CSV: Semikolon, UTF-8 mit BOM, Dezimalkomma,
Formelzeichen am Zellanfang mit Apostroph neutralisiert; Kennzahlen, Ergebnis,
Erläuterung, Hinweise und die Herleitung mit Quelle je Schritt. Dateiname
`hochrechnung-<methode>-<12 Zeichen Fingerabdruck>.<format>`.

## Erweiterungen nach Leitfaden Kapitel 6 und 7 (abwärtskompatibel)

Alle Felder sind optional; Anfragen ohne sie werden wie bisher ausgewertet. Die
Antwort enthält zusätzlich immer `design` (`single`, `periods`, `groups`),
`subsamples` (Liste), `groups` (Liste) und `confidence_recalculation`.
Der Vertragsname bleibt `auditcore_extrapolation.evaluation/1`; Clients, die
unbekannte Felder übergehen, müssen nichts ändern.

### Mehrere Zeiträume (Leitfaden 6.1.3, 6.2.3, 6.3.3, 6.3.4, 6.4.9, 7.3)

```json
{"method": "mus.standard", "confidence_level": 0.6, "factor_profile": "kom_2017_tables",
 "periods": [{"name": "1. Halbjahr"}, {"name": "2. Halbjahr"}],
 "strata": [{"name": "Programm", "period": "1. Halbjahr", "book_value": 1827930259},
            {"name": "Programm", "period": "2. Halbjahr", "book_value": 2961930008}],
 "units": [{"id": "V-01", "period": "1. Halbjahr", "stratum": "Programm", "book_value": 1200000, "random_error": 900}]}
```

Jede Schicht und jede Einheit nennt ihren Zeitraum; Schichtnamen gelten je
Zeitraum, dieselbe Vorhabenkennung darf in mehreren Zeiträumen vorkommen.
Gerechnet wird je Zeitraum mit der gewählten Methode (auch geschichtet),
dann EE = Σ EE_t und SE = √Σ SE_t². Nicht zulässig für `mus.conservative` und
`mus.ratio`. `population_units` (optional) ist die Zahl verschiedener Einheiten
des Jahres für die Abdeckungsprüfung nicht-statistischer Verfahren (6.4.9).
Antwort: `projection.extra.periods` (je Zeitraum `name`, `book_value`,
`projected_random_error`, `precision`, `sample_size`, `extra`) und `period` je
Schichtergebnis.

### Teilstichprobe einer Einheit (7.6, 6.4.10, 6.5.3)

```json
{"id": "OP-7", "stratum": "Programm", "book_value": 1425315,
 "subsample": {"estimator": "ratio",
   "strata": [{"name": "Lead-Partner", "book_value": 658748}, {"name": "Projektpartner", "book_value": 766567}],
   "units": [{"id": "LP", "stratum": "Lead-Partner", "book_value": 658748, "random_error": 5274, "exhaustive": true},
             {"id": "PP-3", "stratum": "Projektpartner", "book_value": 152024, "random_error": 23}]}}
```

`estimator`: `ratio`, `mean_per_unit` (verlangt `population_size` je
Teilschicht) oder `pps`. Der zufällige Fehler der Einheit wird hochgerechnet
(`random_error` darf dann nicht gesetzt sein); `book_value` muss der Summe der
Teilschichten entsprechen. Teileinheiten tragen nur zufällige Fehler;
systemische und anomale Fehler stehen bei der Einheit. Eine Teileinheit darf
selbst eine `subsample` haben (dreistufig), tiefer nicht. Antwort `subsamples`:
je Einheit `projected_error`, `error_rate`, `coverage`, `sampled_items`,
Herleitung und Hinweise (unter 30 Teileinheiten).

### Gruppen von Programmen (7.8)

`group` an jeder Schicht (alle oder keine). Mit `periods` kombinierbar:
Programme als Schichten je Zeitraum (6.3.4, Beispiel 6.3.4.7); die Gruppe wird
über alle Zeiträume ausgewertet, jedes Programm über seine Schichten aller
Zeiträume.
Die Hauptauswertung gilt der ganzen Gruppe; `groups` enthält je Programm
`name`, `observations`, `warnings`, `projection` und `total_error_rate`.

### Neuberechnung des Konfidenzniveaus (7.7)

`system_assessment` (Kategorie 1–4 nach Tabelle 1 in 3.2.1: 60/70/80/90 %)
oder `required_confidence_level` (Anteil). `confidence_recalculation`:
`applicable`, `reason`, `coefficient` (z), `recalculated_coefficient` (z*),
`confidence_level`, `required_level`, `supports_not_material`, `steps`.
Anwendbar nur bei nicht schlüssigem Ergebnis statistischer Verfahren außer
dem konservativen MUS-Ansatz.

### Ausschluss und Ersetzen nach verhältnismäßiger Kontrolle (7.10)

Je Schicht optional `excluded_book_value`, `excluded_units` (Stichprobenteil)
und `excluded_exhaustive_book_value`, `excluded_exhaustive_units`
(Hochwertschicht). `book_value` und `population_size` beschreiben dann die
reduzierte, tatsächlich gezogene Grundgesamtheit. Die Hochrechnung wird je
Schicht mit BV_original/BV_reduziert (MUS, Verhältnisschätzung, PPS,
konservativ) bzw. N_original/N_reduziert (Mittelwert- und
Differenzenschätzung) erweitert; die TER bezieht sich auf den ursprünglichen
Buchwert (`total_error_rate.book_value`). Ersetzen einer Einheit der
Hochwertschicht durch eine Einheit der Stichprobenschicht (7.10.3.1 b):
`excluded_exhaustive_*` setzen, die Ersatzeinheit gehört zur Stichprobe.

### `POST /attributes` (7.9)

```json
{"approach": "normal", "deviations": 3, "sample_size": 150, "confidence_level": 0.95,
 "factor_profile": "kom_2017_tables", "tolerable_rate": 0.05}
```

`approach`: `normal` (Voreinstellung, Merkmalsstichprobe 7.9.3–7.9.5,
verlangt `factor_profile`), `discovery` oder `stop_or_go` (7.9.6, exakte
Binomial-Obergrenze; `tolerable_rate` ist bei `discovery` die kritische Quote).
Antwort `attributes`: `approach`, `rate` (EDR), `upper_limit` (ULD),
`conclusion` (`supported`/`not_supported`, `criterion_met`/`deviation_found`/`go`,
`stop`/`go`), `steps`; bei `normal` zusätzlich `precision`
(z × √(p(1 − p)/n)) und `tolerable_rate`, sonst `threshold`.

### `POST /negative-units` (4.6)

```json
{"approach": 3,
 "units": [{"id": "Y", "new_expenditure": 25000, "current_corrections": 700, "previous_corrections": 4300}],
 "checks": [{"id": "Z", "corrected_amount": 12000, "decided_amount": 15000}]}
```

`approach` 1–3 nach Leitfaden 4.6 (2 und 3 empfohlen). Antwort `population`
(`positive`, `negative`, `positive_total`, `negative_total`, `net_declared`,
Herleitung, Hinweise) und `review` (`shortfalls`, `total_shortfall`,
`disclose` = im Kontrollbericht offenlegen). Für die negative Grundgesamtheit
wird keine Fehlerquote berechnet.

### Katalog

`/profiles` enthält zusätzlich `designs`, `subsample_estimators`,
`system_assessment` (Kategorie, Bezeichnung, Konfidenzniveau),
`limits.max_periods`, `attribute_approaches`, `negative_approaches` und je
Methode `periods` (Mehrperiodenform vorhanden).
