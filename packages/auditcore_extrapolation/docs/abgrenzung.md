# Abgrenzung zu bestehenden Anwendungen

Die Bibliothek ist neu geschrieben; es wurde kein Code übernommen und kein
Anwendungsverhalten charakterisiert.

- **audit_designer, Modul flowstat** (`sampling_service.run_error_projection`,
  `run_precision_calculation`): rechnet mit Endlichkeitskorrektur und für MUS mit
  der mittleren Fehlerquote × Buchwert; beides weicht von den Formeln des
  Leitfadens ab (6.1.1.4, 6.3.1.4). Eine Umstellung auf diese Bibliothek ändert
  daher Ergebnisse und braucht eine fachliche Entscheidung.
- **audit-portal** (`rer_service.compute_rer`): setzt dieselbe Vorlage Annex 3
  mit `Decimal` um. Die Zeilen A–M sind gleich definiert; die Bibliothek prüft
  zusätzlich die Wesentlichkeitsschwelle (≤ 2 %) und verlangt nicht negative
  Beträge für E1, E2 und H.
- **auditcore_sampling**: bleibt zuständig für Stichprobenumfang und Auswahl.
  Die KOM-Formeln für den Umfang (z. B. n = (z × BV × σ_r/(TE − AE))² oder
  n = BV × RF/(TE − AE × EF)) sind dort noch nicht enthalten.

## Abdeckung des Leitfadens EGESIF_16-0014-01 (Fassung vom 20.01.2017)

Geprüft am Inhaltsverzeichnis der Fassung vom 20.01.2017 (275 Seiten). Die
Bibliothek deckt die **Auswertung** ab. Stichprobenumfang und Auswahl
(Abschnitte *.2 „Sample size“ und *.3 „Sample selection“, 7.1, 7.2.2 Umfang,
7.3.2.1 Neuplanung, 7.6.2, 7.9.2) sind Planung und gehören zu
`auditcore_sampling` (Modul `auditcore_sampling.guidance`).

| Abschnitt | Inhalt | Stand | Umsetzung |
|---|---|---|---|
| 3.2.1 | Konfidenzniveau nach Systembewertung (Tabelle 1) | abgedeckt | `SYSTEM_ASSESSMENT_LEVELS`, `system_confidence_level` (für 7.7) |
| 3.2.2 | Gruppe von Programmen: ein Zusicherungsniveau | abgedeckt (Hinweis) | anspruchsvollste Kategorie wählen; siehe 7.8 |
| 4.6 | Negative Stichprobeneinheiten | abgedeckt | `split_population` (Varianten 1–3, Abstimmung netto/positiv/negativ), `review_negative_units`; REST `/negative-units`. Einheiten mit negativem Buchwert bleiben in der Hochrechnung unzulässig (gesonderte Grundgesamtheit, keine Fehlerquote) |
| 4.9–4.14 | Wesentlichkeit, TE, Obergrenze, Ergebnis, Fehlerquoten | abgedeckt | `evaluate`, `conclude` |
| 6.1.1, 6.1.2 | SRS, geschichtet | abgedeckt | `srs.*` |
| 6.1.3 | SRS, zwei Zeiträume | abgedeckt | `project_periods` |
| 6.2.1, 6.2.2 | Differenzenschätzung, geschichtet | abgedeckt | `difference` |
| 6.2.3 | Differenzenschätzung, zwei Zeiträume | abgedeckt | `project_periods` |
| 6.3.1, 6.3.2 | MUS, geschichtet | abgedeckt | `mus.standard` |
| 6.3.3, 6.3.4 | MUS zwei Zeiträume, auch geschichtet | abgedeckt | `project_periods` |
| 6.3.5 | MUS konservativ | abgedeckt (ein Zeitraum) | `mus.conservative`; für mehrere Zeiträume beschreibt der Leitfaden kein Verfahren |
| 6.4.1–6.4.8 | nicht-statistisch, kleine Grundgesamtheiten (Art. 79 Abs. 2 CPR: unter 300 Einheiten, Abdeckung) | abgedeckt | `nonstatistical.*`, Abdeckungsprüfung |
| 6.4.9 | nicht-statistisch, zwei Zeiträume | abgedeckt | `project_periods` mit `population_units` |
| 6.4.10 | Teilstichproben bei nicht-statistischen Verfahren | abgedeckt | `project_subsample` (Hinweis unter 30 Teileinheiten / 10 % Deckung) |
| 6.5 | ETC-Programme: Stichprobeneinheit, zwei- und dreistufig, Lead-Partner + Partner-Stichprobe | abgedeckt | `project_subsample` (verschachtelt für drei Stufen), UI mit Teilschichten und dritter Stufe; Wahl der Stichprobeneinheit ist fachliche Entscheidung |
| 7.1 | Erwarteter Fehler | Planung | `auditcore_sampling` |
| 7.2.1 | Ergänzende (risikobasierte) Stichprobe | nicht rechnerisch | getrennt auswerten, nicht in die Fehlerquote (7.2.1) – Auswertung als eigene Grundgesamtheit möglich |
| 7.2.2 | Zusätzliche Stichprobe bei nicht schlüssigem Ergebnis | abgedeckt (Auswertung) | vereinigte Stichprobe mit `assess`; Umfang: Planung |
| 7.3 | Stichprobe im Jahresverlauf, mehrere Zeiträume | abgedeckt | `project_periods` (beliebig viele Zeiträume, Anhang 2 für drei/vier) |
| 7.4 | Methodenwechsel | nicht rechnerisch | – |
| 7.5 | Fehlerquoten EER = EE/BV, SER = SE/BV | abgedeckt | `rate`, `upper_limit_rate` |
| 7.6 | Zweistufige Stichprobe | abgedeckt | `project_subsample`, `unit_from_subsample`; Präzision wie einstufig (7.6.4) |
| 7.7 | Neuberechnung des Konfidenzniveaus | abgedeckt | `recalculate_confidence` (nicht für den konservativen Ansatz) |
| 7.8 | Gruppen von Programmen und Mehrfonds-Programme | abgedeckt | `assess_groups` (top-down mit Auswertung je Programm), über mehrere Zeiträume `assess_groups_over_periods` (6.3.4 + 7.8) |
| 7.9 | Merkmalsstichprobe für Systemprüfungen | abgedeckt (Auswertung) | `evaluate_attributes`; Discovery/Stop-or-go (7.9.6) mit exakter Binomialgrenze `evaluate_discovery`, `evaluate_stop_or_go` (Methodenwahl, der Leitfaden nennt keine Formel); REST `/attributes`, UI `AttributeSampling` |
| 7.10 | Verhältnismäßige Kontrolle (Art. 148 VO 1303/2013; 2021–2027 Art. 80 VO 2021/1060): Ersetzen/Ausschluss von Einheiten | abgedeckt | `excluded_*` je Schicht, Erweiterung mit BV- bzw. N-Verhältnis je Stichproben- und Hochwertschicht (`extension_factor`); geschichtete SRS mit Ausschluss in mehreren Schichten nicht beschrieben (abgelehnt) |
| Anhang 1 | Systemische Fehler | abgedeckt | Fehlerklassen, `mus.ratio` |
| Anhang 2 | Drei und vier Zeiträume | abgedeckt | `project_periods` |
| Anhang 3, 4 | Faktoren, z-Werte | abgedeckt | `KOM_TABLES` |

Kombinationen: Zeiträume und Gruppen sind kombinierbar (Programme als Schichten
je Zeitraum, 6.3.4); Teilstichproben und Ausschlüsse lassen sich mit jedem
Aufbau verbinden.
