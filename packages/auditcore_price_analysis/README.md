# auditcore_price_analysis

## Zweck

Exakte Jahreskostenberechnung für regulierte Tarife (Nahwärme, Wasser mit Staffeln), deterministische Tarifauswahl und Vergleichsregeln (Abweichung, Ampel, Gruppenstatistik) auf versionierten, quellengebundenen Profilen.

Erster Consumer ist `janpow77/regulierung` (Preismonitoring,
`services/calculator.py`, `services/preisauswahl.py`). LLM-Extraktion,
Plausibilisierung, Reviewqueue, Scheduler, Datenbank und Rechte bleiben in der
Anwendung; die Bibliothek gibt keinen Preis frei.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install auditcore_price_analysis \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (zuletzt veröffentlicht: 0.1.2 im
Release v0.4.1; weitere Versionen und Hashes unter
`https://janpow77.github.io/auditcore/simple/auditcore-price-analysis/`):

```text
auditcore_price_analysis @ https://github.com/janpow77/auditcore/releases/download/v0.4.1/auditcore_price_analysis-0.1.2-py3-none-any.whl#sha256=43e225c80c6be00b3c1a511bccbbe6a7d41f188048f18748885c375bb5290100
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-price-analysis
```

Extras: nur `[dev]` (Test- und Prüfwerkzeuge).

## Schnellstart

```python
from decimal import Decimal

from auditcore_price_analysis import Tariff, calculate, load_calculation_profile

profil = load_calculation_profile("regulierung.hpp.nahwaerme", "2026.09.1")
tarif = Tariff.from_mapping(
    {"grundpreis_eur_kw": "28.50", "arbeitspreis_ct_kwh": "10.82"},
    profil,
    release="freigegeben",
    valid_from="2025-01-01",
)
ergebnis = calculate(
    tarif, profil, consumption={"kw": 12, "kwh": 27000}, stichtag="2025-07-01"
)

# Fehlende optionale Bestandteile zählen nicht still als 0:
# die Summe ist eine Untergrenze.
assert ergebnis.total_rounded == Decimal("3263.40")
assert ergebnis.total_is_lower_bound
```

```pycon
>>> ergebnis.missing_optional
('verrechnungspreis_eur_jahr', 'emissionspreis_ct_kwh', 'waermeumlagenpreis_ct_kwh')
```

`ergebnis.to_dict()` liefert JSON mit Profil-ID, -Version und -Fingerprint,
Zeilen und Einheiten.

## API-Überblick

Vertrag `auditcore_price_analysis.contract/1`:

- `calculate` – Jahreskosten mit exakten Dezimalwerten und Rundung je Profil.
  Fehlender Verbrauch ist ein Fehler, fehlende Bestandteile stehen im Ergebnis.
- `select_tariff` – deterministische Auswahl nach Freigabe, Stichtag, Q3 (mit
  Rückfallkennzeichen) und Standardvariante; ausgeschlossene Zeilen mit Grund.
- `delta_pct`, `traffic_light`, `group_statistics` – Vergleichsregeln ohne
  Gleitkommaartefakte; ohne gültige Referenz `None`.
