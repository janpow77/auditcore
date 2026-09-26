# auditcore_statistics

## Zweck

Beschreibende Prüfstatistik (Benford-Test erster und erster zwei Ziffern, Konformitätsmaße nach MAD und z-Test) mit benannten, quellengebundenen Methodenprofilen.

Für Prüfanwendungen wie flowstat, flowinvoice und audit-portal. Die
Ergebnisse sind Statistiken, keine Feststellungen: Nichts markiert Datensätze
als auffällig, eine Signifikanzaussage gibt es nur mit ausdrücklich
gewähltem Niveau. Ausreißer-, Dubletten- und weitere Analysen der
Quellanwendungen gehören nicht dazu.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install auditcore_statistics \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (zuletzt veröffentlicht: 0.3.3 im
Release v0.4.1; weitere Versionen und Hashes unter
`https://janpow77.github.io/auditcore/simple/auditcore-statistics/`):

```text
auditcore_statistics @ https://github.com/janpow77/auditcore/releases/download/v0.4.1/auditcore_statistics-0.3.3-py3-none-any.whl#sha256=cdc9a14dc2ec778c26f6dc71e16c7fc615aeaff8305f0934904f915f3fafc177
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-statistics
```

Extras: `[web]` – REST-Vertrag `auditcore_statistics.web` als
Starlette-Routen, FastAPI-Router zusätzlich mit installiertem FastAPI;
`[dev]` – Test- und Prüfwerkzeuge.

## Schnellstart

```python
import random

from auditcore_statistics import benford_test
from auditcore_statistics.conformity import assess

# Ausschlüsse werden gezählt, nicht still verworfen
klein = benford_test([123, 187, 2450, 31, 4.2, 0, None], digits=1)
assert (klein.analysed, klein.zero, klein.missing) == (5, 1, 1)
assert klein.deviates_at_level is None      # ohne α keine Signifikanzaussage

# Synthetische, logarithmisch gleichverteilte Beträge
rng = random.Random(7)
betraege = [round(10 ** rng.uniform(1, 5), 2) for _ in range(2000)]
ergebnis = benford_test(betraege, digits=1, significance_level=0.05)
assert ergebnis.analysed == 2000 and ergebnis.deviates_at_level is False

konformitaet = assess(ergebnis, "first", "nigrini.2012")
assert konformitaet.mad_label == "Akzeptable Übereinstimmung"
```

```pycon
>>> round(konformitaet.mad, 4)
0.0068
```

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_statistics.__all__` (12):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `LEGACY_METHOD` | Konstante | – | `benford` |
| `METHOD` | Konstante | – | `benford` |
| `BenfordResult` | Datenklasse | Distribution, exclusions and chi-square statistic of one analysis. | `benford` |
| `DigitRow` | Datenklasse | Observed and expected frequency of one leading digit (group). | `benford` |
| `StatisticsInputError` | Ausnahme | Input does not satisfy the documented contract. | `benford` |
| `__version__` | Wert | – | `(Paketstamm)` |
| `benford_test` | Funktion | Compare leading digits with Benford's law. | `benford` |
| `chi2_survival` | Funktion | P(X ≥ statistic) for a chi-square distribution. | `numeric` |
| `expected_share` | Funktion | Benford probability log10(1 + 1/d) of a leading digit group d. | `benford` |
| `legacy_flowinvoice_benford` | Funktion | Result fields of the source ``BenfordResult`` as a dictionary (same values). | `legacy_flowinvoice` |
| `legacy_run_benford` | Funktion | Exact ``run_benford`` result for values already coerced by ``pd.to_numeric``. | `benford` |
| `recommended_flowinvoice_benford` | Funktion | ``benford_test`` with the decided parameters (replaces the legacy variant). | `legacy_flowinvoice` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_statistics.benford` | Benford first-digit and first-two-digit distribution with a chi-square statistic. |
| `auditcore_statistics.conformity` | Benford conformity measures (MAD, z per digit, second digit) with named profiles. |
| `auditcore_statistics.legacy_flowinvoice` | Exact legacy variant of flowinvoice ``BenfordsLawAnalyzer.analyze`` (fraud detection). |
| `auditcore_statistics.numeric` | Standard-library numerics with explicitly documented floating-point behavior. |
| `auditcore_statistics.web` | REST contract and routes for Benford user interfaces (extra ``web``). |
<!-- api-overview:end -->

