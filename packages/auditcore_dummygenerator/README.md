# auditcore_dummygenerator

Installierbarer, frameworkunabhängiger Generator für synthetische Testdaten.
Version 0.1.0 wird im gemeinsamen auditcore-Repository gepflegt. Das Paket
benötigt zur Laufzeit keine auditcore-Plattform, FastAPI, Datenbank oder UI.

```bash
python -m pip install auditcore_dummygenerator==0.1.0
# Optionaler paralleler Backend:
python -m pip install 'auditcore_dummygenerator[parallel]==0.1.0'
```

Der Rechteberechtigte hat den hier übernommenen Generator am 22.09.2026
explizit unter MIT freigegeben (`USER_AUTHORIZED_MIT`). `LICENSE`, `NOTICE`
und `provenance.json` dokumentieren den genauen Quellumfang und die Erklärung.
Das ursprüngliche private Repository hatte historisch keine erkannte Lizenz;
daraus wird keine pauschale Umlizenzierung des gesamten Repositories abgeleitet.
Eine Paket-/APT-Installation ersetzt weiterhin keine Betriebsfreigabe der
Anwendung. GitHub-Contributors der Quelle waren `janpow77` und `claude`.

## API und Beispiel

```python
from datetime import date
from auditcore_dummygenerator import TestDataGenerator

generator = TestDataGenerator(seed=42, base_date=date(2024, 1, 1), max_workers=1)
rows = generator.generate_rows(
    {
        "rows": 3,
        "countries": "DE",
        "fields": [
            {"name": "id", "type": "auto_increment", "params": {"start": 10, "step": 3}},
            {"name": "name", "type": "first_name"},
            {"name": "amount", "type": "amount_eur", "params": {"min": 100, "max": 1000}},
        ],
    }
)
```

`TestDataGenerator(seed=None, *, base_date=None, max_workers=None,
use_joblib=None)` erhält alle bestehenden Methoden des Originals:

- Grunddaten: `generate_first_name(country)`, `generate_last_name(country)`,
  `generate_street(country)`, `generate_house_number()`,
  `generate_city(country)` → `(Stadt, PLZ)`, `generate_postal_code(country)`,
  `generate_company()`, `generate_phone(country)`;
- synthetische Kennungen: `generate_iban(country)`, `generate_bic(country)`,
  `generate_ustid(country)`, `generate_invoice_no(pattern="numeric_8_10")`;
- Werte: `generate_date_range(start, end)`,
  `generate_date_after(ref_date, min_days, max_days)`,
  `generate_amount(min_val, max_val, decimals=2)`,
  `generate_amount_relative(ref_amount, min_factor, max_factor)`,
  `generate_purpose_text(min_words=2, max_words=8)`,
  `generate_weighted_choice(items)`, `generate_number(min_val=0, max_val=100)`,
  `generate_boolean()`;
- `generate_field(field_type, params, country, row_data)`,
  `apply_deviation(row, scenario, rate)`, `generate_rows(request)`,
  `generate_rows_parallel(request, n_workers=None)`,
  `generate_rows_parallel_joblib(request, n_jobs=-1)`.

Außerdem exportiert: `JOBLIB_AVAILABLE`, `get_optimal_workers()`,
`BatchGenerationError`, `list_profiles()` und `profile_reference(artifact_id)`.
Die letzten beiden Funktionen liefern geprüfte Versions-/Hashreferenzen für
27 bestehende Profile; siehe [Profilversionierung](docs/profile-versioning.md). Der bestehende Anwendungsimport aller drei alten
Symbole kann auf `from auditcore_dummygenerator import ...` umgestellt werden.
HTTP, Dateiexporte, UI und Authentifizierung bleiben im Consumer.

## Reproduzierbarkeit und unveränderte Legacy-Regeln

Die 58 Originalfälle in `tests/fixtures/legacy_observed.json` wurden vor den
Änderungen beobachtet und erneut am verifizierten Git-Blob ausgeführt.
`tools/capture_legacy.py ORIGINAL_GENERATOR OUTPUT_JSON` prüft den Blob und
nimmt echte Ergebnisse/Ausnahmen auf; es importiert niemals das neue Paket.

