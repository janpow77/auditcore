# auditcore_sampling

## Zweck

Stichprobenumfänge (MUS, einfache Zufallsstichprobe), systematische MUS-Auswahl, Zufallsauswahl und Schichtung mit ausdrücklich benannten, quellengebundenen Methoden.

Für Prüfanwendungen wie flowstat und audit-portal, die Stichproben
nachvollziehbar und mit Seed reproduzierbar ziehen müssen. Die Bibliothek
wählt keine Methode still: Maßgeblich für MUS ist nach der Entscheidung vom
23.09.2026 `portal.mus_poisson`. Zwei-Perioden-Verfahren,
Differenzschätzung, Fehlerprojektion und nicht-statistische Auswahl gehören
(noch) nicht dazu.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install auditcore_sampling \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (zuletzt veröffentlicht: 0.2.2 im
Release v0.4.1; weitere Versionen und Hashes unter
`https://janpow77.github.io/auditcore/simple/auditcore-sampling/`):

```text
auditcore_sampling @ https://github.com/janpow77/auditcore/releases/download/v0.4.1/auditcore_sampling-0.2.2-py3-none-any.whl#sha256=c735af5fea79f0b47506f789c0df8b6e21d5391a41e537659cc68d48b9d0a6b1
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-sampling
```

Extras: `[web]` – REST-Vertrag `auditcore_sampling.web` als Starlette-Routen
(`starlette>=0.26`, Debian `python3-starlette`), FastAPI-Router zusätzlich mit
installiertem FastAPI; `[dev]` – Test- und Prüfwerkzeuge.

## Schnellstart

```python
import random

from auditcore_sampling import (
    SamplingInputError,
    draw_start,
    recommended_mus_size,
    stratified_allocation,
    systematic_mus,
)

# Aufgezeichneter Referenzfall der Entscheidung „mus 30“
plan = recommended_mus_size(
    population_value=475_478.94, materiality=50_000.0,
    expected_error_rate=0.005, confidence_level=0.95,
)
assert (plan.method, plan.sample_size) == ("portal.mus_poisson", 30)

# Zufall nur aus einem übergebenen Generator: mit Seed reproduzierbar
betraege = [1200.0, -50.0, 0.0, 80_000.0, 15_000.5, 3_300.0] * 5
start = draw_start(random.Random(42), plan.interval)
auswahl = systematic_mus(
    betraege, sample_size=10, interval=plan.interval, start=start, variant="portal"
)
assert auswahl.positions == (3, 4, 9)          # jede Position einmal
assert auswahl.excluded_negative == (1, 7, 13, 19, 25)

assert stratified_allocation(30, {"A": 100, "B": 50, "C": 10}, "proportional") == {
    "A": 19, "B": 10, "C": 2,
}

# Kein stiller Ersatzwert für unbekannte Konfidenzniveaus
try:
    recommended_mus_size(population_value=1.0, materiality=1.0,
                         expected_error_rate=0.0, confidence_level=0.93)
except SamplingInputError:
    pass
else:
    raise AssertionError("0,93 muss abgewiesen werden")
```

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_sampling.__all__` (21):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `METHODS` | Konstante | – | `sizes` |
| `MUS_DECISION` | Konstante | – | `sizes` |
| `MUS_POISSON` | Konstante | – | `sizes` |
| `MUS_Z_ATTRIBUTE` | Konstante | – | `sizes` |
| `SRS_FLOWSTAT` | Konstante | – | `sizes` |
| `SRS_PORTAL` | Konstante | – | `sizes` |
| `Method` | Datenklasse | A named, source-bound sample-size method. | `sizes` |
| `RECOMMENDED_MUS_METHOD` | Konstante | Authoritative MUS method, decided by the user on 2026-09-23. | `sizes` |
| `MusSelection` | Datenklasse | Selected positions of one systematic MUS draw. | `selection` |
| `SamplingInputError` | Ausnahme | Input or method choice does not satisfy the documented contract. | `sizes` |
| `SizePlan` | Datenklasse | Result of a sample-size calculation with its method and inputs. | `sizes` |
| `__version__` | Wert | – | `(Paketstamm)` |
| `draw_start` | Funktion | Random start in [0, interval) from an explicit generator; 0 without interval. | `selection` |
| `first_reaching` | Funktion | For each target the first position whose cumulative value is ≥ target. | `selection` |
| `mus_size` | Funktion | MUS sample size and sampling interval with strict inputs. | `sizes` |
| `recommended_mus_method` | Funktion | The decided MUS method (``portal.mus_poisson``), see ``MUS_DECISION``. | `sizes` |
| `recommended_mus_size` | Funktion | MUS sample size with the decided method; same contract as :func:`mus_size`. | `sizes` |
| `simple_random` | Funktion | Draw ``size`` distinct elements without replacement from an explicit generator. | `selection` |
| `srs_size` | Funktion | SRS sample size n = z²p(1-p)/e² with finite population correction, capped at N. | `sizes` |
| `stratified_allocation` | Funktion | flowstat allocation: proportional ceil(n·Nh/N) or equal ceil(n/H), capped at Nh. | `selection` |
| `systematic_mus` | Funktion | Systematic monetary-unit selection. | `selection` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_sampling.legacy` | Behavior-compatible adapters for ``flowstat@d665ac2`` and ``audit-portal@d8eefa4``. |
| `auditcore_sampling.selection` | Deterministic selection mechanics with explicitly supplied randomness. |
| `auditcore_sampling.sizes` | Sample-size methods for monetary-unit (MUS) and simple random sampling (SRS). |
| `auditcore_sampling.web` | REST contract and routes for sampling user interfaces (extra ``web``). |
<!-- api-overview:end -->

