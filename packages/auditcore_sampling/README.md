# auditcore_sampling

Stichprobenumfänge, systematische MUS-Auswahl, Zufallsauswahl und Schichtung
mit ausdrücklich benannten Methoden. Nur Standardbibliothek; keine
Abhängigkeit von `auditcore`, `auditcore_statistics` oder NumPy.

```python
import random
from auditcore_sampling import draw_start, recommended_mus_size, systematic_mus

plan = recommended_mus_size(population_value=475_478.94, materiality=50_000.0,
                            expected_error_rate=0.005, confidence_level=0.95)  # n = 30
start = draw_start(random.Random(42), plan.interval)          # reproduzierbar
auswahl = systematic_mus(betraege, sample_size=plan.sample_size,
                         interval=plan.interval, start=start, variant="portal")
```

**Entscheidung vom 23.09.2026 (Nutzer: „mus 30“):** Maßgeblich ist
`portal.mus_poisson` (Poisson-Zuverlässigkeitsfaktoren), abrufbar als
`recommended_mus_size` bzw. `RECOMMENDED_MUS_METHOD`. Die flowstat-Formel
`flowstat.mus_z_attribute` bleibt als benannte, fachlich abgelöste
Legacy-Methode (Status `SUPERSEDED`) für Nachvollzug und Migration erhalten.
`mus_size(methode, …)` verlangt weiterhin eine ausdrücklich benannte Methode. Unbekannte Konfidenzniveaus werden abgewiesen,
Zufall kommt nur aus einem übergebenen `random.Random`.

`auditcore_sampling.legacy` reproduziert die charakterisierten Ergebnisse
beider Quellanwendungen exakt. Details: [docs/behavior-changes.md](docs/behavior-changes.md).
Herkunft und MIT-Freigabe: `NOTICE`, `provenance.json`. Debian: `python3-auditcore-sampling`.

**Oberflächen (ab 0.2.0):** `auditcore_sampling.web` stellt den REST-Vertrag
für `<flowaudit-sampling>` bereit (Methodenprofile, Umfang mit Herleitung,
Allokation, reproduzierbare Auswahl mit Seed, CSV/JSON-Export). Starlette-Routen
mit `pip install auditcore_sampling[web]`, FastAPI-Router zusätzlich mit
FastAPI. Vertrag: `docs/ui/sampling-rest.md` im Repository.
