# Changelog auditcore_compute

## 0.1.0 – 2026-10-03 – erste Fassung (noch nicht veröffentlicht)

Neuimplementierung nach dem Lastenheft „hardwarenah kompilierter Rechenkern“,
als Ergänzung zu `auditcore_sampling` und `auditcore_extrapolation`.

- Engine: `accelerate` (Numba `njit` beim ersten Aufruf, `parallel` nur für
  elementweise Kernel, `fastmath` verboten), `jitable`, `prange`,
  `use_python`, `engine_info`, `engine_report`; Rückfall auf dieselbe
  Python-Funktion ohne Numba, bei `AUDITCORE_COMPUTE_DISABLE_JIT=1` oder bei
  Kompilierfehlern, einmalig über `logging` gemeldet; Numba-Cache mit
  Quell-Fingerabdruck des Pakets, ohne Cache bei schreibgeschütztem Verzeichnis.
- Puffer: `to_buffer` (Listen, ndarray, pandas, polars; ohne Kopie, wo
  möglich; fehlende Werte als Fehler oder Maske), `to_cents`,
  `to_cents_buffer`, `from_cents`, `to_days`.
- `finance`: tagesgenaue Zinsen (act/360, act/365, act/act ISDA, 30E/360,
  30E/360 ISDA) mit stückweisen Sätzen aus einer Satztabelle, einzeln und als
  Batch; Kürzung, Kofinanzierung, Eigenanteil und Quotenprüfung in ganzen Cent.
- `validation`: Soll-/Ist-Abgleich mit Toleranz, feste Schwelle, MAD- und
  IQR-Regel, Doppelförderung über faktorisierte Schlüssel.
- `stats`: kompensierte sequenzielle Summe, gewichteter Mittelwert, Varianz
  (Grundgesamtheit, Häufigkeits- und Zuverlässigkeitsgewichte) und
  Standardabweichung.
- `tools/benchmark.py` für 500.000 synthetische Buchungszeilen.

Nachtrag vor der Veröffentlichung (vektorisierte Umwandlung, Ergebnisse unverändert):

- `to_cents_buffer` rechnet float- und Ganzzahl-Arrays bzw. -Serien
  vektorisiert und bitgleich zu `to_cents` je Wert (Hypothesis-Abgleich über
  ganze Wertebereiche, Grenzfälle 2,675, 1,005, 0,125, negative Beträge, bis
  10 Mrd. €). Nur Werte nahe einem halben Cent und Beträge ab 10¹¹ € gehen über
  `Decimal(str(x))`; Fehler (fehlender Wert, nicht endlich, Überlauf) wie bisher.
  500.000 Werte: 14 ms statt 525 ms.
- `factorize` faktorisiert bool-, Ganzzahl- und float-Arrays bzw. -Serien
  vektorisiert (gleiche Codes und Schlüssel in Erstauftritts-Reihenfolge);
  Texte bleiben im Elementpfad.
- `validation.first_occurrence_codes(codes, count)` nummeriert Gruppencodes
  nach ihrem ersten Auftreten um (für Verbraucher, die fehlende Schlüssel als
  eigene Gruppe führen).
