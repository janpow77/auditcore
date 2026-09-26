# auditcore_dummygenerator

## Zweck

Frameworkunabhängiger Generator für synthetische Testdaten: einzelne Felder (Namen, Adressen, Kennungen, Beträge, Datumswerte) und ganze Zeilen mit festem Seed und Bezugsdatum.

Für Anwendungen und Bibliotheken, die reproduzierbare Testdaten brauchen –
etwa `auditcore_invoicegenerator` oder der FlowAudit-Testdatengenerator. HTTP,
Dateiexporte, Oberfläche und Authentifizierung bleiben beim Consumer. Die
erzeugten IBAN, BIC und USt-IdNr. sind synthetische Zeichenketten ohne
Prüfziffern- oder Gültigkeitszusage.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install auditcore_dummygenerator \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (zuletzt veröffentlicht: 0.1.3 im
Release v0.4.2; weitere Versionen und Hashes unter
`https://janpow77.github.io/auditcore/simple/auditcore-dummygenerator/`):

```text
auditcore_dummygenerator @ https://github.com/janpow77/auditcore/releases/download/v0.4.2/auditcore_dummygenerator-0.1.3-py3-none-any.whl#sha256=854afcdf7a14765ddca2acb33226099c223e464c244e6fc05969b3223b8fd457
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-dummygenerator
```

Extras: `[parallel]` – joblib als alternatives Backend für parallele
Zeilenerzeugung (ohne Extra: `ProcessPoolExecutor`); `[dev]` – Test- und
Prüfwerkzeuge.

## Schnellstart

```python
from datetime import date

from auditcore_dummygenerator import TestDataGenerator

request = {
    "rows": 3,
    "countries": "DE",
    "fields": [
        {"name": "id", "type": "auto_increment", "params": {"start": 10, "step": 3}},
        {"name": "name", "type": "first_name"},
        {"name": "amount", "type": "amount_eur", "params": {"min": 100, "max": 1000}},
    ],
}
generator = TestDataGenerator(seed=42, base_date=date(2024, 1, 1), max_workers=1)
rows = generator.generate_rows(request)

assert [row["id"] for row in rows] == [10, 13, 16]
assert all(100 <= row["amount"] <= 1000 for row in rows)

# Neue Instanz mit gleichem Seed: dieselben Zeilen.
again = TestDataGenerator(seed=42, base_date=date(2024, 1, 1), max_workers=1)
assert again.generate_rows(request) == rows
```

```pycon
>>> rows[0]
{'id': 10, 'name': 'Max', 'amount': 767.4}
```

## API-Überblick

`TestDataGenerator(seed=None, *, base_date=None, max_workers=None,
use_joblib=None)` enthält alle Methoden des Originals: Grunddaten
(`generate_first_name`, `generate_city` → `(Stadt, PLZ)`, `generate_phone` …),
synthetische Kennungen (`generate_iban`, `generate_bic`, `generate_ustid`,
`generate_invoice_no`), Werte (`generate_date_range`, `generate_amount`,
`generate_weighted_choice` …), `generate_field`, `apply_deviation`,
`generate_rows` und die beiden parallelen Varianten.

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_dummygenerator.__all__` (6):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `JOBLIB_AVAILABLE` | Konstante | – | `generator` |
| `BatchGenerationError` | Ausnahme | A worker failed or returned fewer rows; no partial success is returned. | `rows` |
| `TestDataGenerator` | Klasse | Generate synthetic rows; seeded output retains the recorded legacy rules. | `generator` |
| `get_optimal_workers` | Funktion | Ermittelt die optimale Anzahl an Worker-Prozessen. | `rows` |
| `list_profiles` | Funktion | Read independently owned metadata; reject altered content or implementation hashes. | `profiles` |
| `profile_reference` | Funktion | Return an exact ID/version/hash reference for a caller-owned run manifest. | `profiles` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_dummygenerator.generator` | Seeded synthetic rows extracted from the recorded FlowAudit implementation. |
| `auditcore_dummygenerator.profiles` | Version and fingerprint references for the shipped synthetic-data profiles. |
| `auditcore_dummygenerator.rows` | Row assembly and ordered worker batches for :class:`TestDataGenerator`. |
<!-- api-overview:end -->

## Profile und Konfiguration

