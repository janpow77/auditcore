# auditcore_extrapolation

## Zweck

Hochrechnung von Stichprobenfehlern für Prüfbehörden nach dem KOM-Leitfaden zur Stichprobenziehung: Präzision, Fehlerobergrenze, Gesamtfehlerquote (TER) und getrennt davon die Restfehlerquote (RER).

Für Prüfbehörden aller ESI-Fonds (Art. 79 VO (EU) 2021/1060) und die
Anwendungen der FlowAudit-Familie, die Vorhabenprüfungen auswerten. Abgedeckt
sind einfache Zufallsstichprobe (Mittelwert- und Verhältnisschätzung),
Differenzenschätzung, MUS (Standardansatz, geschichtet, konservativer Ansatz,
Verhältnisschätzung bei systemischen Fehlern), nicht-statistische Stichproben,
die Hochwertschicht (Vollerhebung) sowie systemische und anomale Fehler.
Nicht enthalten: Stichprobenumfang und Auswahl (das bleibt in
`auditcore_sampling`), Zwei-Perioden-Verfahren und mehrstufige Stichproben.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install auditcore_extrapolation \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Noch nicht veröffentlicht: 0.1.0 erscheint mit dem nächsten Release. Danach
hashgebunden in einer `requirements.txt` (Direkt-URL und `sha256` stehen im
Index unter `https://janpow77.github.io/auditcore/simple/auditcore-extrapolation/`):

```text
auditcore_extrapolation @ https://github.com/janpow77/auditcore/releases/download/v<release>/auditcore_extrapolation-0.1.0-py3-none-any.whl#sha256=<sha256>
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-extrapolation
```

Extras: `[web]` – REST-Vertrag `auditcore_extrapolation.web` als
Starlette-Routen (`starlette>=0.26`, Debian `python3-starlette`),
FastAPI-Router zusätzlich mit installiertem FastAPI; `[dev]` – Test- und
Prüfwerkzeuge (u. a. Hypothesis, `auditcore_sampling` für die Abgleichstests).

## Schnellstart

Beispiel 6.4.7 des Leitfadens (nicht-statistische Stichprobe mit
wertproportionaler Auswahl), aus synthetischen Einheiten nachgebaut:

```python
from decimal import Decimal

from auditcore_extrapolation import (
    KOM_TABLES, ResidualInputs, SampleUnit, Stratum, assess, residual_error_rate,
)

# 4 Einheiten der Vollerhebung (Fehler 80.028 €), 4 Einheiten der Stichprobe
vollerhebung = tuple(
    SampleUnit(f"H{i}", 12_411_965 / 4, fehler)
    for i, fehler in enumerate((50_000.0, 30_028.0, 0.0, 0.0))
)
stichprobe = tuple(
    SampleUnit(f"S{i}", 500_000.0, 500_000.0 * quote)
    for i, quote in enumerate((0.02, 0.0072, 0.0, 0.0))
)
schicht = Stratum("Programm", 22_031_228.0, stichprobe, vollerhebung, population_size=36)

ergebnis = assess("nonstatistical.pps", [schicht])
ter = ergebnis.total_error_rate
assert round(ter.total_error) == 145_439          # Leitfaden: 145.439 €
assert ter.upper_limit is None                    # nicht-statistisch: keine Obergrenze
assert ter.conclusion == "not_material"

# Dieselbe Stichprobe statistisch (MUS-Standardansatz, 90 %)
mus = assess("mus.standard", [schicht], confidence_level=0.9, factor_profile=KOM_TABLES)
assert mus.total_error_rate.upper_limit > mus.total_error_rate.total_error

# Restfehlerquote getrennt davon: Beispiel B der Vorlage CPRE_23-0013-01 Annex 3
rer = residual_error_rate(ResidualInputs(1000, Decimal("0.025"), financial_corrections=2.1))
assert rer.rate_rounded == Decimal("0.0229") and rer.exceeds_materiality
assert abs(rer.rate_after_correction - Decimal("0.02")) < Decimal("1e-20")
```

Anomale Fehler werden nur mit Begründung aus der Hochrechnung genommen:

```pycon
>>> assess("nonstatistical.pps", [Stratum("P", 1000.0, (SampleUnit("x", 100.0, anomalous_error=5.0),), population_size=5)])
Traceback (most recent call last):
...
auditcore_extrapolation.errors.ExtrapolationInputError: Einheit 'x': Ein anomaler Fehler wird nur mit Begründung aus der Hochrechnung ausgenommen (Leitfaden, Anhang 6: nachweislich nicht repräsentativ).
```

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_extrapolation.__all__` (48):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `EXACT` | Konstante | – | `factors` |
| `INCONCLUSIVE` | Konstante | – | `evaluation` |
| `KOM_TABLES` | Konstante | – | `factors` |
| `MATERIAL` | Konstante | – | `evaluation` |
| `MATERIALITY_RATE` | Konstante | Materiality threshold of 2 % of the expenditure (guidance section 4.9). | `evaluation` |
| `METHODS` | Konstante | – | `methods` |
| `NOT_MATERIAL` | Konstante | – | `evaluation` |
| `PROFILES` | Konstante | – | `factors` |
| `RECOMMENDED_PROFILE` | Konstante | – | `factors` |
| `Allowance` | Datenklasse | Incremental allowance of the error in position ``order`` (1-based). | `conservative` |
| `Assessment` | Datenklasse | Projection and total error rate of one audited sample. | `evaluation` |
| `DifferenceFigures` | Datenklasse | Corrected book value view of difference estimation (section 6.2.1.5). | `evaluation` |
| `ErrorClasses` | Datenklasse | Sample totals of the error classes (for the TER breakdown). | `units` |
| `EstimatorCheck` | Datenklasse | Rule of section 6.1.1.3: ratio estimation if COV(E,BV)/VAR(BV) > ER/2. | `equal_probability` |
| `ExtrapolationInputError` | Ausnahme | Input, method or profile does not satisfy the documented contract. | `errors` |
| `FactorProfile` | Datenklasse | A named source of z values and reliability factors. | `factors` |
| `Method` | Datenklasse | A projection method of the guidance. | `methods` |
| `Projection` | Datenklasse | Projected random error (EE) and precision (SE) of one method. | `projection` |
| `ResidualErrorRate` | Datenklasse | Rows F–M of the template; ``rate`` is K (None if I = 0). | `residual` |
| `ResidualInputs` | Datenklasse | Rows A–H of the template (B and C are informational only). | `residual` |
| `SampleUnit` | Datenklasse | One audited sampling unit (operation or payment claim). | `units` |
| `Step` | Datenklasse | One retraceable line of a derivation: formula, value and source. | `sources` |
| `Stratum` | Datenklasse | One stratum: book value, sampled units, exhaustive units, systemic errors. | `design` |
| `StratumResult` | Datenklasse | Projection of one stratum (sampling part plus exhaustive units). | `projection` |
| `TopStratum` | Datenklasse | Result of the iterative separation of the high-value stratum. | `design` |
| `TotalErrorRate` | Datenklasse | TER with its components, upper limit and conclusion (not the RER). | `evaluation` |
| `__version__` | Wert | – | `(Paketstamm)` |
| `assess` | Funktion | Project and evaluate in one step; BV is the sum of the strata book values. | `evaluation` |
| `basic_reliability_factor` | Funktion | Reliability factor for zero errors (basic precision, conservative MUS). | `factors` |
| `conclude` | Funktion | Conclusion of guidance section 4.12, or 6.4.6 when ``upper`` is None (non-statistical). | `evaluation` |
| `estimator_check` | Funktion | Recommend mean-per-unit or ratio estimation from the sample (section 6.1.1.3). | `equal_probability` |
| `evaluate` | Funktion | TER, upper limit and conclusion for a projection over population ``book_value``. | `evaluation` |
| `incremental_allowances` | Funktion | IA_i for the positive taintings by decreasing projected error (guidance section 6.3.5.5). | `conservative` |
| `mean_per_unit_error` | Funktion | EE₁ = N × ΣE_i / n (section 6.1.1.3, also 6.2.1.3 and 6.4.5.1). | `equal_probability` |
| `mus_precision` | Funktion | SE = z × √(Σ BV_hs² / n_hs × s_rh²) (section 6.3.2.5; H = 1: 6.3.1.5). | `mus` |
| `poisson_factor` | Funktion | Upper Poisson limit λ with P(X ≤ errors \| λ) = 1 − CL (exact Appendix 3 factor). | `factors` |
| `precision` | Funktion | SE = N × z × s / √n (sections 6.1.1.4 and 6.2.1.4). | `equal_probability` |
| `project` | Funktion | Project the random errors of an audited sample to the population. | `methods` |
| `ratio_error` | Funktion | EE₂ = BV × ΣE_i / ΣBV_i (section 6.1.1.3; Appendix 1, 2.3 with BV′). | `equal_probability` |
| `ratio_q_values` | Funktion | q_i = E_i − (ΣE / ΣBV) × BV_i (section 6.1.1.4). | `equal_probability` |
| `reliability_factor` | Funktion | Reliability factor RF(k) for the k-th error (incremental allowance). | `factors` |
| `residual_error_rate` | Funktion | RER after financial corrections (template CPRE_23-0013-01 Annex 3, Art. 2 Nr. 36 CPR). | `residual` |
| `residual_from_total` | Funktion | RER with A = audited population and D = TER of an evaluation. | `residual` |
| `split_top_stratum` | Funktion | Separate the 100 % stratum for MUS (guidance section 6.3.1.3). | `design` |
| `split_top_stratum_for_plan` | Funktion | :func:`split_top_stratum` with the sample size of an ``auditcore_sampling`` plan. | `design` |
| `stratified_precision` | Funktion | SE = N × z × s_w / √n with s_w² = Σ N_h/N × s_h² (sections 6.1.2.4, 6.2.2.4). | `equal_probability` |
| `tainting_projection` | Funktion | EE_s = SI × Σ E_i / BV_i with SI = BV_s / n_s (section 6.3.1.4). | `mus` |
| `z_value` | Funktion | z coefficient of the precision formulas. | `factors` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_extrapolation.conservative` | Monetary unit sampling, conservative approach (guidance section 6.3.5). |
| `auditcore_extrapolation.design` | Population strata and the separation of the high-value (top) stratum. |
| `auditcore_extrapolation.equal_probability` | Equal-probability projection: mean-per-unit, ratio and difference estimation. |
| `auditcore_extrapolation.errors` | The single exception type of the package. |
| `auditcore_extrapolation.evaluation` | Total error rate (TER), upper limit of error and audit conclusion. |
| `auditcore_extrapolation.factors` | Confidence coefficients: z values and Poisson reliability factors. |
| `auditcore_extrapolation.methods` | Named projection methods and the single entry point :func:`project`. |
| `auditcore_extrapolation.mus` | Monetary unit sampling (MUS), standard approach, also stratified. |
| `auditcore_extrapolation.projection` | Result of a projection: projected random error, precision and derivation. |
| `auditcore_extrapolation.residual` | Residual error rate (RER) after financial corrections – Annex 3 template. |
| `auditcore_extrapolation.sources` | Source references and the derivation step shared by all estimators. |
| `auditcore_extrapolation.units` | Audited sampling units, error classification and sample statistics. |
| `auditcore_extrapolation.web` | REST contract ``auditcore_extrapolation.evaluation/1`` (extra ``web``). |
<!-- api-overview:end -->