- `auditcore_price_analysis.legacy` – exakte Nachbildung der Originalfunktionen
  für die schrittweise Umstellung des Consumers.

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_price_analysis.__all__` (45):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `CONTRACT_VERSION` | Konstante | – | `(Paketstamm)` |
| `GREEN` | Konstante | – | `comparison` |
| `RED` | Konstante | – | `comparison` |
| `STATUS_NONE` | Konstante | – | `selection` |
| `STATUS_OK` | Konstante | – | `selection` |
| `STATUS_Q3_FALLBACK` | Konstante | – | `selection` |
| `YELLOW` | Konstante | – | `comparison` |
| `CalculationProfile` | Datenklasse | Versioned rules of one annual cost calculation. | `_profile_model` |
| `CalculationResult` | Datenklasse | Structured result; exact values plus values rounded by the profile rule. | `calculation` |
| `ComparisonProfile` | Datenklasse | Versioned rules for deviation, traffic light, statistics and tariff selection. | `_profile_model` |
| `ComponentRule` | Datenklasse | One price component: amount = price × quantity(basis) × factor. | `_profile_model` |
| `ConsumptionRule` | Datenklasse | A consumption quantity of the formula (``legacy_default`` is documentation only). | `_profile_model` |
| `GroupStatistics` | Datenklasse | Statistics of one comparison group; ``None`` when the group is empty. | `comparison` |
| `Line` | Datenklasse | One component of the formula on the reference day. | `calculation` |
| `PriceAnalysisError` | Ausnahme | Invalid input, profile or tariff; ``code`` is stable and machine-readable. | `errors` |
| `ProfileError` | Ausnahme | A profile is unknown, malformed or does not fit the tariff. | `errors` |
| `ReleaseStatus` | Aufzählung | Release status of a price record as recorded by the consumer. | `tariff` |
| `Rounding` | Datenklasse | A named rounding rule: quantum and mode (for example 0.01, ROUND_HALF_UP). | `numbers` |
| `Selection` | Datenklasse | Chosen tariff (or ``None``) with data status, ambiguity and exclusions. | `selection` |
| `Tariff` | Datenklasse | One price record of a provider for one kind (``nahwaerme``/``wasser``). | `tariff` |
| `Tier` | Datenklasse | One tier: price applies up to ``limit`` (``None`` = open-ended last tier). | `tariff` |
| `TierRule` | Datenklasse | Tiered price for one component (for example the water work price). | `_profile_model` |
| `TierUse` | Datenklasse | Quantity billed in one tier. | `calculation` |
| `__version__` | Wert | – | `(Paketstamm)` |
| `available_profiles` | Funktion | Shipped profiles with id, version, type, status and fingerprint. | `profiles` |
| `calculate` | Funktion | Annual costs of ``tariff`` on ``stichtag`` under ``profile``. | `calculation` |
| `calculation_profile_from_dict` | Funktion | Validate and freeze a calculation profile. | `profiles` |
| `comparison_profile_from_dict` | Funktion | Validate and freeze a comparison profile. | `profiles` |
| `delta_pct` | Funktion | Percentage deviation ``(value - reference) / reference × 100``, rounded by profile. | `comparison` |
| `group_statistics` | Funktion | Median, mean, standard deviation (population or sample per profile), min and max. | `comparison` |
| `ignored_tier_keys` | Funktion | Keys inside tiers that the calculation does not use (reported, not dropped silently). | `tariff` |
| `legacy_parse_decimal` | Funktion | Characterized 0.1.1 behaviour: point text only, every comma is rejected. | `numbers` |
| `load_calculation_profile` | Funktion | Shipped calculation profile; the version must be named explicitly. | `profiles` |
| `load_comparison_profile` | Funktion | Shipped comparison profile; the version must be named explicitly. | `profiles` |
| `load_recommended_calculation_profile` | Funktion | The recommended (decided) calculation profile, e.g. ``regulierung.hpp.wasser``. | `profiles` |
| `load_recommended_comparison_profile` | Funktion | The recommended (decided) comparison profile. | `profiles` |
| `non_negative` | Funktion | Like :func:`parse_decimal` but rejects negative values. | `numbers` |
| `parse_day` | Funktion | A calendar day from ``date`` or ISO text ``YYYY-MM-DD``; datetimes are rejected. | `numbers` |
| `parse_decimal` | Funktion | Exact decimal from ``int``, ``Decimal``, finite ``float`` or number text. | `numbers` |
| `parse_tiers` | Funktion | Validate tiers; ``None`` or an empty list means "no tiers". | `tariff` |
| `recommended_version` | Funktion | Version of ``profile_id`` marked as recommended (decided rules); exactly one must exist. | `profiles` |
| `select_tariff` | Funktion | Select one tariff for ``stichtag`` (and meter size ``q3`` for water). | `selection` |
| `standard_consumption` | Funktion | Standard consumption stated by the profile (single source); error if a value is missing. | `profiles` |
| `tiered_amount` | Funktion | Bill ``quantity`` through sorted tiers; returns amount, usage and "beyond last limit". | `calculation` |
| `traffic_light` | Funktion | ``gruen`` up to threshold × fraction, ``gelb`` up to the threshold, else ``rot``. | `comparison` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_price_analysis.calculation` | Annual cost calculation with exact decimals, explicit units and a trace. |
| `auditcore_price_analysis.comparison` | Deviation, traffic light and group statistics with exact decimals. |
| `auditcore_price_analysis.errors` | Structured errors of the price analysis contract. |
| `auditcore_price_analysis.legacy` | Legacy-compatible calculation of ``regulierung`` (exact replay, for consumer migration). |
| `auditcore_price_analysis.numbers` | Exact number parsing and explicit rounding (no binary floating point in results). |
| `auditcore_price_analysis.profiles` | Versioned, source-bound calculation and comparison profiles. |
| `auditcore_price_analysis.selection` | Deterministic selection of the tariff that applies on a reference day. |
| `auditcore_price_analysis.tariff` | Tariffs (price records) with explicit validity, release status and tiers. |
<!-- api-overview:end -->