Ein Seed reproduziert dieselbe Methoden-/Feldreihenfolge, Länderwahl und
Batchkonfiguration. Der Generator verwendet eine eigene `random.Random`-
Instanz. Neue Instanz plus gleicher Seed startet dieselbe Sequenz; wiederholte
Aufrufe auf derselben Instanz schreiten fort. Parallelbatches verwenden wie
bisher `seed + batch_index * 1000`; parallele und sequenzielle Ausgaben sind
nicht identisch. Ab 1000 Zeilen wählt `generate_rows` den parallelen Weg;
`max_workers=1` erzwingt effektiv sequenzielle Erzeugung. Bei fehlendem Seed
wählt der Parallelpfad weiterhin einen zufälligen Basiswert.

Fehlt bei `date_after` das referenzierte Feld, gilt `base_date` oder wie bisher
das aktuelle lokale Datum. Für stabile Ergebnisse Datum und Workerzahl setzen.
Die übrigen Datumsintervalle stammen aus dem Request bzw. den Legacy-Defaults.
`MAX_WORKERS` begrenzt die automatische Workerzahl. `use_joblib=False` wählt
ProcessPoolExecutor; `True` erfordert das optionale Extra, `None` entscheidet
nach Verfügbarkeit. CPU-Zahl oder Backend nicht still als Teil eines Seeds
interpretieren.

AT verwendet die österreichischen Kataloge, andere Länderwerte legacygemäß
DE. Stadt/PLZ-Einzelaufrufe sind separate Ziehungen; für ein zusammengehöriges
Paar `generate_city` verwenden. IBAN, BIC und USt-ID sind synthetische Strings:
keine Prüfziffer-, Register-, Zahlungs- oder Rechtsgültigkeitszusage. Beträge
verwenden unverändert `float`/`round`. Der Generator dient Testdaten, nicht
verbindlichen fachlichen oder steuerrechtlichen Entscheidungen.

Unbekannte Feldtypen liefern wie zuvor `""`, negative Zeilenzahlen leere
Ergebnisse, leere gewichtete Listen `""`; ungültige Intervalle erzeugen die
beobachteten Ausnahmen. `apply_deviation` verändert absichtlich den übergebenen
Row-Dict und liefert ihn zurück. Requests werden bei der Zeilenerzeugung
nicht verändert. Fachliche Abweichungsszenarien bleiben unveränderte Profile.

## Explizite technische Korrekturen

Die Originalbeobachtungen stehen in `tests/fixtures/legacy_technical_defects.json`:

- Ein Worker rief den automatischen Parallel-Dispatcher erneut auf; jetzt
  erzeugt jeder Worker seinen Batch ausschließlich sequenziell.
- Der Worker veränderte verschachtelte Auto-Increment-Parameter des Requests;
  jetzt arbeitet er auf einer tiefen Kopie.
- Fehler in ProcessPool-Workern konnten bei 200 angefragten Zeilen still eine
  leere Ergebnisliste liefern. Jetzt löst jeder Backendfehler
  `BatchGenerationError` mit ursprünglicher Ursache aus; unvollständige
  Gesamtergebnisse sind ebenfalls Fehler.
- Der Prozesspool startet mit `spawn` statt `fork`, damit Aufrufe aus
  mehrthreadigen Anwendungen keinen geerbten Threadzustand verwenden.
  Eigenständige Skripte müssen parallele Aufrufe unter
  `if __name__ == "__main__":` ausführen.
- Workergrenzen kleiner eins sind explizite `ValueError`; die alte unklare
  Behandlung wird nicht als gültiger Vertrag übernommen.

Diese Korrekturen und der zusätzliche optionale Datums-/Backendvertrag sind
gezielt getestet. Sie enthalten keine Änderung der fachlichen Datenerzeugung.

## Lokale Prüfung

```bash
python -m pip install -e '.[dev,parallel]'
pytest
ruff check .
mypy src
python -m build
python -I tests/installed_smoke.py  # nach Installation des Wheels, nicht editable
```

`auditcore-context.json` gilt für die reine Bibliothek mit synthetischen Testdaten;
es wird nicht auf Consumeranwendungen übertragen. Policy-Nachweise werden
an das tatsächliche Artefakt gebunden. Ungeklärte Nachweise/Freigaben bleiben
`REVIEW_REQUIRED`, nicht PASS. Sicherheits-/Betriebsprüfung einer migrierten
FastAPI-Anwendung ist eine gesonderte Aufgabe.