`auditcore_extrapolation.web` enthält den REST-Vertrag
`auditcore_extrapolation.evaluation/1` (`catalogue`, `evaluate`, `residual`,
`export_evaluation`) für `<flowaudit-extrapolation>`; Vertrag:
[docs/ui/extrapolation-rest.md](../../docs/ui/extrapolation-rest.md).

## Profile und Konfiguration

Methoden (`METHODS`, immer ausdrücklich gewählt, keine Voreinstellung):

| Methode | Leitfaden | Schichtung | Präzision |
|---|---|---|---|
| `srs.mean_per_unit`, `srs.ratio` | 6.1.1, 6.1.2; Anhang 1, 2 | ja | N·z·s_w/√n |
| `difference` | 6.2.1, 6.2.2; Anhang 1, 3 | ja | N·z·s_w/√n, CBV und Untergrenze |
| `mus.standard` | 6.3.1, 6.3.2; Anhang 1, 4.1 | ja | z·√(Σ BV_hs²/n_hs·s_rh²) |
| `mus.ratio` | Anhang 1, 4.2 | nein | z·BV_s/√n_s·s_rq |
| `mus.conservative` | 6.3.5 | nein | SI·RF + Σ Zuschläge |
| `nonstatistical.mean_per_unit`, `.ratio`, `.pps` | 6.4.5 | ja | keine |