## Profile und Konfiguration

Profile unter `profiles/*.json` (versioniert, quellengebunden, Fingerprint):
Bestandteile mit Einheit, Bezugsgröße und Faktor, Gültigkeitsfenster
(Umlagenwechsel 01.07.2025), Staffelregeln, Rundung, Umgang mit fehlenden
Werten, Freigabeanforderung, Ampel-, Statistik- und Auswahlregeln. Mitgeliefert:
`regulierung.hpp.nahwaerme`, `.wasser` und `.vergleich` jeweils in
**2026.09.1** (charakterisiert, bitgenau zum Original) und **2026.09.2**
(empfohlen, Nutzerentscheidungen PA-H01 bis PA-H04 vom 23.09.2026, u. a.
Wasser-Standardverbrauch 180 m³ über `standard_consumption`, Beachtung von
`valid_to`). Es gibt kein stilles Standardprofil: Version immer angeben oder
ausdrücklich `load_recommended_calculation_profile` bzw.
`load_recommended_comparison_profile` verwenden.

`ReleaseStatus` wird nur gelesen; nicht freigegebene oder am Stichtag nicht
gültige Tarife sind „nicht vergleichbar“ mit Grund.

## Herkunft und Charakterisierung

Aus `janpow77/regulierung@853676d2` (`backend/app/services/calculator.py`,
`backend/app/services/preisauswahl.py`). `tools/capture_regulierung_calculator.py`
hat das Original ausgeführt; 274 Fälle mit Eingabe und Ergebnis bzw. Fehler
stehen in `tests/fixtures/regulierung_calculator_observed.json`.
`auditcore_price_analysis.legacy` reproduziert alle 274 Fälle **exakt** (Werte,
Gleitkommadarstellung, Fehlertyp und -text). Der neue Vertrag liefert überall,
wo beide Seiten rechnen, dieselben gerundeten Beträge und dieselbe
Vergleichbarkeit; jede Abweichung ist fallgenau getestet.

## Bewusste Verhaltensabweichungen

Siebzehn Befunde am Original (PA-L01 bis PA-L17) und ihre Behandlung im neuen
Vertrag stehen in [docs/behavior-changes.md](docs/behavior-changes.md), unter
anderem: fehlender Verbrauch und fehlende Staffelpreise sind Fehler statt 0,
fehlende optionale Bestandteile machen die Summe zur Untergrenze, exakte
Dezimalrundung (ROUND_HALF_UP) statt `round` auf Binärwerten, unbekannte
Preisschlüssel und Staffelformen sind Fehler, Stichtag nur als Kalendertag.
Seit 0.1.2 liest `parse_decimal` deutsche Schreibweise („1.234,56 €“,
„1234,56“) nach dem gemeinsamen Vertrag `parse-number` (Modus `de`);
Mehrdeutiges („1,234“) ist `ambiguous_number`, Punkttext bleibt unverändert,
das bisherige Verhalten steht als `legacy_parse_decimal` bereit (PA-C01).
Offen (`REVIEW_REQUIRED`): die Rechtsgrundlage des Umlagenstichtags
01.07.2025. Umstellung von regulierung:
[docs/consumer-migration.md](docs/consumer-migration.md).

## Abhängigkeiten

Python ≥ 3.11, zur Laufzeit die Standardbibliothek und
`auditcore_common==0.2.0` (Zahleneingabe `numbers_de`, ab 0.1.2). Keine Netzwerk- oder
Datenbankabhängigkeit, keine Abhängigkeit von der Plattform `auditcore`.
Preisquellen liefert bei Bedarf `auditcore_price_sources`.

## Sicherheit und Datenschutz

Reine Berechnung ohne Netzwerk, Dateien oder personenbezogene Daten. Eingaben
werden streng geprüft (Punktschreibweise oder eindeutige deutsche
Schreibweise, kein Exponent, Mehrdeutiges wird abgelehnt statt geraten). Keine Tarifdaten realer Versorger im Paket; alle
Fixtures sind synthetisch. Ergebnisse sind Rechenwerte, keine Preisfreigabe
oder rechtliche Bewertung.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Freigabe des Rechteinhabers vom 22.09.2026 für die
Bibliothek (`USER_AUTHORIZED_MIT`); das Quellrepository behält seinen eigenen
Status, keine Umlizenzierung. Quelldateien mit Git-Blobs: `provenance.json`;
Zuschreibung: `NOTICE`.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