`auditcore_sampling.legacy` reproduziert die Ergebnisse beider
Quellanwendungen exakt; `auditcore_sampling.web` enthält den REST-Vertrag
(`catalogue`, `calculate_size` mit schrittweiser Herleitung, `allocate`,
`select` mit sichtbarem Seed und Eingabe-Fingerabdruck, `export_selection`
als CSV/JSON) für `<flowaudit-sampling>`; Vertrag:
[docs/ui/sampling-rest.md](../../docs/ui/sampling-rest.md).

## Profile und Konfiguration

Methoden (`METHODS`) mit Quelle, zulässigen Konfidenzniveaus und Status:

| Methode | Art | Status | Konfidenzniveaus |
|---|---|---|---|
| `portal.mus_poisson` | MUS, Poisson-Zuverlässigkeitsfaktoren | `RECOMMENDED` (`RECOMMENDED_MUS_METHOD`) | 0,50 / 0,80 / 0,90 / 0,95 / 0,97 / 0,99 |
| `flowstat.mus_z_attribute` | MUS, z-Formel | `SUPERSEDED` (Nachvollzug und Migration, Warnhinweis) | 0,90 / 0,95 / 0,99 |
| `flowstat.srs_normal` | SRS, n = z²p(1-p)/e² mit Endlichkeitskorrektur | `LEGACY_CHARACTERIZED` | 0,90 / 0,95 / 0,99 |
| `portal.srs_normal` | SRS, gleiche Formel | `LEGACY_CHARACTERIZED` | 0,50 / 0,80 / 0,90 / 0,95 / 0,99 |

`mus_size(methode, …)` und `srs_size(methode, …)` verlangen eine
ausdrücklich benannte Methode; `recommended_mus_size` nutzt die entschiedene.
`MUS_DECISION` hält die Entscheidung vom 23.09.2026 mit Referenzfall fest.
`systematic_mus` hat zwei Varianten: `flowstat` (kumulierte Summe über alle
Werte, Mehrfachtreffer bleiben) und `portal` (nur positive Werte, negative
sowie Null-/Fehlwerte werden ausgewiesen, jede Position einmal).
`stratified_allocation` teilt proportional (`ceil(n·Nh/N)`) oder gleich
(`ceil(n/H)`) auf, jeweils höchstens `Nh`.

## Herkunft und Charakterisierung

Extrahiert aus `janpow77/flowstat@d665ac2` und
`janpow77/audit-portal@d8eefa4` (jeweils `sampling_service.py`). Vor der
Übernahme wurden 8 883 Fälle mit numpy 1.26.2, pandas 2.1.3 und scipy 1.11.4
tatsächlich ausgeführt (`tools/capture_sampling_legacy.py`,
`tests/fixtures/sampling_legacy_observed.json.gz`). `legacy` reproduziert alle
Fälle **legacy-exakt** (Umfänge einschließlich Fehlern, systematische und
geschichtete MUS, Aufteilung der geschichteten SRS). Die Zufallsziehung mit
NumPy bleibt beim Consumer. Nach der Umstellung von flowstat ergab ein
erneuter Erfassungslauf 8 883 identische Fälle. Eine fachliche Validierung
der Methoden wurde nicht durchgeführt (`method_validation: NOT_PERFORMED`).
`auditcore_sampling.web` (0.2.0) ist eine eigene Ergänzung ohne neue Methode.

## Bewusste Verhaltensabweichungen

Details: [docs/behavior-changes.md](docs/behavior-changes.md).

- SA-C01: Beide MUS-Formeln sind benannte Methoden; die flowstat-Formel ergibt
  im Referenzfall n = 1 und ist abgelöst (Entscheidung „mus 30“).
- SA-C02: Unbekannte Konfidenzniveaus sind ein Fehler statt still 95 %.
- SA-C03: Eingaben werden validiert (negative Grundgesamtheit, Fehlerrate ≥ 1,
  Wesentlichkeit 0).
- SA-C04: Zufall nur über ein übergebenes `random.Random`.
- SA-C05: Die MUS-Auswahl bietet die Varianten `flowstat` und `portal`,
  keine stille Vereinheitlichung.

## Abhängigkeiten

Python ≥ 3.11 und `auditcore_common==0.1.1` (nur Standardbibliothek;
NumPy-kompatible Summe und Rundung, rahmenwerkfreier Teil der REST-Schicht;
APT `python3-auditcore-common`); keine Abhängigkeit von `auditcore`,
`auditcore_statistics` oder NumPy. Optional
`starlette>=0.26` über `[web]` (FastAPI nur, wenn der Consumer es installiert).

## Sicherheit und Datenschutz

Rechnet nur mit übergebenen Beträgen und Schichtgrößen; keine Speicherung,
kein Netzwerk im Kern. Die Routen von `[web]` validieren Eingaben
(`_validate`) und geben den verwendeten Seed sichtbar zurück;
Authentifizierung und Mandantentrennung liefert die einbindende Anwendung.
Methodenprofile sind charakterisiertes Softwareverhalten, keine validierte
Prüfmethodik; die in den Quellen genannten Leitfäden (EU-KOM Guidance Note
„Sampling for Audit“, ISA 530) sind nur namentlich zitiert.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Die Quellrepositories tragen keine Open-Source-Lizenz; der
Rechteinhaber hat am 22.09.2026 den extrahierten Bibliothekscode freigegeben
(`USER_AUTHORIZED_MIT`), die Quellen selbst werden nicht umlizenziert. Details:
`NOTICE` und `provenance.json`.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