`profiles.json` beschreibt 27 Profile (Feldregeln, Abweichungsszenarien,
DE-/AT-Kataloge) mit stabiler ID, Version 0.1.0, Status **Draft**, Herkunft
und Inhaltshash, der an die Bytes von `generator.py` gebunden ist.
`list_profiles()` und `profile_reference(artifact_id)` liefern diese
Referenzen; eine menschliche Releasefreigabe liegt nicht vor
(`NOT_GRANTED`). Regeln: [Profilversionierung](docs/profile-versioning.md).

Laufparameter:

- `seed` – eigene `random.Random`-Instanz; neue Instanz plus gleicher Seed
  startet dieselbe Sequenz, wiederholte Aufrufe schreiten fort.
- `base_date` – Bezugsdatum für `date_after` ohne Referenzfeld (sonst wie
  bisher das lokale Tagesdatum).
- `max_workers` – ab 1 000 Zeilen wählt `generate_rows` den parallelen Weg;
  `max_workers=1` erzwingt sequenzielle Erzeugung. Parallelbatches nutzen
  `seed + batch_index * 1000`; parallele und sequenzielle Ausgaben sind
  nicht identisch.
- `use_joblib` – `False` wählt `ProcessPoolExecutor`, `True` verlangt das
  Extra `[parallel]`, `None` entscheidet nach Verfügbarkeit.

Länderwert `AT` nutzt die österreichischen Kataloge, alle anderen legacygemäß
DE. Für ein zusammengehöriges Stadt/PLZ-Paar `generate_city` verwenden.

## Herkunft und Charakterisierung

Übernommen aus `janpow77/flowaudit_testdatengenerator_frontend`,
`backend/generator.py` (Commit `05bc5ac5`, Blob `a9204a08`). Vor der Übernahme
wurden 58 Fälle am Original beobachtet (`tests/fixtures/legacy_observed.json`,
erneut ausgeführt am 22.09.2026 mit `tools/capture_legacy.py`, das nie das neue
Paket importiert). Die fachliche Datenerzeugung ist **legacy-exakt**: gleicher
Seed, gleiche Feld- und Ziehungsreihenfolge, gleiche Ausnahmen, `float`/`round`
bei Beträgen, unbekannte Feldtypen liefern `""`. Die Refaktorierung 0.1.1 wurde
zusätzlich mit 4 500 Zufallsanfragen gegen die alte Implementierung verglichen.

## Bewusste Verhaltensabweichungen

Nur technische Korrekturen der Parallelverarbeitung, keine Änderung der
Datenerzeugung; die Originalbeobachtungen stehen in
`tests/fixtures/legacy_technical_defects.json`:

- Worker erzeugen ihren Batch nur noch sequenziell (vorher rief ein Worker den
  Parallel-Dispatcher erneut auf).
- Worker arbeiten auf einer tiefen Kopie des Requests (vorher wurden
  verschachtelte Auto-Increment-Parameter verändert).
- Jeder Backendfehler und jedes unvollständige Gesamtergebnis löst
  `BatchGenerationError` mit Ursache aus (vorher konnte still eine leere Liste
  entstehen).
- Der Prozesspool startet mit `spawn` statt `fork`; eigenständige Skripte
  müssen parallele Aufrufe unter `if __name__ == "__main__":` ausführen.
- Workergrenzen kleiner eins sind ein `ValueError`.

Weiterhin unverändert: `apply_deviation` verändert den übergebenen Zeilen-Dict
und gibt ihn zurück.

## Abhängigkeiten

Python ≥ 3.11, zur Laufzeit nur die Standardbibliothek. Optional `joblib>=1.3.2`
über `[parallel]`. Keine Abhängigkeit von der Plattform `auditcore`, FastAPI,
Datenbanken oder anderen Fachpaketen.

## Sicherheit und Datenschutz

Erzeugt ausschließlich synthetische Daten; es werden keine personenbezogenen
Echtdaten gelesen oder geschrieben, kein Netzwerk und keine Dateien genutzt.
Namen und Adressen stammen aus festen Katalogen und können zufällig realen
Personen gleichen. Kennungen und Beträge sind nicht für verbindliche
fachliche oder steuerrechtliche Entscheidungen bestimmt. Der Paketkontext
`auditcore-context.json` gilt nur für die Bibliothek, nicht für Consumer.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Der Rechteinhaber hat den übernommenen Generator am 22.09.2026
ausdrücklich unter MIT freigegeben (`USER_AUTHORIZED_MIT`); das ursprüngliche
private Repository hatte keine erkannte Lizenz, daraus folgt keine pauschale
Umlizenzierung. Quellumfang und Erklärung: `NOTICE` und `provenance.json`.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