Faktorprofile (`PROFILES`): `kom_2017_tables` (empfohlen, Werte wie gedruckt:
Tabelle 3 für z, Tabelle 4 für RF(0), Anhang 3 für RF(k); nur deren
Konfidenzniveaus) und `exact` (Normalquantil und Poisson-Obergrenze,
ungerundet, jedes Niveau). Wesentlichkeitsschwelle `MATERIALITY_RATE` = 2 %,
niedrigere Werte zulässig, höhere nicht. Formeln, Quellen je Formel und die
nachgerechneten Beispiele: [docs/referenzfaelle.md](docs/referenzfaelle.md).

## Herkunft und Charakterisierung

Neuimplementierung ohne Vorläufercode (`provenance.json`: `NEW_IMPLEMENTATION`).
Grundlage sind der KOM-Leitfaden EGESIF_16-0014-01 (20.01.2017) und die
RER-Vorlage CPRE_23-0013-01 Annex 3; beide sind nur mit Fundstellen zitiert.
Nachweis: die Beispiele 6.1.1.6, 6.1.2.6, 6.2.1.6, 6.3.1.7, 6.3.2.7, 6.3.5.7
und 6.4.7 des Leitfadens sowie die Beispiele A, B, C.1, C.2 und „Negative
units“ der Vorlage sind als Tests nachgerechnet; alle 510 Faktoren aus Anhang 3
stimmen mit der exakten Poisson-Obergrenze auf zwei Stellen überein;
Eigenschaftstests (Hypothesis) prüfen die Invarianten. Die Abgrenzung zu den
Hochrechnungen in audit_designer und audit-portal steht in
[docs/abgrenzung.md](docs/abgrenzung.md).

## Bewusste Verhaltensabweichungen

Keine gegenüber einem Vorläufer (Neuimplementierung). Druckfehler und
Rundungen des Leitfadens sind in [docs/referenzfaelle.md](docs/referenzfaelle.md)
festgehalten.

## Abhängigkeiten

Python ≥ 3.11 und `auditcore_common==0.1.1` (gemeinsame REST-Schicht
`auditcore_common.rest` des Extras `[web]`; selbst nur Standardbibliothek). Der
Rechenkern nutzt nur die Standardbibliothek. Optional `starlette>=0.26` über
`[web]` (FastAPI nur, wenn der Consumer es installiert).
`auditcore_sampling` ist keine Laufzeitabhängigkeit: `split_top_stratum_for_plan`
nimmt jedes Objekt mit `sample_size` (z. B. dessen `SizePlan`).

## Sicherheit und Datenschutz

Rechnet nur mit übergebenen Beträgen; kein Netzwerk, keine Speicherung im
Kern. Kennungen der Einheiten sollten Vorgangsnummern sein, keine
personenbezogenen Daten. Die Routen von `[web]` validieren jede Eingabe,
begrenzen Anfragegröße und Umfang und neutralisieren Formeln im CSV-Export;
Authentisierung und Mandantentrennung liefert die einbindende Anwendung. Das
Ergebnis gibt die Entscheidungsregeln des Leitfadens wieder und ersetzt nicht
das fachliche Urteil der Prüfbehörde.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Freigabe des Rechteinhabers vom 22.09.2026 für die
Bibliotheken in auditcore (`USER_AUTHORIZED_MIT`); Details in `NOTICE` und
`provenance.json`.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
