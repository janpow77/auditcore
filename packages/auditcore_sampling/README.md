# auditcore_sampling

Stichprobenumfänge, systematische MUS-Auswahl, Zufallsauswahl und Schichtung
mit ausdrücklich benannten Methoden. Nur Standardbibliothek; keine
Abhängigkeit von `auditcore`, `auditcore_statistics` oder NumPy.

```python
import random
from auditcore_sampling import draw_start, mus_size, systematic_mus

plan = mus_size("portal.mus_poisson", population_value=515_000.0, materiality=50_000.0,
                expected_error_rate=0.005, confidence_level=0.95)
start = draw_start(random.Random(42), plan.interval)          # reproduzierbar
auswahl = systematic_mus(betraege, sample_size=plan.sample_size,
                         interval=plan.interval, start=start, variant="portal")
```

Es gibt keine Standardmethode. `flowstat.mus_z_attribute` (Formel aus
flowstat) und `portal.mus_poisson` (Poisson-Faktoren aus audit-portal) liefern
stark unterschiedliche Umfänge; die Wahl ist eine fachliche Entscheidung
(HUMAN_DECISION_REQUIRED). Unbekannte Konfidenzniveaus werden abgewiesen,
Zufall kommt nur aus einem übergebenen `random.Random`.

`auditcore_sampling.legacy` reproduziert die charakterisierten Ergebnisse
beider Quellanwendungen exakt. Details: [docs/behavior-changes.md](docs/behavior-changes.md).
Herkunft und MIT-Freigabe: `NOTICE`, `provenance.json`. Debian: `python3-auditcore-sampling`.