`auditcore_statistics.conformity.assess(result, test, profile_id)` liefert
MAD-Band, z-Werte je Ziffer und den Zweitziffertest; `auditcore_statistics.web`
enthält den REST-Vertrag für `<flowaudit-benford>`
([docs/ui/benford-rest.md](../../docs/ui/benford-rest.md)).

## Profile und Konfiguration

- `benford_test(values, *, digits, short_values=None, significance_level=None)`:
  Methode `METHOD` mit exakten Erwartungswerten und χ²-p-Wert; für zwei
  Ziffern ist `short_values="exclude"` oder `"pad"` ausdrücklich anzugeben.
- `legacy_run_benford`: Profil `LEGACY_METHOD`, reproduziert
  `flowstat@d665ac2 run_benford`.
- `legacy_flowinvoice_benford`: Profil `flowinvoice.fraud_benford`
  (gerundete Erwartungswerte, fester kritischer Wert 15,507, Stufen-p-Wert,
  Mindestumfang 50).
- `recommended_flowinvoice_benford(values)`: Entscheidung vom 23.09.2026 –
  ruft `benford_test(values, digits=1, significance_level=0.05)` auf.
- Konformitätsprofil `nigrini.2012` (einziges Profil in
  `conformity.PROFILES`): MAD-Grenzen je Test (`first`, `first_two`,
  `second`), z-Grenze 1,96 mit Stetigkeitskorrektur, α = 0,05; es gibt kein
  implizites Standardprofil.

## Herkunft und Charakterisierung

Extrahiert aus `janpow77/flowstat@d665ac2`
(`analysis_core_service.py:run_benford`), tatsächlich ausgeführt mit numpy
1.26.2, pandas 2.1.3 und scipy 1.11.4 (`tools/capture_flowstat_benford.py`,
32 Fälle, 40 χ²-Referenzen); `legacy_run_benford` reproduziert alle 29
datenbezogenen Fälle **legacy-exakt** ohne NumPy/SciPy. Seit 0.2.0 zusätzlich
`flowinvoice@fb2d185` (`BenfordsLawAnalyzer.analyze`, in audit-portal
identisch; 65 Fälle, alle exakt). `conformity` und `web` (0.3.0) sind eigene
Ergänzungen; die MAD-Grenzen entsprechen FlowStat
`_interpret_benford_mad`. Eine fachliche Methodenvalidierung wurde nicht
durchgeführt. Die abweichende Benford-Implementierung in audit-portal
(`audit_tests_service.benford_test`) ist nicht übernommen.

## Bewusste Verhaltensabweichungen

`benford_test` weicht vom Original ab, die Legacy-Funktionen nicht
([docs/behavior-changes.md](docs/behavior-changes.md)):

- ST-C01: Zwei-Ziffern-Test mit einstelligen Werten bricht nicht ab;
  `short_values` wird ausdrücklich gewählt (Konvention noch
  `HUMAN_DECISION_REQUIRED`).
- ST-C02/ST-C03: Ziffern aus der exakten Dezimaldarstellung, unabhängig vom
  Datentyp und auch bei wissenschaftlicher Notation.
- ST-C04: Booleans, Texte und Unendlich werden abgewiesen.
- ST-C05: Fehlende, Null-, negative und zu kurze Werte werden gezählt.
- ST-C06: Keine fest eingebaute Schwelle `p < 0.05`.
- ST-C07: `±inf` in `legacy_flowinvoice_benford` löst `ValueError` aus statt
  einer Endlosschleife.

## Abhängigkeiten

Python ≥ 3.11 und `auditcore_common==0.2.0` (Summe und Rundung, seit
Unreleased auch der rahmenwerkfreie Teil der REST-Schicht aus
`auditcore_common.rest`; APT `python3-auditcore-common`); keine Abhängigkeit von `auditcore`, NumPy
oder SciPy. Optional `starlette>=0.26` über `[web]`.

## Sicherheit und Datenschutz

Rechnet nur mit übergebenen Zahlen, speichert nichts und nutzt im Kern kein
Netzwerk. Die `[web]`-Routen validieren Eingaben; Authentifizierung und
Mandantentrennung liefert die einbindende Anwendung. Einstufungen wie
„Keine Übereinstimmung“ beschreiben die Verteilung und sind keine
Feststellung über Datensätze.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Die Quellrepositories tragen keine Open-Source-Lizenz; der
Rechteinhaber hat am 22.09.2026 den extrahierten Bibliothekscode freigegeben
(`USER_AUTHORIZED_MIT`), die Quellen selbst werden nicht umlizenziert. Details:
`NOTICE` und `provenance.json`.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
